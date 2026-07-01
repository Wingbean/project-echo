# app/config.py - Application Configuration
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _get_secret_key() -> str:
    """Return SECRET_KEY, refusing to start production with a default one."""
    key = os.getenv("SECRET_KEY")
    env = os.getenv("FLASK_ENV", "production")
    if not key:
        if env == "production":
            raise RuntimeError(
                "SECRET_KEY is not set. Refusing to start in production "
                "with a default key — set SECRET_KEY in .env."
            )
        return "dev-secret-key-change-in-production"
    return key


class Config:
    """Base configuration loaded from environment variables."""

    # Flask Core
    SECRET_KEY = _get_secret_key()
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # JSON
    JSON_AS_ASCII = False  # Support Thai characters in JSON responses

    # CSRF Protection
    WTF_CSRF_ENABLED = os.getenv("CSRF_ENABLED", "true").lower() == "true"
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Session Security
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY = os.getenv("SESSION_COOKIE_HTTPONLY", "true").lower() == "true"
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    # HosXP Database
    HOSXP_HOST = os.getenv("HOSXP_HOST", "")
    HOSXP_USER = os.getenv("HOSXP_USER", "")
    HOSXP_PASS = os.getenv("HOSXP_PASS", "")
    HOSXP_DB = os.getenv("HOSXP_DB", "")
    HOSXP_PORT = int(os.getenv("HOSXP_PORT", "3306"))

    # Base URL of this app (used to build the Google OAuth redirect + email links)
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5009").rstrip("/")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = f"{BASE_URL}/auth/callback"

    # Email (Gmail SMTP — sends email-verification links)
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    # Google displays App Passwords with spaces for readability — strip them
    # so a copy-pasted "abcd efgh ijkl mnop" still works.
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "").replace(" ", "")

    # Admin whitelist (comma-separated emails, case-insensitive)
    ADMIN_EMAILS = [
        e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()
    ]

    # Email verification token expiry, in seconds (default 24h)
    EMAIL_VERIFY_TOKEN_MAX_AGE = int(os.getenv("EMAIL_VERIFY_TOKEN_MAX_AGE", "86400"))

    # Instance dir (local users DB + barcode cache + lock files)
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
