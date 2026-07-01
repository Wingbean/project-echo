# app/api/routes_auth.py - Secret-code verification endpoints
import hmac

from flask import jsonify, request, session

from app.api import api_bp
from app.config import Config


def _verify_secret_code(session_key: str):
    """Shared verification logic for secret-code protected pages.

    Args:
        session_key: Session key to set on success (e.g. 'echo_authenticated').

    Returns:
        Flask JSON response tuple.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("code"):
        return jsonify({"status": "error", "message": "กรุณาระบุรหัส"}), 400

    code = str(data["code"]).strip()
    correct_code = Config.ECHO_SECRET_CODE

    if not correct_code:
        return jsonify({"status": "error", "message": "ECHO_SECRET_CODE not configured"}), 500

    # constant-time comparison to avoid leaking the code via timing
    if not hmac.compare_digest(code, correct_code):
        return jsonify({"status": "error", "message": "รหัสไม่ถูกต้อง"}), 401

    session[session_key] = True
    return jsonify({"status": "success", "message": "ยืนยันรหัสสำเร็จ"})


@api_bp.route("/verify_echo", methods=["POST"])
def verify_echo():
    """Verify secret code for Echo page access."""
    return _verify_secret_code("echo_authenticated")


@api_bp.route("/verify_emr", methods=["POST"])
def verify_emr():
    """Verify secret code for EMR page access."""
    return _verify_secret_code("emr_authenticated")
