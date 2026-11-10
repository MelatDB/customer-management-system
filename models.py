from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="Staff")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    email = db.Column(db.String(150), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    registration_date = db.Column(db.DateTime, nullable=False, server_default=func.now())
    interactions = db.relationship(
        "Interaction",
        backref="customer",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="desc(Interaction.interaction_date)",
    )
    reports = db.relationship(
        "Report",
        backref="customer",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="desc(Report.generated_date)",
    )


class Interaction(db.Model):
    __tablename__ = "interactions"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    interaction_date = db.Column(db.DateTime, nullable=False, server_default=func.now())
    interaction_type = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=False)


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False, index=True)
    generated_date = db.Column(db.DateTime, nullable=False, server_default=func.now())
    type = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
