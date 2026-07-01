# app/models/connection.py - Database Connection Management
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

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8"


# Module-level engine (singleton). Creating an engine per request throws away
# the connection pool, so build it once and reuse.
_hosxp_engine = None


def get_hosxp_engine():
    """Get the shared HosXP MySQL engine, creating it on first use."""
    global _hosxp_engine
    if _hosxp_engine is None:
        url = _build_hosxp_url()
        if url is None:
            raise ConnectionError(
                "HosXP connection not configured. "
                "Check HOSXP_HOST, HOSXP_USER, HOSXP_DB in .env"
            )
        _hosxp_engine = create_engine(url, echo=False, pool_pre_ping=True)
    return _hosxp_engine


@contextmanager
def get_hosxp_connection():
    """Context manager for HosXP database connections.

    Usage:
        with get_hosxp_connection() as conn:
            df = pd.read_sql(query, conn)
    """
    engine = get_hosxp_engine()
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()
