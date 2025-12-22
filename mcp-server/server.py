#!/usr/bin/env python3
"""
MCP Server for AI News Digest submission.

This server exposes the `submit_digest` tool that Claude uses to submit
structured news digests instead of returning free-form text.

The digest is validated against the schema and written to a JSON file
that FastAPI reads to return to n8n.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("submit-digest")

# Output directory for digests (mounted volume in Docker)
DIGESTS_DIR = Path(os.getenv("DIGESTS_DIR", "/app/logs/digests"))


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
    The digest will be validated and saved for the workflow to process.

    Args:
        execution_id: The execution ID provided in the prompt parameters
        headlines: List of major news items (required, at least 1)
        research: List of research/paper items (can be empty)
        industry: List of industry/business items (can be empty)
        watching: List of trends to watch (can be empty)
        metadata: Execution metadata with fields:
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
    required_fields = ["title", "summary", "url", "source", "category", "confidence"]
    for category_name, items in [
        ("headlines", headlines),
        ("research", research),
        ("industry", industry),
        ("watching", watching),
    ]:
        for i, item in enumerate(items or []):
            for field in required_fields:
                if field not in item:
                    errors.append(f"{category_name}[{i}]: missing '{field}'")

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

    # Build the digest structure
    digest = {
        "digest": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "headline_count": len(headlines),
            "categories": ["headlines", "research", "industry", "watching"],
        },
        "headlines": headlines,
        "research": research or [],
        "industry": industry or [],
        "watching": watching or [],
        "metadata": {
            "execution_id": execution_id,
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

    # Ensure output directory exists
    DIGESTS_DIR.mkdir(parents=True, exist_ok=True)

    # Write to file
    output_file = DIGESTS_DIR / f"{execution_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)

    total_items = len(headlines) + len(research or []) + len(industry or []) + len(watching or [])

    return {
        "status": "success",
        "execution_id": execution_id,
        "output_path": str(output_file),
        "total_items": total_items,
        "message": f"Digest saved successfully with {total_items} news items.",
    }


if __name__ == "__main__":
    # Run the MCP server (stdio transport)
    mcp.run()
