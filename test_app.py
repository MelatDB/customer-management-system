import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///cms_test.db"

from app import app, db
from models import Customer, Interaction, User


class CmsSmokeTests(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///cms_test.db",
        )
        self.client = app.test_client()

        with app.app_context():
            db.drop_all()
            db.create_all()

            admin = User(name="Admin User", email="admin@test.com", role="Admin")
            admin.set_password("secret123")
            db.session.add(admin)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self):
        return self.client.post(
            "/login",
            data={"email": "admin@test.com", "password": "secret123"},
            follow_redirects=True,
        )

    def test_login_and_add_customer(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/customers/add",
            data={
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "1234567890",
                "address": "Nairobi",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Customer added successfully.", response.data)

        with app.app_context():
            self.assertEqual(Customer.query.count(), 1)

    def test_search_supports_customer_id(self):
        with app.app_context():
            customer = Customer(name="John Doe", email="john@example.com")
            db.session.add(customer)
            db.session.commit()
            customer_id = customer.id

        self.login()
        response = self.client.get(f"/customers/search?q={customer_id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"John Doe", response.data)

    def test_admin_can_create_user_account(self):
        self.login()
        response = self.client.post(
            "/users",
            data={
                "name": "Operations Staff",
                "email": "ops@example.com",
                "password": "StrongPass123",
                "role": "Staff",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"User account created successfully.", response.data)

        with app.app_context():
            created_user = User.query.filter_by(email="ops@example.com").first()
            self.assertIsNotNone(created_user)
            self.assertEqual(created_user.role, "Staff")

    def test_interaction_can_be_deleted(self):
        with app.app_context():
            customer = Customer(name="Delete Test", email="delete@test.com")
            db.session.add(customer)
            db.session.commit()

            interaction = Interaction(
                customer_id=customer.id,
                interaction_type="Call",
                notes="Follow up on onboarding",
            )
            db.session.add(interaction)
            db.session.commit()
            interaction_id = interaction.id

        self.login()
        response = self.client.post(
            f"/interactions/{interaction_id}/delete",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Interaction deleted successfully.", response.data)

        with app.app_context():
            deleted_interaction = db.session.get(Interaction, interaction_id)
            self.assertIsNone(deleted_interaction)


if __name__ == "__main__":
    unittest.main()
