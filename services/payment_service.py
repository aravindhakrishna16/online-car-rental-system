import uuid
from datetime import datetime
from database import db
from models.payment import Payment
from services.booking_service import BookingService
from services.notification_service import NotificationService

class PaymentService:
    """
    Business service simulating safe, demo payment gateway flows (UPI QR, Card, Cash on Pickup),
    receipt generation, and revenue reporting.
    """
    @staticmethod
    def generate_transaction_ref() -> str:
        """Generates a realistic transaction reference number."""
        token = uuid.uuid4().hex[:12].upper()
        return f"TXN-{token}"

    @staticmethod
    def process_payment(booking_id: int, customer_id: int, payment_method: str,
                        upi_id: str = None, card_holder: str = None, card_number: str = None):
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking:
            return False, "Booking record not found.", None

        if booking.customer_id != customer_id:
            return False, "Unauthorized access to this booking.", None

        # Check if already paid
        existing = PaymentService.get_payment_by_booking(booking_id)
        if existing and existing.payment_status == "Completed":
            return False, "This booking has already been paid for.", existing.transaction_reference

        if payment_method not in ("UPI", "CARD", "CASH"):
            payment_method = "UPI"

        txn_ref = PaymentService.generate_transaction_ref()
        amount = booking.total_amount

        query = """
            INSERT INTO payments (
                booking_id, customer_id, amount, payment_method,
                payment_status, transaction_reference, payment_date
            ) VALUES (
                %s, %s, %s, %s,
                'Completed', %s, CURRENT_TIMESTAMP
            )
        """
        last_id, _ = db.execute_query(query, (
            booking_id, customer_id, amount, payment_method, txn_ref
        ))

        # Notify Customer with confirmation
        NotificationService.send_notification(
            user_id=customer_id,
            title="Payment Received! 💳",
            message=f"Demo payment of ₹{amount:,.2f} via {payment_method} successful. Ref: {txn_ref}.",
            type="payment",
            link=f"/customer/invoice/{txn_ref}"
        )

        # Notify Car Owner
        NotificationService.send_notification(
            user_id=booking.owner_id,
            title="Rental Payment Recorded",
            message=f"Renter completed payment of ₹{amount:,.2f} for booking {booking.booking_reference}.",
            type="payment",
            link="/owner/dashboard"
        )

        return True, "Payment processed successfully!", txn_ref

    @staticmethod
    def get_payment_by_booking(booking_id: int):
        query = "SELECT * FROM payments WHERE booking_id = %s"
        row = db.fetch_one(query, (booking_id,))
        if not row:
            return None
        return Payment.from_dict(row)

    @staticmethod
    def get_payment_by_ref(transaction_ref: str):
        query = """
            SELECT p.*, b.booking_reference, u.name as customer_name,
                   c.name as car_name, c.brand as car_brand
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            JOIN users u ON p.customer_id = u.id
            JOIN cars c ON b.car_id = c.id
            WHERE p.transaction_reference = %s
        """
        row = db.fetch_one(query, (transaction_ref,))
        if not row:
            return None
        return Payment.from_dict(row)

    @staticmethod
    def get_owner_earnings_summary(owner_id: int):
        query = """
            SELECT
                COALESCE(SUM(p.amount), 0) as total_earnings,
                COUNT(DISTINCT b.id) as total_rentals,
                COUNT(DISTINCT CASE WHEN b.booking_status = 'Pending' THEN b.id END) as pending_requests,
                COUNT(DISTINCT CASE WHEN b.booking_status = 'Confirmed' THEN b.id END) as active_rentals
            FROM cars c
            LEFT JOIN bookings b ON c.id = b.car_id
            LEFT JOIN payments p ON b.id = p.booking_id AND p.payment_status = 'Completed'
            WHERE c.owner_id = %s
        """
        row = db.fetch_one(query, (owner_id,))
        return {
            "total_earnings": float(row["total_earnings"]) if row else 0.0,
            "total_rentals": int(row["total_rentals"]) if row else 0,
            "pending_requests": int(row["pending_requests"]) if row else 0,
            "active_rentals": int(row["active_rentals"]) if row else 0
        }

    @staticmethod
    def get_all_payments_admin(limit: int = 100):
        query = """
            SELECT p.*, b.booking_reference, u.name as customer_name, u.email as customer_email,
                   c.name as car_name, c.brand as car_brand
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            JOIN users u ON p.customer_id = u.id
            JOIN cars c ON b.car_id = c.id
            ORDER BY p.payment_date DESC
            LIMIT %s
        """
        rows = db.fetch_all(query, (limit,))
        return [Payment.from_dict(r) for r in rows]
