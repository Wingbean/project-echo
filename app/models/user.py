# app/models/user.py - User model (local auth DB)
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    # google_sub (the OIDC 'sub' claim) is the real lookup key — immutable,
    # unlike email which a Google account could change.
    google_sub = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)

    is_verified = Column(Boolean, default=False, nullable=False)  # clicked the emailed link
    is_active = Column(Boolean, default=False, nullable=False)    # admin-approved

    can_access_echo = Column(Boolean, default=False, nullable=False)
    can_access_emr = Column(Boolean, default=False, nullable=False)

    totp_secret = Column(String(32), nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
