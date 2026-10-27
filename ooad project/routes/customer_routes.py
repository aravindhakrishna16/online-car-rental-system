from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.auth_routes import login_required, role_required
from services.car_service import CarService
from services.booking_service import BookingService
from services.payment_service import PaymentService
from services.review_service import ReviewService
from database import db

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")

@customer_bp.route("/dashboard")
@login_required
@role_required(["customer"])
def dashboard():
    customer_id = session.get("user_id")
    bookings = BookingService.get_customer_bookings(customer_id)
    
    # Calculate customer metrics
    active_bookings = [b for b in bookings if b.booking_status in ("Pending", "Confirmed")]
    completed_bookings = [b for b in bookings if b.booking_status == "Completed"]
    total_spent = sum(b.total_amount for b in completed_bookings)

    return render_template(
        "customer/dashboard.html",
        bookings=bookings,
        active_bookings=active_bookings,
        completed_bookings=completed_bookings,
        total_spent=total_spent
    )

@customer_bp.route("/book/<int:car_id>", methods=["GET", "POST"])
@login_required
@role_required(["customer"])
def book_car(car_id: int):
    customer_id = session.get("user_id")
    car = CarService.get_car_by_id(car_id)

    if not car or not car.is_bookable():
        flash("This vehicle is currently unavailable for rental.", "warning")
        return redirect(url_for("public.cars"))

    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        pickup_location = request.form.get("pickup_location", "").strip() or car.location
        drop_location = request.form.get("drop_location", "").strip() or car.location
        estimated_km = request.form.get("estimated_km", 100)
        try:
            estimated_km = max(0, int(estimated_km))
        except (ValueError, TypeError):
            estimated_km = 100

        if not start_date or not end_date:
            flash("Please choose valid pickup and return dates.", "danger")
            return render_template("booking.html", car=car)

        success, msg, booking_ref = BookingService.create_booking(
            customer_id=customer_id,
            car_id=car_id,
            start_str=start_date,
            end_str=end_date,
            pickup_location=pickup_location,
            drop_location=drop_location,
            estimated_km=estimated_km
        )

        if not success:
            flash(msg, "danger")
            return render_template("booking.html", car=car, form=request.form)

        flash("Booking request submitted! Your estimated km charges are included. Complete payment to confirm.", "success")
        return redirect(url_for("customer.make_payment", booking_ref=booking_ref))

    # Prepopulate with query params if coming from search or car details
    pre_start = request.args.get("start_date", "")
    pre_end = request.args.get("end_date", "")
    pre_km = request.args.get("estimated_km", "100")

    return render_template("booking.html", car=car, pre_start=pre_start, pre_end=pre_end, pre_km=pre_km)

@customer_bp.route("/payment/<booking_ref>", methods=["GET", "POST"])
@login_required
@role_required(["customer"])
def make_payment(booking_ref: str):
    customer_id = session.get("user_id")
    booking = BookingService.get_booking_by_ref(booking_ref)

    if not booking or booking.customer_id != customer_id:
        flash("Booking not found or access denied.", "danger")
        return redirect(url_for("customer.dashboard"))

    # Check if already paid
    existing_payment = PaymentService.get_payment_by_booking(booking.id)
    if existing_payment and existing_payment.payment_status == "Completed":
        flash("Payment already recorded for this booking.", "info")
        return redirect(url_for("customer.view_invoice", txn_ref=existing_payment.transaction_reference))

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "UPI")
        upi_id = request.form.get("upi_id", "")
        card_holder = request.form.get("card_holder", "")
        card_number = request.form.get("card_number", "")

        success, msg, txn_ref = PaymentService.process_payment(
            booking_id=booking.id,
            customer_id=customer_id,
            payment_method=payment_method,
            upi_id=upi_id,
            card_holder=card_holder,
            card_number=card_number
        )

        if not success:
            flash(msg, "danger")
            return render_template("customer/payment.html", booking=booking)

        flash("Payment Successful! Receipt generated.", "success")
        return redirect(url_for("customer.view_invoice", txn_ref=txn_ref))

    return render_template("customer/payment.html", booking=booking)

@customer_bp.route("/invoice/<txn_ref>")
@login_required
def view_invoice(txn_ref: str):
    user_id = session.get("user_id")
    role = session.get("role")
    
    payment = PaymentService.get_payment_by_ref(txn_ref)
    if not payment:
        flash("Payment transaction record not found.", "danger")
        return redirect(url_for("public.index"))

    booking = BookingService.get_booking_by_id(payment.booking_id)
    if not booking:
        flash("Associated booking not found.", "danger")
        return redirect(url_for("public.index"))

    # Access control: Only the customer, owner, or admin can view this invoice
    if role != "admin" and booking.customer_id != user_id and booking.owner_id != user_id:
        flash("Access denied to view this invoice.", "danger")
        return redirect(url_for("public.index"))

    return render_template("customer/invoice.html", payment=payment, booking=booking)

@customer_bp.route("/cancel-booking/<int:booking_id>", methods=["POST"])
@login_required
@role_required(["customer"])
def cancel_booking(booking_id: int):
    customer_id = session.get("user_id")
    success = BookingService.cancel_booking(booking_id, customer_id, is_admin=False)
    if success:
        flash("Booking has been successfully cancelled.", "success")
    else:
        flash("Unable to cancel this booking. Please check its status.", "danger")
    return redirect(url_for("customer.dashboard"))

@customer_bp.route("/review/<int:booking_id>", methods=["POST"])
@login_required
@role_required(["customer"])
def submit_review(booking_id: int):
    customer_id = session.get("user_id")
    rating = request.form.get("rating", 5)
    comment = request.form.get("comment", "").strip()

    success, msg = ReviewService.add_review(booking_id, customer_id, rating, comment)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for("customer.dashboard"))
