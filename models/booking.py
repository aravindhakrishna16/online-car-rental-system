from datetime import datetime, date

class Booking:
    """
    Booking Domain Entity managing vehicle reservations and reservation state machine.
    Statuses: Pending, Confirmed, Rejected, Cancelled, Completed.
    Includes per-km pricing: estimated_km, km_rate, km_charges stored on each booking.
    """
    STATUS_PENDING = "Pending"
    STATUS_CONFIRMED = "Confirmed"
    STATUS_REJECTED = "Rejected"
    STATUS_CANCELLED = "Cancelled"
    STATUS_COMPLETED = "Completed"

    def __init__(self, id=None, booking_reference="", customer_id=None, car_id=None,
                 start_date=None, end_date=None, total_days=1, daily_rate=0.0,
                 estimated_km=100, km_rate=10.0, km_charges=0.0,
                 total_amount=0.0, pickup_location="", drop_location="",
                 booking_status="Pending", rejection_reason=None, created_at=None,
                 updated_at=None, car_name="", car_brand="", car_model="",
                 car_image=None, car_registration="", customer_name="",
                 customer_email="", customer_phone="", owner_id=None,
                 owner_name="", owner_phone="", payment_status=None, has_reviewed=False, **kwargs):
        self.id = id
        self.booking_reference = booking_reference
        self.customer_id = customer_id
        self.car_id = car_id
        self.start_date = start_date
        self.end_date = end_date
        self.total_days = int(total_days) if total_days else 1
        self.daily_rate = float(daily_rate) if daily_rate else 0.0
        self.estimated_km = int(estimated_km) if estimated_km else 100
        self.km_rate = float(km_rate) if km_rate else 10.0
        self.km_charges = float(km_charges) if km_charges else 0.0
        self.total_amount = float(total_amount) if total_amount else 0.0
        self.pickup_location = pickup_location
        self.drop_location = drop_location
        self.booking_status = booking_status
        self.rejection_reason = rejection_reason
        self.created_at = created_at
        self.updated_at = updated_at

        # Joined data
        self.car_name = car_name
        self.car_brand = car_brand
        self.car_model = car_model
        self.car_image = car_image or "/static/images/default_car.jpg"
        self.car_registration = car_registration
        self.customer_name = customer_name
        self.customer_email = customer_email
        self.customer_phone = customer_phone
        self.owner_id = owner_id
        self.owner_name = owner_name
        self.owner_phone = owner_phone
        self.payment_status = payment_status
        self.has_reviewed = bool(has_reviewed)

    @property
    def base_rental_cost(self) -> float:
        """Day-rate only portion of the fare."""
        return round(self.daily_rate * self.total_days, 2)

    @property
    def gst_amount(self) -> float:
        """5% GST applied on (base_rental + km_charges)."""
        return round((self.base_rental_cost + self.km_charges) * 0.05, 2)

    def can_cancel(self) -> bool:
        """Booking can only be cancelled by customer if Pending or Confirmed."""
        return self.booking_status in (self.STATUS_PENDING, self.STATUS_CONFIRMED)

    def can_owner_action(self) -> bool:
        """Owner can accept or reject only Pending bookings."""
        return self.booking_status == self.STATUS_PENDING

    def can_complete(self) -> bool:
        """Only Confirmed bookings can transition to Completed."""
        return self.booking_status == self.STATUS_CONFIRMED

    def can_review(self) -> bool:
        """Reviews are strictly restricted to Completed rentals that haven't been reviewed yet."""
        return self.booking_status == self.STATUS_COMPLETED and not self.has_reviewed

    def get_status_badge_class(self) -> str:
        """Returns CSS class for modern Uber/Rapido badges."""
        classes = {
            self.STATUS_PENDING: "badge-warning",
            self.STATUS_CONFIRMED: "badge-success",
            self.STATUS_REJECTED: "badge-danger",
            self.STATUS_CANCELLED: "badge-secondary",
            self.STATUS_COMPLETED: "badge-primary"
        }
        return classes.get(self.booking_status, "badge-light")

    def to_dict(self):
        return {
            "id": self.id,
            "booking_reference": self.booking_reference,
            "customer_id": self.customer_id,
            "car_id": self.car_id,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "total_days": self.total_days,
            "daily_rate": self.daily_rate,
            "estimated_km": self.estimated_km,
            "km_rate": self.km_rate,
            "km_charges": self.km_charges,
            "total_amount": self.total_amount,
            "pickup_location": self.pickup_location,
            "drop_location": self.drop_location,
            "booking_status": self.booking_status,
            "rejection_reason": self.rejection_reason,
            "car_name": self.car_name,
            "car_brand": self.car_brand,
            "car_image": self.car_image,
            "customer_name": self.customer_name,
            "payment_status": self.payment_status,
            "has_reviewed": self.has_reviewed,
            "created_at": str(self.created_at) if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
