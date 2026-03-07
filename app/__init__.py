# app/__init__.py - Flask Application Factory
import os
import fcntl
from flask import Flask
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

from app.api import api_bp, views_bp
from app.services.hosxp_service import get_last_sync_time
from app.services.scheduler_service import start_scheduler

def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    # Load configuration from config.py
    app.config.from_object("app.config.Config")

    # Initialize CSRF protection
    csrf.init_app(app)

    # Ensure instance directory exists
    os.makedirs(app.config.get("INSTANCE_DIR", "instance"), exist_ok=True)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(views_bp)

    # Register template filters
    _register_template_filters(app)

    # Register context processors
    _register_context_processors(app)

    # Start scheduler if enabled
    _start_scheduler(app)

    return app


def _register_template_filters(app):
    """Register custom Jinja2 template filters."""

    @app.template_filter("format_date")
    def format_date(value, fmt="%d/%m/%Y"):
        """Format a datetime object to Thai-friendly date string."""
        if value is None:
            return "-"
        try:
            return value.strftime(fmt)
        except AttributeError:
            return str(value)

    @app.template_filter("format_number")
    def format_number(value):
        """Format a number with comma separators."""
        if value is None:
            return "0"
        try:
            return "{:,}".format(int(value))
        except (ValueError, TypeError):
            return str(value)


def _register_context_processors(app):
    """Register context processors available to all templates."""

    @app.context_processor
    def inject_globals():
        return dict(
            last_sync=get_last_sync_time(),
            app_name="Project Echo",
        )


def _start_scheduler(app):
    """Start the background scheduler (only one worker)."""
    lock_path = os.path.join(
        app.config.get("INSTANCE_DIR", "instance"), "scheduler.lock"
    )
    try:
        lock_fd = open(lock_path, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("✅ Scheduler lock acquired. Starting scheduler thread.")
        start_scheduler()
    except (BlockingIOError, OSError):
        print("⏳ Scheduler is already running in another worker. Skipping.")
    except Exception as e:
        print(f"❌ Could not start scheduler: {e}")
