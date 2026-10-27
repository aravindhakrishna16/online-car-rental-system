import uuid
from datetime import datetime, date
from database import db
from models.booking import Booking
from services.car_service import CarService
from services.notification_service import NotificationService

class BookingService:
    """
    Business service enforcing reservation rules, overlap detection,
    price computations, and rental lifecycle state transitions.
    """
    @staticmethod
    def generate_booking_reference() -> str:
        """Generates a clean human-readable booking reference."""
        token = uuid.uuid4().hex[:8].upper()
        return f"BK-{token}"

    @staticmethod
    def validate_dates(start_str: str, end_str: str):
        """
        Validates pickup and return dates according to business rules:
        - Return date must be >= pickup date.
        - Start date must not be in the past.
        Returns (is_valid: bool, total_days: int, start_date: date, end_date: date, error: str)
        """
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return False, 0, None, None, "Invalid date format. Use YYYY-MM-DD."

        today = date.today()
        if start_date < today:
            return False, 0, None, None, "Pickup date cannot be in the past."

        if end_date < start_date:
            return False, 0, None, None, "Return date must be equal to or later than pickup date."

        total_days = (end_date - start_date).days
        if total_days == 0:
            total_days = 1  # Same day rental is counted as 1 day minimum

        return True, total_days, start_date, end_date, None

    @staticmethod
    def is_car_available_for_dates(car_id: int, start_date: date, end_date: date, exclude_booking_id: int = None) -> bool:
        """
        Overlapping intervals query:
        Overlap exists if: (start_date <= existing.end_date) AND (end_date >= existing.start_date)
        Only considers active bookings ('Pending', 'Confirmed').
        """
        query = """
            SELECT COUNT(*) as count FROM bookings
            WHERE car_id = %s
              AND booking_status IN ('Pending', 'Confirmed')
              AND NOT (%s > end_date OR %s < start_date)
        """
        params = [car_id, str(start_date), str(end_date)]

        if exclude_booking_id:
            query += " AND id != %s"
            params.append(exclude_booking_id)

        row = db.fetch_one(query, tuple(params))
        count = row["count"] if row else 0
        return count == 0

    @staticmethod
    def create_booking(customer_id: int, car_id: int, start_str: str, end_str: str,
                       pickup_location: str, drop_location: str, estimated_km: int = 100):
        """Creates a booking reservation while enforcing all validation rules.
        
        Total Amount = (daily_rate × days) + (price_per_km × estimated_km) + 5% GST
        """
        is_valid, days, start_d, end_d, err = BookingService.validate_dates(start_str, end_str)
        if not is_valid:
            return False, err, None

        # Clamp estimated_km to a sane range
        estimated_km = max(0, min(int(estimated_km or 100), 10000))

        car = CarService.get_car_by_id(car_id)
        if not car:
            return False, "Vehicle not found.", None

        if not car.is_bookable():
            return False, "This vehicle is currently unavailable or unverified.", None

        if not BookingService.is_car_available_for_dates(car_id, start_d, end_d):
            return False, "The vehicle is already booked for the selected dates. Please choose different dates.", None

        # --- Fare Engine ---
        daily_rate = car.price_per_day
        km_rate = car.price_per_km
        base_rental = round(daily_rate * days, 2)
        km_charges = round(km_rate * estimated_km, 2)
        subtotal = base_rental + km_charges
        gst = round(subtotal * 0.05, 2)
        total_amount = round(subtotal + gst, 2)

        ref = BookingService.generate_booking_reference()

        query = """
            INSERT INTO bookings (
                booking_reference, customer_id, car_id, start_date, end_date,
                total_days, daily_rate, estimated_km, km_rate, km_charges,
                total_amount, pickup_location, drop_location,
                booking_status, created_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                'Pending', CURRENT_TIMESTAMP
            )
        """
        last_id, _ = db.execute_query(query, (
            ref, customer_id, car_id, str(start_d), str(end_d),
            days, daily_rate, estimated_km, km_rate, km_charges,
            total_amount, pickup_location, drop_location
        ))

        # Send in-app notification to Car Owner
        NotificationService.send_notification(
            user_id=car.owner_id,
            title="New Booking Request!",
            message=f"New booking {ref} received for {car.name} ({days} days, {estimated_km} km, ₹{total_amount:,.2f}).",
            type="booking",
            link="/owner/dashboard"
        )

        # Send in-app notification to Customer
        NotificationService.send_notification(
            user_id=customer_id,
            title="Booking Submitted",
            message=f"Booking {ref} for {car.name} submitted. Est. fare ₹{total_amount:,.2f} for {days} day(s) + {estimated_km} km.",
            type="booking",
            link="/customer/dashboard"
        )

        return True, "Booking created successfully!", ref

    @staticmethod
    def get_booking_by_id(booking_id: int) -> Booking:
        query = """
            SELECT b.*,
                   c.name as car_name, c.brand as car_brand, c.model as car_model,
                   c.image_url as car_image, c.registration_number as car_registration,
                   c.owner_id as owner_id,
                   u_cust.name as customer_name, u_cust.email as customer_email, u_cust.phone as customer_phone,
                   u_owner.name as owner_name, u_owner.phone as owner_phone,
                   p.payment_status as payment_status,
                   CASE WHEN r.id IS NOT NULL THEN 1 ELSE 0 END as has_reviewed
            FROM bookings b
            JOIN cars c ON b.car_id = c.id
            JOIN users u_cust ON b.customer_id = u_cust.id
            JOIN users u_owner ON c.owner_id = u_owner.id
            LEFT JOIN payments p ON b.id = p.booking_id
            LEFT JOIN reviews r ON b.id = r.booking_id
            WHERE b.id = %s
        """
        row = db.fetch_one(query, (booking_id,))
        if not row:
            return None
        return Booking.from_dict(row)

    @staticmethod
    def get_booking_by_ref(booking_ref: str) -> Booking:
        query = """
            SELECT b.*,
                   c.name as car_name, c.brand as car_brand, c.model as car_model,
                   c.image_url as car_image, c.registration_number as car_registration,
                   c.owner_id as owner_id,
                   u_cust.name as customer_name, u_cust.email as customer_email, u_cust.phone as customer_phone,
                   u_owner.name as owner_name, u_owner.phone as owner_phone,
                   p.payment_status as payment_status,
                   CASE WHEN r.id IS NOT NULL THEN 1 ELSE 0 END as has_reviewed
            FROM bookings b
            JOIN cars c ON b.car_id = c.id
            JOIN users u_cust ON b.customer_id = u_cust.id
            JOIN users u_owner ON c.owner_id = u_owner.id
            LEFT JOIN payments p ON b.id = p.booking_id
            LEFT JOIN reviews r ON b.id = r.booking_id
            WHERE b.booking_reference = %s
        """
        row = db.fetch_one(query, (booking_ref,))
        if not row:
            return None
        return Booking.from_dict(row)

    @staticmethod
    def get_customer_bookings(customer_id: int):
        query = """
            SELECT b.*,
                   c.name as car_name, c.brand as car_brand, c.model as car_model,
                   c.image_url as car_image, c.registration_number as car_registration,
                   c.owner_id as owner_id,
                   u_owner.name as owner_name, u_owner.phone as owner_phone,
                   p.payment_status as payment_status,
                   CASE WHEN r.id IS NOT NULL THEN 1 ELSE 0 END as has_reviewed
            FROM bookings b
            JOIN cars c ON b.car_id = c.id
            JOIN users u_owner ON c.owner_id = u_owner.id
            LEFT JOIN payments p ON b.id = p.booking_id
            LEFT JOIN reviews r ON b.id = r.booking_id
            WHERE b.customer_id = %s
            ORDER BY b.created_at DESC
        """
        rows = db.fetch_all(query, (customer_id,))
        return [Booking.from_dict(r) for r in rows]

    @staticmethod
    def get_owner_bookings(owner_id: int, status_filter=None):
        where = "WHERE c.owner_id = %s"
        params = [owner_id]
        if status_filter and status_filter != "all":
            where += " AND b.booking_status = %s"
            params.append(status_filter)

        query = f"""
            SELECT b.*,
                   c.name as car_name, c.brand as car_brand, c.model as car_model,
                   c.image_url as car_image, c.registration_number as car_registration,
                   u_cust.name as customer_name, u_cust.email as customer_email, u_cust.phone as customer_phone,
                   p.payment_status as payment_status
            FROM bookings b
            JOIN cars c ON b.car_id = c.id
            JOIN users u_cust ON b.customer_id = u_cust.id
            LEFT JOIN payments p ON b.id = p.booking_id
            {where}
            ORDER BY b.created_at DESC
        """
        rows = db.fetch_all(query, tuple(params))
        return [Booking.from_dict(r) for r in rows]

    @staticmethod
    def get_all_bookings_admin(status_filter=None):
        where = ""
        params = []
        if status_filter and status_filter != "all":
            where = "WHERE b.booking_status = %s"
            params.append(status_filter)

        query = f"""
            SELECT b.*,
                   c.name as car_name, c.brand as car_brand, c.model as car_model,
                   u_cust.name as customer_name, u_cust.email as customer_email,
                   u_owner.name as owner_name,
                   p.payment_status as payment_status
            FROM bookings b
            JOIN cars c ON b.car_id = c.id
            JOIN users u_cust ON b.customer_id = u_cust.id
            JOIN users u_owner ON c.owner_id = u_owner.id
            LEFT JOIN payments p ON b.id = p.booking_id
            {where}
            ORDER BY b.created_at DESC
        """
        rows = db.fetch_all(query, tuple(params) if params else None)
        return [Booking.from_dict(r) for r in rows]

    @staticmethod
    def approve_booking(booking_id: int, owner_id: int) -> bool:
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking or booking.owner_id != owner_id or not booking.can_owner_action():
            return False

        query = "UPDATE bookings SET booking_status = 'Confirmed', updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        _, count = db.execute_query(query, (booking_id,))

        NotificationService.send_notification(
            user_id=booking.customer_id,
            title="Booking Confirmed! 🚗",
            message=f"Host approved your booking {booking.booking_reference} for {booking.car_name}. Ready for payment & pickup!",
            type="booking",
            link="/customer/dashboard"
        )
        return count > 0

    @staticmethod
    def reject_booking(booking_id: int, owner_id: int, reason: str = "Unavailable") -> bool:
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking or booking.owner_id != owner_id or not booking.can_owner_action():
            return False

        query = """
            UPDATE bookings
            SET booking_status = 'Rejected', rejection_reason = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        _, count = db.execute_query(query, (reason, booking_id))

        NotificationService.send_notification(
            user_id=booking.customer_id,
            title="Booking Request Declined",
            message=f"Host declined booking {booking.booking_reference}: '{reason}'.",
            type="cancellation",
            link="/customer/dashboard"
        )
        return count > 0

    @staticmethod
    def cancel_booking(booking_id: int, user_id: int, is_admin: bool = False) -> bool:
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking:
            return False

        # Customer or Admin can cancel
        if not is_admin and booking.customer_id != user_id:
            return False

        if not booking.can_cancel():
            return False

        query = "UPDATE bookings SET booking_status = 'Cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        _, count = db.execute_query(query, (booking_id,))

        # Notify Owner
        NotificationService.send_notification(
            user_id=booking.owner_id,
            title="Booking Cancelled",
            message=f"Booking {booking.booking_reference} for {booking.car_name} was cancelled by the renter.",
            type="cancellation",
            link="/owner/dashboard"
        )
        return count > 0

    @staticmethod
    def complete_booking(booking_id: int, owner_or_admin_id: int) -> bool:
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking or not booking.can_complete():
            return False

        query = "UPDATE bookings SET booking_status = 'Completed', updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        _, count = db.execute_query(query, (booking_id,))

        # Notify Customer to leave a review
        NotificationService.send_notification(
            user_id=booking.customer_id,
            title="Trip Completed! How was your ride?",
            message=f"Your trip with {booking.car_name} is complete. Rate your experience now!",
            type="review",
            link="/customer/dashboard"
        )
        return count > 0
