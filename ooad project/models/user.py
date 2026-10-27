from werkzeug.security import generate_password_hash, check_password_hash

class User:
    """
    Base User class representing standard credentials and profile.
    Demonstrates OOAD Encapsulation, Abstraction, and Base Polymorphism.
    """
    def __init__(self, id=None, name="", email="", phone="", password_hash="",
                 role="customer", status="active", address=None, license_number=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.password_hash = password_hash
        self.role = role
        self.status = status
        self.address = address
        self.license_number = license_number
        self.created_at = created_at
        self.updated_at = updated_at

    def set_password(self, plain_password: str):
        """Hashes and stores password using Werkzeug security."""
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        """Verifies plain password against stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, plain_password)

    def is_active(self) -> bool:
        """Check if account is active."""
        return self.status == "active"

    def can_book_cars(self) -> bool:
        """Default permission for booking."""
        return False

    def can_manage_cars(self) -> bool:
        """Default permission for managing cars."""
        return False

    def is_admin_user(self) -> bool:
        """Default admin check."""
        return False

    def to_dict(self):
        """Serialize user object to dictionary (excluding password hash)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "status": self.status,
            "address": self.address,
            "license_number": self.license_number,
            "created_at": str(self.created_at) if self.created_at else None
        }


class Customer(User):
    """
    Customer subclass with renting and booking capabilities.
    Inherits from User.
    """
    def __init__(self, **kwargs):
        kwargs["role"] = "customer"
        super().__init__(**kwargs)

    def can_book_cars(self) -> bool:
        return self.is_active()

    def can_review(self) -> bool:
        return self.is_active()


class CarOwner(User):
    """
    CarOwner subclass with vehicle listing and rental hosting privileges.
    Inherits from User.
    """
    def __init__(self, **kwargs):
        kwargs["role"] = "owner"
        super().__init__(**kwargs)

    def can_manage_cars(self) -> bool:
        return self.is_active()

    def can_approve_bookings(self) -> bool:
        return self.is_active()


class Admin(User):
    """
    Admin subclass with full supervisory and platform governance permissions.
    Inherits from User.
    """
    def __init__(self, **kwargs):
        kwargs["role"] = "admin"
        super().__init__(**kwargs)

    def is_admin_user(self) -> bool:
        return True

    def can_verify_cars(self) -> bool:
        return True

    def can_manage_users(self) -> bool:
        return True


class UserFactory:
    """
    Factory Pattern for instantiating appropriate User entity
    polymorphically based on database role string.
    """
    @staticmethod
    def create_user(data: dict) -> User:
        if not data:
            return None
        role = data.get("role", "customer").lower()
        if role == "admin":
            return Admin(**data)
        elif role == "owner":
            return CarOwner(**data)
        else:
            return Customer(**data)
