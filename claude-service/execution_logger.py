#!/usr/bin/env python3
"""
Execution Logger - Generates detailed log documents for each workflow execution.

Creates both Markdown (human-readable) and JSON (machine-parsable) logs
for complete traceability of the summarization pipeline.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ArticleLog(BaseModel):
    """Article data for logging."""

    title: str
    url: str
    source: str
    pub_date: str
    description_preview: str = Field(default="", description="First 100 chars")


class StreamEvent(BaseModel):
    """Represents a single event from Claude CLI stream-json output."""

    timestamp: float = 0.0  # Seconds since start
    event_type: str  # init, assistant, tool_use, tool_result, result, error
    content: str = ""  # Human-readable summary of the event
    raw_data: dict = Field(default_factory=dict)  # Original JSON data


class ExecutionMetrics(BaseModel):
    """Metrics captured during execution."""

    prompt_length: int = 0
    response_length: int = 0
    articles_received: int = 0
    duration_seconds: float = 0.0
    total_cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0


class ExecutionLog(BaseModel):
    """Complete execution log data."""

    execution_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = False
    error: str | None = None

    # Input data
    articles: list[ArticleLog] = Field(default_factory=list)

    # Processing data
    prompt_sent: str = ""
    claude_response: str = ""

    # Timeline of events from stream-json
    timeline: list[StreamEvent] = Field(default_factory=list)

    # Metrics
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)


class ExecutionLogger:
    """Handles creation and storage of execution logs."""

    def __init__(self, logs_dir: str = "/app/logs") -> None:
        """Initialize the logger with a logs directory.

        Args:
            logs_dir: Path to the directory where logs will be stored.
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, execution_log: ExecutionLog) -> str:
        """Generate a filename based on timestamp and execution ID.

        Args:
            execution_log: The execution log to generate filename for.

        Returns:
            Base filename without extension.
        """
        ts = execution_log.timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        return f"{ts}_{execution_log.execution_id}"

    def _format_timeline(self, timeline: list[StreamEvent]) -> str:
        """Format timeline events as Markdown.

        Args:
            timeline: List of stream events.

        Returns:
            Markdown formatted timeline.
        """
        if not timeline:
            return "*No timeline events captured*"

        # Event type to emoji mapping
        emoji_map = {
            "init": "🚀",
            "assistant": "💬",
            "tool_use": "🔧",
            "tool_result": "📋",
            "result": "✅",
            "error": "❌",
            "system": "⚙️",
        }

        lines = ["| Time | Event | Details |", "|------|-------|---------|"]
        for event in timeline:
            emoji = emoji_map.get(event.event_type, "📌")
            time_str = f"{event.timestamp:.1f}s"
            # Truncate content for table display
            content_short = (
                event.content[:80] + "..." if len(event.content) > 80 else event.content
            )
            # Escape pipe characters for markdown table
            content_escaped = content_short.replace("|", "\\|")
            lines.append(f"| {time_str} | {emoji} {event.event_type} | {content_escaped} |")

        return "\n".join(lines)

    def _format_tool_details(self, timeline: list[StreamEvent]) -> str:
        """Format detailed tool usage as Markdown.

        Args:
            timeline: List of stream events.

        Returns:
            Markdown formatted tool details.
        """
        tool_events = [e for e in timeline if e.event_type in ("tool_use", "tool_result")]
        if not tool_events:
            return ""

        sections = ["## Tool Usage Details\n"]
        for event in tool_events:
            if event.event_type == "tool_use":
                tool_name = event.raw_data.get("name", "Unknown")
                tool_input = event.raw_data.get("input", {})
                sections.append(f"### 🔧 {tool_name}\n")
                sections.append("<details>")
                sections.append(f"<summary>Input ({event.timestamp:.1f}s)</summary>\n")
                sections.append("```json")
                sections.append(json.dumps(tool_input, indent=2, ensure_ascii=False)[:1000])
                sections.append("```\n")
                sections.append("</details>\n")
            elif event.event_type == "tool_result":
                sections.append("<details>")
                sections.append(f"<summary>Result ({event.timestamp:.1f}s)</summary>\n")
                sections.append("```")
                sections.append(event.content[:2000])
                sections.append("```\n")
                sections.append("</details>\n")

        return "\n".join(sections)

    def _format_markdown(self, log: ExecutionLog) -> str:
        """Format execution log as Markdown document.

        Args:
            log: The execution log to format.

        Returns:
            Markdown formatted string.
        """
        status_emoji = "✅" if log.success else "❌"
        status_text = "SUCCESS" if log.success else "FAILED"

        # Build articles table
        articles_table = "| # | Title | Source | Date |\n|---|-------|--------|------|\n"
        for i, article in enumerate(log.articles, 1):
            title_short = (
                article.title[:50] + "..." if len(article.title) > 50 else article.title
            )
            articles_table += f"| {i} | {title_short} | {article.source} | {article.pub_date[:10] if article.pub_date else 'N/A'} |\n"

        # Format cost if available
        cost_str = f"${log.metrics.total_cost_usd:.4f}" if log.metrics.total_cost_usd > 0 else "N/A"
        tokens_str = f"{log.metrics.input_tokens:,} in / {log.metrics.output_tokens:,} out" if log.metrics.input_tokens > 0 else "N/A"

        md = f"""# Execution Log - {log.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

## Metadata

| Field | Value |
|-------|-------|
| **Execution ID** | `{log.execution_id}` |
| **Timestamp** | {log.timestamp.isoformat()} |
| **Status** | {status_emoji} {status_text} |
| **Duration** | {log.metrics.duration_seconds:.2f}s |
| **Articles Received** | {log.metrics.articles_received} |
| **Tokens** | {tokens_str} |
| **Cost** | {cost_str} |

"""

        if log.error:
            md += f"""## Error

```
{log.error}
```

"""

        # Add execution timeline
        md += f"""## Execution Timeline

{self._format_timeline(log.timeline)}

"""

        # Add tool details if any
        tool_details = self._format_tool_details(log.timeline)
        if tool_details:
            md += tool_details + "\n"

        md += f"""## Input Articles

{articles_table}

## Prompt Sent to Claude

<details>
<summary>Click to expand prompt ({log.metrics.prompt_length} characters)</summary>

```
{log.prompt_sent}
```

</details>

## Claude Response

```
{log.claude_response}
```

## Metrics

| Metric | Value |
|--------|-------|
| Prompt Length | {log.metrics.prompt_length:,} chars |
| Response Length | {log.metrics.response_length:,} chars |
| Input Tokens | {log.metrics.input_tokens:,} |
| Output Tokens | {log.metrics.output_tokens:,} |
| Total Cost | {cost_str} |
| Total Duration | {log.metrics.duration_seconds:.2f}s |

---
*Generated by claude-service v1.1.0*
"""
        return md

    def save(self, execution_log: ExecutionLog) -> tuple[Path, Path]:
        """Save execution log as both Markdown and JSON files.

        Args:
            execution_log: The execution log to save.

        Returns:
            Tuple of (markdown_path, json_path).
        """
        base_filename = self._generate_filename(execution_log)

        # Save Markdown
        md_path = self.logs_dir / f"{base_filename}.md"
        md_content = self._format_markdown(execution_log)
        md_path.write_text(md_content, encoding="utf-8")

        # Save JSON
        json_path = self.logs_dir / f"{base_filename}.json"
        json_content = execution_log.model_dump_json(indent=2)
        json_path.write_text(json_content, encoding="utf-8")

        return md_path, json_path


