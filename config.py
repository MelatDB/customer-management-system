import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _required_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Copy .env.example to .env and fill in your database settings."
        )
    return value


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        MYSQL_HOST = _required_env("MYSQL_HOST")
        MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
        MYSQL_USER = _required_env("MYSQL_USER")
        MYSQL_PASSWORD = _required_env("MYSQL_PASSWORD")
        MYSQL_DB = _required_env("MYSQL_DB")
        MYSQL_CA_CERT = os.environ.get("MYSQL_CA_CERT", str(BASE_DIR / "ca.pem"))
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+mysqlconnector://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}"
            f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
            f"?ssl_ca={quote_plus(MYSQL_CA_CERT)}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
