class Notification:
    """
    Notification Domain Entity for in-app real-time alerts and lifecycle events.
    """
    def __init__(self, id=None, user_id=None, title="", message="",
                 type="info", is_read=False, link=None, created_at=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.message = message
        self.type = type
        self.is_read = bool(is_read)
        self.link = link
        self.created_at = created_at

    def get_icon(self) -> str:
        """Returns visual indicator icon for notification category."""
        icons = {
            "booking": "fa-calendar-check",
            "payment": "fa-credit-card",
            "approval": "fa-shield-halved",
            "cancellation": "fa-circle-xmark",
            "review": "fa-star",
            "info": "fa-bell"
        }
        return icons.get(self.type, "fa-bell")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.type,
            "is_read": self.is_read,
            "link": self.link,
            "created_at": str(self.created_at) if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
