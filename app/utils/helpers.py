# app/utils/helpers.py - General Helper Functions
import calendar
from datetime import datetime


def get_current_month_range() -> tuple[str, str]:
    """Get start and end date of the current month.

    Returns:
        Tuple of (start_date, end_date) as YYYY-MM-DD strings.
    """
    now = datetime.now()
    start_date = now.replace(day=1).strftime("%Y-%m-%d")
    _, last_day = calendar.monthrange(now.year, now.month)
    end_date = now.replace(day=last_day).strftime("%Y-%m-%d")
    return start_date, end_date


def format_thai_date(dt: datetime) -> str:
    """Format a datetime to Thai-friendly display.

    Args:
        dt: A datetime object.

    Returns:
        Formatted string like '26/02/2569' (Buddhist Era).
    """
    if dt is None:
        return "-"
    thai_year = dt.year + 543
    return f"{dt.day:02d}/{dt.month:02d}/{thai_year}"


def safe_int(value, default: int = 0) -> int:
    """Safely convert a value to int.

    Args:
        value: Value to convert.
        default: Default if conversion fails.

    Returns:
        Integer value or default.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert a value to float.

    Args:
        value: Value to convert.
        default: Default if conversion fails.

    Returns:
        Float value or default.
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
