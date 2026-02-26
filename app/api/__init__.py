# app/api/__init__.py - API Blueprint Registration
from flask import Blueprint

# API Blueprint (for JSON endpoints)
api_bp = Blueprint("api", __name__)

# Views Blueprint (for page rendering)
views_bp = Blueprint("views", __name__)

# Import routes to register them with blueprints
from app.api import routes  # noqa: F401, E402
from app.api import views   # noqa: F401, E402
