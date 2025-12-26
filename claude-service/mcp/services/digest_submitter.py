"""Daily digest submission service.

Handles validation, database save, and file output for daily digests.
"""

from datetime import date
from typing import Any

from ..logger import logger
from ..repositories.base import get_db_connection
from ..repositories.digest import DigestRepository
from ..utils import (
    build_daily_digest_structure,
    collect_selected_items,
    compute_exclusion_breakdown,
    write_digest_to_file,
)
from ..validators import validate_daily_digest


class DigestSubmitter:
    """Service for submitting daily digests."""

    @staticmethod
    def submit(
        execution_id: str,
        headlines: list[dict[str, Any]],
        research: list[dict[str, Any]],
        industry: list[dict[str, Any]],
        watching: list[dict[str, Any]],
        excluded: list[dict[str, Any]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit a daily digest for publication.

        Args:
            execution_id: The execution identifier.
            headlines: List of headline items (at least 1 required).
            research: List of research items.
            industry: List of industry items.
            watching: List of watching items.
            excluded: List of excluded items.
            metadata: Submission metadata.

        Returns:
            Dict with status, file path, and validation results.
        """
        # Validate input
        errors = validate_daily_digest(
            headlines, research, industry, watching, excluded, metadata
        )

        if errors:
            return {
                "status": "error",
                "errors": errors,
                "message": "Validation failed. Please fix the errors and resubmit.",
            }

        mission_id = metadata.get("mission_id", "ai-news")
        selected_count = DigestSubmitter._count_selected(
            headlines, research, industry, watching
        )
        excluded_count = len(excluded or [])

        logger.info(
            f"submit_digest called",
            execution_id=execution_id,
            items=selected_count,
        )

        # Save to database
        db_result = DigestSubmitter._save_to_database(
            execution_id, mission_id, headlines, research,
            industry, watching, excluded, metadata
        )

        # Build digest structure (includes digest_id if saved)
        digest = build_daily_digest_structure(
            execution_id, headlines, research, industry,
            watching, excluded, metadata, db_result["digest_id"]
        )

        # Write to file
        output_file = write_digest_to_file(digest, execution_id)
        logger.operation("write_file", "success", str(output_file))

        # Build response
        return DigestSubmitter._build_response(
            execution_id, output_file, selected_count,
            excluded_count, db_result
        )

    @staticmethod
    def _count_selected(
        headlines: list[dict[str, Any]],
        research: list[dict[str, Any]],
        industry: list[dict[str, Any]],
        watching: list[dict[str, Any]],
    ) -> int:
        """Count total selected items.

        Args:
            headlines: List of headline items.
            research: List of research items.
            industry: List of industry items.
            watching: List of watching items.

        Returns:
            Total count of selected items.
        """
        return (
            len(headlines) +
            len(research or []) +
            len(industry or []) +
            len(watching or [])
        )

    @staticmethod
    def _save_to_database(
        execution_id: str,
        mission_id: str,
        headlines: list[dict[str, Any]],
        research: list[dict[str, Any]],
        industry: list[dict[str, Any]],
        watching: list[dict[str, Any]],
        excluded: list[dict[str, Any]],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Save digest and articles to database.

        Args:
            execution_id: The execution identifier.
            mission_id: The mission ID.
            headlines: List of headline items.
            research: List of research items.
            industry: List of industry items.
            watching: List of watching items.
            excluded: List of excluded items.
            metadata: Submission metadata.

        Returns:
            Dict with db_saved, db_error, digest_id, articles_saved.
        """
        conn, conn_error = get_db_connection()

        if not conn:
            logger.operation("db_connect", "error", conn_error or "Unknown error")
            return {
                "db_saved": False,
                "db_error": conn_error,
                "digest_id": None,
                "articles_saved": 0,
            }

        logger.operation("db_connect", "success", "Connected to PostgreSQL")

        try:
            with conn.cursor() as cur:
                # Build digest structure for DB storage
                digest_content = build_daily_digest_structure(
                    execution_id, headlines, research, industry,
                    watching, excluded, metadata, None
                )

                # Insert digest
                digest_id = DigestRepository.insert_daily_digest(
                    cur, mission_id, date.today(), digest_content
                )
                logger.operation("insert_digest", "success", f"digest_id={digest_id}")

                # Insert articles
                selected_items = collect_selected_items(
                    headlines, research, industry, watching
                )
                selected_saved, excluded_saved = DigestRepository.batch_insert_articles(
                    cur, mission_id, digest_id, selected_items, excluded or []
                )

                logger.operation(
                    "insert_selected", "success",
                    f"{selected_saved} selected articles"
                )
                logger.operation(
                    "insert_excluded", "success",
                    f"{excluded_saved} excluded articles"
                )

                conn.commit()
                logger.operation("commit", "success", "Transaction committed")

                return {
                    "db_saved": True,
                    "db_error": None,
                    "digest_id": digest_id,
                    "articles_saved": selected_saved + excluded_saved,
                }

        except Exception as e:
            conn.rollback()
            logger.operation("db_save", "error", str(e))
            logger.error(f"Database save failed: {e}")
            return {
                "db_saved": False,
                "db_error": str(e),
                "digest_id": None,
                "articles_saved": 0,
            }
        finally:
            conn.close()

    @staticmethod
    def _build_response(
        execution_id: str,
        output_file: Any,
        selected_count: int,
        excluded_count: int,
        db_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the response dict.

        Args:
            execution_id: The execution identifier.
            output_file: Path to output file.
            selected_count: Number of selected items.
            excluded_count: Number of excluded items.
            db_result: Database operation result.

        Returns:
            Complete response dict.
        """
        result = {
            "status": "success",
            "execution_id": execution_id,
            "digest_id": db_result["digest_id"],
            "output_path": str(output_file),
            "selected_count": selected_count,
            "excluded_count": excluded_count,
            "total_archived": db_result["articles_saved"],
            "db_saved": db_result["db_saved"],
            "db_error": db_result["db_error"],
            "operations": logger.get_operations_summary(),
            "message": (
                f"Digest saved: {selected_count} selected, "
                f"{excluded_count} excluded, "
                f"{db_result['articles_saved']} archived to DB."
            ),
        }

        if db_result["db_saved"]:
            logger.success(
                "submit_digest completed",
                digest_id=db_result["digest_id"],
                selected=selected_count,
                excluded=excluded_count,
            )
        else:
            logger.warn(
                "submit_digest completed without DB save",
                error=db_result["db_error"],
            )

        return result
