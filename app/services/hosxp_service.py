# app/services/hosxp_service.py - HosXP Data Sync Service
import os
import fcntl
from datetime import datetime

import pandas as pd

from app.config import Config
from app.models.connection import get_hosxp_connection, sqlite_engine
from app.utils.sql_reader import get_sql_content

# Paths
_INSTANCE_DIR = Config.INSTANCE_DIR
_LOCK_FILE = os.path.join(_INSTANCE_DIR, "data_cache.sync.lock")
_TIMESTAMP_FILE = os.path.join(_INSTANCE_DIR, "last_sync.txt")


def sync_data_from_hosxp(
    start_date: str,
    end_date: str,
    tasks: list[tuple[str, str]] | None = None,
    exclude: list[str] | None = None,
) -> dict:
    """Sync data from HosXP server to local SQLite cache.

    Reads SQL files, executes them on HosXP, and stores results in SQLite.

    Args:
        start_date: Start date for queries (YYYY-MM-DD).
        end_date: End date for queries (YYYY-MM-DD).
        tasks: Optional list of (sql_filename, table_name) tuples.
               If None, uses default task list.
        exclude: Optional list of SQL filenames to exclude.

    Returns:
        Dictionary with sync status and per-table results.
    """
    os.makedirs(_INSTANCE_DIR, exist_ok=True)

    # File lock to prevent concurrent syncs
    lock_fd = open(_LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, OSError):
        print("⏳ Sync is already running. Skipping.")
        return {
            "status": "error",
            "message": "การซิงค์ข้อมูลกำลังทำงานอยู่ กรุณารอสักครู่",
        }

    results = {}

    # Default tasks if not provided
    if tasks is None:
        tasks = _get_default_tasks()

    # Apply exclusions
    if exclude:
        tasks = [t for t in tasks if t[0] not in exclude]

    query_params = {"start_date": start_date, "end_date": end_date}

    try:
        with get_hosxp_connection() as conn:
            print(f"🚀 Starting Sync: {start_date} to {end_date}")

            for sql_file, table_name in tasks:
                try:
                    query = get_sql_content(sql_file)
                    df = pd.read_sql(query, conn, params=query_params)
                    df.to_sql(
                        table_name,
                        sqlite_engine,
                        if_exists="replace",
                        index=False,
                    )
                    row_count = len(df)
                    results[table_name] = f"Success ({row_count} rows)"
                    print(f"✅ Synced {table_name}: {row_count} rows")
                except Exception as e:
                    print(f"❌ Error syncing {table_name}: {e}")
                    results[table_name] = f"Error: {str(e)}"

        save_last_sync_time()
        return {"status": "success", "details": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
        except Exception:
            pass


def execute_sql_on_hosxp(sql_filename: str, params: dict | None = None) -> pd.DataFrame:
    """Execute a single SQL file on HosXP and return results as DataFrame.

    This is for ad-hoc queries that don't need to be cached in SQLite.

    Args:
        sql_filename: Name of the SQL file in sql/ directory.
        params: Query parameters for parameterized queries.

    Returns:
        pandas DataFrame with query results.
    """
    query = get_sql_content(sql_filename)
    with get_hosxp_connection() as conn:
        return pd.read_sql(query, conn, params=params or {})


def get_dataframe_from_sqlite(table_name: str) -> pd.DataFrame:
    """Read a table from the local SQLite cache.

    Args:
        table_name: Name of the table in SQLite.

    Returns:
        pandas DataFrame with table data, or empty DataFrame if not found.
    """
    try:
        return pd.read_sql(f"SELECT * FROM [{table_name}]", sqlite_engine)
    except Exception:
        return pd.DataFrame()


def save_last_sync_time():
    """Save the current timestamp as last sync time."""
    os.makedirs(_INSTANCE_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d : %H.%M.%S")
    try:
        with open(_TIMESTAMP_FILE, "w") as f:
            f.write(now)
    except Exception as e:
        print(f"Error saving timestamp: {e}")


def get_last_sync_time() -> str:
    """Read the last sync timestamp.

    Returns:
        Timestamp string or '-' if not available.
    """
    if os.path.exists(_TIMESTAMP_FILE):
        try:
            with open(_TIMESTAMP_FILE, "r") as f:
                return f.read().strip()
        except Exception:
            return "-"
    return "-"


def _get_default_tasks() -> list[tuple[str, str]]:
    """Get default sync task list.

    Override this with your actual SQL files and table names.

    Returns:
        List of (sql_filename, sqlite_table_name) tuples.
    """
    # Example tasks - customize for your project
    return [
        # ('your_query.sql', 'your_table_name'),
    ]
