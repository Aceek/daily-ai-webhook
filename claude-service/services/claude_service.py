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


async def call_claude_cli(
    prompt: str,
    exec_dir: "ExecutionDirectory",
    settings: Settings,
) -> ClaudeResult:
    """Call Claude Code CLI with agentic capabilities.

    Args:
        prompt: The prompt to send to Claude CLI.
        exec_dir: The execution directory for this run.
        settings: Application settings.

    Returns:
        ClaudeResult with response, timeline, and metrics.
    """
    cmd = _build_cli_command(settings)

    for attempt in range(settings.retry_count + 1):
        result = await _execute_cli(cmd, prompt, exec_dir, settings, attempt)
        if result is not None:
            return result

    return ClaudeResult(success=False, error="All retry attempts failed")


def _build_cli_command(settings: Settings) -> list[str]:
    """Build Claude CLI command arguments."""
    return [
        "claude",
        "--model", settings.claude_model,
        "--allowedTools", settings.allowed_tools,
        "--output-format", "stream-json",
        "--verbose",
    ]


async def _execute_cli(
    cmd: list[str],
    prompt: str,
    exec_dir: "ExecutionDirectory",
    settings: Settings,
    attempt: int,
) -> ClaudeResult | None:
    """Execute CLI command with error handling.

    Returns:
        ClaudeResult if complete, None if should retry.
    """
    try:
        logger.info("Calling Claude CLI (attempt %d)", attempt + 1)
        start_time = time.time()

        env = os.environ.copy()
        env["EXECUTION_DIR"] = str(exec_dir.path)

        full_cmd = cmd + ["-p", prompt]
        process = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=settings.claude_timeout,
        )

        if process.returncode != 0:
            return _handle_cli_error(
                process.returncode, stdout, stderr, settings, attempt
            )

        return parse_stream_output(stdout.decode(), start_time)

    except asyncio.TimeoutError:
        logger.error("Claude CLI timeout after %ds", settings.claude_timeout)
        if attempt < settings.retry_count:
            return None
        return ClaudeResult(
            success=False,
            error=f"Claude CLI timeout after {settings.claude_timeout}s",
        )


def _handle_cli_error(
    returncode: int,
    stdout: bytes,
    stderr: bytes,
    settings: Settings,
    attempt: int,
) -> ClaudeResult | None:
    """Handle CLI execution error.

    Returns:
        ClaudeResult if final, None if should retry.
    """
    error_msg = stderr.decode().strip()
    stdout_msg = stdout.decode().strip()[-2000:]
    logger.error(
        "Claude CLI error (code %d): stderr=%s, stdout=%s",
        returncode, error_msg, stdout_msg,
    )

    if attempt < settings.retry_count:
        return None

    return ClaudeResult(
        success=False,
        error=f"Claude CLI failed (code {returncode}): {error_msg or stdout_msg}",
    )


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
            response_text, input_tokens, output_tokens, cost_usd = _extract_event_data(
                event, response_text, input_tokens, output_tokens, cost_usd
            )

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


def _extract_event_data(
    event: StreamEvent,
    response_text: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
) -> tuple[str, int, int, float]:
    """Extract relevant data from stream event."""
    if event.event_type == "result":
        data = event.raw_data
        response_text = data.get("result", "")
        cost_usd = data.get("total_cost_usd", 0.0)
        usage = data.get("usage", {})
        if usage:
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            input_tokens += usage.get("cache_creation_input_tokens", 0)
            input_tokens += usage.get("cache_read_input_tokens", 0)

    elif event.event_type == "assistant" and not response_text:
        message = event.raw_data.get("message", {})
        for c in message.get("content", []):
            if isinstance(c, dict) and c.get("type") == "text":
                response_text = c.get("text", "")

    return response_text, input_tokens, output_tokens, cost_usd


def _parse_stream_event(line: str, start_time: float) -> StreamEvent | None:
    """Parse a single line of stream-json output."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    event_type = data.get("type", "unknown")
    timestamp = time.time() - start_time
    content = _get_event_content(event_type, data)

    if event_type in ("tool_use", "result"):
        return StreamEvent(
            timestamp=timestamp,
            event_type=event_type,
            content=content,
            raw_data=_get_raw_data(event_type, data),
        )

    return StreamEvent(
        timestamp=timestamp,
        event_type=event_type,
        content=content,
        raw_data=data,
    )


def _get_event_content(event_type: str, data: dict) -> str:
    """Get human-readable content for event."""
    if event_type == "init":
        return f"Session started: {data.get('session_id', '')[:12]}"

    if event_type == "assistant":
        return _get_assistant_content(data)

    if event_type == "tool_use":
        return f"Calling {data.get('name', 'unknown')}"

    if event_type == "tool_result":
        output = data.get("output", "")
        return output[:200] if output else "(empty result)"

    if event_type == "result":
        cost = data.get("total_cost_usd", 0)
        duration = data.get("duration_ms", 0) / 1000
        return f"Completed (cost: ${cost:.4f}, duration: {duration:.1f}s)"

    if event_type == "error":
        return f"Error: {data.get('error', {}).get('message', 'Unknown error')}"

    if event_type == "system":
        return data.get("message", "System message")

    return ""


def _get_assistant_content(data: dict) -> str:
    """Extract content from assistant message."""
    message = data.get("message", {})
    parts = []
    for c in message.get("content", []):
        if isinstance(c, dict):
            if c.get("type") == "text":
                parts.append(c.get("text", "")[:200])
            elif c.get("type") == "tool_use":
                parts.append(f"[Using tool: {c.get('name', 'unknown')}]")
    return " ".join(parts)


def _get_raw_data(event_type: str, data: dict) -> dict:
    """Get raw data to store for event."""
    if event_type == "tool_use":
        return {"name": data.get("name", ""), "input": data.get("input", {})}
    return data
