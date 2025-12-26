"""
Database service for Discord bot.

Provides async connection pool and utility queries.
Digest-specific queries are in repositories/digest_repository.py.
"""

import logging
from datetime import date
from typing import Any

import asyncpg

from config import settings

logger = logging.getLogger(__name__)

# Global connection pool (singleton pattern for async database access)
_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    """Initialize the database connection pool."""
    global _pool

    if not settings.database_url:
        logger.warning("DATABASE_URL not set, database features disabled")
        return

    # Convert SQLAlchemy URL to asyncpg format
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

    _pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)
    logger.info("Database pool initialized")


async def close_db() -> None:
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


def get_pool() -> asyncpg.Pool | None:
    """Get the current connection pool.

    Returns:
        The connection pool or None if not initialized
    """
    return _pool


# Re-export digest functions for backward compatibility
from services.repositories.digest_repository import (  # noqa: E402
    get_daily_digest_by_date,
    get_latest_daily_digest,
    get_latest_weekly_digest,
    mark_daily_digest_posted,
    mark_weekly_digest_posted,
)

__all__ = [
    "init_db",
    "close_db",
    "get_pool",
    "get_latest_daily_digest",
    "get_daily_digest_by_date",
    "get_latest_weekly_digest",
    "mark_daily_digest_posted",
    "mark_weekly_digest_posted",
    "get_database_stats",
    "check_database_health",
]


async def get_database_stats() -> dict[str, Any] | None:
    """Get database statistics for admin command.

    Returns:
        Dict with counts and dates, or None if DB unavailable
    """
    if not _pool:
        return None

    try:
        async with _pool.acquire() as conn:
            # Get counts
            articles_count = await conn.fetchval("SELECT COUNT(*) FROM articles")
            categories_count = await conn.fetchval("SELECT COUNT(*) FROM categories")
            daily_count = await conn.fetchval("SELECT COUNT(*) FROM daily_digests")
            weekly_count = await conn.fetchval("SELECT COUNT(*) FROM weekly_digests")

            # Get latest dates
            last_daily = await conn.fetchval(
                "SELECT date FROM daily_digests ORDER BY date DESC LIMIT 1"
            )
            last_weekly = await conn.fetchval(
                "SELECT week_end FROM weekly_digests ORDER BY week_end DESC LIMIT 1"
            )

            # Get articles from last 7 days
            articles_last_week = await conn.fetchval(
                "SELECT COUNT(*) FROM articles WHERE created_at >= NOW() - INTERVAL '7 days'"
            )

            return {
                "articles": articles_count,
                "categories": categories_count,
                "daily_digests": daily_count,
                "weekly_digests": weekly_count,
                "last_daily_date": last_daily,
                "last_weekly_date": last_weekly,
                "articles_last_7_days": articles_last_week,
            }
    except Exception as e:
        logger.error("Error fetching database stats: %s", e)
        return None


async def check_database_health() -> tuple[bool, str]:
    """Check if database is healthy.

    Returns:
        Tuple of (is_healthy, message)
    """
    if not _pool:
        return False, "No connection pool"

    try:
        async with _pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                return True, "Connected"
            return False, "Unexpected response"
    except Exception as e:
        return False, str(e)
