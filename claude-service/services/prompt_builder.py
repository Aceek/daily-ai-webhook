#!/usr/bin/env python3
"""
Prompt builder for Claude Service.

Functions to build prompts for Claude CLI.
"""

from datetime import datetime


def build_prompt(
    mission: str,
    articles_path: str,
    execution_id: str,
    research_path: str,
    workflow_execution_id: str | None = None,
) -> str:
    """Build minimal prompt for multi-mission architecture.

    Claude will read mission files itself based on CLAUDE.md instructions.

    Args:
        mission: Name of the mission to execute.
        articles_path: Path to the articles JSON file.
        execution_id: Unique execution ID for this run.
        research_path: Path where Claude should write the research document.
        workflow_execution_id: Optional n8n workflow execution ID.

    Returns:
        Minimal prompt string for Claude CLI.
    """
    return f"""=== EXECUTION PARAMETERS ===

mission: {mission}
articles_path: {articles_path}
execution_id: {execution_id}
research_path: {research_path}
workflow_id: {workflow_execution_id or "standalone"}
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

=== INSTRUCTIONS ===

Suis le protocole de demarrage de ton CLAUDE.md.
Lis les fichiers de mission dans l'ordre indique avant de commencer ton analyse.

Remplace {{mission}} par: {mission}
"""


def build_weekly_prompt(
    mission: str,
    week_start: str,
    week_end: str,
    execution_id: str,
    research_path: str,
    theme: str | None = None,
    workflow_execution_id: str | None = None,
) -> str:
    """Build prompt for weekly analysis.

    Claude will use MCP DB tools to fetch articles and analyze trends.

    Args:
        mission: Name of the mission to execute.
        week_start: Start of week (YYYY-MM-DD).
        week_end: End of week (YYYY-MM-DD).
        execution_id: Unique execution ID for this run.
        research_path: Path where Claude should write the research document.
        theme: Optional theme to focus the analysis on.
        workflow_execution_id: Optional n8n workflow execution ID.

    Returns:
        Prompt string for Claude CLI.
    """
    theme_instruction = _build_theme_instruction(theme)
    instructions = _build_weekly_instructions(mission, week_start, week_end, research_path)

    return f"""=== WEEKLY ANALYSIS PARAMETERS ===

mission: {mission}
week_start: {week_start}
week_end: {week_end}
execution_id: {execution_id}
research_path: {research_path}
workflow_id: {workflow_execution_id or "standalone"}
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
{theme_instruction}
{instructions}
"""


def _build_theme_instruction(theme: str | None) -> str:
    """Build theme instruction section."""
    if not theme:
        return ""
    return f"""
theme: {theme}

IMPORTANT: This is a THEMATIC analysis. Focus exclusively on articles related to "{theme}".
Filter articles by relevance to this theme. Set is_standard: false in your submission.
"""


def _build_weekly_instructions(
    mission: str,
    week_start: str,
    week_end: str,
    research_path: str,
) -> str:
    """Build weekly analysis instructions."""
    return f"""=== INSTRUCTIONS ===

This is a WEEKLY DIGEST analysis. You must:

1. Read the weekly mission files:
   - /app/missions/{mission}/weekly/mission.md
   - /app/missions/{mission}/weekly/analysis-rules.md
   - /app/missions/{mission}/weekly/output-schema.md
   - /app/missions/_common/mcp-usage.md

2. Use MCP database tools to fetch data:
   - get_article_stats(mission_id="{mission}", date_from="{week_start}", date_to="{week_end}")
   - get_categories(mission_id="{mission}", date_from="{week_start}", date_to="{week_end}")
   - get_articles(mission_id="{mission}", date_from="{week_start}", date_to="{week_end}", limit=200)

3. Analyze trends and patterns from the week's articles

4. Write your research document to: {research_path}

5. Submit via submit_weekly_digest with all required fields

DO NOT use submit_digest - use submit_weekly_digest for weekly analysis."""
