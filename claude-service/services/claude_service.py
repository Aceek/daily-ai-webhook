#!/usr/bin/env python3
"""
Claude CLI service for Claude Service.

Handles calling Claude Code CLI and parsing its output.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from api.models import Article, ClaudeResult
from config import Settings
from loggers.models import StreamEvent

if TYPE_CHECKING:
    from utils.execution_dir import ExecutionDirectory


logger = logging.getLogger("claude-service")


def write_articles_file(articles: list[Article], path: Path) -> None:
    """Write articles to JSON file for Claude to read.

    Args:
        articles: List of articles to write.
        path: Path to write the JSON file.
    """
    data = [
        {
            "title": a.title,
            "url": a.url,
            "description": a.description[:500] if a.description else "",
            "pub_date": a.pub_date,
            "source": a.source,
        }
        for a in articles
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %d articles to %s", len(articles), path)


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
    theme_instruction = ""
    if theme:
        theme_instruction = f"""
theme: {theme}

IMPORTANT: This is a THEMATIC analysis. Focus exclusively on articles related to "{theme}".
Filter articles by relevance to this theme. Set is_standard: false in your submission.
"""

    return f"""=== WEEKLY ANALYSIS PARAMETERS ===

mission: {mission}
week_start: {week_start}
week_end: {week_end}
execution_id: {execution_id}
research_path: {research_path}
workflow_id: {workflow_execution_id or "standalone"}
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
{theme_instruction}
=== INSTRUCTIONS ===

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

DO NOT use submit_digest - use submit_weekly_digest for weekly analysis.
"""


async def call_claude_cli(
    prompt: str,
    exec_dir: "ExecutionDirectory",
    settings: Settings,
) -> ClaudeResult:
    """Call Claude Code CLI with agentic capabilities.

    Executes claude CLI as a subprocess with retry logic
    and timeout handling. Enables WebSearch, WebFetch, Write,
    and Task tools for intelligent news research.

    Args:
        prompt: The prompt to send to Claude CLI.
        exec_dir: The execution directory for this run.
        settings: Application settings.

    Returns:
        ClaudeResult with response, timeline, and metrics.
    """
    cmd = [
        "claude",
        "-p", prompt,
        "--model", settings.claude_model,
        "--allowedTools", settings.allowed_tools,
        "--output-format", "stream-json",
        "--verbose",
    ]

    for attempt in range(settings.retry_count + 1):
        try:
            logger.info("Calling Claude CLI (attempt %d)", attempt + 1)
            start_time = time.time()

            env = os.environ.copy()
            env["EXECUTION_DIR"] = str(exec_dir.path)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=settings.claude_timeout,
            )

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                stdout_msg = stdout.decode().strip()[-2000:]
                logger.error(
                    "Claude CLI error (code %d): stderr=%s, stdout=%s",
                    process.returncode, error_msg, stdout_msg,
                )
                if attempt < settings.retry_count:
                    await asyncio.sleep(2)
                    continue
                return ClaudeResult(
                    success=False,
                    error=f"Claude CLI failed (code {process.returncode}): {error_msg or stdout_msg}",
                )

            return parse_stream_output(stdout.decode(), start_time)

        except asyncio.TimeoutError:
            logger.error("Claude CLI timeout after %ds", settings.claude_timeout)
            if attempt < settings.retry_count:
                continue
            return ClaudeResult(
                success=False,
                error=f"Claude CLI timeout after {settings.claude_timeout}s",
            )

    return ClaudeResult(success=False, error="All retry attempts failed")


def parse_stream_output(output: str, start_time: float) -> ClaudeResult:
    """Parse stream-json output from Claude CLI.

    Args:
        output: Raw stdout from Claude CLI with stream-json format.
        start_time: Start time for calculating relative timestamps.

    Returns:
        ClaudeResult with parsed data.
    """
    timeline: list[StreamEvent] = []
    response_text = ""
    input_tokens = 0
    output_tokens = 0
    cost_usd = 0.0

    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        event = _parse_stream_event(line, start_time)
        if event:
            timeline.append(event)

            if event.event_type == "result":
                result_data = event.raw_data
                response_text = result_data.get("result", "")
                cost_usd = result_data.get("total_cost_usd", 0.0)
                usage = result_data.get("usage", {})
                if usage:
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    cache_creation = usage.get("cache_creation_input_tokens", 0)
                    cache_read = usage.get("cache_read_input_tokens", 0)
                    input_tokens += cache_creation + cache_read

            elif event.event_type == "assistant" and not response_text:
                message = event.raw_data.get("message", {})
                contents = message.get("content", [])
                for c in contents:
                    if isinstance(c, dict) and c.get("type") == "text":
                        response_text = c.get("text", "")

    logger.info(
        "Parsed %d events, %d input tokens, %d output tokens, $%.4f",
        len(timeline), input_tokens, output_tokens, cost_usd,
    )

    return ClaudeResult(
        response=response_text,
        timeline=timeline,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        success=True,
    )


def _parse_stream_event(line: str, start_time: float) -> StreamEvent | None:
    """Parse a single line of stream-json output into a StreamEvent.

    Args:
        line: Single line of JSON from stream output.
        start_time: Start time for relative timestamps.

    Returns:
        Parsed StreamEvent or None if parsing fails.
    """
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    event_type = data.get("type", "unknown")
    timestamp = time.time() - start_time
    content = ""

    if event_type == "init":
        session_id = data.get("session_id", "")[:12]
        content = f"Session started: {session_id}"

    elif event_type == "assistant":
        message = data.get("message", {})
        contents = message.get("content", [])
        text_parts = []
        for c in contents:
            if isinstance(c, dict) and c.get("type") == "text":
                text = c.get("text", "")
                text_parts.append(text[:200])
            elif isinstance(c, dict) and c.get("type") == "tool_use":
                tool_name = c.get("name", "unknown")
                text_parts.append(f"[Using tool: {tool_name}]")
        content = " ".join(text_parts)

    elif event_type == "tool_use":
        tool_name = data.get("name", "unknown")
        content = f"Calling {tool_name}"
        return StreamEvent(
            timestamp=timestamp,
            event_type=event_type,
            content=content,
            raw_data={"name": tool_name, "input": data.get("input", {})},
        )

    elif event_type == "tool_result":
        output = data.get("output", "")
        content = output[:200] if output else "(empty result)"

    elif event_type == "result":
        cost = data.get("total_cost_usd", 0)
        duration = data.get("duration_ms", 0) / 1000
        content = f"Completed (cost: ${cost:.4f}, duration: {duration:.1f}s)"
        return StreamEvent(
            timestamp=timestamp,
            event_type=event_type,
            content=content,
            raw_data=data,
        )

    elif event_type == "error":
        error_msg = data.get("error", {}).get("message", "Unknown error")
        content = f"Error: {error_msg}"

    elif event_type == "system":
        content = data.get("message", "System message")

    return StreamEvent(
        timestamp=timestamp,
        event_type=event_type,
        content=content,
        raw_data=data,
    )
