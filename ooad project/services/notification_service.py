from database import db
from models.notification import Notification

class NotificationService:
    """
    Business service managing user alerts, badges, and read/unread lifecycle.
    """
    @staticmethod
    def send_notification(user_id: int, title: str, message: str,
                          type: str = "info", link: str = None) -> int:
        query = """
            INSERT INTO notifications (user_id, title, message, type, is_read, link, created_at)
            VALUES (%s, %s, %s, %s, 0, %s, CURRENT_TIMESTAMP)
        """
        last_id, _ = db.execute_query(query, (user_id, title, message, type, link))
        return last_id

    @staticmethod
    def get_user_notifications(user_id: int, limit: int = 15):
        query = """
            SELECT * FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        rows = db.fetch_all(query, (user_id, limit))
        return [Notification.from_dict(r) for r in rows]

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        query = "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0"
        row = db.fetch_one(query, (user_id,))
        return row["count"] if row else 0

    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> bool:
        query = "UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s"
        _, count = db.execute_query(query, (notification_id, user_id))
        return count > 0

    @staticmethod
    def mark_all_as_read(user_id: int) -> bool:
        query = "UPDATE notifications SET is_read = 1 WHERE user_id = %s"
        _, count = db.execute_query(query, (user_id,))
        return count > 0
