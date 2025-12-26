"""Repository modules for database access."""

from services.repositories.digest_repository import (
    get_daily_digest_by_date,
    get_latest_daily_digest,
    get_latest_weekly_digest,
    mark_daily_digest_posted,
    mark_weekly_digest_posted,
)

__all__ = [
    "get_daily_digest_by_date",
    "get_latest_daily_digest",
    "get_latest_weekly_digest",
    "mark_daily_digest_posted",
    "mark_weekly_digest_posted",
]
