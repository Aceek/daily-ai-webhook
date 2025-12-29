"""Article repository for database operations.

Handles all article-related database queries and inserts.
"""

from datetime import datetime
from typing import Any


class ArticleRepository:
    """Repository for article database operations."""

    @staticmethod
    def get_articles(
        cur: Any,
        mission_id: str,
        categories: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get articles from database with optional filters.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            categories: Optional list of category names to filter.
            date_from: Optional start date (YYYY-MM-DD).
            date_to: Optional end date (YYYY-MM-DD).
            limit: Maximum articles to return (capped at 500).

        Returns:
            List of article dicts.
        """
        limit = min(limit, 500)

        query = """
            SELECT a.id, a.title, a.url, a.source, a.description,
                   a.pub_date, a.created_at, c.name as category_name
            FROM articles a
            LEFT JOIN categories c ON a.category_id = c.id
            WHERE a.mission_id = %s
        """
        params: list[Any] = [mission_id]

        if categories:
            query += " AND c.name = ANY(%s)"
            params.append(categories)

        if date_from:
            query += " AND a.created_at >= %s"
            params.append(date_from)

        if date_to:
            query += " AND a.created_at < %s::date + INTERVAL '1 day'"
            params.append(date_to)

        query += " ORDER BY a.created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        return [ArticleRepository._format_article(row) for row in cur.fetchall()]

    @staticmethod
    def _format_article(row: dict[str, Any]) -> dict[str, Any]:
        """Format article row to response dict.

        Args:
            row: Database row.

        Returns:
            Formatted article dict.
        """
        return {
            "id": row["id"],
            "title": row["title"],
            "url": row["url"],
            "source": row["source"],
            "description": row["description"][:200] if row["description"] else None,
            "pub_date": row["pub_date"].isoformat() if row["pub_date"] else None,
            "category": row["category_name"],
        }

    @staticmethod
    def get_recent_headlines(
        cur: Any,
        mission_id: str,
        days: int = 3,
    ) -> list[dict[str, Any]]:
        """Get recent headlines to avoid duplicate coverage.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            days: Number of days to look back (max 7).

        Returns:
            List of headline dicts.
        """
        days = min(days, 7)

        cur.execute(
            """
            SELECT a.title, a.url, DATE(a.created_at) as date, c.name as category
            FROM articles a
            LEFT JOIN categories c ON a.category_id = c.id
            WHERE a.mission_id = %s
              AND a.status = 'selected'
              AND a.created_at >= NOW() - INTERVAL '%s days'
            ORDER BY a.created_at DESC
            LIMIT 50
            """,
            (mission_id, days),
        )

        return [
            {
                "title": row["title"],
                "url": row["url"],
                "date": str(row["date"]),
                "category": row["category"],
            }
            for row in cur.fetchall()
        ]

    @staticmethod
    def insert_selected_article(
        cur: Any,
        mission_id: str,
        category_id: int,
        digest_id: int,
        item: dict[str, Any],
    ) -> None:
        """Insert a selected article into the database.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            category_id: Category ID for the article.
            digest_id: Daily digest ID.
            item: Article data dict.
        """
        cur.execute(
            """
            INSERT INTO articles (mission_id, category_id, daily_digest_id,
                                 title, url, source, description, created_at,
                                 status, relevance_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
            """,
            (
                mission_id,
                category_id,
                digest_id,
                item["title"],
                item["url"],
                item["source"],
                item.get("summary", ""),
                datetime.now(),
                "selected",
                item.get("relevance_score"),
            ),
        )

    @staticmethod
    def insert_excluded_article(
        cur: Any,
        mission_id: str,
        category_id: int,
        item: dict[str, Any],
    ) -> None:
        """Insert an excluded article into the database.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            category_id: Category ID for the article.
            item: Excluded article data dict.
        """
        cur.execute(
            """
            INSERT INTO articles (mission_id, category_id, daily_digest_id,
                                 title, url, source, description, created_at,
                                 status, exclusion_reason, relevance_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING
            """,
            (
                mission_id,
                category_id,
                None,  # No digest association for excluded
                item["title"],
                item["url"],
                item.get("source", "unknown"),
                None,  # No summary for excluded
                datetime.now(),
                "excluded",
                item["reason"],
                item["score"],
            ),
        )
