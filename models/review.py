class Review:
    """
    Review Domain Entity capturing rating (1-5 stars) and customer feedback
    for completed vehicle rentals.
    """
    def __init__(self, id=None, booking_id=None, car_id=None, customer_id=None,
                 rating=5, comment="", created_at=None,
                 customer_name=None, car_name=None, car_brand=None, **kwargs):
        self.id = id
        self.booking_id = booking_id
        self.car_id = car_id
        self.customer_id = customer_id
        self.rating = int(rating) if rating else 5
        self.comment = comment or ""
        self.created_at = created_at
        
        # Joined attributes
        self.customer_name = customer_name
        self.car_name = car_name
        self.car_brand = car_brand

    def is_valid(self) -> bool:
        """Enforce 1-5 star constraints and comment presence."""
        return 1 <= self.rating <= 5 and len(self.comment.strip()) > 0

    def get_stars_html(self) -> str:
        """Returns visual star icons for easy rendering."""
        stars = "★" * self.rating + "☆" * (5 - self.rating)
        return stars

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "car_id": self.car_id,
            "customer_id": self.customer_id,
            "rating": self.rating,
            "comment": self.comment,
            "customer_name": self.customer_name,
            "car_name": self.car_name,
            "car_brand": self.car_brand,
            "created_at": str(self.created_at) if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
