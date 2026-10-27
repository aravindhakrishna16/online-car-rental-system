import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
from routes.auth_routes import login_required, role_required
from services.car_service import CarService
from services.booking_service import BookingService
from services.payment_service import PaymentService
from database import db

owner_bp = Blueprint("owner", __name__, url_prefix="/owner")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

@owner_bp.route("/dashboard")
@login_required
@role_required(["owner"])
def dashboard():
    owner_id = session.get("user_id")
    cars = CarService.get_owner_cars(owner_id)
    bookings = BookingService.get_owner_bookings(owner_id)
    earnings_stats = PaymentService.get_owner_earnings_summary(owner_id)

    pending_bookings = [b for b in bookings if b.booking_status == "Pending"]
    confirmed_bookings = [b for b in bookings if b.booking_status == "Confirmed"]
    completed_bookings = [b for b in bookings if b.booking_status == "Completed"]

    # Host's vehicle reviews
    reviews = db.fetch_all("""
        SELECT r.*, u.name as customer_name, c.name as car_name, c.brand as car_brand
        FROM reviews r
        JOIN cars c ON r.car_id = c.id
        JOIN users u ON r.customer_id = u.id
        WHERE c.owner_id = %s
        ORDER BY r.created_at DESC
        LIMIT 10
    """, (owner_id,))

    return render_template(
        "owner/dashboard.html",
        cars=cars,
        bookings=bookings,
        pending_bookings=pending_bookings,
        confirmed_bookings=confirmed_bookings,
        completed_bookings=completed_bookings,
        earnings_stats=earnings_stats,
        reviews=reviews
    )

@owner_bp.route("/my-cars")
@login_required
@role_required(["owner"])
def my_cars():
    owner_id = session.get("user_id")
    cars = CarService.get_owner_cars(owner_id)
    return render_template("owner/my_cars.html", cars=cars)

@owner_bp.route("/add-car", methods=["GET", "POST"])
@login_required
@role_required(["owner"])
def add_car():
    owner_id = session.get("user_id")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        brand = request.form.get("brand", "").strip()
        model = request.form.get("model", "").strip()
        year = request.form.get("year", 2024)
        reg_number = request.form.get("registration_number", "").strip().upper()
        category = request.form.get("category", "Sedan")
        fuel_type = request.form.get("fuel_type", "Petrol")
        transmission = request.form.get("transmission", "Manual")
        seating_capacity = request.form.get("seating_capacity", 5)
        price_per_day = request.form.get("price_per_day", 1500.0)
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()

        if not name or not brand or not model or not reg_number or not location:
            flash("Please fill in all mandatory vehicle details.", "danger")
            return render_template("owner/car_form.html", action="Add")

        # Check for duplicate registration number
        existing = db.fetch_one("SELECT id FROM cars WHERE registration_number = %s", (reg_number,))
        if existing:
            flash(f"A vehicle with registration number '{reg_number}' already exists.", "danger")
            return render_template("owner/car_form.html", action="Add")

        # Handle Image Upload
        image_url = "/static/images/default_car.jpg"
        if "car_image" in request.files:
            file = request.files["car_image"]
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{reg_number}_{file.filename}")
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                image_url = f"/static/uploads/{filename}"

        car_data = {
            "name": name,
            "brand": brand,
            "model": model,
            "year": year,
            "registration_number": reg_number,
            "category": category,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "seating_capacity": seating_capacity,
            "price_per_day": price_per_day,
            "price_per_km": request.form.get("price_per_km", 10.0),
            "location": location,
            "description": description,
            "image_url": image_url
        }

        car_id = CarService.add_car(owner_id, car_data)
        flash(f"Vehicle '{name}' listed successfully! It has been submitted for admin verification.", "success")
        return redirect(url_for("owner.my_cars"))

    return render_template("owner/car_form.html", action="Add")