def parse_stream_event(line: str, start_time: float) -> StreamEvent | None:
    """Parse a single line of stream-json output into a StreamEvent.

    Args:
        line: A single JSON line from Claude CLI stream-json output.
        start_time: The start time of the execution for calculating relative timestamps.

    Returns:
        StreamEvent if parsing successful, None otherwise.
    """
    import time

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    event_type = data.get("type", "unknown")
    timestamp = time.time() - start_time
    content = ""

    # Extract human-readable content based on event type
    if event_type == "init":
        session_id = data.get("session_id", "")[:12]
        content = f"Session started: {session_id}"

    elif event_type == "assistant":
        # Assistant message - extract text content
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
        # Store tool details in raw_data
        return StreamEvent(
            timestamp=timestamp,
            event_type=event_type,
            content=content,
            raw_data={"name": tool_name, "input": data.get("input", {})}
        )

    elif event_type == "tool_result":
        output = data.get("output", "")
        content = output[:200] if output else "(empty result)"

    elif event_type == "result":
        # Final result with cost info
        cost = data.get("total_cost_usd", 0)
        duration = data.get("duration_ms", 0) / 1000
        content = f"Completed (cost: ${cost:.4f}, duration: {duration:.1f}s)"
        return StreamEvent(
            timestamp=timestamp,
            event_type=event_type,
            content=content,
            raw_data=data
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
        raw_data=data
    )


def create_execution_log(
    articles: list[Any],
    prompt: str,
    response: str,
    duration: float,
    success: bool,
    error: str | None = None,
    timeline: list[StreamEvent] | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
) -> ExecutionLog:
    """Factory function to create an ExecutionLog from raw data.

    Args:
        articles: List of Article objects from the request.
        prompt: The prompt sent to Claude CLI.
        response: Claude's response.
        duration: Execution duration in seconds.
        success: Whether the execution succeeded.
        error: Error message if failed.
        timeline: List of stream events from Claude CLI.
        input_tokens: Number of input tokens used.
        output_tokens: Number of output tokens used.
        cost_usd: Total cost in USD.

    Returns:
        Populated ExecutionLog instance.
    """
    article_logs = [
        ArticleLog(
            title=a.title,
            url=a.url,
            source=a.source,
            pub_date=a.pub_date,
            description_preview=a.description[:100] if a.description else "",
        )
        for a in articles
    ]

    metrics = ExecutionMetrics(
        prompt_length=len(prompt),
        response_length=len(response),
        articles_received=len(articles),
        duration_seconds=duration,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_cost_usd=cost_usd,
    )

    return ExecutionLog(
        success=success,
        error=error,
        articles=article_logs,
        prompt_sent=prompt,
        claude_response=response,
        timeline=timeline or [],
        metrics=metrics,
    )
