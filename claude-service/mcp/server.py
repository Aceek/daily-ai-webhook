#!/usr/bin/env python3
"""
MCP Server for AI News Digest.

Exposes tools for:
- Querying database (categories, articles, stats)
- Submitting daily and weekly digests

The server uses synchronous psycopg2 for DB operations.
"""

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor
from mcp.server.fastmcp import FastMCP


# =============================================================================
# MCP Logger - Writes to execution directory for debugging
# =============================================================================


class MCPLogger:
    """
    Structured logger for MCP operations.

    Writes to mcp.log in the execution directory for persistent debugging.
    Also outputs to stderr for real-time monitoring.
    """

    def __init__(self):
        self.exec_dir = os.getenv("EXECUTION_DIR")
        self.log_file = Path(self.exec_dir) / "mcp.log" if self.exec_dir else None
        self.operations: list[dict] = []  # Track operations for summary

    def _timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _write(self, level: str, message: str, details: dict | None = None):
        """Write log entry to file and stderr."""
        timestamp = self._timestamp()
        log_line = f"[{timestamp}] [{level}] {message}"

        # Always write to stderr (may be captured by parent)
        print(f"[MCP] {log_line}", file=sys.stderr, flush=True)

        # Write to file if execution directory is set
        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(f"{log_line}\n")
                    if details:
                        for key, value in details.items():
                            f.write(f"         {key}: {value}\n")
            except Exception:
                pass  # Don't fail on logging errors

    def info(self, message: str, **details):
        self._write("INFO", message, details if details else None)

    def success(self, message: str, **details):
        self._write("OK", message, details if details else None)

    def error(self, message: str, **details):
        self._write("ERROR", message, details if details else None)

    def warn(self, message: str, **details):
        self._write("WARN", message, details if details else None)

    def operation(self, name: str, status: str, details: str = ""):
        """Record an operation for the summary."""
        self.operations.append({
            "timestamp": self._timestamp(),
            "name": name,
            "status": status,
            "details": details
        })
        symbol = "✓" if status == "success" else "✗" if status == "error" else "○"
        self._write("OP", f"{symbol} {name}", {"details": details} if details else None)

    def get_operations_summary(self) -> list[dict]:
        """Get list of operations for inclusion in response."""
        return self.operations.copy()


# Global logger instance
logger = MCPLogger()

# Initialize MCP server
mcp = FastMCP("submit-digest")

# Log startup
logger.info("MCP Server starting",
            database_url_set=bool(os.getenv("DATABASE_URL")),
            execution_dir=os.getenv("EXECUTION_DIR", "not set"))


def get_db_connection() -> tuple[Any | None, str | None]:
    """Get a synchronous database connection.

    Returns:
        Tuple of (connection, error_message).
        Connection is None if unavailable, with error_message explaining why.
    """
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        error = "DATABASE_URL not set"
        logger.warn(error)
        return None, error

    # Convert asyncpg URL to psycopg2 format
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        conn = psycopg2.connect(sync_url, cursor_factory=RealDictCursor)
        logger.success("Database connected", host=sync_url.split("@")[1].split("/")[0] if "@" in sync_url else "unknown")
        return conn, None
    except Exception as e:
        error = f"Connection failed: {e}"
        logger.error(error)
        return None, error


def get_output_dir() -> Path:
    """Get the output directory for the digest file."""
    exec_dir = os.getenv("EXECUTION_DIR")
    if exec_dir:
        return Path(exec_dir)
    return Path(os.getenv("DIGESTS_DIR", "/app/logs/digests"))


# =============================================================================
# DB Query Tools
# =============================================================================


