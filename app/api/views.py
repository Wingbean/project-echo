# app/api/views.py - Page Rendering Routes
from flask import redirect, render_template, url_for

from app.api import views_bp
from app.utils.auth import access_required, get_current_user, login_required


@views_bp.route("/")
@login_required
def index(current_user):
    """Homepage — static grid of links to the search tools."""
    return render_template("pages/index.html")


@views_bp.route("/consult")
@login_required
def consult_page(current_user):
    """Consult search page."""
    return render_template("pages/consult.html")


@views_bp.route("/flow_opd")
@login_required
def flow_opd_page(current_user):
    """OPD Flow search page."""
    return render_template("pages/flow_opd.html")


@views_bp.route("/egfr")
@login_required
def egfr_page(current_user):
    """eGFR lab result search page."""
    return render_template("pages/egfr.html")


@views_bp.route("/a1c")
@login_required
def a1c_page(current_user):
    """A1C lab result search page."""
    return render_template("pages/a1c.html")


@views_bp.route("/inr")
@login_required
def inr_page(current_user):
    """INR lab result search page."""
    return render_template("pages/inr.html")


@views_bp.route("/emr")
@access_required("can_access_emr")
def emr_page(current_user):
    """EMR (Electronic Medical Record) search page. Requires login + access."""
    return render_template("pages/emr.html")


@views_bp.route("/echo")
@access_required("can_access_echo")
def echo_page(current_user):
    """Secret integrated dashboard page. Requires login + access."""
    return render_template("pages/echo.html")


@views_bp.route("/login")
def login_page():
    """Login page — single 'Login with Gmail' button."""
    user = get_current_user()
    if user is not None and user.is_verified and user.is_active:
        return redirect(url_for("views.index"))
    return render_template("pages/login.html")


@views_bp.route("/pending-approval")
def pending_approval_page():
    """Shown after Google login while awaiting email verification or admin approval."""
    user = get_current_user()
    return render_template("pages/pending_approval.html", user=user)
