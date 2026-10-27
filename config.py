import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "driveease-secret-key-2026-supersecure")
    
    # MySQL Database Settings
    DB_TYPE = os.getenv("DB_TYPE", "mysql")  # 'mysql' or 'sqlite'
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "car_rental_db")
    
    # SQLite Fallback / Development Database Path
    SQLITE_DB_PATH = os.path.join(BASE_DIR, "car_rental.db")
    USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "true").lower() in ("true", "1", "yes")
    
    # Upload Settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    
    # Application Info
    APP_NAME = "DriveEase - Online Car Rental"
    CURRENCY_SYMBOL = "₹"
