"""Utility functions for MCP server.

Pure helper functions without side effects.
"""

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any


def get_output_dir() -> Path:
    """Get the output directory for digest files.

    Returns:
        Path to output directory.
    """
    exec_dir = os.getenv("EXECUTION_DIR")
    if exec_dir:
        return Path(exec_dir)
    return Path(os.getenv("DIGESTS_DIR", "/app/logs/digests"))


def get_output_file_path(execution_id: str) -> Path:
    """Get the output file path for a digest.

    Args:
        execution_id: The execution identifier.

    Returns:
        Path to the output file.
    """
    output_dir = get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    if os.getenv("EXECUTION_DIR"):
        return output_dir / "digest.json"
    return output_dir / f"{execution_id}.json"


def write_digest_to_file(digest: dict[str, Any], execution_id: str) -> Path:
    """Write digest to JSON file.

    Args:
        digest: Digest data to write.
        execution_id: The execution identifier.

    Returns:
        Path to the written file.
    """
    output_file = get_output_file_path(execution_id)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)
    return output_file


def compute_exclusion_breakdown(excluded: list[dict[str, Any]]) -> dict[str, int]:
    """Compute breakdown of exclusion reasons.

    Args:
        excluded: List of excluded items.

    Returns:
        Dict mapping reason to count.
    """
    breakdown = {
        "off_topic": 0,
        "duplicate": 0,
        "low_priority": 0,
        "outdated": 0,
    }
    for item in excluded or []:
        reason = item.get("reason")
        if reason in breakdown:
            breakdown[reason] += 1
    return breakdown


def build_daily_digest_structure(
    execution_id: str,
    headlines: list[dict[str, Any]],
    research: list[dict[str, Any]],
    industry: list[dict[str, Any]],
    watching: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
    metadata: dict[str, Any],
    digest_id: int | None = None,
) -> dict[str, Any]:
    """Build the complete daily digest structure.

    Args:
        execution_id: The execution identifier.
        headlines: List of headline items.
        research: List of research items.
        industry: List of industry items.
        watching: List of watching items.
        excluded: List of excluded items.
        metadata: Submission metadata.
        digest_id: Database ID if saved.

    Returns:
        Complete digest structure as dict.
    """
    today = date.today()
    selected_count = (
        len(headlines) +
        len(research or []) +
        len(industry or []) +
        len(watching or [])
    )
    excluded_count = len(excluded or [])
    exclusion_breakdown = compute_exclusion_breakdown(excluded)

    digest: dict[str, Any] = {
        "digest": {
            "date": today.isoformat(),
            "headline_count": len(headlines),
            "categories": ["headlines", "research", "industry", "watching"],
        },
        "headlines": headlines,
        "research": research or [],
        "industry": industry or [],
        "watching": watching or [],
        "excluded": excluded or [],
        "metadata": {
            "execution_id": execution_id,
            "mission_id": metadata.get("mission_id", "ai-news"),
            "articles_analyzed": metadata.get("articles_analyzed", 0),
            "web_searches": metadata.get("web_searches", 0),
            "fact_checks": metadata.get("fact_checks", 0),
            "deep_dives": metadata.get("deep_dives", 0),
            "research_doc": metadata.get("research_doc", ""),
            "selected_count": selected_count,
            "excluded_count": excluded_count,
            "exclusion_breakdown": exclusion_breakdown,
        },
        "submitted_at": datetime.now().isoformat(),
    }

    if digest_id:
        digest["digest_id"] = digest_id

    return digest


def build_weekly_digest_structure(
    execution_id: str,
    mission_id: str,
    week_start: str,
    week_end: str,
    summary: str,
    trends: list[dict[str, Any]],
    top_stories: list[dict[str, Any]],
    category_analysis: dict[str, Any],
    metadata: dict[str, Any],
    digest_id: int | None = None,
) -> dict[str, Any]:
    """Build the complete weekly digest structure.

    Args:
        execution_id: The execution identifier.
        mission_id: The mission ID.
        week_start: Start date (YYYY-MM-DD).
        week_end: End date (YYYY-MM-DD).
        summary: Executive summary.
        trends: List of trend dicts.
        top_stories: List of top story dicts.
        category_analysis: Category breakdown.
        metadata: Additional metadata.
        digest_id: Database ID if saved.

    Returns:
        Complete weekly digest structure as dict.
    """
    return {
        "digest_id": digest_id,
        "summary": summary,
        "trends": trends,
        "top_stories": top_stories,
        "category_analysis": category_analysis or {},
        "metadata": {
            **(metadata or {}),
            "execution_id": execution_id,
            "mission_id": mission_id,
            "week_start": week_start,
            "week_end": week_end,
        },
        "generated_at": datetime.now().isoformat(),
    }


def collect_selected_items(
    headlines: list[dict[str, Any]],
    research: list[dict[str, Any]],
    industry: list[dict[str, Any]],
    watching: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], str]]:
    """Collect all selected items with their section names.

    Args:
        headlines: List of headline items.
        research: List of research items.
        industry: List of industry items.
        watching: List of watching items.

    Returns:
        List of (item, section_name) tuples.
    """
    return [
        *[(item, "headlines") for item in headlines],
        *[(item, "research") for item in (research or [])],
        *[(item, "industry") for item in (industry or [])],
        *[(item, "watching") for item in (watching or [])],
    ]
