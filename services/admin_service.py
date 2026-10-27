from database import db
from models.user import UserFactory

class AdminService:
    """
    Business service providing platform-wide telemetry, user governance,
    vehicle verification metrics, and financial reporting.
    """
    @staticmethod
    def get_dashboard_metrics():
        metrics = {}

        # Users counts
        cust_row = db.fetch_one("SELECT COUNT(*) as count FROM users WHERE role = 'customer'")
        metrics["total_customers"] = cust_row["count"] if cust_row else 0

        owner_row = db.fetch_one("SELECT COUNT(*) as count FROM users WHERE role = 'owner'")
        metrics["total_owners"] = owner_row["count"] if owner_row else 0

        # Cars counts
        cars_total = db.fetch_one("SELECT COUNT(*) as count FROM cars")
        metrics["total_cars"] = cars_total["count"] if cars_total else 0

        cars_pending = db.fetch_one("SELECT COUNT(*) as count FROM cars WHERE approval_status = 'pending'")
        metrics["pending_cars"] = cars_pending["count"] if cars_pending else 0

        # Bookings counts
        bookings_total = db.fetch_one("SELECT COUNT(*) as count FROM bookings")
        metrics["total_bookings"] = bookings_total["count"] if bookings_total else 0

        bookings_confirmed = db.fetch_one("SELECT COUNT(*) as count FROM bookings WHERE booking_status = 'Confirmed'")
        metrics["confirmed_bookings"] = bookings_confirmed["count"] if bookings_confirmed else 0

        # Revenue
        rev_row = db.fetch_one("SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE payment_status = 'Completed'")
        metrics["total_revenue"] = float(rev_row["total"]) if rev_row else 0.0

        # Reviews
        reviews_count = db.fetch_one("SELECT COUNT(*) as count FROM reviews")
        metrics["total_reviews"] = reviews_count["count"] if reviews_count else 0

        return metrics

    @staticmethod
    def get_all_users(role_filter=None, status_filter=None):
        where = []
        params = []
        if role_filter and role_filter != "all":
            where.append("role = %s")
            params.append(role_filter)
        if status_filter and status_filter != "all":
            where.append("status = %s")
            params.append(status_filter)

        where_clause = f"WHERE {' AND '.join(where)}" if where else ""
        query = f"SELECT * FROM users {where_clause} ORDER BY created_at DESC"
        rows = db.fetch_all(query, tuple(params) if params else None)
        return [UserFactory.create_user(r) for r in rows]

    @staticmethod
    def toggle_user_status(user_id: int, current_status: str) -> bool:
        new_status = "inactive" if current_status == "active" else "active"
        query = "UPDATE users SET status = %s WHERE id = %s"
        _, count = db.execute_query(query, (new_status, user_id))
        return count > 0

    @staticmethod
    def get_category_distribution():
        query = """
            SELECT category, COUNT(*) as car_count,
                   AVG(price_per_day) as avg_price
            FROM cars
            WHERE approval_status = 'approved'
            GROUP BY category
            ORDER BY car_count DESC
        """
        return db.fetch_all(query)
