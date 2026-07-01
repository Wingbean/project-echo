# app/utils/email.py - Send email-verification links via Gmail SMTP
import smtplib
from email.mime.text import MIMEText

from app.config import Config

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


def send_verification_email(to_email: str, verify_url: str):
    """Send a plain-text email-verification link. Raises on SMTP failure."""
    msg = MIMEText(
        f"กรุณายืนยันอีเมลของคุณโดยคลิกลิงก์นี้:\n{verify_url}\n\nลิงก์นี้หมดอายุใน 24 ชั่วโมง",
        "plain",
        "utf-8",
    )
    msg["Subject"] = "ยืนยันอีเมล - Project Echo"
    msg["From"] = Config.EMAIL_FROM
    msg["To"] = to_email

    with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
        server.starttls()
        server.login(Config.EMAIL_FROM, Config.EMAIL_PASSWORD)
        server.sendmail(Config.EMAIL_FROM, [to_email], msg.as_string())
