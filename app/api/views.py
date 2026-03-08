# app/api/views.py - Page Rendering Routes
from flask import render_template
from app.api import views_bp
from app.services.render_service import get_dashboard_data


@views_bp.route("/")
def index():
    """Homepage / Dashboard."""
    data = get_dashboard_data()
    return render_template("pages/index.html", data=data)


@views_bp.route("/consult")
def consult_page():
    """Consult search page."""
    return render_template("pages/consult.html")


@views_bp.route("/flow_opd")
def flow_opd_page():
    """OPD Flow search page."""
    return render_template("pages/flow_opd.html")


@views_bp.route("/egfr")
def egfr_page():
    """eGFR lab result search page."""
    return render_template("pages/egfr.html")


@views_bp.route("/a1c")
def a1c_page():
    """A1C lab result search page."""
    return render_template("pages/a1c.html")


@views_bp.route("/emr")
def emr_page():
    """EMR (Electronic Medical Record) search page."""
    return render_template("pages/emr.html")


@views_bp.route("/echo")
def echo_page():
    """Secret integrated dashboard page."""
    return render_template("pages/echo.html")