@mcp.tool()
def get_categories(
    mission_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Get all categories for a mission, optionally filtered by date range.

    Use this tool at the start of analysis to see existing categories.
    This helps you reuse categories instead of creating duplicates.

    Args:
        mission_id: The mission ID (e.g., "ai-news")
        date_from: Optional start date (YYYY-MM-DD) to filter categories with articles
        date_to: Optional end date (YYYY-MM-DD) to filter categories with articles

    Returns:
        Dict with categories list and count
    """
    conn, db_error = get_db_connection()
    if not conn:
        return {"status": "error", "message": f"Database not available: {db_error}"}

    try:
        with conn.cursor() as cur:
            if date_from and date_to:
                # Get categories that have articles in the date range
                cur.execute(
                    """
                    SELECT DISTINCT c.id, c.name, c.created_at
                    FROM categories c
                    JOIN articles a ON a.category_id = c.id
                    WHERE c.mission_id = %s
                      AND a.created_at >= %s
                      AND a.created_at <= %s
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
            rows = cur.fetchall()

            categories = [
                {"id": row["id"], "name": row["name"]}
                for row in rows
            ]

            return {
                "status": "success",
                "mission_id": mission_id,
                "categories": categories,
                "count": len(categories),
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def get_articles(
    mission_id: str,
    categories: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
) -> dict:
    """
    Get articles from the database with optional filters.

    Use this tool to retrieve historical articles for analysis,
    particularly for weekly digest generation.

    Args:
        mission_id: The mission ID (e.g., "ai-news")
        categories: Optional list of category names to filter by
        date_from: Optional start date (YYYY-MM-DD)
        date_to: Optional end date (YYYY-MM-DD)
        limit: Maximum number of articles to return (default 100, max 500)

    Returns:
        Dict with articles list and metadata
    """
    conn, db_error = get_db_connection()
    if not conn:
        return {"status": "error", "message": f"Database not available: {db_error}"}

    limit = min(limit, 500)  # Cap at 500

    try:
        with conn.cursor() as cur:
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
                query += " AND a.created_at <= %s"
                params.append(date_to)

            query += " ORDER BY a.created_at DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            rows = cur.fetchall()

            articles = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "url": row["url"],
                    "source": row["source"],
                    "description": row["description"][:200] if row["description"] else None,
                    "pub_date": row["pub_date"].isoformat() if row["pub_date"] else None,
                    "category": row["category_name"],
                }
                for row in rows
            ]

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
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def get_article_stats(
    mission_id: str,
    date_from: str,
    date_to: str,
) -> dict:
    """
    Get statistics about articles in a date range.

    Use this tool to understand the volume and distribution of news
    before generating a weekly digest.

    Args:
        mission_id: The mission ID (e.g., "ai-news")
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)

    Returns:
        Dict with total count, category breakdown, source breakdown, and daily counts
    """
    conn, db_error = get_db_connection()
    if not conn:
        return {"status": "error", "message": f"Database not available: {db_error}"}

    try:
        with conn.cursor() as cur:
            # Total count
            cur.execute(
                """
                SELECT COUNT(*) as total
                FROM articles
                WHERE mission_id = %s AND created_at >= %s AND created_at <= %s
                """,
                (mission_id, date_from, date_to),
            )
            total = cur.fetchone()["total"]

            # By category
            cur.execute(
                """
                SELECT c.name, COUNT(*) as count
                FROM articles a
                LEFT JOIN categories c ON a.category_id = c.id
                WHERE a.mission_id = %s AND a.created_at >= %s AND a.created_at <= %s
                GROUP BY c.name
                ORDER BY count DESC
                """,
                (mission_id, date_from, date_to),
            )
            by_category = {row["name"] or "uncategorized": row["count"] for row in cur.fetchall()}

            # By source
            cur.execute(
                """
                SELECT source, COUNT(*) as count
                FROM articles
                WHERE mission_id = %s AND created_at >= %s AND created_at <= %s
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
                """,
                (mission_id, date_from, date_to),
            )
            by_source = {row["source"]: row["count"] for row in cur.fetchall()}

            # By day
            cur.execute(
                """
                SELECT DATE(created_at) as day, COUNT(*) as count
                FROM articles
                WHERE mission_id = %s AND created_at >= %s AND created_at <= %s
                GROUP BY DATE(created_at)
                ORDER BY day
                """,
                (mission_id, date_from, date_to),
            )
            by_day = {str(row["day"]): row["count"] for row in cur.fetchall()}

            return {
                "status": "success",
                "mission_id": mission_id,
                "date_range": {"from": date_from, "to": date_to},
                "total_articles": total,
                "by_category": by_category,
                "by_source": by_source,
                "by_day": by_day,
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# =============================================================================
# Submit Tools
# =============================================================================


def _get_or_create_category(cur, mission_id: str, category_name: str) -> int:
    """Get or create a category, returning its ID."""
    cur.execute(
        "SELECT id FROM categories WHERE mission_id = %s AND name = %s",
        (mission_id, category_name),
    )
    row = cur.fetchone()
    if row:
        return row["id"]

    cur.execute(
        "INSERT INTO categories (mission_id, name) VALUES (%s, %s) RETURNING id",
        (mission_id, category_name),
    )
    return cur.fetchone()["id"]


def _validate_news_items(items: list[dict], section_name: str) -> list[str]:
    """Validate news items have required fields."""
    errors = []
    required_fields = ["title", "summary", "url", "source", "category", "confidence"]
    for i, item in enumerate(items or []):
        for field in required_fields:
            if field not in item:
                errors.append(f"{section_name}[{i}]: missing '{field}'")
    return errors


@mcp.tool()
def submit_digest(
    execution_id: str,
    headlines: list[dict],
    research: list[dict],
    industry: list[dict],
    watching: list[dict],
    metadata: dict,
) -> dict:
    """
    Submit the final AI news digest for publication to Discord.

    Call this tool ONCE at the end of your analysis with the complete digest.
    The digest will be validated, saved to file, and optionally stored in DB.

    Args:
        execution_id: The execution ID provided in the prompt parameters
        headlines: List of major news items (required, at least 1)
        research: List of research/paper items (can be empty)
        industry: List of industry/business items (can be empty)
        watching: List of trends to watch (can be empty)
        metadata: Execution metadata with fields:
            - mission_id: str (e.g., "ai-news")
            - articles_analyzed: int
            - web_searches: int
            - fact_checks: int
            - deep_dives: int
            - research_doc: str (path to research document)
            - total_news_included: int
            - total_news_excluded: int

    Returns:
        Dict with status, file path, and validation results
    """
    errors = []

    # Validate headlines (required, at least 1)
    if not headlines or len(headlines) == 0:
        errors.append("headlines: at least 1 item required")

    # Validate each news item has required fields
    errors.extend(_validate_news_items(headlines, "headlines"))
    errors.extend(_validate_news_items(research, "research"))
    errors.extend(_validate_news_items(industry, "industry"))
    errors.extend(_validate_news_items(watching, "watching"))

    # Validate metadata
    required_meta = ["articles_analyzed", "web_searches", "research_doc"]
    for field in required_meta:
        if field not in metadata:
            errors.append(f"metadata: missing '{field}'")

    if errors:
        return {
            "status": "error",
            "errors": errors,
            "message": "Validation failed. Please fix the errors and resubmit.",
        }

    mission_id = metadata.get("mission_id", "ai-news")
    today = date.today()

    # Build the digest structure (digest_id added after DB save)
    digest = {
        "digest": {
            "date": today.isoformat(),
            "headline_count": len(headlines),
            "categories": ["headlines", "research", "industry", "watching"],
        },
        "headlines": headlines,
        "research": research or [],
        "industry": industry or [],
        "watching": watching or [],
        "metadata": {
            "execution_id": execution_id,
            "mission_id": mission_id,
            "articles_analyzed": metadata.get("articles_analyzed", 0),
            "web_searches": metadata.get("web_searches", 0),
            "fact_checks": metadata.get("fact_checks", 0),
            "deep_dives": metadata.get("deep_dives", 0),
            "research_doc": metadata.get("research_doc", ""),
            "total_news_included": metadata.get("total_news_included", 0),
            "total_news_excluded": metadata.get("total_news_excluded", 0),
        },
        "submitted_at": datetime.now().isoformat(),
    }

    total_items = len(headlines) + len(research or []) + len(industry or []) + len(watching or [])

    # Save to database if available
    logger.info(f"submit_digest called", execution_id=execution_id, items=total_items)

    db_saved = False
    db_error = None
    digest_id = None
    articles_saved = 0

    conn, conn_error = get_db_connection()

    if not conn:
        db_error = conn_error
        logger.operation("db_connect", "error", conn_error or "Unknown error")
    else:
        logger.operation("db_connect", "success", "Connected to PostgreSQL")
        try:
            with conn.cursor() as cur:
                # Insert or update daily_digest
                cur.execute(
                    """
                    INSERT INTO daily_digests (mission_id, date, content, generated_at, posted_to_discord)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (mission_id, date)
                    DO UPDATE SET content = EXCLUDED.content, generated_at = EXCLUDED.generated_at
                    RETURNING id
                    """,
                    (mission_id, today, json.dumps(digest), datetime.now(), False),
                )
                digest_id = cur.fetchone()["id"]
                logger.operation("insert_digest", "success", f"digest_id={digest_id}")

                # Create categories and store articles
                all_items = [
                    *[(item, "headlines") for item in headlines],
                    *[(item, "research") for item in (research or [])],
                    *[(item, "industry") for item in (industry or [])],
                    *[(item, "watching") for item in (watching or [])],
                ]

                for item, section in all_items:
                    category_id = _get_or_create_category(cur, mission_id, item["category"])

                    # Insert article (ignore duplicates by URL)
                    cur.execute(
                        """
                        INSERT INTO articles (mission_id, category_id, daily_digest_id,
                                             title, url, source, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
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
                        ),
                    )
                    articles_saved += 1

                conn.commit()
                db_saved = True
                logger.operation("insert_articles", "success", f"{articles_saved} articles")
                logger.operation("commit", "success", "Transaction committed")

        except Exception as e:
            conn.rollback()
            db_error = str(e)
            logger.operation("db_save", "error", str(e))
            logger.error(f"Database save failed: {e}")
        finally:
            conn.close()

    # Add digest_id to the digest structure before writing to file
    if digest_id:
        digest["digest_id"] = digest_id

    # Write to file (after DB save so digest_id is included)
    output_dir = get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    if os.getenv("EXECUTION_DIR"):
        output_file = output_dir / "digest.json"
    else:
        output_file = output_dir / f"{execution_id}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)

    logger.operation("write_file", "success", str(output_file))

    # Build result with detailed error info
    result = {
        "status": "success",
        "execution_id": execution_id,
        "digest_id": digest_id,
        "output_path": str(output_file),
        "total_items": total_items,
        "db_saved": db_saved,
        "articles_saved": articles_saved,
        "db_error": db_error,  # Include error details for debugging
        "operations": logger.get_operations_summary(),  # Include operation log
        "message": f"Digest saved successfully with {total_items} news items.",
    }

    if db_saved:
        logger.success(f"submit_digest completed", digest_id=digest_id, articles=articles_saved)
    else:
        logger.warn(f"submit_digest completed without DB save", error=db_error)

    return result


@mcp.tool()
def submit_weekly_digest(
    execution_id: str,
    mission_id: str,
    week_start: str,
    week_end: str,
    summary: str,
    trends: list[dict],
    top_stories: list[dict],
    category_analysis: dict,
    metadata: dict,
    is_standard: bool = True,
) -> dict:
    """
    Submit a weekly digest with trend analysis.

    Call this tool after analyzing a week's worth of articles from the database.

    Args:
        execution_id: The execution ID
        mission_id: The mission ID (e.g., "ai-news")
        week_start: Start date of the week (YYYY-MM-DD)
        week_end: End date of the week (YYYY-MM-DD)
        summary: Executive summary of the week (2-3 paragraphs)
        trends: List of identified trends with fields:
            - name: Trend name
            - description: What's happening
            - evidence: List of supporting article titles/urls
            - direction: "rising", "stable", or "declining"
        top_stories: List of the week's most important stories with fields:
            - title: Story title
            - summary: Brief summary
            - url: Primary source URL
            - impact: Why this matters
        category_analysis: Dict mapping category names to analysis:
            - count: Number of articles
            - highlights: Key developments
        metadata: Additional metadata:
            - articles_analyzed: int
            - theme: Optional theme filter used

    Returns:
        Dict with status and storage confirmation
    """
    errors = []

    if not summary:
        errors.append("summary: required")
    if not trends:
        errors.append("trends: at least 1 trend required")
    if not top_stories:
        errors.append("top_stories: at least 1 story required")

    # Validate trends
    for i, trend in enumerate(trends or []):
        for field in ["name", "description", "direction"]:
            if field not in trend:
                errors.append(f"trends[{i}]: missing '{field}'")

    # Validate top_stories
    for i, story in enumerate(top_stories or []):
        for field in ["title", "summary", "url"]:
            if field not in story:
                errors.append(f"top_stories[{i}]: missing '{field}'")

    if errors:
        return {
            "status": "error",
            "errors": errors,
            "message": "Validation failed. Please fix the errors and resubmit.",
        }

    content = {
        "summary": summary,
        "trends": trends,
        "top_stories": top_stories,
        "category_analysis": category_analysis or {},
        "metadata": metadata or {},
        "generated_at": datetime.now().isoformat(),
    }

    params = metadata.get("theme") if metadata else None

    # Save to database
    conn = get_db_connection()
    if not conn:
        return {"status": "error", "message": "Database not available for weekly digest"}

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO weekly_digests (mission_id, week_start, week_end, params, content, is_standard, posted_to_discord)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (mission_id, week_start, week_end, json.dumps({"theme": params}) if params else None, json.dumps(content), is_standard, False),
            )
            digest_id = cur.fetchone()["id"]
            conn.commit()

            return {
                "status": "success",
                "execution_id": execution_id,
                "digest_id": digest_id,
                "week_range": f"{week_start} to {week_end}",
                "trends_count": len(trends),
                "top_stories_count": len(top_stories),
                "message": "Weekly digest saved successfully.",
            }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


if __name__ == "__main__":
    # Run the MCP server (stdio transport)
    mcp.run()
