# app/utils/validators.py - Input Validation Utilities
import re
from datetime import datetime


def validate_date(date_str: str, fmt: str = "%Y-%m-%d") -> bool:
    """Validate a date string against a format.

    Args:
        date_str: The date string to validate.
        fmt: Expected format (default: YYYY-MM-DD).

    Returns:
        True if valid, False otherwise.
    """
    try:
        datetime.strptime(date_str, fmt)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize a string input by stripping and truncating.

    Args:
        value: The input string.
        max_length: Maximum allowed length.

    Returns:
        Sanitized string.
    """
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]


def validate_table_name(name: str) -> bool:
    """Validate that a table name is safe (alphanumeric + underscore only).

    Prevents SQL injection via table names.

    Args:
        name: The table name to validate.

    Returns:
        True if safe, False otherwise.
    """
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))


def validate_required_fields(data: dict, required: list[str]) -> list[str]:
    """Check that all required fields are present and non-empty.

    Args:
        data: Dictionary of field values.
        required: List of required field names.

    Returns:
        List of missing/empty field names. Empty list means all valid.
    """
    missing = []
    for field in required:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return missing
