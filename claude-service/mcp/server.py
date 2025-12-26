#!/usr/bin/env python3
"""MCP Server for AI News Digest.

Entry point that exposes MCP tools for:
- Querying database (categories, articles, stats)
- Submitting daily and weekly digests

The server delegates all logic to service layer modules.
"""

import os

from mcp.server.fastmcp import FastMCP

from .logger import logger
from .services.article_query import ArticleQueryService
from .services.digest_submitter import DigestSubmitter
from .services.weekly_digest import WeeklyDigestSubmitter


# Initialize MCP server
mcp = FastMCP("submit-digest")

# Log startup
logger.info(
    "MCP Server starting",
    database_url_set=bool(os.getenv("DATABASE_URL")),
    execution_dir=os.getenv("EXECUTION_DIR", "not set"),
)


# =============================================================================
# Query Tools
# =============================================================================


@mcp.tool()
def get_categories(
    mission_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """Get all categories for a mission, optionally filtered by date range.

    Use this tool at the start of analysis to see existing categories.
    This helps you reuse categories instead of creating duplicates.

    Args:
        mission_id: The mission ID (e.g., "ai-news")
        date_from: Optional start date (YYYY-MM-DD) to filter categories with articles
        date_to: Optional end date (YYYY-MM-DD) to filter categories with articles

    Returns:
        Dict with categories list and count
    """
    return ArticleQueryService.get_categories(mission_id, date_from, date_to)


@mcp.tool()
def get_articles(
    mission_id: str,
    categories: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
) -> dict:
    """Get articles from the database with optional filters.

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
    return ArticleQueryService.get_articles(
        mission_id, categories, date_from, date_to, limit
    )


@mcp.tool()
def get_article_stats(
    mission_id: str,
    date_from: str,
    date_to: str,
) -> dict:
    """Get statistics about articles in a date range.

    Use this tool to understand the volume and distribution of news
    before generating a weekly digest.

    Args:
        mission_id: The mission ID (e.g., "ai-news")
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)

    Returns:
        Dict with total count, category breakdown, source breakdown, and daily counts
    """
    return ArticleQueryService.get_article_stats(mission_id, date_from, date_to)


@mcp.tool()
def get_recent_headlines(
    mission_id: str,
    days: int = 3,
) -> dict:
    """Get recent headlines to avoid duplicate coverage.

    Call this tool BEFORE analyzing articles to check what topics
    have already been covered in recent days. Avoid selecting articles
    that cover the same topic unless there's a significant update.

    Args:
        mission_id: The mission ID (e.g., "ai-news")
        days: Number of days to look back (default 3, max 7)

    Returns:
        Dict with list of recent headlines (title, url, date, category)
    """
    return ArticleQueryService.get_recent_headlines(mission_id, days)


# =============================================================================
# Submit Tools
# =============================================================================


@mcp.tool()
def submit_digest(
    execution_id: str,
    headlines: list[dict],
    research: list[dict],
    industry: list[dict],
    watching: list[dict],
    excluded: list[dict],
    metadata: dict,
) -> dict:
    """Submit the final AI news digest for publication to Discord.

    Call this tool ONCE at the end of your analysis with the complete digest.
    The digest will be validated, saved to file, and stored in DB.
    Both selected AND excluded articles are archived for complete data retention.

    Args:
        execution_id: The execution ID provided in the prompt parameters
        headlines: List of major news items (required, at least 1)
        research: List of research/paper items (can be empty)
        industry: List of industry/business items (can be empty)
        watching: List of trends to watch (can be empty)
        excluded: List of excluded articles with minimal info:
            - url: str (article URL)
            - title: str (article title)
            - category: str (assigned category)
            - reason: str (off_topic|duplicate|low_priority|outdated)
            - score: int (relevance score 1-10)
            - source: str (optional, article source)
        metadata: Execution metadata with fields:
            - mission_id: str (e.g., "ai-news")
            - articles_analyzed: int
            - web_searches: int
            - fact_checks: int
            - deep_dives: int
            - research_doc: str (path to research document)

    Returns:
        Dict with status, file path, and validation results
    """
    return DigestSubmitter.submit(
        execution_id, headlines, research, industry, watching, excluded, metadata
    )


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
    """Submit a weekly digest with trend analysis.

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
    return WeeklyDigestSubmitter.submit(
        execution_id, mission_id, week_start, week_end, summary,
        trends, top_stories, category_analysis, metadata, is_standard
    )


if __name__ == "__main__":
    # Run the MCP server (stdio transport)
    mcp.run()
