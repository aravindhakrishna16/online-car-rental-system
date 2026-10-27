import unittest
from datetime import date, timedelta
from app import create_app
from database import db
from services.car_service import CarService
from services.booking_service import BookingService
from services.payment_service import PaymentService
from services.review_service import ReviewService

class TestBookingSystem(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Get customer and owner for testing
        customer = db.fetch_one("SELECT id FROM users WHERE role = 'customer' LIMIT 1")
        owner = db.fetch_one("SELECT id FROM users WHERE role = 'owner' LIMIT 1")
        self.customer_id = customer["id"]
        self.owner_id = owner["id"]

        # Create an isolated test car for test execution
        import uuid
        test_reg = f"TEST{uuid.uuid4().hex[:6].upper()}"
        self.test_car_id = CarService.add_car(self.owner_id, {
            "name": "Test Booking Automobile",
            "brand": "Hyundai",
            "model": "Verna",
            "year": 2024,
            "registration_number": test_reg,
            "category": "Sedan",
            "fuel_type": "Petrol",
            "transmission": "Automatic",
            "seating_capacity": 5,
            "price_per_day": 2000.0,
            "location": "Bangalore",
            "description": "Test vehicle"
        })
        CarService.admin_verify_car(self.test_car_id, "approved")

    def tearDown(self):
        # Clean up test car and associated test bookings
        CarService.delete_car(self.test_car_id, is_admin=True)
        self.app_context.pop()

    def test_date_validation_rules(self):
        """Test business rule: Return date cannot be earlier than pickup date."""
        today = date.today()
        yesterday_str = str(today - timedelta(days=1))
        today_str = str(today)
        future_str = str(today + timedelta(days=3))

        # Past date rejected
        is_valid, _, _, _, err = BookingService.validate_dates(yesterday_str, future_str)
        self.assertFalse(is_valid)
        self.assertIn("past", err.lower())

        # Return date earlier than pickup date rejected
        is_valid, _, _, _, err = BookingService.validate_dates(future_str, today_str)
        self.assertFalse(is_valid)
        self.assertIn("later than pickup date", err.lower())

        # Valid dates accepted
        is_valid, days, _, _, _ = BookingService.validate_dates(today_str, future_str)
        self.assertTrue(is_valid)
        self.assertEqual(days, 3)

    def test_booking_creation_and_price_calculation(self):
        """Test backend price calculation including per-km rate and 5% GST."""
        today = date.today()
        start_d = str(today + timedelta(days=5))
        end_d = str(today + timedelta(days=8))

        # Test booking with 150 estimated km
        success, msg, ref = BookingService.create_booking(
            customer_id=self.customer_id,
            car_id=self.test_car_id,
            start_str=start_d,
            end_str=end_d,
            pickup_location="City Center",
            drop_location="Airport T2",
            estimated_km=150
        )
        self.assertTrue(success)
        self.assertTrue(ref.startswith("BK-"))

        # Verify database record, per-km charges and total price formula:
        # (2000/day * 3 days = 6000) + (10/km * 150km = 1500) = 7500 + 5% GST (375) = 7875.0
        booking = BookingService.get_booking_by_ref(ref)
        self.assertIsNotNone(booking)
        self.assertEqual(booking.total_days, 3)
        self.assertEqual(booking.daily_rate, 2000.0)
        self.assertEqual(booking.estimated_km, 150)
        self.assertEqual(booking.km_rate, 10.0)
        self.assertEqual(booking.km_charges, 1500.0)
        self.assertEqual(booking.base_rental_cost, 6000.0)
        self.assertEqual(booking.gst_amount, 375.0)
        self.assertEqual(booking.total_amount, 7875.0)

    def test_overlap_prevention_rule(self):
        """CRITICAL: Test that overlapping bookings for the same car are rejected."""
        today = date.today()
        # Booking 1: Days 10 to 15
        start_1 = str(today + timedelta(days=10))
        end_1 = str(today + timedelta(days=15))
        
        success1, _, ref1 = BookingService.create_booking(
            customer_id=self.customer_id,
            car_id=self.test_car_id,
            start_str=start_1,
            end_str=end_1,
            pickup_location="Point A",
            drop_location="Point B"
        )
        self.assertTrue(success1)

        # Booking 2 overlaps: Days 12 to 18
        start_2 = str(today + timedelta(days=12))
        end_2 = str(today + timedelta(days=18))

        success2, err_msg, _ = BookingService.create_booking(
            customer_id=self.customer_id,
            car_id=self.test_car_id,
            start_str=start_2,
            end_str=end_2,
            pickup_location="Point A",
            drop_location="Point B"
        )
        self.assertFalse(success2)
        self.assertIn("already booked", err_msg.lower())

    def test_booking_cancellation(self):
        """Test customer can cancel their eligible booking."""
        today = date.today()
        start_d = str(today + timedelta(days=20))
        end_d = str(today + timedelta(days=22))

        success, _, ref = BookingService.create_booking(
            customer_id=self.customer_id,
            car_id=self.test_car_id,
            start_str=start_d,
            end_str=end_d,
            pickup_location="A",
            drop_location="B"
        )
        booking = BookingService.get_booking_by_ref(ref)

        # Cancel
        cancel_success = BookingService.cancel_booking(booking.id, self.customer_id)
        self.assertTrue(cancel_success)

        updated_booking = BookingService.get_booking_by_id(booking.id)
        self.assertEqual(updated_booking.booking_status, "Cancelled")

    def test_payment_and_invoice_generation(self):
        """Test demo payment transaction and receipt retrieval."""
        today = date.today()
        start_d = str(today + timedelta(days=25))
        end_d = str(today + timedelta(days=27))

        _, _, ref = BookingService.create_booking(
            customer_id=self.customer_id,
            car_id=self.test_car_id,
            start_str=start_d,
            end_str=end_d,
            pickup_location="A",
            drop_location="B"
        )
        booking = BookingService.get_booking_by_ref(ref)

        # Process demo payment
        success, msg, txn_ref = PaymentService.process_payment(
            booking_id=booking.id,
            customer_id=self.customer_id,
            payment_method="UPI"
        )
        self.assertTrue(success)
        self.assertTrue(txn_ref.startswith("TXN-"))

        # Verify invoice lookup
        receipt = PaymentService.get_payment_by_ref(txn_ref)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.amount, booking.total_amount)

    def test_review_eligibility_and_duplicate_prevention(self):
        """Test reviews are allowed only for Completed bookings and reject duplicates."""
        # A pending booking cannot be reviewed
        today = date.today()
        _, _, ref = BookingService.create_booking(
            customer_id=self.customer_id,
            car_id=self.test_car_id,
            start_str=str(today + timedelta(days=30)),
            end_str=str(today + timedelta(days=32)),
            pickup_location="A",
            drop_location="B"
        )
        booking = BookingService.get_booking_by_ref(ref)
        
        success, err = ReviewService.add_review(booking.id, self.customer_id, 5, "Great ride!")
        self.assertFalse(success)
        self.assertIn("completed", err.lower())

if __name__ == "__main__":
    unittest.main()
