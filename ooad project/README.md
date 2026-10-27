# DriveEase - Online Car Rental Management System
> **An Object-Oriented Analysis & Design (OOAD) College Project**  
> *Built with Python Flask, MySQL, Modern CSS (Rapido & Uber Aesthetic), and Object-Oriented Principles.*

---

## 1. Project Overview

**DriveEase** is a full-stack, enterprise-grade, web-based car rental platform that connects vehicle hosts with customers looking for self-drive automobiles. It simplifies car listings, search & multi-filtering, booking date conflict detection, demo payment verification, review scoring, and platform governance.

The application reflects pure **Object-Oriented Analysis and Design (OOAD)** concepts, featuring:
- **Encapsulation & Domain Entities**: `User`, `Car`, `Booking`, `Payment`, `Review`, `Notification`.
- **Inheritance & Polymorphism**: Base class `User` with specialized derived subclasses `Customer`, `CarOwner`, and `Admin`.
- **Design Patterns**: Factory Pattern (`UserFactory`), Singleton Pattern (`DatabaseManager`), Service-Oriented Layer (`BookingService`, `PaymentService`, `CarService`, `NotificationService`).
- **UI Aesthetic**: High-contrast, modern dark & vibrant yellow design inspired by **Uber** and **Rapido**.

---

## 2. User Roles & Access Control

The platform implements 3 distinct user roles enforced via server-side session checks and role-based decorators (`@login_required`, `@role_required`):

### 🚗 A. Customer (Renter)
- **Account**: Secure registration, login, profile management with driving license records.
- **Search & Filters**: Search by location, category (Hatchback, Sedan, SUV, Luxury, Electric), fuel type, transmission, price range, and seats.
- **Live Fare Calculator**: Real-time interactive calculation of duration, base fare, 5% GST, and refundable deposit without page reloads.
- **Booking Flow**: Multi-day booking with pickup and drop addresses, date conflict detection, and booking reference (`BK-XXXXXXXX`).
- **Simulated Payment Gateway**: Demo UPI (Dynamic QR Code, VPA input, GPay/PhonePe tabs), Credit/Debit Card, or Cash on Pickup.
- **Receipts & Invoices**: Clean, printable tax invoice with transaction reference (`TXN-XXXXXXXXXXXX`).
- **Booking Management**: View active and historical trips; cancel eligible reservations.
- **Ratings & Reviews**: Submit 1-to-5 star feedback with comments for completed rentals (duplicate reviews prevented).

### 🔑 B. Car Owner (Vehicle Host)
- **Host Dashboard**: High-level telemetry of listed fleet, pending requests, active trips, and earnings summary.
- **Vehicle Listing Lifecycle**: Add, edit, and delete cars with specifications, registration numbers, daily rates, and photo uploads.
- **Listing Status**: Visibility into Admin Verification (`Pending`, `Approved`, `Rejected`).
- **Availability Switch**: Toggle car availability (`Available` vs `Paused`) with a single click.
- **Request Decisions**: Review pending customer bookings and **Approve** or **Reject** with reasons.
- **Trip Completion**: Mark finished rentals as **Completed**, prompting customers for reviews.
- **Host Reviews**: Read verified feedback submitted for their fleet.

### 🛡️ C. Administrator (Superadmin)
- **Admin Dashboard**: System telemetry tracking total customers, hosts, cars, total revenue, and pending verification queues.
- **Vehicle Listing Verification**: Inspect uploaded vehicle specifications and RC documents to approve or reject listings.
- **User Governance Directory**: Search and view user accounts; toggle account status (`Active` vs `Deactivated`).
- **Bookings Ledger**: Surveillance of all platform bookings with real-time status filtering.
- **Financial Ledger**: Complete ledger of payments, amounts, transaction references, and dates.
- **Review Moderation**: Inspect reviews and delete inappropriate or abusive entries.
- **Analytical Reports**: KPI reports, vehicle category market share, and revenue summaries.

---

## 3. The 7 Core OOAD Modules

| Module | Description | Implementation File(s) |
|---|---|---|
| **1. User Management** | Registration, login, password hashing, session RBAC | `models/user.py`, `routes/auth_routes.py` |
| **2. Car Management** | CRUD vehicle listings, photo uploads, availability, verification | `models/car.py`, `services/car_service.py`, `routes/owner_routes.py` |
| **3. Booking Management** | Date validation, overlap interval queries, 5-stage status lifecycle | `models/booking.py`, `services/booking_service.py`, `routes/customer_routes.py` |
| **4. Payment Management** | Demo UPI QR / Card / Cash checkout, unique references, tax invoices | `models/payment.py`, `services/payment_service.py` |
| **5. Review & Rating** | 1-5 star ratings, duplicate prevention, vehicle score aggregation | `models/review.py`, `services/review_service.py` |
| **6. Admin Governance** | Verification queue, user deactivation, system analytics, reports | `services/admin_service.py`, `routes/admin_routes.py` |
| **7. Notification Management** | In-app alerts, unread badges, mark-as-read API | `models/notification.py`, `services/notification_service.py`, `routes/api_routes.py` |

