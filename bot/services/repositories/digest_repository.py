"""
Digest repository for database queries.

Provides data access functions for daily and weekly digests.
Uses the connection pool from database module.
"""

import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)


def _row_to_dict(row: Any, fields: list[str]) -> dict[str, Any]:
    """Convert asyncpg row to dictionary.

    Args:
        row: Database row
        fields: List of field names

    Returns:
        Dictionary with field values
    """
    return {field: row[field] for field in fields}


async def _fetch_digest(
    table: str,
    fields: list[str],
    where_clause: str,
    params: list[Any],
    order_by: str = "",
    limit: int | None = None,
) -> dict[str, Any] | None:
    """Generic digest fetch function.

    Args:
        table: Table name
        fields: Fields to select
        where_clause: WHERE clause conditions
        params: Query parameters
        order_by: ORDER BY clause
        limit: Optional LIMIT

    Returns:
        Digest data or None
    """
    # Import here to avoid circular imports
    from services.database import get_pool

    pool = get_pool()
    if not pool:
        return None

    query = f"SELECT {', '.join(fields)} FROM {table} WHERE {where_clause}"
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit:
        query += f" LIMIT {limit}"

    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *params)
        if not row:
            return None
        return _row_to_dict(row, fields)


# Daily digest queries

DAILY_FIELDS = ["id", "mission_id", "date", "content", "generated_at", "posted_to_discord"]


async def get_latest_daily_digest(mission_id: str) -> dict[str, Any] | None:
    """Get the most recent daily digest for a mission.

    Args:
        mission_id: The mission ID (e.g., "ai-news")

    Returns:
        Digest data or None if not found
    """
    return await _fetch_digest(
        table="daily_digests",
        fields=DAILY_FIELDS,
        where_clause="mission_id = $1",
        params=[mission_id],
        order_by="date DESC",
        limit=1,
    )


async def get_daily_digest_by_date(mission_id: str, digest_date: date) -> dict[str, Any] | None:
    """Get a daily digest for a specific date.

    Args:
        mission_id: The mission ID
        digest_date: The date to fetch

    Returns:
        Digest data or None if not found
    """
    return await _fetch_digest(
        table="daily_digests",
        fields=DAILY_FIELDS,
        where_clause="mission_id = $1 AND date = $2",
        params=[mission_id, digest_date],
    )


async def mark_daily_digest_posted(digest_id: int) -> None:
    """Mark a daily digest as posted to Discord.

    Args:
        digest_id: The digest ID to update
    """
    from services.database import get_pool

    pool = get_pool()
    if not pool:
        return

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE daily_digests SET posted_to_discord = true WHERE id = $1",
            digest_id,
        )


# Weekly digest queries

WEEKLY_FIELDS = [
    "id", "mission_id", "week_start", "week_end",
    "params", "content", "generated_at", "is_standard"
]


async def get_latest_weekly_digest(
    mission_id: str,
    standard_only: bool = True,
) -> dict[str, Any] | None:
    """Get the most recent weekly digest for a mission.

    Args:
        mission_id: The mission ID
        standard_only: If True, only return standard (non-themed) digests

    Returns:
        Digest data or None if not found
    """
    where_clause = "mission_id = $1"
    if standard_only:
        where_clause += " AND is_standard = true"

    return await _fetch_digest(
        table="weekly_digests",
        fields=WEEKLY_FIELDS,
        where_clause=where_clause,
        params=[mission_id],
        order_by="week_end DESC",
        limit=1,
    )


async def mark_weekly_digest_posted(digest_id: int) -> None:
    """Mark a weekly digest as posted to Discord.

    Args:
        digest_id: The digest ID to update
    """
    from services.database import get_pool

    pool = get_pool()
    if not pool:
        return

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE weekly_digests SET posted_to_discord = true WHERE id = $1",
            digest_id,
        )
