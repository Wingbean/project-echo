# app/api/views.py - Page Rendering Routes
from flask import render_template, session, redirect, url_for
from app.api import views_bp


@views_bp.route("/")
def index():
    """Homepage — static grid of links to the search tools."""
    return render_template("pages/index.html")


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


@views_bp.route("/inr")
def inr_page():
    """INR lab result search page."""
    return render_template("pages/inr.html")


@views_bp.route("/emr")
def emr_page():
    """EMR (Electronic Medical Record) search page. Requires authentication."""
    if not session.get("emr_authenticated"):
        return redirect(url_for("views.emr_login_page"))
    return render_template("pages/emr.html")


@views_bp.route("/emr/login")
def emr_login_page():
    """EMR login page - enter secret code to access."""
    if session.get("emr_authenticated"):
        return redirect(url_for("views.emr_page"))
    return render_template("pages/emr_login.html")


@views_bp.route("/emr/logout")
def emr_logout():
    """Clear EMR authentication and redirect to index."""
    session.pop("emr_authenticated", None)
    return redirect(url_for("views.index"))


@views_bp.route("/echo")
def echo_page():
    """Secret integrated dashboard page. Requires authentication."""
    if not session.get("echo_authenticated"):
        return redirect(url_for("views.echo_login_page"))
    return render_template("pages/echo.html")


@views_bp.route("/echo/login")
def echo_login_page():
    """Echo login page - enter secret code to access."""
    if session.get("echo_authenticated"):
        return redirect(url_for("views.echo_page"))
    return render_template("pages/echo_login.html")


@views_bp.route("/echo/logout")
def echo_logout():
    """Clear echo authentication and redirect to login."""
    session.pop("echo_authenticated", None)
    return redirect(url_for("views.index"))
