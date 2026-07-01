# app/__init__.py - Flask Application Factory
import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from authlib.integrations.flask_client import OAuth

csrf = CSRFProtect()
oauth = OAuth()

from app.api import api_bp, views_bp

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

    # Initialize Google OAuth client
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    # Ensure instance directory exists
    os.makedirs(app.config.get("INSTANCE_DIR", "instance"), exist_ok=True)

    # Create local users DB tables (idempotent — safe on every worker start)
    from app.models.local_db import get_local_engine
    from app.models.user import Base as UserBase
    UserBase.metadata.create_all(get_local_engine())

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(views_bp)

    # Register template filters
    _register_template_filters(app)

    # Register context processors
    _register_context_processors(app)

    # Register cache busting
    _register_cache_busting(app)

    return app

def _register_cache_busting(app):
    """Automatically bust cache for static files based on mtime."""
    
    @app.url_defaults
    def hashed_static_file(endpoint, values):
        if endpoint == 'static' and 'filename' in values:
            filepath = os.path.join(app.static_folder, values['filename'])
            if os.path.isfile(filepath):
                # Use file modification time as the version hash
                mtime = os.path.getmtime(filepath)
                values['v'] = int(mtime)


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
        from app.utils.auth import get_current_user

        user = get_current_user()
        is_admin = user is not None and user.email.lower() in app.config["ADMIN_EMAILS"]
        return dict(app_name="Project Echo", current_user=user, is_admin=is_admin)
