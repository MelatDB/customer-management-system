# Customer Management System (CMS)

A Flask-based customer management portal for tracking customers, interactions, and activity reports. It is a small CRM-style web application with session-based authentication, role-based access control (`Admin` / `Staff`), and CSV report export.

## Features

- **Authentication** — login/logout with hashed passwords and server-side sessions.
- **Role-based access** — `Admin` and `Staff` roles; administrative routes are protected.
- **Customer management** — create, edit, and delete (admin only) customers; list and search by name, email, or customer ID.
- **Interaction tracking** — record call/email/meeting notes per customer, browse recent interactions, and delete entries.
- **Account management** — admins can create and delete user accounts (an admin cannot delete their own account).
- **Reports** — admin-only customer activity summaries (total interactions, last interaction date) with CSV export.
- **Responsive UI** — Jinja2 templates styled with Bootstrap 5.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Flask 3.1, Flask-SQLAlchemy 3.1 |
| Database | MySQL (hosted on Aiven, TLS via `ca.pem`); SQLite for tests |
| Frontend | Jinja2, Bootstrap 5.3, custom CSS |
| Auth | Werkzeug password hashing, Flask sessions |
| Testing | Python `unittest` |

## Project Structure

```
CMS/
├── app.py                  # Routes, auth, validation, reports, CSV export
├── models.py               # SQLAlchemy models: User, Customer, Interaction, Report
├── config.py               # App configuration and database connection
├── test_app.py             # Smoke tests (runs against SQLite)
├── requirements.txt        # Python dependencies
├── run_cms.bat             # Windows launcher (installs deps and starts the app)
├── .env.example            # Template for local environment variables
├── ca.pem                  # CA certificate for the hosted MySQL server
├── instance/               # Local SQLite databases (not committed)
├── static/
│   └── styles.css          # Custom styling
└── templates/
    ├── base.html           # Layout, sidebar, flash messages
    ├── login.html
    ├── index.html          # Customer dashboard
    ├── add_customer.html   # Add/edit customer form
    ├── search.html
    ├── interactions.html
    ├── interactions_overview.html
    ├── users.html
    ├── reports.html
    └── partials/
        └── alerts.html
```

## Getting Started

### Prerequisites

- Python 3.11+
- Access to a MySQL database (or adjust the config to use SQLite locally)

### Quick Start (Windows)

Double-click `run_cms.bat`. It installs the dependencies, opens `http://127.0.0.1:5000`, and starts the app.

### Manual Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your local environment file
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
# then edit .env with your database credentials

# 4. Run the app
python app.py
```

The app is available at `http://127.0.0.1:5000`. Tables are created automatically on first run.

## Configuration

Settings are read from environment variables. For local development, copy `.env.example` to `.env` and fill in your values — `.env` is loaded automatically and is excluded from Git.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session signing key |
| `DATABASE_URL` | Full SQLAlchemy database URI (overrides the individual MySQL settings) |
| `MYSQL_HOST` | MySQL hostname |
| `MYSQL_PORT` | MySQL port |
| `MYSQL_USER` | MySQL username |
| `MYSQL_PASSWORD` | MySQL password |
| `MYSQL_DB` | Database name |
| `MYSQL_CA_CERT` | Path to the CA certificate (defaults to `ca.pem` in the project root) |

Example using a local SQLite database instead of MySQL:

```bash
set DATABASE_URL=sqlite:///cms.db
python app.py
```

## Default Accounts

On first run, two accounts are seeded automatically:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@cmsdemo.com` | `Admin@123` |
| Staff | `staff@cmsdemo.com` | `Staff@123` |

> Change these credentials before deploying the application anywhere public.

## Running Tests

```bash
python -m unittest test_app.py
```

The tests use a SQLite database (`instance/cms_test.db`) and cover login, customer creation, ID-based search, user creation, and interaction deletion.

## Security Notes

- Database credentials and the `SECRET_KEY` are read from environment variables / `.env` and are not committed to the repository.
- The seeded demo accounts use weak, well-known passwords. Change them before deploying anywhere public.
- The development server (`app.run(debug=True)`) should not be used in production; use a WSGI server such as Gunicorn or Waitress instead.

## License

This project was created for educational purposes. Add a license here if you plan to distribute it.
