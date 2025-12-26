"""Article query service.

Handles all read operations for articles, categories, and stats.
"""

from typing import Any

from ..logger import logger
from ..repositories.base import get_db_connection
from ..repositories.article import ArticleRepository
from ..repositories.category import CategoryRepository
from ..repositories.stats import StatsRepository


class ArticleQueryService:
    """Service for querying articles, categories, and statistics."""

    @staticmethod
    def get_categories(
        mission_id: str,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """Get all categories for a mission.

        Args:
            mission_id: The mission ID.
            date_from: Optional start date (YYYY-MM-DD).
            date_to: Optional end date (YYYY-MM-DD).

        Returns:
            Dict with status, categories list, and count.
        """
        conn, db_error = get_db_connection()
        if not conn:
            return {
                "status": "error",
                "message": f"Database not available: {db_error}",
            }

        try:
            with conn.cursor() as cur:
                categories = CategoryRepository.get_categories_by_mission(
                    cur, mission_id, date_from, date_to
                )
                return {
                    "status": "success",
                    "mission_id": mission_id,
                    "categories": categories,
                    "count": len(categories),
                }
        except Exception as e:
            logger.error(f"get_categories failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    @staticmethod
    def get_articles(
        mission_id: str,
        categories: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Get articles with optional filters.

        Args:
            mission_id: The mission ID.
            categories: Optional category filter.
            date_from: Optional start date (YYYY-MM-DD).
            date_to: Optional end date (YYYY-MM-DD).
            limit: Maximum articles to return.

        Returns:
            Dict with status, articles list, and filters.
        """
        conn, db_error = get_db_connection()
        if not conn:
            return {
                "status": "error",
                "message": f"Database not available: {db_error}",
            }

        try:
            with conn.cursor() as cur:
                articles = ArticleRepository.get_articles(
                    cur, mission_id, categories, date_from, date_to, limit
                )
                return {
                    "status": "success",
                    "mission_id": mission_id,
                    "articles": articles,
                    "count": len(articles),
                    "filters": {
                        "categories": categories,
                        "date_from": date_from,
                        "date_to": date_to,
                    },
                }
        except Exception as e:
            logger.error(f"get_articles failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    @staticmethod
    def get_article_stats(
        mission_id: str,
        date_from: str,
        date_to: str,
    ) -> dict[str, Any]:
        """Get article statistics for a date range.

        Args:
            mission_id: The mission ID.
            date_from: Start date (YYYY-MM-DD).
            date_to: End date (YYYY-MM-DD).

        Returns:
            Dict with total, by_category, by_source, by_day.
        """
        conn, db_error = get_db_connection()
        if not conn:
            return {
                "status": "error",
                "message": f"Database not available: {db_error}",
            }

        try:
            with conn.cursor() as cur:
                stats = StatsRepository.get_full_stats(
                    cur, mission_id, date_from, date_to
                )
                return {
                    "status": "success",
                    "mission_id": mission_id,
                    "date_range": {"from": date_from, "to": date_to},
                    **stats,
                }
        except Exception as e:
            logger.error(f"get_article_stats failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    @staticmethod
    def get_recent_headlines(
        mission_id: str,
        days: int = 3,
    ) -> dict[str, Any]:
        """Get recent headlines to avoid duplicate coverage.

        Args:
            mission_id: The mission ID.
            days: Number of days to look back (max 7).

        Returns:
            Dict with headlines list.
        """
        conn, db_error = get_db_connection()
        if not conn:
            return {
                "status": "error",
                "message": f"Database not available: {db_error}",
            }

        days = min(days, 7)

        try:
            with conn.cursor() as cur:
                headlines = ArticleRepository.get_recent_headlines(
                    cur, mission_id, days
                )
                return {
                    "status": "success",
                    "mission_id": mission_id,
                    "days": days,
                    "headlines": headlines,
                    "count": len(headlines),
                }
        except Exception as e:
            logger.error(f"get_recent_headlines failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()
