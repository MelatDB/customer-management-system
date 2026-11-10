from functools import wraps

import csv
import io

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func, or_

from config import Config
from models import Customer, Interaction, Report, User, db


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "Admin":
            flash("Only administrators can perform that action.", "danger")
            return redirect(url_for("index"))
        return view_func(*args, **kwargs)

    return wrapper


def build_customer_search_filter(query):
    like_term = f"%{query}%"
    filters = [Customer.name.ilike(like_term), Customer.email.ilike(like_term)]

    if query.isdigit():
        filters.append(Customer.id == int(query))

    return or_(*filters)


def validate_customer_form(name, email, current_customer_id=None):
    errors = []

    if not name:
        errors.append("Customer name is required.")
    if not email:
        errors.append("Customer email is required.")

    duplicate_query = Customer.query.filter(func.lower(Customer.email) == email)
    if current_customer_id is not None:
        duplicate_query = duplicate_query.filter(Customer.id != current_customer_id)

    if email and duplicate_query.first():
        errors.append("A customer with that email already exists.")

    return errors


def validate_user_form(name, email, password, role, current_user_id=None):
    errors = []

    if not name:
        errors.append("User name is required.")
    if not email:
        errors.append("User email is required.")
    if not password:
        errors.append("Password is required.")
    if role not in {"Admin", "Staff"}:
        errors.append("A valid role is required.")

    duplicate_query = User.query.filter(func.lower(User.email) == email)
    if current_user_id is not None:
        duplicate_query = duplicate_query.filter(User.id != current_user_id)

    if email and duplicate_query.first():
        errors.append("A user with that email already exists.")

    return errors


@app.context_processor
def inject_user():
    return {
        "current_user_name": session.get("user_name"),
        "current_user_role": session.get("role"),
    }


def seed_users():
    default_users = [
        {
            "name": "System Admin",
            "email": "admin@cmsdemo.com",
            "role": "Admin",
            "password": "Admin@123",
        },
        {
            "name": "Support Staff",
            "email": "staff@cmsdemo.com",
            "role": "Staff",
            "password": "Staff@123",
        },
    ]

    changes_made = False
    for user_data in default_users:
        existing_user = User.query.filter(
            func.lower(User.email) == user_data["email"].lower()
        ).first()

        if existing_user:
            existing_user.name = user_data["name"]
            existing_user.role = user_data["role"]
            existing_user.set_password(user_data["password"])
        else:
            new_user = User(
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"],
            )
            new_user.set_password(user_data["password"])
            db.session.add(new_user)

        changes_made = True

    if changes_made:
        db.session.commit()


def create_snapshot_report(customer, interaction_count):
    content = (
        f"Customer {customer.name} has {interaction_count} recorded interaction(s). "
        f"Latest contact email: {customer.email}."
    )
    report = Report.query.filter_by(customer_id=customer.id, type="Customer Activity Summary").first()

    if report:
        report.content = content
    else:
        report = Report(customer_id=customer.id, type="Customer Activity Summary", content=content)
        db.session.add(report)

    return report


def build_report_rows():
    query = (
        db.session.query(
            Customer,
            func.count(Interaction.id).label("interaction_total"),
            func.max(Interaction.interaction_date).label("last_interaction"),
        )
        .outerjoin(Interaction, Customer.id == Interaction.customer_id)
        .group_by(Customer.id)
        .order_by(Customer.name.asc())
    )

    report_rows = []
    for customer, interaction_total, last_interaction in query.all():
        report_record = create_snapshot_report(customer, interaction_total)
        report_rows.append(
            {
                "customer": customer,
                "interaction_total": interaction_total,
                "last_interaction": last_interaction,
                "report_type": report_record.type,
                "report_content": report_record.content,
            }
        )

    return report_rows


