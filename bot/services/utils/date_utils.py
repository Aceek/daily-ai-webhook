"""
Date utility functions for bot services.

Provides common date calculations and formatting.
"""

from datetime import datetime, timedelta


def get_last_7_days() -> tuple[str, str]:
    """Calculate last 7 days date range.

    Returns:
        Tuple of (week_start, week_end) as YYYY-MM-DD strings
        where week_start is 7 days ago and week_end is today.
    """
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)

    return seven_days_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def format_date_display(date_str: str) -> str:
    """Format a date string for display.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        Formatted date string (e.g., "December 26, 2025")
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return date_str


def calculate_days_in_range(start_date: str, end_date: str) -> int:
    """Calculate number of days in a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Number of days (inclusive)
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days + 1
    except (ValueError, TypeError):
        return 7  # Default to week


def validate_date_format(date_str: str) -> bool:
    """Validate that a string is in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False
