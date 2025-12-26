"""Weekly digest submission service.

Handles validation, database save, and file output for weekly digests.
"""

from typing import Any

from ..logger import logger
from ..repositories.base import get_db_connection
from ..repositories.digest import DigestRepository
from ..utils import build_weekly_digest_structure, write_digest_to_file
from ..validators import validate_weekly_digest


class WeeklyDigestSubmitter:
    """Service for submitting weekly digests."""

    @staticmethod
    def submit(
        execution_id: str,
        mission_id: str,
        week_start: str,
        week_end: str,
        summary: str,
        trends: list[dict[str, Any]],
        top_stories: list[dict[str, Any]],
        category_analysis: dict[str, Any],
        metadata: dict[str, Any],
        is_standard: bool = True,
    ) -> dict[str, Any]:
        """Submit a weekly digest with trend analysis.

        Args:
            execution_id: The execution identifier.
            mission_id: The mission ID.
            week_start: Start date (YYYY-MM-DD).
            week_end: End date (YYYY-MM-DD).
            summary: Executive summary.
            trends: List of identified trends.
            top_stories: List of top stories.
            category_analysis: Category breakdown.
            metadata: Additional metadata.
            is_standard: Whether this is a standard weekly digest.

        Returns:
            Dict with status and storage confirmation.
        """
        # Validate input
        errors = validate_weekly_digest(summary, trends, top_stories)

        if errors:
            return {
                "status": "error",
                "errors": errors,
                "message": "Validation failed. Please fix the errors and resubmit.",
            }

        logger.info(
            "submit_weekly_digest called",
            execution_id=execution_id,
            week=f"{week_start} to {week_end}",
        )

        # Save to database
        db_result = WeeklyDigestSubmitter._save_to_database(
            mission_id, week_start, week_end, summary, trends,
            top_stories, category_analysis, metadata, is_standard
        )

        # Build digest structure
        digest = build_weekly_digest_structure(
            execution_id, mission_id, week_start, week_end,
            summary, trends, top_stories, category_analysis,
            metadata, db_result["digest_id"]
        )

        # Write to file
        output_file = write_digest_to_file(digest, execution_id)
        logger.operation("write_file", "success", str(output_file))

        # Build response
        return WeeklyDigestSubmitter._build_response(
            execution_id, output_file, week_start, week_end,
            trends, top_stories, db_result
        )

    @staticmethod
    def _save_to_database(
        mission_id: str,
        week_start: str,
        week_end: str,
        summary: str,
        trends: list[dict[str, Any]],
        top_stories: list[dict[str, Any]],
        category_analysis: dict[str, Any],
        metadata: dict[str, Any],
        is_standard: bool,
    ) -> dict[str, Any]:
        """Save weekly digest to database.

        Args:
            mission_id: The mission ID.
            week_start: Start date (YYYY-MM-DD).
            week_end: End date (YYYY-MM-DD).
            summary: Executive summary.
            trends: List of trends.
            top_stories: List of top stories.
            category_analysis: Category breakdown.
            metadata: Additional metadata.
            is_standard: Whether standard weekly digest.

        Returns:
            Dict with db_saved, db_error, digest_id.
        """
        conn, conn_error = get_db_connection()

        if not conn:
            logger.operation("db_connect", "error", conn_error or "Unknown error")
            return {
                "db_saved": False,
                "db_error": conn_error,
                "digest_id": None,
            }

        logger.operation("db_connect", "success", "Connected to PostgreSQL")

        try:
            with conn.cursor() as cur:
                # Build content structure
                content = WeeklyDigestSubmitter._build_content(
                    summary, trends, top_stories, category_analysis, metadata
                )

                # Get theme param if present
                theme_param = metadata.get("theme") if metadata else None

                # Insert digest
                digest_id = DigestRepository.insert_weekly_digest(
                    cur, mission_id, week_start, week_end,
                    content, theme_param, is_standard
                )

                conn.commit()
                logger.operation(
                    "insert_weekly_digest", "success",
                    f"digest_id={digest_id}"
                )

                return {
                    "db_saved": True,
                    "db_error": None,
                    "digest_id": digest_id,
                }

        except Exception as e:
            conn.rollback()
            logger.operation("db_save", "error", str(e))
            logger.error(f"Database save failed: {e}")
            return {
                "db_saved": False,
                "db_error": str(e),
                "digest_id": None,
            }
        finally:
            conn.close()

    @staticmethod
    def _build_content(
        summary: str,
        trends: list[dict[str, Any]],
        top_stories: list[dict[str, Any]],
        category_analysis: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Build content dict for database storage.

        Args:
            summary: Executive summary.
            trends: List of trends.
            top_stories: List of top stories.
            category_analysis: Category breakdown.
            metadata: Additional metadata.

        Returns:
            Content dict for storage.
        """
        from datetime import datetime

        return {
            "summary": summary,
            "trends": trends,
            "top_stories": top_stories,
            "category_analysis": category_analysis or {},
            "metadata": metadata or {},
            "generated_at": datetime.now().isoformat(),
        }

    @staticmethod
    def _build_response(
        execution_id: str,
        output_file: Any,
        week_start: str,
        week_end: str,
        trends: list[dict[str, Any]],
        top_stories: list[dict[str, Any]],
        db_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the response dict.

        Args:
            execution_id: The execution identifier.
            output_file: Path to output file.
            week_start: Start date.
            week_end: End date.
            trends: List of trends.
            top_stories: List of top stories.
            db_result: Database operation result.

        Returns:
            Complete response dict.
        """
        if db_result["db_saved"]:
            logger.success(
                "submit_weekly_digest completed",
                digest_id=db_result["digest_id"],
            )
            return {
                "status": "success",
                "execution_id": execution_id,
                "digest_id": db_result["digest_id"],
                "output_path": str(output_file),
                "week_range": f"{week_start} to {week_end}",
                "trends_count": len(trends),
                "top_stories_count": len(top_stories),
                "operations": logger.get_operations_summary(),
                "message": "Weekly digest saved successfully.",
            }
        else:
            logger.warn(
                "submit_weekly_digest completed without DB save",
                error=db_result["db_error"],
            )
            return {
                "status": "error",
                "message": (
                    f"Failed to save weekly digest to database: "
                    f"{db_result['db_error']}"
                ),
                "operations": logger.get_operations_summary(),
            }
