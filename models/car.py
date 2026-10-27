class Car:
    """
    Car Domain Entity representing an automobile available for rental.
    Encapsulates specifications, availability status, and pricing calculations.
    Supports per-day AND per-km pricing for transparent fare computation.
    """
    def __init__(self, id=None, owner_id=None, name="", brand="", model="", year=2023,
                 registration_number="", category="Sedan", fuel_type="Petrol",
                 transmission="Manual", seating_capacity=5, price_per_day=0.0,
                 price_per_km=10.0,
                 location="", description="", image_url=None, is_available=True,
                 approval_status="pending", created_at=None, updated_at=None,
                 owner_name=None, owner_phone=None, avg_rating=0.0, total_reviews=0, **kwargs):
        self.id = id
        self.owner_id = owner_id
        self.name = name
        self.brand = brand
        self.model = model
        self.year = int(year) if year else 2023
        self.registration_number = registration_number.upper() if registration_number else ""
        self.category = category
        self.fuel_type = fuel_type
        self.transmission = transmission
        self.seating_capacity = int(seating_capacity) if seating_capacity else 5
        self.price_per_day = float(price_per_day) if price_per_day else 0.0
        self.price_per_km = float(price_per_km) if price_per_km else 10.0
        self.location = location
        self.description = description
        self.image_url = image_url or "/static/images/default_car.jpg"
        self.is_available = bool(is_available)
        self.approval_status = approval_status
        self.created_at = created_at
        self.updated_at = updated_at

        # Joined / presentation attributes
        self.owner_name = owner_name
        self.owner_phone = owner_phone
        self.avg_rating = round(float(avg_rating), 1) if avg_rating else 0.0
        self.total_reviews = int(total_reviews) if total_reviews else 0

    def is_bookable(self) -> bool:
        """Business rule: Car must be marked available and approved by Admin."""
        return self.is_available and self.approval_status == "approved"

    def calculate_cost(self, days: int, estimated_km: int = 0) -> float:
        """
        Calculates total rental cost combining:
        - Daily rate × number of days
        - Per-km charge × estimated kilometres
        """
        if days < 1:
            days = 1
        day_cost = round(self.price_per_day * days, 2)
        km_cost = round(self.price_per_km * max(0, estimated_km), 2)
        return round(day_cost + km_cost, 2)

    def calculate_km_charges(self, estimated_km: int) -> float:
        """Returns the km-only portion of the fare."""
        return round(self.price_per_km * max(0, estimated_km), 2)

    def get_badge_class(self) -> str:
        """Returns styling badge category class for UI."""
        mapping = {
            "hatchback": "badge-hatch",
            "sedan": "badge-sedan",
            "suv": "badge-suv",
            "luxury": "badge-lux",
            "electric": "badge-ev"
        }
        return mapping.get(self.category.lower(), "badge-default")

    def to_dict(self):
        """Serialize Car object to dictionary."""
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "registration_number": self.registration_number,
            "category": self.category,
            "fuel_type": self.fuel_type,
            "transmission": self.transmission,
            "seating_capacity": self.seating_capacity,
            "price_per_day": self.price_per_day,
            "price_per_km": self.price_per_km,
            "location": self.location,
            "description": self.description,
            "image_url": self.image_url,
            "is_available": self.is_available,
            "approval_status": self.approval_status,
            "owner_name": self.owner_name,
            "owner_phone": self.owner_phone,
            "avg_rating": self.avg_rating,
            "total_reviews": self.total_reviews,
            "created_at": str(self.created_at) if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
