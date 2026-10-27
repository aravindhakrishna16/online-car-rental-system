import unittest
from app import create_app
from database import db
from models.user import User, Customer, CarOwner, Admin, UserFactory

class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_user_password_hashing(self):
        """Test OOAD User password hashing and verification."""
        user = Customer(name="Test User", email="test@example.com")
        user.set_password("Secret123")
        self.assertNotEqual(user.password_hash, "Secret123")
        self.assertTrue(user.check_password("Secret123"))
        self.assertFalse(user.check_password("WrongPassword"))

    def test_user_factory_polymorphism(self):
        """Test UserFactory returns correct subclass with specific permissions."""
        cust = UserFactory.create_user({"name": "C", "email": "c@test.com", "role": "customer"})
        self.assertIsInstance(cust, Customer)
        self.assertTrue(cust.can_book_cars())
        self.assertFalse(cust.can_manage_cars())
        self.assertFalse(cust.is_admin_user())

        owner = UserFactory.create_user({"name": "O", "email": "o@test.com", "role": "owner"})
        self.assertIsInstance(owner, CarOwner)
        self.assertFalse(owner.can_book_cars())
        self.assertTrue(owner.can_manage_cars())
        self.assertFalse(owner.is_admin_user())

        admin = UserFactory.create_user({"name": "A", "email": "a@test.com", "role": "admin"})
        self.assertIsInstance(admin, Admin)
        self.assertTrue(admin.is_admin_user())

    def test_successful_login(self):
        """Test login with demo customer credentials."""
        response = self.client.post("/login", data={
            "email": "arjun.renter@driveease.com",
            "password": "customer123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Arjun", response.data)

    def test_invalid_login(self):
        """Test login with wrong credentials fails with error message."""
        response = self.client.post("/login", data={
            "email": "arjun.renter@driveease.com",
            "password": "WrongPassword999"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid email or password", response.data)

    def test_duplicate_registration_prevented(self):
        """Test system rejects duplicate registration with existing email."""
        response = self.client.post("/register", data={
            "name": "Arjun Duplicate",
            "email": "arjun.renter@driveease.com",  # Already exists in seed
            "phone": "9998887776",
            "role": "customer",
            "password": "password123",
            "confirm_password": "password123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"already exists", response.data)

if __name__ == "__main__":
    unittest.main()
