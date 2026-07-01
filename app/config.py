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

    # Echo Secret Code
    ECHO_SECRET_CODE = os.getenv("ECHO_SECRET_CODE", "")

    # Instance dir (barcode cache + lock files)
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
