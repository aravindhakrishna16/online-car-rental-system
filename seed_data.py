from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from database import db

def seed_all():
    print("[Seed] Initializing database schema...")
    db.init_database()

    # Check if users already seeded
    existing = db.fetch_one("SELECT COUNT(*) as count FROM users")
    if existing and existing["count"] > 0:
        print(f"[Seed] Database already contains {existing['count']} users. Skipping seeding.")
        return

    print("[Seed] Seeding demo users...")
    password_hash = generate_password_hash("password123")
    admin_pw = generate_password_hash("admin123")
    owner_pw = generate_password_hash("owner123")
    cust_pw = generate_password_hash("customer123")

    users_data = [
        # Admin
        ("Admin Authority", "admin@driveease.com", "9876543210", admin_pw, "admin", "active", "Koramangala, Bangalore", "DL-ADM-001"),
        # Car Owners
        ("Rahul Sharma", "rahul.host@driveease.com", "9876543211", owner_pw, "owner", "active", "Indiranagar, Bangalore", "DL-OWN-101"),
        ("Priya Patel", "priya.fleet@driveease.com", "9876543212", owner_pw, "owner", "active", "Bandra West, Mumbai", "DL-OWN-102"),
        # Customers
        ("Arjun Verma", "arjun.renter@driveease.com", "9876543213", cust_pw, "customer", "active", "HSR Layout, Bangalore", "DL-CUST-201"),
        ("Sneha Nair", "sneha.travel@driveease.com", "9876543214", cust_pw, "customer", "active", "Connaught Place, Delhi", "DL-CUST-202"),
    ]

    user_ids = {}
    for name, email, phone, pw, role, status, addr, lic in users_data:
        uid, _ = db.execute_query(
            """INSERT INTO users (name, email, phone, password_hash, role, status, address, license_number, created_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)""",
            (name, email, phone, pw, role, status, addr, lic)
        )
        user_ids[email] = uid

    print(f"[Seed] Created {len(user_ids)} users.")

    rahul_id = user_ids["rahul.host@driveease.com"]
    priya_id = user_ids["priya.fleet@driveease.com"]

    print("[Seed] Seeding cars...")
    cars_data = [
        # Owner 1 (Rahul)
        (rahul_id, "Swift ZXi AMT", "Maruti Suzuki", "Swift", 2023, "KA01MF1234",
         "Hatchback", "Petrol", "Automatic", 5, 1499.0, 8.0, "Bangalore",
         "Zippy, fuel-efficient city hatchback. Perfect for daily commutes and quick weekend getaways. Sanitized and well-maintained.",
         "/static/images/cars/swift.jpg", 1, "approved"),

        (rahul_id, "Honda City ZX", "Honda", "City", 2024, "KA03NB5678",
         "Sedan", "Petrol", "Automatic", 5, 2399.0, 10.0, "Bangalore",
         "Premium executive sedan with plush leather seats, sunroof, Android Auto/Apple CarPlay, and great highway stability.",
         "/static/images/cars/city.jpg", 1, "approved"),

        (rahul_id, "Mahindra Thar LX 4x4", "Mahindra", "Thar", 2023, "KA04TR9999",
         "SUV", "Diesel", "Manual", 4, 3499.0, 14.0, "Bangalore",
         "Iconic 4x4 adventure SUV with convertible hard top, rugged styling, and great ground clearance for off-road trails.",
         "/static/images/cars/thar.jpg", 1, "approved"),

        (rahul_id, "Tata Nexon EV Max", "Tata", "Nexon EV", 2024, "KA05EV7788",
         "Electric", "Electric", "Automatic", 5, 2699.0, 7.0, "Bangalore",
         "Eco-friendly electric compact SUV with 400km range, ventilated seats, wireless charging, and silent drive experience.",
         "/static/images/cars/nexon_ev.jpg", 1, "approved"),

        # Owner 2 (Priya)
        (priya_id, "Hyundai Creta SX(O)", "Hyundai", "Creta", 2024, "MH02CR4321",
         "SUV", "Diesel", "Automatic", 5, 3199.0, 13.0, "Mumbai",
         "India's favorite panoramic-sunroof compact SUV. Loaded with ADAS, Bose sound system, and supreme legroom.",
         "/static/images/cars/creta.jpg", 1, "approved"),

        (priya_id, "Toyota Fortuner 4x4 Legender", "Toyota", "Fortuner", 2023, "MH01FT8888",
         "SUV", "Diesel", "Automatic", 7, 5499.0, 18.0, "Mumbai",
         "Mighty 7-seater full-size luxury SUV. Unmatched road presence, bulletproof reliability, and luxury comfort.",
         "/static/images/cars/fortuner.jpg", 1, "approved"),

        (priya_id, "BMW 3 Series Gran Limousine", "BMW", "3 Series", 2024, "MH04BM0007",
         "Luxury", "Petrol", "Automatic", 5, 7999.0, 25.0, "Mumbai",
         "Ultra-luxurious German saloon with extended wheelbase, M-Sport styling, and sublime twin-turbo performance.",
         "/static/images/cars/bmw.jpg", 1, "approved"),

        # Pending approval car for Admin demonstration
        (rahul_id, "Kia Seltos X-Line", "Kia", "Seltos", 2024, "KA02KS5544",
         "SUV", "Petrol", "Automatic", 5, 2899.0, 12.0, "Bangalore",
         "Matte graphite edition Seltos with head-up display and 360-degree camera. Awaiting admin verification.",
         "/static/images/cars/seltos.jpg", 1, "pending"),
    ]

    car_ids = []
    for c in cars_data:
        cid, _ = db.execute_query(
            """INSERT INTO cars (
                owner_id, name, brand, model, year, registration_number,
                category, fuel_type, transmission, seating_capacity,
                price_per_day, price_per_km, location, description, image_url,
                is_available, approval_status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)""",
            c
        )
        car_ids.append(cid)

    print(f"[Seed] Created {len(car_ids)} cars.")

    # Upload document sample for pending car
    db.execute_query(
        """INSERT INTO vehicle_documents (car_id, document_type, document_url, uploaded_at)
           VALUES (%s, %s, %s, CURRENT_TIMESTAMP)""",
        (car_ids[-1], "RC_BOOK", "/static/images/sample_rc.png")
    )

    arjun_id = user_ids["arjun.renter@driveease.com"]
    sneha_id = user_ids["sneha.travel@driveease.com"]

    today = date.today()
    past_start = today - timedelta(days=5)
    past_end = today - timedelta(days=2)
    current_start = today
    current_end = today + timedelta(days=3)
    future_start = today + timedelta(days=7)
    future_end = today + timedelta(days=10)

    print("[Seed] Seeding bookings...")
    # 1. Completed Booking (Arjun with Honda City)
    b1_id, _ = db.execute_query(
        """INSERT INTO bookings (
            booking_reference, customer_id, car_id, start_date, end_date,
            total_days, daily_rate, estimated_km, km_rate, km_charges, total_amount,
            pickup_location, drop_location, booking_status, created_at
        ) VALUES (
            'BK-COMPLETED1', %s, %s, %s, %s,
            3, 2399.0, 150, 10.0, 1500.0, 9131.85,
            'Koramangala 4th Block', 'Bangalore Airport T1',
            'Completed', CURRENT_TIMESTAMP
        )""",
        (arjun_id, car_ids[1], str(past_start), str(past_end))
    )

    # Payment for Completed booking
    db.execute_query(
        """INSERT INTO payments (
            booking_id, customer_id, amount, payment_method,
            payment_status, transaction_reference, payment_date
        ) VALUES (%s, %s, 9131.85, 'UPI', 'Completed', 'TXN-ARJUN990011', CURRENT_TIMESTAMP)""",
        (b1_id, arjun_id)
    )

    # Review for Completed booking
    db.execute_query(
        """INSERT INTO reviews (booking_id, car_id, customer_id, rating, comment, created_at)
           VALUES (%s, %s, %s, 5, 'Super smooth experience! The Honda City was sparkling clean, delivered on time, and gave great mileage on Mysore highway. Highly recommended host!', CURRENT_TIMESTAMP)""",
        (b1_id, car_ids[1], arjun_id)
    )

    # 2. Confirmed Booking (Sneha with Creta)
    b2_id, _ = db.execute_query(
        """INSERT INTO bookings (
            booking_reference, customer_id, car_id, start_date, end_date,
            total_days, daily_rate, estimated_km, km_rate, km_charges, total_amount,
            pickup_location, drop_location, booking_status, created_at
        ) VALUES (
            'BK-CONFIRM882', %s, %s, %s, %s,
            3, 3199.0, 200, 13.0, 2600.0, 12806.85,
            'Bandra Kurla Complex', 'Mumbai Domestic Airport',
            'Confirmed', CURRENT_TIMESTAMP
        )""",
        (sneha_id, car_ids[4], str(current_start), str(current_end))
    )

    # Payment for Confirmed booking
    db.execute_query(
        """INSERT INTO payments (
            booking_id, customer_id, amount, payment_method,
            payment_status, transaction_reference, payment_date
        ) VALUES (%s, %s, 12806.85, 'CARD', 'Completed', 'TXN-SNEHA445566', CURRENT_TIMESTAMP)""",
        (b2_id, sneha_id)
    )

    # 3. Pending Booking (Arjun with Thar - for Host approval demo)
    b3_id, _ = db.execute_query(
        """INSERT INTO bookings (
            booking_reference, customer_id, car_id, start_date, end_date,
            total_days, daily_rate, estimated_km, km_rate, km_charges, total_amount,
            pickup_location, drop_location, booking_status, created_at
        ) VALUES (
            'BK-PENDING773', %s, %s, %s, %s,
            3, 3499.0, 250, 14.0, 3500.0, 14696.85,
            'Indiranagar Metro Station', 'Coorg Hill Station',
            'Pending', CURRENT_TIMESTAMP
        )""",
        (arjun_id, car_ids[2], str(future_start), str(future_end))
    )

    print("[Seed] Seeding sample notifications...")
    notifications = [
        (arjun_id, "Booking Confirmed!", "Your booking BK-CONFIRM882 is confirmed. Have a safe journey!", "booking", "/customer/dashboard"),
        (rahul_id, "New Booking Request", "You received a new booking request BK-PENDING773 for Thar 4x4.", "booking", "/owner/dashboard"),
        (user_ids["admin@driveease.com"], "Car Verification Needed", "Kia Seltos X-Line submitted by Rahul Sharma requires verification.", "approval", "/admin/verify-cars"),
    ]
    for uid, title, msg, ntype, link in notifications:
        db.execute_query(
            """INSERT INTO notifications (user_id, title, message, type, is_read, link, created_at)
               VALUES (%s, %s, %s, %s, 0, %s, CURRENT_TIMESTAMP)""",
            (uid, title, msg, ntype, link)
        )

    print("[Seed] Database seeding completed successfully!")

if __name__ == "__main__":
    seed_all()
