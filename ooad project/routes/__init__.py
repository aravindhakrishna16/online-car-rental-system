from .auth_routes import auth_bp
from .public_routes import public_bp
from .customer_routes import customer_bp
from .owner_routes import owner_bp
from .admin_routes import admin_bp
from .api_routes import api_bp

__all__ = [
    "auth_bp",
    "public_bp",
    "customer_bp",
    "owner_bp",
    "admin_bp",
    "api_bp"
]
