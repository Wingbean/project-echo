# app/models/connection.py - Database Connection Management
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from app.config import Config


def _build_hosxp_url():
    """Build SQLAlchemy connection URL for HosXP MySQL server."""
    host = Config.HOSXP_HOST
    user = Config.HOSXP_USER
    password = Config.HOSXP_PASS
    db = Config.HOSXP_DB
    port = Config.HOSXP_PORT

    if not all([host, user, db]):
        return None

    return (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8"
    )


def get_sqlite_engine():
    """Get or create the SQLite engine for local cache."""
    db_path = Config.SQLITE_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_hosxp_engine():
    """Get or create the HosXP MySQL engine."""
    url = _build_hosxp_url()
    if url is None:
        raise ConnectionError(
            "HosXP connection not configured. "
            "Check HOSXP_HOST, HOSXP_USER, HOSXP_DB in .env"
        )
    return create_engine(url, echo=False, pool_pre_ping=True)


@contextmanager
def get_hosxp_connection():
    """Context manager for HosXP database connections.

    Usage:
        with get_hosxp_connection() as conn:
            df = pd.read_sql(query, conn)
    """
    engine = get_hosxp_engine()
    conn = None
    try:
        conn = engine.connect()
        yield conn
    except Exception as e:
        print(f"❌ Error connecting to HosXP: {e}")
        raise
    finally:
        if conn:
            conn.close()


# Module-level SQLite engine (singleton)
sqlite_engine = get_sqlite_engine()
