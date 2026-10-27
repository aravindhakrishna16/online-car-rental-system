from database import db
from models.car import Car
from models.review import Review
from services.notification_service import NotificationService

class CarService:
    """
    Business service encapsulating Car catalog querying, filtering,
    listing lifecycle, and administrative verification.
    """
    @staticmethod
    def get_car_by_id(car_id: int) -> Car:
        query = """
            SELECT c.*, u.name as owner_name, u.phone as owner_phone,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.id) as total_reviews
            FROM cars c
            JOIN users u ON c.owner_id = u.id
            LEFT JOIN reviews r ON c.id = r.car_id
            WHERE c.id = %s
            GROUP BY c.id
        """
        row = db.fetch_one(query, (car_id,))
        if not row:
            return None
        return Car.from_dict(row)

    @staticmethod
    def search_cars(location=None, category=None, fuel_type=None,
                    transmission=None, min_price=None, max_price=None,
                    seating=None, sort_by="popular", limit=50):
        conditions = ["c.approval_status = 'approved'", "c.is_available = 1", "u.status = 'active'"]
        params = []

        if location:
            conditions.append("LOWER(c.location) LIKE %s")
            params.append(f"%{location.strip().lower()}%")

        if category and category.lower() != "all":
            conditions.append("LOWER(c.category) = %s")
            params.append(category.strip().lower())

        if fuel_type and fuel_type.lower() != "all":
            conditions.append("LOWER(c.fuel_type) = %s")
            params.append(fuel_type.strip().lower())

        if transmission and transmission.lower() != "all":
            conditions.append("LOWER(c.transmission) = %s")
            params.append(transmission.strip().lower())

        if min_price:
            try:
                conditions.append("c.price_per_day >= %s")
                params.append(float(min_price))
            except ValueError:
                pass

        if max_price:
            try:
                conditions.append("c.price_per_day <= %s")
                params.append(float(max_price))
            except ValueError:
                pass

        if seating:
            try:
                conditions.append("c.seating_capacity >= %s")
                params.append(int(seating))
            except ValueError:
                pass

        where_clause = " AND ".join(conditions)

        order_clause = "c.created_at DESC"
        if sort_by == "price_asc":
            order_clause = "c.price_per_day ASC"
        elif sort_by == "price_desc":
            order_clause = "c.price_per_day DESC"
        elif sort_by == "rating":
            order_clause = "avg_rating DESC"

        query = f"""
            SELECT c.*, u.name as owner_name, u.phone as owner_phone,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.id) as total_reviews
            FROM cars c
            JOIN users u ON c.owner_id = u.id
            LEFT JOIN reviews r ON c.id = r.car_id
            WHERE {where_clause}
            GROUP BY c.id
            ORDER BY {order_clause}
            LIMIT %s
        """
        params.append(limit)
        rows = db.fetch_all(query, tuple(params))
        return [Car.from_dict(r) for r in rows]

    @staticmethod
    def get_featured_cars(limit: int = 6):
        query = """
            SELECT c.*, u.name as owner_name, u.phone as owner_phone,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.id) as total_reviews
            FROM cars c
            JOIN users u ON c.owner_id = u.id
            LEFT JOIN reviews r ON c.id = r.car_id
            WHERE c.approval_status = 'approved' AND c.is_available = 1 AND u.status = 'active'
            GROUP BY c.id
            ORDER BY avg_rating DESC, c.price_per_day ASC
            LIMIT %s
        """
        rows = db.fetch_all(query, (limit,))
        return [Car.from_dict(r) for r in rows]

    @staticmethod
    def get_owner_cars(owner_id: int):
        query = """
            SELECT c.*, u.name as owner_name,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.id) as total_reviews
            FROM cars c
            JOIN users u ON c.owner_id = u.id
            LEFT JOIN reviews r ON c.id = r.car_id
            WHERE c.owner_id = %s
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """
        rows = db.fetch_all(query, (owner_id,))
        return [Car.from_dict(r) for r in rows]

    @staticmethod
    def get_all_cars_admin(approval_filter=None):
        where = ""
        params = []
        if approval_filter and approval_filter != "all":
            where = "WHERE c.approval_status = %s"
            params.append(approval_filter)

        query = f"""
            SELECT c.*, u.name as owner_name, u.email as owner_email, u.phone as owner_phone,
                   COALESCE(AVG(r.rating), 0) as avg_rating,
                   COUNT(r.id) as total_reviews
            FROM cars c
            JOIN users u ON c.owner_id = u.id
            LEFT JOIN reviews r ON c.id = r.car_id
            {where}
            GROUP BY c.id
            ORDER BY c.created_at DESC
        """
        rows = db.fetch_all(query, tuple(params) if params else None)
        return [Car.from_dict(r) for r in rows]

    @staticmethod
    def add_car(owner_id: int, car_data: dict) -> int:
        query = """
            INSERT INTO cars (
                owner_id, name, brand, model, year, registration_number,
                category, fuel_type, transmission, seating_capacity,
                price_per_day, price_per_km, location, description, image_url,
                is_available, approval_status, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                1, 'pending', CURRENT_TIMESTAMP
            )
        """
        last_id, _ = db.execute_query(query, (
            owner_id,
            car_data.get("name"),
            car_data.get("brand"),
            car_data.get("model"),
            car_data.get("year", 2023),
            car_data.get("registration_number", "").upper(),
            car_data.get("category", "Sedan"),
            car_data.get("fuel_type", "Petrol"),
            car_data.get("transmission", "Manual"),
            car_data.get("seating_capacity", 5),
            car_data.get("price_per_day", 1500.0),
            car_data.get("price_per_km", 10.0),
            car_data.get("location", "Bangalore"),
            car_data.get("description", ""),
            car_data.get("image_url", "/static/images/default_car.jpg")
        ))

        # Notify Admins of new vehicle submission
        admin_row = db.fetch_one("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        if admin_row:
            NotificationService.send_notification(
                user_id=admin_row["id"],
                title="New Vehicle Pending Verification",
                message=f"Car '{car_data.get('name')}' ({car_data.get('registration_number')}) submitted for verification.",
                type="approval",
                link="/admin/verify-cars"
            )

        return last_id

    @staticmethod
    def update_car(car_id: int, owner_id: int, car_data: dict) -> bool:
        # Check car ownership
        car = CarService.get_car_by_id(car_id)
        if not car or car.owner_id != owner_id:
            return False

        query = """
            UPDATE cars SET
                name = %s, brand = %s, model = %s, year = %s,
                category = %s, fuel_type = %s, transmission = %s,
                seating_capacity = %s, price_per_day = %s, price_per_km = %s,
                location = %s, description = %s,
                image_url = COALESCE(%s, image_url),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND owner_id = %s
        """
        _, count = db.execute_query(query, (
            car_data.get("name"),
            car_data.get("brand"),
            car_data.get("model"),
            car_data.get("year"),
            car_data.get("category"),
            car_data.get("fuel_type"),
            car_data.get("transmission"),
            car_data.get("seating_capacity"),
            car_data.get("price_per_day"),
            car_data.get("price_per_km", 10.0),
            car_data.get("location"),
            car_data.get("description"),
            car_data.get("image_url"),
            car_id,
            owner_id
        ))
        return count > 0

    @staticmethod
    def delete_car(car_id: int, owner_id: int = None, is_admin: bool = False) -> bool:
        car = CarService.get_car_by_id(car_id)
        if not car:
            return False
        if not is_admin and car.owner_id != owner_id:
            return False

        query = "DELETE FROM cars WHERE id = %s"
        _, count = db.execute_query(query, (car_id,))
        return count > 0

    @staticmethod
    def toggle_availability(car_id: int, owner_id: int) -> bool:
        car = CarService.get_car_by_id(car_id)
        if not car or car.owner_id != owner_id:
            return False

        new_status = 0 if car.is_available else 1
        query = "UPDATE cars SET is_available = %s WHERE id = %s AND owner_id = %s"
        _, count = db.execute_query(query, (new_status, car_id, owner_id))
        return count > 0

    @staticmethod
    def admin_verify_car(car_id: int, status: str) -> bool:
        if status not in ("approved", "rejected"):
            return False

        query = "UPDATE cars SET approval_status = %s WHERE id = %s"
        _, count = db.execute_query(query, (status, car_id))

        car = CarService.get_car_by_id(car_id)
        if car:
            title = f"Vehicle Listing {status.capitalize()}"
            msg = f"Your listing for '{car.name}' ({car.registration_number}) has been {status} by administrator."
            NotificationService.send_notification(
                user_id=car.owner_id,
                title=title,
                message=msg,
                type="approval",
                link="/owner/my-cars"
            )
        return count > 0

    @staticmethod
    def get_car_reviews(car_id: int):
        query = """
            SELECT r.*, u.name as customer_name
            FROM reviews r
            JOIN users u ON r.customer_id = u.id
            WHERE r.car_id = %s
            ORDER BY r.created_at DESC
        """
        rows = db.fetch_all(query, (car_id,))
        return [Review.from_dict(r) for r in rows]

    @staticmethod
    def get_unique_locations():
        query = "SELECT DISTINCT location FROM cars WHERE approval_status = 'approved' ORDER BY location ASC"
        rows = db.fetch_all(query)
        return [r["location"] for r in rows if r.get("location")]
