# app/api/views.py - Page Rendering Routes
from flask import render_template, request
from app.api import views_bp
from app.services.render_service import get_dashboard_data, get_table_data


@views_bp.route("/")
def index():
    """Homepage / Dashboard."""
    data = get_dashboard_data()
    return render_template("pages/index.html", data=data)


@views_bp.route("/query")
def query_page():
    """Query input page."""
    return render_template("pages/query.html")


@views_bp.route("/results")
def results_page():
    """Results display page."""
    table_name = request.args.get("table", "")
    data = {}
    if table_name:
        data = get_table_data(table_name)
    return render_template("pages/results.html", data=data, table_name=table_name)
