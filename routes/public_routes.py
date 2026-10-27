from flask import Blueprint, render_template, request, flash
from services.car_service import CarService
from services.admin_service import AdminService
from database import db

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    featured_cars = CarService.get_featured_cars(limit=6)
    locations = CarService.get_unique_locations()
    stats = AdminService.get_dashboard_metrics()
    
    # Recent top reviews for social proof
    recent_reviews = db.fetch_all("""
        SELECT r.*, u.name as customer_name, c.name as car_name, c.brand as car_brand
        FROM reviews r
        JOIN users u ON r.customer_id = u.id
        JOIN cars c ON r.car_id = c.id
        WHERE r.rating >= 4
        ORDER BY r.created_at DESC
        LIMIT 3
    """)
    
    return render_template(
        "index.html",
        featured_cars=featured_cars,
        locations=locations,
        stats=stats,
        recent_reviews=recent_reviews
    )

@public_bp.route("/cars")
def cars():
    location = request.args.get("location")
    category = request.args.get("category")
    fuel_type = request.args.get("fuel_type")
    transmission = request.args.get("transmission")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    seating = request.args.get("seating")
    sort_by = request.args.get("sort_by", "popular")

    cars_list = CarService.search_cars(
        location=location,
        category=category,
        fuel_type=fuel_type,
        transmission=transmission,
        min_price=min_price,
        max_price=max_price,
        seating=seating,
        sort_by=sort_by
    )

    locations = CarService.get_unique_locations()

    return render_template(
        "cars.html",
        cars=cars_list,
        locations=locations,
        current_filters={
            "location": location or "",
            "category": category or "",
            "fuel_type": fuel_type or "",
            "transmission": transmission or "",
            "min_price": min_price or "",
            "max_price": max_price or "",
            "seating": seating or "",
            "sort_by": sort_by
        }
    )

@public_bp.route("/cars/<int:car_id>")
def car_details(car_id: int):
    car = CarService.get_car_by_id(car_id)
    if not car or (car.approval_status != "approved" and not car.is_available):
        flash("Vehicle not found or not currently available for rental.", "warning")
        return render_template("404.html"), 404

    reviews = CarService.get_car_reviews(car_id)
    similar_cars = CarService.search_cars(category=car.category, limit=3)
    similar_cars = [c for c in similar_cars if c.id != car.id]

    return render_template(
        "car_details.html",
        car=car,
        reviews=reviews,
        similar_cars=similar_cars
    )

@public_bp.route("/about")
def about():
    stats = AdminService.get_dashboard_metrics()
    return render_template("about.html", stats=stats)

@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()
        flash(f"Thank you, {name}! Your query regarding '{subject}' has been received. Our team will contact you shortly.", "success")
    return render_template("contact.html")
