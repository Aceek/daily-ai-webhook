"""Category repository for database operations.

Handles all category-related database queries.
"""

from datetime import datetime
from typing import Any


class CategoryRepository:
    """Repository for category database operations."""

    @staticmethod
    def get_categories_by_mission(
        cur: Any,
        mission_id: str,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get categories for a mission, optionally filtered by date range.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            date_from: Optional start date (YYYY-MM-DD).
            date_to: Optional end date (YYYY-MM-DD).

        Returns:
            List of category dicts with id and name.
        """
        if date_from and date_to:
            cur.execute(
                """
                SELECT DISTINCT c.id, c.name, c.created_at
                FROM categories c
                JOIN articles a ON a.category_id = c.id
                WHERE c.mission_id = %s
                  AND a.created_at >= %s
                  AND a.created_at < %s::date + INTERVAL '1 day'
                ORDER BY c.name
                """,
                (mission_id, date_from, date_to),
            )
        else:
            cur.execute(
                """
                SELECT id, name, created_at
                FROM categories
                WHERE mission_id = %s
                ORDER BY name
                """,
                (mission_id,),
            )

        return [{"id": row["id"], "name": row["name"]} for row in cur.fetchall()]

    @staticmethod
    def get_or_create_category(
        cur: Any,
        mission_id: str,
        category_name: str,
    ) -> int:
        """Get or create a category, returning its ID.

        Args:
            cur: Database cursor.
            mission_id: The mission ID.
            category_name: Name of the category.

        Returns:
            Category ID.
        """
        cur.execute(
            "SELECT id FROM categories WHERE mission_id = %s AND name = %s",
            (mission_id, category_name),
        )
        row = cur.fetchone()
        if row:
            return row["id"]

        cur.execute(
            """
            INSERT INTO categories (mission_id, name, created_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (mission_id, category_name, datetime.now()),
        )
        return cur.fetchone()["id"]
