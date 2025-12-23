"""
Database service for Discord bot.

Provides async queries for digests and articles.
"""

import logging
from datetime import date
from typing import Any

import asyncpg

from config import settings

logger = logging.getLogger(__name__)

# Global connection pool
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


async def get_latest_daily_digest(mission_id: str) -> dict[str, Any] | None:
    """Get the most recent daily digest for a mission.

    Args:
        mission_id: The mission ID (e.g., "ai-news")

    Returns:
        Digest data or None if not found
    """
    if not _pool:
        return None

    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, mission_id, date, content, generated_at, posted_to_discord
            FROM daily_digests
            WHERE mission_id = $1
            ORDER BY date DESC
            LIMIT 1
            """,
            mission_id,
        )

        if not row:
            return None

        return {
            "id": row["id"],
            "mission_id": row["mission_id"],
            "date": row["date"],
            "content": row["content"],
            "generated_at": row["generated_at"],
            "posted_to_discord": row["posted_to_discord"],
        }


async def get_daily_digest_by_date(mission_id: str, digest_date: date) -> dict[str, Any] | None:
    """Get a daily digest for a specific date.

    Args:
        mission_id: The mission ID
        digest_date: The date to fetch

    Returns:
        Digest data or None if not found
    """
    if not _pool:
        return None

    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, mission_id, date, content, generated_at, posted_to_discord
            FROM daily_digests
            WHERE mission_id = $1 AND date = $2
            """,
            mission_id,
            digest_date,
        )

        if not row:
            return None

        return {
            "id": row["id"],
            "mission_id": row["mission_id"],
            "date": row["date"],
            "content": row["content"],
            "generated_at": row["generated_at"],
            "posted_to_discord": row["posted_to_discord"],
        }


async def get_latest_weekly_digest(mission_id: str, standard_only: bool = True) -> dict[str, Any] | None:
    """Get the most recent weekly digest for a mission.

    Args:
        mission_id: The mission ID
        standard_only: If True, only return standard (non-themed) digests

    Returns:
        Digest data or None if not found
    """
    if not _pool:
        return None

    async with _pool.acquire() as conn:
        query = """
            SELECT id, mission_id, week_start, week_end, params, content, generated_at, is_standard
            FROM weekly_digests
            WHERE mission_id = $1
        """
        params = [mission_id]

        if standard_only:
            query += " AND is_standard = true"

        query += " ORDER BY week_end DESC LIMIT 1"

        row = await conn.fetchrow(query, *params)

        if not row:
            return None

        return {
            "id": row["id"],
            "mission_id": row["mission_id"],
            "week_start": row["week_start"],
            "week_end": row["week_end"],
            "params": row["params"],
            "content": row["content"],
            "generated_at": row["generated_at"],
            "is_standard": row["is_standard"],
        }


async def mark_daily_digest_posted(digest_id: int) -> None:
    """Mark a daily digest as posted to Discord.

    Args:
        digest_id: The digest ID to update
    """
    if not _pool:
        return

    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE daily_digests SET posted_to_discord = true WHERE id = $1",
            digest_id,
        )
