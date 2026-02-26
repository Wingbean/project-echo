# app/utils/sql_reader.py - SQL File Reader Utility
import os

# Base directory for SQL files
_SQL_DIR = os.path.join(
    os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "sql",
)


def get_sql_content(filename: str) -> str:
    """Read a SQL file from the sql/ directory.

    Args:
        filename: Name of the SQL file (e.g., 'schema.sql').

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


def list_sql_files() -> list[str]:
    """List all .sql files available in the sql/ directory.

    Returns:
        Sorted list of SQL filenames.
    """
    if not os.path.isdir(_SQL_DIR):
        return []
    return sorted(f for f in os.listdir(_SQL_DIR) if f.endswith(".sql"))
