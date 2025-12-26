"""Digest repository for database operations.

Handles daily and weekly digest inserts.
"""

import json
from datetime import date, datetime
from typing import Any

from .article import ArticleRepository
from .category import CategoryRepository


class DigestRepository:
    """Repository for digest database operations."""

    @staticmethod
    def insert_daily_digest(
        cur: Any,
        mission_id: str,
        digest_date: date,
        content: dict[str, Any],
    ) -> int:
        """Insert or update a daily digest.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            digest_date: Date of the digest.
            content: Full digest content as dict.

        Returns:
            Digest ID.
        """
        cur.execute(
            """
            INSERT INTO daily_digests (mission_id, date, content, generated_at, posted_to_discord)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (mission_id, date)
            DO UPDATE SET content = EXCLUDED.content, generated_at = EXCLUDED.generated_at
            RETURNING id
            """,
            (mission_id, digest_date, json.dumps(content), datetime.now(), False),
        )
        return cur.fetchone()["id"]

    @staticmethod
    def insert_weekly_digest(
        cur: Any,
        mission_id: str,
        week_start: str,
        week_end: str,
        content: dict[str, Any],
        params: str | None = None,
        is_standard: bool = True,
    ) -> int:
        """Insert a weekly digest.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            week_start: Start date (YYYY-MM-DD).
            week_end: End date (YYYY-MM-DD).
            content: Digest content as dict.
            params: Optional JSON params (theme filter).
            is_standard: Whether this is a standard weekly digest.

        Returns:
            Digest ID.
        """
        cur.execute(
            """
            INSERT INTO weekly_digests (mission_id, week_start, week_end, params, content,
                                        is_standard, posted_to_discord, generated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                mission_id,
                week_start,
                week_end,
                json.dumps({"theme": params}) if params else None,
                json.dumps(content),
                is_standard,
                False,
                datetime.now(),
            ),
        )
        return cur.fetchone()["id"]

    @staticmethod
    def batch_insert_articles(
        cur: Any,
        mission_id: str,
        digest_id: int,
        selected_items: list[tuple[dict[str, Any], str]],
        excluded_items: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """Insert selected and excluded articles in batch.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            digest_id: Daily digest ID.
            selected_items: List of (item, section_name) tuples.
            excluded_items: List of excluded item dicts.

        Returns:
            Tuple of (selected_count, excluded_count).
        """
        selected_count = 0
        for item, _ in selected_items:
            category_id = CategoryRepository.get_or_create_category(
                cur, mission_id, item["category"]
            )
            ArticleRepository.insert_selected_article(
                cur, mission_id, category_id, digest_id, item
            )
            selected_count += 1

        excluded_count = 0
        for item in excluded_items:
            category_id = CategoryRepository.get_or_create_category(
                cur, mission_id, item["category"]
            )
            ArticleRepository.insert_excluded_article(
                cur, mission_id, category_id, item
            )
            excluded_count += 1

        return selected_count, excluded_count
