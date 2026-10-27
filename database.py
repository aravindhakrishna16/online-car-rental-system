import sqlite3
import re
import os
import pymysql
import pymysql.cursors
from config import Config

class DatabaseManager:
    """
    Object-Oriented Database Abstraction Manager.
    Supports primary MySQL database with intelligent fallback to SQLite
    to ensure seamless local running and zero-failure college demos.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.db_type = Config.DB_TYPE
        self.mysql_config = {
            "host": Config.DB_HOST,
            "port": Config.DB_PORT,
            "user": Config.DB_USER,
            "password": Config.DB_PASSWORD,
            "database": Config.DB_NAME,
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "autocommit": True
        }
        self.sqlite_path = Config.SQLITE_DB_PATH
        self.active_engine = "mysql"
        self._test_and_select_engine()
        self._initialized = True

    def _test_and_select_engine(self):
        """Attempts connection to MySQL; falls back to SQLite if unreachable."""
        if self.db_type == "sqlite":
            self.active_engine = "sqlite"
            return

        try:
            # First attempt connection to host without db to ensure DB exists
            conn = pymysql.connect(
                host=self.mysql_config["host"],
                port=self.mysql_config["port"],
                user=self.mysql_config["user"],
                password=self.mysql_config["password"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4;")
            conn.close()

            # Now connect to target database
            conn = pymysql.connect(**self.mysql_config)
            conn.close()
            self.active_engine = "mysql"
            print(f"[DB] Successfully connected to MySQL ({Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}).")
        except Exception as e:
            if Config.USE_SQLITE_FALLBACK:
                print(f"[DB] Warning: MySQL connection failed ({e}). Falling back to SQLite for seamless execution.")
                self.active_engine = "sqlite"
            else:
                raise RuntimeError(
                    f"MySQL connection error: {e}. Please ensure MySQL is running or set USE_SQLITE_FALLBACK=True in .env."
                )

    def get_connection(self):
        """Returns an active database connection."""
        if self.active_engine == "mysql":
            return pymysql.connect(**self.mysql_config)
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn

    def _adapt_query_for_sqlite(self, query: str) -> str:
        """Adapts MySQL parameterized syntax (%s) to SQLite syntax (?) if needed."""
        # Replace %s placeholders with ? for sqlite
        return re.sub(r'%s', '?', query)

    def execute_query(self, query: str, params=None):
        """Executes an INSERT, UPDATE, or DELETE query and returns lastrowid and rowcount."""
        conn = self.get_connection()
        try:
            if self.active_engine == "mysql":
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    last_id = cursor.lastrowid
                    row_count = cursor.rowcount
                    conn.commit()
                    return last_id, row_count
            else:
                adapted_query = self._adapt_query_for_sqlite(query)
                cursor = conn.cursor()
                cursor.execute(adapted_query, params or ())
                last_id = cursor.lastrowid
                row_count = cursor.rowcount
                conn.commit()
                return last_id, row_count
        finally:
            conn.close()

    def fetch_one(self, query: str, params=None):
        """Fetches a single row as a dictionary."""
        conn = self.get_connection()
        try:
            if self.active_engine == "mysql":
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    row = cursor.fetchone()
                    return row
            else:
                adapted_query = self._adapt_query_for_sqlite(query)
                cursor = conn.cursor()
                cursor.execute(adapted_query, params or ())
                row = cursor.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def fetch_all(self, query: str, params=None):
        """Fetches multiple rows as a list of dictionaries."""
        conn = self.get_connection()
        try:
            if self.active_engine == "mysql":
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
            else:
                adapted_query = self._adapt_query_for_sqlite(query)
                cursor = conn.cursor()
                cursor.execute(adapted_query, params or ())
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        finally:
            conn.close()

    def init_database(self):
        """Initializes tables for MySQL or SQLite."""
        if self.active_engine == "mysql":
            schema_file = os.path.join(Config.BASE_DIR, "schema.sql")
            if os.path.exists(schema_file):
                with open(schema_file, "r", encoding="utf-8") as f:
                    content = f.read()
                # Split and execute individual statements
                statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]
                conn = self.get_connection()
                try:
                    with conn.cursor() as cursor:
                        for stmt in statements:
                            if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE"):
                                continue
                            cursor.execute(stmt)
                    conn.commit()
                finally:
                    conn.close()
        else:
            # SQLite compatible schema
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.executescript("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        phone TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'customer',
                        status TEXT NOT NULL DEFAULT 'active',
                        address TEXT,
                        license_number TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE TABLE IF NOT EXISTS cars (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        owner_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        brand TEXT NOT NULL,
                        model TEXT NOT NULL,
                        year INTEGER NOT NULL,
                        registration_number TEXT NOT NULL UNIQUE,
                        category TEXT NOT NULL DEFAULT 'Sedan',
                        fuel_type TEXT NOT NULL DEFAULT 'Petrol',
                        transmission TEXT NOT NULL DEFAULT 'Manual',
                        seating_capacity INTEGER NOT NULL DEFAULT 5,
                        price_per_day REAL NOT NULL,
                        location TEXT NOT NULL,
                        description TEXT,
                        image_url TEXT,
                        is_available INTEGER NOT NULL DEFAULT 1,
                        approval_status TEXT NOT NULL DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS vehicle_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        car_id INTEGER NOT NULL,
                        document_type TEXT NOT NULL,
                        document_url TEXT NOT NULL,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        booking_reference TEXT NOT NULL UNIQUE,
                        customer_id INTEGER NOT NULL,
                        car_id INTEGER NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        total_days INTEGER NOT NULL,
                        daily_rate REAL NOT NULL,
                        total_amount REAL NOT NULL,
                        pickup_location TEXT NOT NULL,
                        drop_location TEXT NOT NULL,
                        booking_status TEXT NOT NULL DEFAULT 'Pending',
                        rejection_reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        booking_id INTEGER NOT NULL,
                        customer_id INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        payment_method TEXT NOT NULL DEFAULT 'UPI',
                        payment_status TEXT NOT NULL DEFAULT 'Completed',
                        transaction_reference TEXT NOT NULL UNIQUE,
                        payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                        FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        booking_id INTEGER NOT NULL UNIQUE,
                        car_id INTEGER NOT NULL,
                        customer_id INTEGER NOT NULL,
                        rating INTEGER NOT NULL,
                        comment TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
                        FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE,
                        FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE
                    );

                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        type TEXT NOT NULL DEFAULT 'info',
                        is_read INTEGER NOT NULL DEFAULT 0,
                        link TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    );
                """)
                conn.commit()
            finally:
                conn.close()

# Singleton accessor instance
db = DatabaseManager()
