# app/api/routes_auth.py - Google OAuth login, logout, email verification, TOTP 2FA
import qrcode
import qrcode.image.svg
import pyotp
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from flask import flash, redirect, render_template, request, session, url_for

from app import oauth
from app.api import views_bp
from app.config import Config
from app.models.local_db import get_db_session
from app.models.user import User
from app.utils.email import send_verification_email


def _get_serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY, salt="email-verify")


def _generate_verify_token(user_id: int) -> str:
    return _get_serializer().dumps(user_id)


def _load_verify_token(token: str):
    try:
        return _get_serializer().loads(token, max_age=Config.EMAIL_VERIFY_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None


def _send_verification(user_id: int, email: str):
    token = _generate_verify_token(user_id)
    verify_url = url_for("views.verify_email", token=token, _external=True)
    send_verification_email(email, verify_url)


@views_bp.route("/auth/login")
def auth_login():
    """Redirect the browser to Google's OAuth consent screen."""
    redirect_uri = Config.GOOGLE_REDIRECT_URI
    return oauth.google.authorize_redirect(redirect_uri)


@views_bp.route("/auth/callback")
def auth_callback():
    """Handle Google's OAuth redirect back: upsert the user, set the session."""
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo") or oauth.google.userinfo()
    google_sub = userinfo["sub"]
    email = userinfo["email"]
    name = userinfo.get("name", "")

    with get_db_session() as db:
        user = db.query(User).filter_by(google_sub=google_sub).first()
        is_new = user is None
        if is_new:
            user = User(email=email, google_sub=google_sub, name=name)
            db.add(user)
            db.flush()  # get the new id before the email is sent
        else:
            user.email = email
            user.name = name
        user_id = user.id
        needs_verification = not user.is_verified
        is_ready = user.is_verified and user.is_active

    session["user_id"] = user_id

    if needs_verification:
        _send_verification(user_id, email)
        return redirect(url_for("views.pending_approval_page"))

    if is_ready:
        return redirect(url_for("views.index"))

    return redirect(url_for("views.pending_approval_page"))


@views_bp.route("/auth/logout")
def auth_logout():
    session.pop("user_id", None)
    session.pop("totp_verified", None)
    return redirect(url_for("views.index"))


def _require_pending_user():
    """Fetch the user mid-login (session['user_id'] set, 2FA not yet done).
    Not login_required — that would redirect back here in a loop."""
    from app.utils.auth import get_current_user

    user = get_current_user()
    if user is None or not (user.is_verified and user.is_active):
        return None
    return user


def _totp_qr_svg(uri: str) -> str:
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(uri, image_factory=factory)
    return img.to_string(encoding="unicode")


@views_bp.route("/auth/setup-2fa", methods=["GET", "POST"])
def setup_2fa():
    """First-time TOTP enrollment: show a QR code, confirm with one code."""
    user = _require_pending_user()
    if user is None:
        return redirect(url_for("views.login_page"))
    if user.totp_enabled:
        return redirect(url_for("views.verify_2fa"))

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if pyotp.TOTP(user.totp_secret).verify(code, valid_window=1):
            with get_db_session() as db:
                db_user = db.get(User, user.id)
                db_user.totp_enabled = True
            session["totp_verified"] = True
            return redirect(url_for("views.index"))
        flash("รหัสไม่ถูกต้อง กรุณาลองใหม่", "error")

    if not user.totp_secret:
        with get_db_session() as db:
            db_user = db.get(User, user.id)
            db_user.totp_secret = pyotp.random_base32()
            secret = db_user.totp_secret
    else:
        secret = user.totp_secret

    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Project Echo")
    return render_template("pages/setup_2fa.html", qr_svg=_totp_qr_svg(uri), secret=secret)


@views_bp.route("/auth/verify-2fa", methods=["GET", "POST"])
def verify_2fa():
    """Routine per-session TOTP check for accounts that already enrolled."""
    user = _require_pending_user()
    if user is None:
        return redirect(url_for("views.login_page"))
    if not user.totp_enabled:
        return redirect(url_for("views.setup_2fa"))

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if pyotp.TOTP(user.totp_secret).verify(code, valid_window=1):
            session["totp_verified"] = True
            return redirect(url_for("views.index"))
        flash("รหัสไม่ถูกต้อง กรุณาลองใหม่", "error")

    return render_template("pages/verify_2fa.html")


@views_bp.route("/auth/verify-email/<token>")
def verify_email(token):
    """Mark the account's email as verified. Still awaits admin activation."""
    user_id = _load_verify_token(token)
    if user_id is None:
        flash("ลิงก์ยืนยันไม่ถูกต้องหรือหมดอายุ กรุณาเข้าสู่ระบบใหม่เพื่อขอลิงก์ใหม่", "error")
        return redirect(url_for("views.login_page"))

    with get_db_session() as db:
        user = db.get(User, user_id)
        if user is not None:
            user.is_verified = True

    flash("ยืนยันอีเมลสำเร็จ กรุณารอผู้ดูแลระบบอนุมัติบัญชี", "success")
    return redirect(url_for("views.pending_approval_page"))
