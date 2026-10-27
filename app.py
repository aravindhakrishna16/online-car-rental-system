import os
from flask import Flask, render_template, session, g
from config import Config
from database import db
from models.user import UserFactory
from services.notification_service import NotificationService
from routes import auth_bp, public_bp, customer_bp, owner_bp, admin_bp, api_bp

def create_app(config_class=Config):
    """Application factory for DriveEase Online Car Rental System."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize Database Schema & Tables
    with app.app_context():
        try:
            db.init_database()
            # Auto-seed if database is clean
            existing_user = db.fetch_one("SELECT COUNT(*) as count FROM users")
            if not existing_user or existing_user["count"] == 0:
                from seed_data import seed_all
                print("[DriveEase] Fresh database detected. Executing automatic seed...")
                seed_all()
        except Exception as e:
            print(f"[DriveEase] Database startup notice: {e}")

    # Register Blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(owner_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Global Context Processors for Templates
    @app.context_processor
    def inject_global_data():
        user = None
        unread_notifications = 0
        user_id = session.get("user_id")
        if user_id:
            user_row = db.fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
            if user_row:
                user = UserFactory.create_user(user_row)
                unread_notifications = NotificationService.get_unread_count(user_id)

        return {
            "current_user": user,
            "unread_count": unread_notifications,
            "app_name": app.config.get("APP_NAME", "DriveEase"),
            "currency": app.config.get("CURRENCY_SYMBOL", "₹"),
            "active_role": session.get("role", "guest")
        }

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html"), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n==================================================")
    print(">> DriveEase Car Rental System running on:")
    print(f">> http://127.0.0.1:{port}")
    print("==================================================\n")
    app.run(host="0.0.0.0", port=port, debug=True)
