from database import db
from models.review import Review
from services.booking_service import BookingService
from services.notification_service import NotificationService

class ReviewService:
    """
    Business service enforcing review eligibility, rating boundaries,
    and review moderation.
    """
    @staticmethod
    def add_review(booking_id: int, customer_id: int, rating: int, comment: str):
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking:
            return False, "Booking not found."

        if booking.customer_id != customer_id:
            return False, "You can only review your own trips."

        if booking.booking_status != "Completed":
            return False, "Reviews can only be submitted for completed rentals."

        # Check for existing review
        existing = db.fetch_one("SELECT id FROM reviews WHERE booking_id = %s", (booking_id,))
        if existing:
            return False, "You have already submitted a review for this booking."

        try:
            rating = int(rating)
        except (ValueError, TypeError):
            return False, "Rating must be a number between 1 and 5."

        if not (1 <= rating <= 5):
            return False, "Rating must be between 1 and 5 stars."

        if not comment or len(comment.strip()) < 5:
            return False, "Please provide feedback of at least 5 characters."

        query = """
            INSERT INTO reviews (booking_id, car_id, customer_id, rating, comment, created_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """
        last_id, _ = db.execute_query(query, (booking_id, booking.car_id, customer_id, rating, comment.strip()))

        # Notify Owner
        NotificationService.send_notification(
            user_id=booking.owner_id,
            title="New Renter Review Received ⭐",
            message=f"{booking.customer_name} left a {rating}★ review for {booking.car_name}.",
            type="review",
            link="/owner/dashboard"
        )

        return True, "Thank you! Your review has been submitted."

    @staticmethod
    def delete_review(review_id: int) -> bool:
        """Admin moderation to delete inappropriate reviews."""
        query = "DELETE FROM reviews WHERE id = %s"
        _, count = db.execute_query(query, (review_id,))
        return count > 0

    @staticmethod
    def get_all_reviews_admin():
        query = """
            SELECT r.*, u.name as customer_name, u.email as customer_email,
                   c.name as car_name, c.brand as car_brand
            FROM reviews r
            JOIN users u ON r.customer_id = u.id
            JOIN cars c ON r.car_id = c.id
            ORDER BY r.created_at DESC
        """
        rows = db.fetch_all(query)
        return [Review.from_dict(r) for r in rows]
