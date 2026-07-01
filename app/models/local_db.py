# app/models/local_db.py - Local app DB (users). SQLite, separate from HosXP.
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Config

_local_engine = None
_SessionLocal = None


def get_local_engine():
    """Singleton engine for the local users SQLite DB (instance/app.db).

    Uses an in-memory DB (shared across connections via StaticPool) under
    FLASK_ENV=testing so tests never touch the real instance/app.db file.
    """
    global _local_engine
    if _local_engine is None:
        if Config.FLASK_ENV == "testing":
            _local_engine = create_engine(
                "sqlite://",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            db_path = os.path.join(Config.INSTANCE_DIR, "app.db")
            # ponytail: gunicorn runs multiple workers/processes against one
            # sqlite file — fine here since writes are rare (login/admin
            # actions), not a hot path. check_same_thread=False covers
            # threads within a worker.
            _local_engine = create_engine(
                f"sqlite:///{db_path}",
                connect_args={"check_same_thread": False},
            )
    return _local_engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_local_engine())
    return _SessionLocal


@contextmanager
def get_db_session():
    """Yield a SQLAlchemy session; commits on success, rolls back on error."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
