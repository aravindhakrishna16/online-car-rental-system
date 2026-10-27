class Payment:
    """
    Payment Domain Entity capturing simulated monetary transactions and invoices.
    Methods: UPI, CARD, CASH.
    Statuses: Pending, Completed, Refunded, Failed.
    """
    METHOD_UPI = "UPI"
    METHOD_CARD = "CARD"
    METHOD_CASH = "CASH"

    STATUS_PENDING = "Pending"
    STATUS_COMPLETED = "Completed"
    STATUS_REFUNDED = "Refunded"
    STATUS_FAILED = "Failed"

    def __init__(self, id=None, booking_id=None, customer_id=None, amount=0.0,
                 payment_method="UPI", payment_status="Completed",
                 transaction_reference="", payment_date=None,
                 booking_reference=None, customer_name=None, car_name=None,
                 car_brand=None, **kwargs):
        self.id = id
        self.booking_id = booking_id
        self.customer_id = customer_id
        self.amount = float(amount) if amount else 0.0
        self.payment_method = payment_method
        self.payment_status = payment_status
        self.transaction_reference = transaction_reference
        self.payment_date = payment_date
        
        # Joined attributes
        self.booking_reference = booking_reference
        self.customer_name = customer_name
        self.car_name = car_name
        self.car_brand = car_brand

    def is_successful(self) -> bool:
        return self.payment_status == self.STATUS_COMPLETED

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "transaction_reference": self.transaction_reference,
            "payment_date": str(self.payment_date) if self.payment_date else None,
            "booking_reference": self.booking_reference,
            "customer_name": self.customer_name,
            "car_name": self.car_name
        }

    @classmethod
    def from_dict(cls, data: dict):
        if not data:
            return None
        return cls(**data)
