# app/api/routes_admin.py - Admin panel: page + user management JSON endpoints
from flask import jsonify, render_template, request

from app.api import api_bp, views_bp
from app.models.local_db import get_db_session
from app.models.user import User
from app.utils.auth import admin_required


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "is_verified": user.is_verified,
        "is_active": user.is_active,
        "can_access_echo": user.can_access_echo,
        "can_access_emr": user.can_access_emr,
        "totp_enabled": user.totp_enabled,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@views_bp.route("/admin")
@admin_required
def admin_page(current_user):
    """Admin panel page — guarded here too so non-admins never see the shell."""
    return render_template("pages/admin.html")


@api_bp.route("/admin/users", methods=["GET"])
@admin_required
def admin_list_users(current_user):
    with get_db_session() as db:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return jsonify({"status": "success", "users": [_user_dict(u) for u in users]})


@api_bp.route("/admin/users/<int:user_id>/activate", methods=["POST"])
@admin_required
def admin_activate_user(current_user, user_id):
    with get_db_session() as db:
        user = db.get(User, user_id)
        if user is None:
            return jsonify({"status": "error", "message": "ไม่พบผู้ใช้"}), 404
        if not user.is_verified:
            return jsonify({"status": "error", "message": "ผู้ใช้ยังไม่ได้ยืนยันอีเมล"}), 400
        user.is_active = True
    return jsonify({"status": "success"})


@api_bp.route("/admin/users/<int:user_id>/deactivate", methods=["POST"])
@admin_required
def admin_deactivate_user(current_user, user_id):
    with get_db_session() as db:
        user = db.get(User, user_id)
        if user is None:
            return jsonify({"status": "error", "message": "ไม่พบผู้ใช้"}), 404
        user.is_active = False
    return jsonify({"status": "success"})


@api_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(current_user, user_id):
    with get_db_session() as db:
        user = db.get(User, user_id)
        if user is None:
            return jsonify({"status": "error", "message": "ไม่พบผู้ใช้"}), 404
        db.delete(user)
    return jsonify({"status": "success"})


@api_bp.route("/admin/users/<int:user_id>/reset-2fa", methods=["POST"])
@admin_required
def admin_reset_2fa(current_user, user_id):
    """Clear a user's TOTP enrollment (e.g. lost authenticator device) so they re-enroll on next login."""
    with get_db_session() as db:
        user = db.get(User, user_id)
        if user is None:
            return jsonify({"status": "error", "message": "ไม่พบผู้ใช้"}), 404
        user.totp_enabled = False
        user.totp_secret = None
    return jsonify({"status": "success"})


@api_bp.route("/admin/users/<int:user_id>/access", methods=["POST"])
@admin_required
def admin_set_access(current_user, user_id):
    data = request.get_json(silent=True) or {}
    with get_db_session() as db:
        user = db.get(User, user_id)
        if user is None:
            return jsonify({"status": "error", "message": "ไม่พบผู้ใช้"}), 404
        if "can_access_echo" in data:
            user.can_access_echo = bool(data["can_access_echo"])
        if "can_access_emr" in data:
            user.can_access_emr = bool(data["can_access_emr"])
    return jsonify({"status": "success"})
