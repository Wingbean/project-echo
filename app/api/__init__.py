# app/api/__init__.py - API Blueprint Registration
from flask import Blueprint

# API Blueprint (for JSON endpoints)
api_bp = Blueprint("api", __name__)

# Views Blueprint (for page rendering)
views_bp = Blueprint("views", __name__)

# Import route modules for their registration side effects
from app.api import routes_auth     # noqa: F401, E402
from app.api import routes_admin    # noqa: F401, E402
from app.api import routes_search   # noqa: F401, E402
from app.api import routes_barcode  # noqa: F401, E402
from app.api import views           # noqa: F401, E402
