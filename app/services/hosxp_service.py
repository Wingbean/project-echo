# app/services/hosxp_service.py - HosXP ad-hoc query service
import pandas as pd

from app.models.connection import get_hosxp_connection
from app.utils.sql_reader import get_sql_content


def execute_sql_on_hosxp(sql_filename: str, params: dict | None = None) -> pd.DataFrame:
    """Execute a single SQL file on HosXP and return results as a DataFrame.

    Ad-hoc query used by the per-HN search endpoints (no local caching).

    Args:
        sql_filename: Name of the SQL file in sql/ directory.
        params: Query parameters for the parameterized query.

    Returns:
        pandas DataFrame with query results.
    """
    query = get_sql_content(sql_filename)
    with get_hosxp_connection() as conn:
        return pd.read_sql(query, conn, params=params or {})
