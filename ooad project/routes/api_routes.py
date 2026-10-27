from flask import Blueprint, jsonify, request, session
from services.notification_service import NotificationService
from services.booking_service import BookingService
from services.car_service import CarService

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/notifications", methods=["GET"])
def get_notifications():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"notifications": [], "unread_count": 0})

    notifications = NotificationService.get_user_notifications(user_id, limit=10)
    unread_count = NotificationService.get_unread_count(user_id)

    return jsonify({
        "notifications": [n.to_dict() for n in notifications],
        "unread_count": unread_count
    })

@api_bp.route("/notifications/mark-read/<int:notification_id>", methods=["POST"])
def mark_notification_read(notification_id: int):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    success = NotificationService.mark_as_read(notification_id, user_id)
    unread_count = NotificationService.get_unread_count(user_id)
    return jsonify({"success": success, "unread_count": unread_count})

@api_bp.route("/notifications/mark-all-read", methods=["POST"])
def mark_all_read():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    success = NotificationService.mark_all_as_read(user_id)
    return jsonify({"success": success, "unread_count": 0})

@api_bp.route("/calculate-fare", methods=["POST"])
def calculate_fare():
    data = request.get_json() or {}
    car_id = data.get("car_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    estimated_km = data.get("estimated_km", 100)
    try:
        estimated_km = max(0, float(estimated_km))
    except (ValueError, TypeError):
        estimated_km = 100.0

    if not car_id or not start_date or not end_date:
        return jsonify({"success": False, "error": "Missing parameters"}), 400

    car = CarService.get_car_by_id(car_id)
    if not car:
        return jsonify({"success": False, "error": "Vehicle not found"}), 404

    is_valid, days, start_d, end_d, err = BookingService.validate_dates(start_date, end_date)
    if not is_valid:
        return jsonify({"success": False, "error": err}), 400

    is_available = BookingService.is_car_available_for_dates(car_id, start_d, end_d)
    base_fare = round(car.price_per_day * days, 2)
    km_rate = float(car.price_per_km or 10.0)
    km_charges = round(km_rate * estimated_km, 2)
    subtotal = base_fare + km_charges
    deposit = 2000.0  # Refundable security deposit for demo
    taxes = round(subtotal * 0.05, 2)  # 5% GST on rental + km
    total_fare = round(subtotal + taxes, 2)

    return jsonify({
        "success": True,
        "is_available": is_available,
        "days": days,
        "daily_rate": car.price_per_day,
        "base_fare": base_fare,
        "price_per_km": km_rate,
        "estimated_km": estimated_km,
        "km_charges": km_charges,
        "taxes": taxes,
        "refundable_deposit": deposit,
        "grand_total": total_fare
    })
