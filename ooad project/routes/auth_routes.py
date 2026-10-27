from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash
from database import db
from models.user import UserFactory

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for("auth.login", next=request.path))
            user_role = session.get("role")
            if user_role not in allowed_roles:
                flash("Access denied: You do not have permission for this section.", "danger")
                return redirect(url_for("public.index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        role = session.get("role")
        if role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif role == "owner":
            return redirect(url_for("owner.dashboard"))
        return redirect(url_for("customer.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_page = request.form.get("next") or request.args.get("next")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html", email=email)

        user_row = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        if not user_row:
            flash("Invalid email or password.", "danger")
            return render_template("login.html", email=email)

        user = UserFactory.create_user(user_row)
        if not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", email=email)

        if not user.is_active():
            flash("Your account has been deactivated. Please contact support.", "danger")
            return render_template("login.html", email=email)

        # Store session variables
        session.clear()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email
        session["role"] = user.role

        flash(f"Welcome back, {user.name}!", "success")

        if next_page and next_page.startswith("/"):
            return redirect(next_page)

        if user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        elif user.role == "owner":
            return redirect(url_for("owner.dashboard"))
        else:
            return redirect(url_for("customer.dashboard"))

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("public.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "customer").lower()
        address = request.form.get("address", "").strip()
        license_number = request.form.get("license_number", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Input validations
        if not name or not email or not phone or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("register.html", form=request.form)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html", form=request.form)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", form=request.form)

        if role not in ("customer", "owner"):
            role = "customer"

        # Check existing email
        existing = db.fetch_one("SELECT id FROM users WHERE email = %s", (email,))
        if existing:
            flash("An account with this email address already exists. Please login instead.", "danger")
            return render_template("register.html", form=request.form)

        pw_hash = generate_password_hash(password)
        query = """
            INSERT INTO users (name, email, phone, password_hash, role, status, address, license_number, created_at)
            VALUES (%s, %s, %s, %s, %s, 'active', %s, %s, CURRENT_TIMESTAMP)
        """
        user_id, _ = db.execute_query(query, (name, email, phone, pw_hash, role, address, license_number))

        session.clear()
        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = email
        session["role"] = role

        flash(f"Account created successfully! Welcome to DriveEase, {name}.", "success")
        if role == "owner":
            return redirect(url_for("owner.dashboard"))
        return redirect(url_for("customer.dashboard"))

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("public.index"))

@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session.get("user_id")
    user_row = db.fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
    user = UserFactory.create_user(user_row)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        license_number = request.form.get("license_number", "").strip()
        new_password = request.form.get("new_password", "").strip()

        if not name or not phone:
            flash("Name and phone number are required.", "danger")
            return render_template("customer/profile.html", user=user)

        if new_password:
            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return render_template("customer/profile.html", user=user)
            pw_hash = generate_password_hash(new_password)
            db.execute_query(
                "UPDATE users SET name=%s, phone=%s, address=%s, license_number=%s, password_hash=%s WHERE id=%s",
                (name, phone, address, license_number, pw_hash, user_id)
            )
        else:
            db.execute_query(
                "UPDATE users SET name=%s, phone=%s, address=%s, license_number=%s WHERE id=%s",
                (name, phone, address, license_number, user_id)
            )

        session["user_name"] = name
        flash("Profile updated successfully!", "success")
        return redirect(url_for("auth.profile"))

    return render_template("customer/profile.html", user=user)
