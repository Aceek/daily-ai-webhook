"""Stats repository for database operations.

Handles article statistics queries.
"""

from typing import Any


class StatsRepository:
    """Repository for article statistics operations."""

    @staticmethod
    def get_total_articles(
        cur: Any,
        mission_id: str,
        date_from: str,
        date_to: str,
    ) -> int:
        """Get total article count for date range.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            date_from: Start date (YYYY-MM-DD).
            date_to: End date (YYYY-MM-DD).

        Returns:
            Total article count.
        """
        cur.execute(
            """
            SELECT COUNT(*) as total
            FROM articles
            WHERE mission_id = %s
              AND created_at >= %s
              AND created_at < %s::date + INTERVAL '1 day'
            """,
            (mission_id, date_from, date_to),
        )
        return cur.fetchone()["total"]

    @staticmethod
    def get_articles_by_category(
        cur: Any,
        mission_id: str,
        date_from: str,
        date_to: str,
    ) -> dict[str, int]:
        """Get article count by category.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            date_from: Start date (YYYY-MM-DD).
            date_to: End date (YYYY-MM-DD).

        Returns:
            Dict mapping category name to count.
        """
        cur.execute(
            """
            SELECT c.name, COUNT(*) as count
            FROM articles a
            LEFT JOIN categories c ON a.category_id = c.id
            WHERE a.mission_id = %s
              AND a.created_at >= %s
              AND a.created_at < %s::date + INTERVAL '1 day'
            GROUP BY c.name
            ORDER BY count DESC
            """,
            (mission_id, date_from, date_to),
        )
        return {
            row["name"] or "uncategorized": row["count"]
            for row in cur.fetchall()
        }

    @staticmethod
    def get_articles_by_source(
        cur: Any,
        mission_id: str,
        date_from: str,
        date_to: str,
        limit: int = 10,
    ) -> dict[str, int]:
        """Get article count by source.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            date_from: Start date (YYYY-MM-DD).
            date_to: End date (YYYY-MM-DD).
            limit: Max sources to return.

        Returns:
            Dict mapping source to count.
        """
        cur.execute(
            """
            SELECT source, COUNT(*) as count
            FROM articles
            WHERE mission_id = %s
              AND created_at >= %s
              AND created_at < %s::date + INTERVAL '1 day'
            GROUP BY source
            ORDER BY count DESC
            LIMIT %s
            """,
            (mission_id, date_from, date_to, limit),
        )
        return {row["source"]: row["count"] for row in cur.fetchall()}

    @staticmethod
    def get_articles_by_day(
        cur: Any,
        mission_id: str,
        date_from: str,
        date_to: str,
    ) -> dict[str, int]:
        """Get article count by day.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            date_from: Start date (YYYY-MM-DD).
            date_to: End date (YYYY-MM-DD).

        Returns:
            Dict mapping date string to count.
        """
        cur.execute(
            """
            SELECT DATE(created_at) as day, COUNT(*) as count
            FROM articles
            WHERE mission_id = %s
              AND created_at >= %s
              AND created_at < %s::date + INTERVAL '1 day'
            GROUP BY DATE(created_at)
            ORDER BY day
            """,
            (mission_id, date_from, date_to),
        )
        return {str(row["day"]): row["count"] for row in cur.fetchall()}

    @staticmethod
    def get_full_stats(
        cur: Any,
        mission_id: str,
        date_from: str,
        date_to: str,
    ) -> dict[str, Any]:
        """Get all article statistics for a date range.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            date_from: Start date (YYYY-MM-DD).
            date_to: End date (YYYY-MM-DD).

        Returns:
            Dict with total, by_category, by_source, by_day.
        """
        return {
            "total_articles": StatsRepository.get_total_articles(
                cur, mission_id, date_from, date_to
            ),
            "by_category": StatsRepository.get_articles_by_category(
                cur, mission_id, date_from, date_to
            ),
            "by_source": StatsRepository.get_articles_by_source(
                cur, mission_id, date_from, date_to
            ),
            "by_day": StatsRepository.get_articles_by_day(
                cur, mission_id, date_from, date_to
            ),
        }
