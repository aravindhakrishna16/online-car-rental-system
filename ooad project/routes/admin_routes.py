from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.auth_routes import login_required, role_required
from services.admin_service import AdminService
from services.car_service import CarService
from services.booking_service import BookingService
from services.payment_service import PaymentService
from services.review_service import ReviewService
from database import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
@role_required(["admin"])
def dashboard():
    metrics = AdminService.get_dashboard_metrics()
    pending_cars = CarService.get_all_cars_admin(approval_filter="pending")
    recent_bookings = BookingService.get_all_bookings_admin()[:8]
    category_dist = AdminService.get_category_distribution()

    return render_template(
        "admin/dashboard.html",
        metrics=metrics,
        pending_cars=pending_cars,
        recent_bookings=recent_bookings,
        category_dist=category_dist
    )

@admin_bp.route("/verify-cars")
@login_required
@role_required(["admin"])
def verify_cars():
    status_filter = request.args.get("status", "pending")
    cars = CarService.get_all_cars_admin(approval_filter=status_filter)
    return render_template("admin/verify_cars.html", cars=cars, current_status=status_filter)

@admin_bp.route("/approve-car/<int:car_id>", methods=["POST"])
@login_required
@role_required(["admin"])
def approve_car(car_id: int):
    success = CarService.admin_verify_car(car_id, "approved")
    if success:
        flash("Vehicle listing approved successfully!", "success")
    else:
        flash("Failed to approve vehicle.", "danger")
    return redirect(url_for("admin.verify_cars"))

@admin_bp.route("/reject-car/<int:car_id>", methods=["POST"])
@login_required
@role_required(["admin"])
def reject_car(car_id: int):
    success = CarService.admin_verify_car(car_id, "rejected")
    if success:
        flash("Vehicle listing rejected.", "info")
    else:
        flash("Failed to reject vehicle.", "danger")
    return redirect(url_for("admin.verify_cars"))

@admin_bp.route("/users")
@login_required
@role_required(["admin"])
def manage_users():
    role_filter = request.args.get("role", "all")
    status_filter = request.args.get("status", "all")
    users = AdminService.get_all_users(role_filter, status_filter)
    return render_template("admin/manage_users.html", users=users, role_filter=role_filter, status_filter=status_filter)

@admin_bp.route("/toggle-user/<int:user_id>", methods=["POST"])
@login_required
@role_required(["admin"])
def toggle_user(user_id: int):
    admin_id = session.get("user_id")
    if user_id == admin_id:
        flash("You cannot deactivate your own administrative account.", "warning")
        return redirect(url_for("admin.manage_users"))

    user_row = db.fetch_one("SELECT status FROM users WHERE id = %s", (user_id,))
    if user_row:
        AdminService.toggle_user_status(user_id, user_row["status"])
        flash("User status updated successfully.", "success")
    return redirect(url_for("admin.manage_users"))

@admin_bp.route("/bookings")
@login_required
@role_required(["admin"])
def all_bookings():
    status_filter = request.args.get("status", "all")
    bookings = BookingService.get_all_bookings_admin(status_filter=status_filter)
    return render_template("admin/all_bookings.html", bookings=bookings, current_status=status_filter)

@admin_bp.route("/payments")
@login_required
@role_required(["admin"])
def payments():
    payments_list = PaymentService.get_all_payments_admin(limit=100)
    total_rev = sum(p.amount for p in payments_list if p.payment_status == "Completed")
    return render_template("admin/payments.html", payments=payments_list, total_revenue=total_rev)

@admin_bp.route("/reviews")
@login_required
@role_required(["admin"])
def reviews():
    reviews_list = ReviewService.get_all_reviews_admin()
    return render_template("admin/reviews.html", reviews=reviews_list)

@admin_bp.route("/delete-review/<int:review_id>", methods=["POST"])
@login_required
@role_required(["admin"])
def delete_review(review_id: int):
    success = ReviewService.delete_review(review_id)
    if success:
        flash("Review removed by moderator.", "success")
    else:
        flash("Failed to delete review.", "danger")
    return redirect(url_for("admin.reviews"))

@admin_bp.route("/reports")
@login_required
@role_required(["admin"])
def reports():
    metrics = AdminService.get_dashboard_metrics()
    categories = AdminService.get_category_distribution()
    return render_template("admin/reports.html", metrics=metrics, categories=categories)