def initialize_database():
    with app.app_context():
        db.create_all()
        seed_users()


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("index"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(func.lower(User.email) == email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role
            flash(f"Welcome back, {user.name}.", "success")
            return redirect(url_for("index"))

        flash("Login failed. Please check your email and password.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def index():
    query = request.args.get("q", "").strip()
    customers_query = Customer.query

    if query:
        customers_query = customers_query.filter(build_customer_search_filter(query))

    customers = customers_query.order_by(Customer.registration_date.desc()).all()
    stats = {
        "customer_count": Customer.query.count(),
        "interaction_count": Interaction.query.count(),
        "report_count": Report.query.count(),
    }
    return render_template("index.html", customers=customers, stats=stats, query=query)


@app.route("/customers/add", methods=["GET", "POST"])
@login_required
def add_customer():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        errors = validate_customer_form(name, email)

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            customer = Customer(name=name, email=email, phone=phone, address=address)
            db.session.add(customer)
            db.session.commit()
            flash("Customer added successfully.", "success")
            return redirect(url_for("index"))

    return render_template("add_customer.html")


@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        errors = validate_customer_form(name, email, current_customer_id=customer.id)

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            customer.name = name
            customer.email = email
            customer.phone = phone
            customer.address = address
            db.session.commit()
            flash("Customer updated successfully.", "success")
            return redirect(url_for("index"))

    return render_template("add_customer.html", customer=customer, edit_mode=True)


@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully.", "warning")
    return redirect(url_for("index"))


@app.route("/customers/search")
@login_required
def search_customer():
    query = request.args.get("q", "").strip()
    customers = []

    if query:
        customers = (
            Customer.query.filter(build_customer_search_filter(query))
            .order_by(Customer.name.asc())
            .all()
        )

    return render_template("search.html", customers=customers, query=query)


@app.route("/customers/<int:customer_id>/interactions", methods=["GET", "POST"])
@login_required
def record_interaction(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":
        interaction_type = request.form.get("interaction_type", "").strip()
        notes = request.form.get("notes", "").strip()

        if not interaction_type or not notes:
            flash("Interaction type and notes are required.", "danger")
        else:
            interaction = Interaction(
                customer_id=customer.id,
                interaction_type=interaction_type,
                notes=notes,
            )
            db.session.add(interaction)
            db.session.commit()
            flash("Interaction recorded successfully.", "success")
            return redirect(url_for("record_interaction", customer_id=customer.id))

    interactions = Interaction.query.filter_by(customer_id=customer.id).order_by(
        Interaction.interaction_date.desc()
    )
    return render_template(
        "interactions.html",
        customer=customer,
        interactions=interactions.all(),
    )


@app.route("/interactions/<int:interaction_id>/delete", methods=["POST"])
@login_required
def delete_interaction(interaction_id):
    interaction = Interaction.query.get_or_404(interaction_id)
    customer_id = interaction.customer_id
    db.session.delete(interaction)
    db.session.commit()
    flash("Interaction deleted successfully.", "warning")
    return redirect(url_for("record_interaction", customer_id=customer_id))


@app.route("/interactions")
@login_required
def interactions_overview():
    customers = Customer.query.order_by(Customer.name.asc()).all()
    interactions = Interaction.query.order_by(Interaction.interaction_date.desc()).limit(15).all()
    return render_template(
        "interactions_overview.html",
        customers=customers,
        interactions=interactions,
    )


@app.route("/users", methods=["GET", "POST"])
@login_required
@admin_required
def manage_users():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "").strip()

        errors = validate_user_form(name, email, password, role)

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("User account created successfully.", "success")
            return redirect(url_for("manage_users"))

    users = User.query.order_by(User.role.asc(), User.name.asc()).all()
    return render_template("users.html", users=users)


@app.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == session.get("user_id"):
        flash("You cannot delete the account you are currently using.", "danger")
        return redirect(url_for("manage_users"))

    db.session.delete(user)
    db.session.commit()
    flash("User account deleted successfully.", "warning")
    return redirect(url_for("manage_users"))


@app.route("/reports")
@login_required
@admin_required
def reports():
    report_rows = build_report_rows()
    db.session.commit()
    return render_template("reports.html", report_rows=report_rows)


@app.route("/reports/export")
@login_required
@admin_required
def export_reports():
    report_rows = build_report_rows()
    db.session.commit()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Customer ID",
            "Customer Name",
            "Email",
            "Report Type",
            "Total Interactions",
            "Last Interaction",
            "Content",
        ]
    )

    for row in report_rows:
        writer.writerow(
            [
                row["customer"].id,
                row["customer"].name,
                row["customer"].email,
                row["report_type"],
                row["interaction_total"],
                row["last_interaction"].strftime("%Y-%m-%d %H:%M:%S")
                if row["last_interaction"]
                else "",
                row["report_content"],
            ]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=customer_activity_report.csv"},
    )


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
