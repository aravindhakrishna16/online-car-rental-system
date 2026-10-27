import unittest
from app import create_app
from database import db
from services.car_service import CarService

class TestAccessControl(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_unauthenticated_protected_routes(self):
        """Unauthenticated requests to protected endpoints must redirect to login."""
        protected_urls = ["/customer/dashboard", "/owner/dashboard", "/admin/dashboard", "/owner/add-car"]
        for url in protected_urls:
            response = self.client.get(url, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.location)

    def test_customer_cannot_access_owner_or_admin(self):
        """Customers must be blocked from host and admin dashboards."""
        # Log in as Customer
        self.client.post("/login", data={
            "email": "arjun.renter@driveease.com",
            "password": "customer123"
        })

        # Try accessing owner dashboard
        resp_owner = self.client.get("/owner/dashboard", follow_redirects=True)
        self.assertIn(b"Access denied", resp_owner.data)

        # Try accessing admin dashboard
        resp_admin = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertIn(b"Access denied", resp_admin.data)

    def test_owner_cannot_access_admin(self):
        """Car Owners must be blocked from admin governance."""
        # Log in as Car Owner
        self.client.post("/login", data={
            "email": "rahul.host@driveease.com",
            "password": "owner123"
        })

        resp = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertIn(b"Access denied", resp.data)

    def test_owner_cannot_modify_other_owner_car(self):
        """Host cannot modify or delete vehicles listed by another host."""
        # Rahul (Owner 1) tries to update Priya's car (Owner 2)
        priya = db.fetch_one("SELECT id FROM users WHERE email = 'priya.fleet@driveease.com'")
        priya_car = db.fetch_one("SELECT id, name FROM cars WHERE owner_id = %s LIMIT 1", (priya["id"],))

        rahul = db.fetch_one("SELECT id FROM users WHERE email = 'rahul.host@driveease.com'")

        # Rahul attempts update on Priya's car
        update_result = CarService.update_car(priya_car["id"], rahul["id"], {"name": "Hacked Car"})
        self.assertFalse(update_result)

        # Rahul attempts delete on Priya's car
        delete_result = CarService.delete_car(priya_car["id"], rahul["id"], is_admin=False)
        self.assertFalse(delete_result)

    def test_admin_can_approve_car_listing(self):
        """Admin can approve pending vehicles."""
        pending_car = db.fetch_one("SELECT id FROM cars WHERE approval_status = 'pending' LIMIT 1")
        if pending_car:
            success = CarService.admin_verify_car(pending_car["id"], "approved")
            self.assertTrue(success)
            car = CarService.get_car_by_id(pending_car["id"])
            self.assertEqual(car.approval_status, "approved")

if __name__ == "__main__":
    unittest.main()
