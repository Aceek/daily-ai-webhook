#!/usr/bin/env python3
"""
Article repository for Claude Service.

Database access layer for article-related operations.
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

if TYPE_CHECKING:
    pass


logger = logging.getLogger("claude-service")


async def check_duplicate_urls(
    engine: AsyncEngine,
    urls: list[str],
    mission_id: str,
    days: int,
) -> tuple[list[str], list[str]]:
    """Check which URLs already exist in the database.

    Args:
        engine: SQLAlchemy async engine.
        urls: List of URLs to check.
        mission_id: Mission ID to filter by.
        days: Number of days to look back.

    Returns:
        Tuple of (new_urls, duplicate_urls).
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT url FROM articles
                    WHERE mission_id = :mission_id
                    AND created_at >= NOW() - make_interval(days => :days)
                    AND url = ANY(:urls)
                """),
                {
                    "mission_id": mission_id,
                    "days": days,
                    "urls": urls,
                },
            )
            existing_urls = {row[0] for row in result.fetchall()}

        new_urls = [url for url in urls if url not in existing_urls]
        duplicate_urls = [url for url in urls if url in existing_urls]

        logger.info(
            "URL check complete: %d new, %d duplicates",
            len(new_urls),
            len(duplicate_urls),
        )

        return new_urls, duplicate_urls

    except Exception as e:
        logger.error("Error checking URLs: %s", e)
        # On error, return all URLs as new (fail-safe)
        return urls, []