---

## 4. Object-Oriented Design & UML Mapping

### A. Class Hierarchy
```
                   +----------------------------------+
                   |               User               |
                   +----------------------------------+
                   | - id: int                        |
                   | - name: str                      |
                   | - email: str                     |
                   | - phone: str                     |
                   | - password_hash: str             |
                   | - role: str                      |
                   | - status: str                    |
                   +----------------------------------+
                   | + set_password(plain_pw)         |
                   | + check_password(plain_pw)       |
                   | + can_book_cars(): bool          |
                   | + can_manage_cars(): bool        |
                   | + is_admin_user(): bool          |
                   +----------------------------------+
                             ▲         ▲         ▲
             ┌───────────────┘         │         └───────────────┐
             │                         │                         │
+-------------------------+ +-------------------------+ +-------------------------+
|        Customer         | |        CarOwner         | |          Admin          |
+-------------------------+ +-------------------------+ +-------------------------+
| + can_book_cars(): True | | + can_manage_cars():True| | + is_admin_user(): True |
| + can_review(): True    | | + can_approve(): True   | | + can_verify_cars():True|
+-------------------------+ +-------------------------+ +-------------------------+
```

### B. OOAD Design Patterns
1. **Factory Method (`UserFactory`)**: `UserFactory.create_user(row_dict)` inspects the `role` field from MySQL and instantiates `Customer`, `CarOwner`, or `Admin` polymorphically.
2. **Singleton Pattern (`DatabaseManager`)**: Ensures a single persistent database manager connects to MySQL or SQLite across all worker threads.
3. **State Machine (`Booking`)**: Manages transitions between `Pending` &rarr; `Confirmed` &rarr; `Completed` or `Cancelled` / `Rejected`.
4. **Service Layer**: Business rules (e.g. interval overlap query `is_car_available_for_dates`) are isolated from HTTP routing.

---

## 5. Technology Stack

- **Backend**: Python 3.12, Flask 3.1, Werkzeug
- **Database**: MySQL 8.0 (with automatic zero-friction SQLite fallback for instant presentation)
- **Database Connectivity**: PyMySQL with parameterized SQL statements (`%s`) preventing SQL Injection
- **Frontend**: HTML5, Vanilla CSS3 (Uber/Rapido Design System), JavaScript (ES6)
- **Testing**: Pytest & Python `unittest`

---

## 6. Installation & Execution Guide (Windows)

