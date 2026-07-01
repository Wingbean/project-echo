# app/utils/sql_reader.py - SQL File Reader Utility
import os
from functools import lru_cache

# Base directory for SQL files
_SQL_DIR = os.path.join(
    os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "sql",
)


@lru_cache(maxsize=32)
def get_sql_content(filename: str) -> str:
    """Read a SQL file from the sql/ directory.

    Cached: .sql files are static at runtime, so read each once.

    Args:
        filename: Name of the SQL file (e.g., 'egfr.sql').

    Returns:
        The SQL file content as a string.

    Raises:
        FileNotFoundError: If the SQL file doesn't exist.
    """
    sql_path = os.path.join(_SQL_DIR, filename)
    if not os.path.isfile(sql_path):
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()