@owner_bp.route("/edit-car/<int:car_id>", methods=["GET", "POST"])
@login_required
@role_required(["owner"])
def edit_car(car_id: int):
    owner_id = session.get("user_id")
    car = CarService.get_car_by_id(car_id)

    if not car or car.owner_id != owner_id:
        flash("Vehicle not found or permission denied.", "danger")
        return redirect(url_for("owner.my_cars"))

    if request.method == "POST":
        image_url = None
        if "car_image" in request.files:
            file = request.files["car_image"]
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{car.registration_number}_{file.filename}")
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                image_url = f"/static/uploads/{filename}"

        car_data = {
            "name": request.form.get("name", "").strip(),
            "brand": request.form.get("brand", "").strip(),
            "model": request.form.get("model", "").strip(),
            "year": request.form.get("year", 2024),
            "category": request.form.get("category", "Sedan"),
            "fuel_type": request.form.get("fuel_type", "Petrol"),
            "transmission": request.form.get("transmission", "Manual"),
            "seating_capacity": request.form.get("seating_capacity", 5),
            "price_per_day": request.form.get("price_per_day", 1500.0),
            "price_per_km": request.form.get("price_per_km", 10.0),
            "location": request.form.get("location", "").strip(),
            "description": request.form.get("description", "").strip(),
            "image_url": image_url
        }

        success = CarService.update_car(car_id, owner_id, car_data)
        if success:
            flash(f"Vehicle '{car.name}' updated successfully.", "success")
            return redirect(url_for("owner.my_cars"))
        else:
            flash("Failed to update vehicle.", "danger")

    return render_template("owner/car_form.html", action="Edit", car=car)

@owner_bp.route("/delete-car/<int:car_id>", methods=["POST"])
@login_required
@role_required(["owner"])
def delete_car(car_id: int):
    owner_id = session.get("user_id")
    success = CarService.delete_car(car_id, owner_id=owner_id, is_admin=False)
    if success:
        flash("Car listing deleted successfully.", "success")
    else:
        flash("Could not delete vehicle. Verify ownership.", "danger")
    return redirect(url_for("owner.my_cars"))

@owner_bp.route("/toggle-availability/<int:car_id>", methods=["POST"])
@login_required
@role_required(["owner"])
def toggle_availability(car_id: int):
    owner_id = session.get("user_id")
    success = CarService.toggle_availability(car_id, owner_id)
    if success:
        flash("Vehicle availability status toggled successfully.", "success")
    else:
        flash("Failed to update availability.", "danger")
    return redirect(url_for("owner.my_cars"))

@owner_bp.route("/approve-booking/<int:booking_id>", methods=["POST"])
@login_required
@role_required(["owner"])
def approve_booking(booking_id: int):
    owner_id = session.get("user_id")
    success = BookingService.approve_booking(booking_id, owner_id)
    if success:
        flash("Booking confirmed successfully!", "success")
    else:
        flash("Failed to approve booking. It may have already been handled.", "danger")
    return redirect(url_for("owner.dashboard"))

@owner_bp.route("/reject-booking/<int:booking_id>", methods=["POST"])
@login_required
@role_required(["owner"])
def reject_booking(booking_id: int):
    owner_id = session.get("user_id")
    reason = request.form.get("reason", "Vehicle unavailable on selected dates")
    success = BookingService.reject_booking(booking_id, owner_id, reason)
    if success:
        flash("Booking declined.", "info")
    else:
        flash("Failed to decline booking.", "danger")
    return redirect(url_for("owner.dashboard"))

@owner_bp.route("/complete-booking/<int:booking_id>", methods=["POST"])
@login_required
@role_required(["owner"])
def complete_booking(booking_id: int):
    owner_id = session.get("user_id")
    success = BookingService.complete_booking(booking_id, owner_id)
    if success:
        flash("Rental marked as Completed! Customer notified for review.", "success")
    else:
        flash("Could not complete booking.", "danger")
    return redirect(url_for("owner.dashboard"))
