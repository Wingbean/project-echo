# app/services/render_service.py - Data Rendering Service
import pandas as pd
from app.models.connection import sqlite_engine
from app.services.hosxp_service import get_dataframe_from_sqlite


def get_dashboard_data() -> dict:
    """Retrieve all dashboard data from SQLite cache.

    Reads cached data and prepares it for template rendering.

    Returns:
        Dictionary with table names as keys and data as values.
    """
    data = {}

    # Example: read cached tables and prepare for display
    # Customize this for your actual tables
    try:
        tables = _list_cached_tables()
        for table_name in tables:
            df = get_dataframe_from_sqlite(table_name)
            if not df.empty:
                data[table_name] = {
                    "records": df.to_dict(orient="records"),
                    "columns": list(df.columns),
                    "row_count": len(df),
                }
    except Exception as e:
        print(f"❌ Error loading dashboard data: {e}")
        data["error"] = str(e)

    return data


def get_table_data(table_name: str) -> dict:
    """Get data for a specific table from SQLite cache.

    Args:
        table_name: Name of the SQLite table.

    Returns:
        Dictionary with records, columns, and row count.
    """
    df = get_dataframe_from_sqlite(table_name)
    if df.empty:
        return {"records": [], "columns": [], "row_count": 0}

    return {
        "records": df.to_dict(orient="records"),
        "columns": list(df.columns),
        "row_count": len(df),
    }


def query_sqlite(sql: str, params: dict | None = None) -> dict:
    """Execute a parameterized query on the local SQLite database.

    Args:
        sql: SQL query string with named parameters (e.g., :param_name).
        params: Dictionary of parameter values.

    Returns:
        Dictionary with records, columns, and row count.
    """
    try:
        from sqlalchemy import text
        with sqlite_engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            columns = list(result.keys())
            records = [dict(zip(columns, row)) for row in result.fetchall()]
            return {
                "records": records,
                "columns": columns,
                "row_count": len(records),
            }
    except Exception as e:
        print(f"❌ SQLite query error: {e}")
        return {"records": [], "columns": [], "row_count": 0, "error": str(e)}


def _list_cached_tables() -> list[str]:
    """List all tables in the SQLite cache database.

    Returns:
        Sorted list of table names.
    """
    try:
        df = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
            sqlite_engine,
        )
        return df["name"].tolist()
    except Exception:
        return []
