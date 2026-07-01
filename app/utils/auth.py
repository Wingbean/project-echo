# app/utils/auth.py - Session auth helpers/decorators for the user-account system
from functools import wraps

from flask import jsonify, redirect, request, session, url_for

from app.config import Config
from app.models.local_db import get_db_session
from app.models.user import User


def get_current_user():
    """Load the logged-in User row from session['user_id'], or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db_session() as db:
        user = db.get(User, user_id)
        if user is None:
            return None
        db.expunge(user)  # detach so callers can use it after the session closes
        return user


def _is_api_request():
    return request.path.startswith("/api/")


def login_required(view):
    """Require a logged-in, verified, admin-activated user."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            if _is_api_request():
                return jsonify({"status": "error", "message": "กรุณาเข้าสู่ระบบก่อนเข้าใช้งาน"}), 401
            return redirect(url_for("views.login_page"))
        if not (user.is_verified and user.is_active):
            if _is_api_request():
                return jsonify({"status": "error", "message": "บัญชียังไม่ได้รับการอนุมัติ"}), 403
            return redirect(url_for("views.pending_approval_page"))
        return view(*args, current_user=user, **kwargs)

    return wrapped


def access_required(flag_name):
    """login_required plus a specific per-user access flag (e.g. 'can_access_echo')."""

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, current_user, **kwargs):
            if not getattr(current_user, flag_name, False):
                if _is_api_request():
                    return jsonify({"status": "error", "message": "ไม่มีสิทธิ์เข้าถึง"}), 403
                return redirect(url_for("views.index"))
            return view(*args, current_user=current_user, **kwargs)

        return wrapped

    return decorator


def admin_required(view):
    """ADMIN_EMAILS whitelist check — bypasses is_verified/is_active on purpose,
    otherwise there'd be no way to bootstrap the very first admin account."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None or user.email.lower() not in Config.ADMIN_EMAILS:
            if _is_api_request():
                return jsonify({"status": "error", "message": "ไม่มีสิทธิ์ผู้ดูแลระบบ"}), 403
            return redirect(url_for("views.index"))
        return view(*args, current_user=user, **kwargs)

    return wrapped