### Prerequisites
- Python 3.10+ installed ([python.org](https://www.python.org/downloads/))
- (Optional for MySQL mode) XAMPP or MySQL Server 8.0

### Step 1: Clone / Open Project
Open PowerShell or Command Prompt in the project folder:
```powershell
cd "c:\Users\kajam\Desktop\ooad project"
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Database

#### Option A: Running with MySQL (Recommended for College Viva)
1. Start MySQL in **XAMPP Control Panel** (click **Start** next to MySQL) or start Windows MySQL Service:
   ```powershell
   net start MySQL80
   ```
2. Create the database in MySQL:
   ```sql
   CREATE DATABASE IF NOT EXISTS car_rental_db;
   ```
3. Update `.env` file (or copy from `.env.example`):
   ```ini
   DB_TYPE=mysql
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=car_rental_db
   ```
4. Run the database seed script to populate tables and demo vehicles:
   ```powershell
   python seed_data.py
   ```

#### Option B: Zero-Friction Demonstration Mode (SQLite)
If MySQL is not installed on the laptop during your presentation, `DatabaseManager` automatically activates demonstration mode without any crashes:
```powershell
python seed_data.py
```

### Step 4: Run the Application
```powershell
python app.py
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 7. Demo Accounts for Presentation & Viva

The login page (`/login`) includes **One-Click Demo Fill buttons** for effortless presentation:

| Role | Demo Email | Password | Primary Capabilities to Demonstrate |
|---|---|---|---|
| 🟢 **Customer** | `arjun.renter@driveease.com` | `customer123` | Search cars, real-time fare estimator, book car, demo UPI QR payment, cancel, leave 5★ review |
| 🟡 **Car Owner** | `rahul.host@driveease.com` | `owner123` | Host dashboard, fleet management, accept/reject booking requests, mark trip completed, earnings |
| 🟣 **Admin** | `admin@driveease.com` | `admin123` | System telemetry, approve/reject pending vehicles, user governance, payments ledger, analytical reports |

---

## 8. Automated Test Suite

To verify all 16 test cases, run:
```powershell
python -m pytest tests/ -v
```

### Verified Test Cases:
1. `test_user_password_hashing`: Verifies PBKDF2 hashing security.
2. `test_user_factory_polymorphism`: Validates dynamic subclass instantiation.
3. `test_successful_login`: Validates session creation and role redirect.
4. `test_invalid_login`: Validates security on bad credentials.
5. `test_duplicate_registration_prevented`: Rejects duplicate email addresses.
6. `test_date_validation_rules`: Rejects past pickup dates and invalid return dates.
7. `test_booking_creation_and_price_calculation`: Verifies backend rate computation.
8. `test_overlap_prevention_rule`: **Blocks overlapping confirmed/pending bookings.**
9. `test_booking_cancellation`: Verifies state transition to `Cancelled`.
10. `test_payment_and_invoice_generation`: Verifies demo payment reference generation.
11. `test_review_eligibility_and_duplicate_prevention`: Ensures reviews only for completed trips.
12. `test_unauthenticated_protected_routes`: Redirects unauthorized requests to `/login`.
13. `test_customer_cannot_access_owner_or_admin`: Enforces RBAC permissions.
14. `test_owner_cannot_access_admin`: Restricts admin access.
15. `test_owner_cannot_modify_other_owner_car`: Prevents unauthorized fleet mutation.
16. `test_admin_can_approve_car_listing`: Verifies verification queue state change.

---

## 9. Presentation Guide: Important Screens to Screenshot

For your college project PPT slides, capture these screens:

1. **Home Page (`/`)**: Hero section with Rapido/Uber dark & yellow theme, instant search widget, category pills, and featured rides.
2. **Explore Cars Catalog (`/cars`)**: Multi-filter sidebar (Location, Category, Fuel, Transmission, Price) and responsive vehicle grid.
3. **Car Details & Live Estimator (`/cars/2`)**: Vehicle specifications grid, verified host superhost badge, and interactive real-time fare calculator.
4. **Checkout & Simulated Payment (`/customer/payment/<ref>`)**: Dynamic UPI QR code preview, Card simulation form, and Cash option.
5. **Printable Tax Invoice (`/customer/invoice/<ref>`)**: Clean formal invoice with transaction ID, customer/host details, and GST breakdown.
6. **Customer Dashboard (`/customer/dashboard`)**: Active bookings table, status badges, and 5-star review submission modal.
7. **Host Dashboard (`/owner/dashboard`)**: Earnings tile, pending booking approval/rejection buttons, and active rentals.
8. **Admin Command Center (`/admin/dashboard`)**: System telemetry counters, fleet distribution, and pending verification alert.
9. **Listing Verification Queue (`/admin/verify-cars`)**: Reviewing vehicle specs, RC book preview, and Approve/Reject buttons.
10. **Users Governance Directory (`/admin/users`)**: Managing customer and host accounts with status toggle.

---

## 10. Viva Voice & Interview Questions (Cheat Sheet)

**Q1: How does your application implement Polymorphism?**  
*Answer:* Base class `User` declares virtual permission methods (`can_book_cars()`, `can_manage_cars()`, `is_admin_user()`). Subclasses `Customer`, `CarOwner`, and `Admin` override these methods with role-specific logic. `UserFactory` dynamically instantiates the correct subclass.

**Q2: How do you prevent overlapping bookings for the same vehicle?**  
*Answer:* In `BookingService.is_car_available_for_dates()`, we execute an interval overlap query:
`NOT (new_start > existing.end_date OR new_end < existing.start_date)` for all bookings with status `Pending` or `Confirmed`. If the count is > 0, the booking is rejected.

**Q3: How are passwords stored and secured?**  
*Answer:* Passwords are never stored in plaintext. We utilize Werkzeug's `generate_password_hash` using salted PBKDF2-HMAC-SHA256, and verify via `check_password_hash`.

**Q4: How is SQL Injection prevented?**  
*Answer:* All SQL queries executed through `DatabaseManager` utilize parameterized statements (`%s` placeholders), ensuring user inputs are treated as literal values rather than executable SQL commands.

---
© 2026 DriveEase Car Rental System. All rights reserved.
