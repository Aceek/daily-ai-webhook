#!/usr/bin/env python3
"""
Execution Logger - Unified logging with folder-per-execution structure.

Creates organized logs with the structure:
    logs/YYYY-MM-DD/HHMMSS_executionid/
        ├── SUMMARY.md      # Quick overview (10 lines)
        ├── digest.json     # Final output for Discord
        ├── research.md     # Research document from Claude
        ├── workflow.md     # n8n workflow log
        └── raw/            # Archive (optional)
            └── timeline.json
"""

import json
import os
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

    timestamp: float = 0.0
    event_type: str
    content: str = ""
    raw_data: dict = Field(default_factory=dict)


class ExecutionMetrics(BaseModel):
    """Metrics captured during execution."""

    prompt_length: int = 0
    response_length: int = 0
    articles_received: int = 0
    duration_seconds: float = 0.0
    total_cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0


class NodeExecutionLog(BaseModel):
    """Represents the execution status of a single n8n workflow node."""

    name: str
    status: str
    error: str | None = None


class WorkflowLog(BaseModel):
    """Complete log data for an n8n workflow execution."""

    workflow_execution_id: str
    workflow_name: str = "Unknown Workflow"
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime = Field(default_factory=datetime.now)
    duration_seconds: float = 0.0
    status: str = "success"
    error_message: str | None = None
    error_node: str | None = None
    nodes_executed: list[NodeExecutionLog] = Field(default_factory=list)
    articles_count: int = 0
    claude_execution_id: str | None = None
    discord_sent: bool = False


class ExecutionLog(BaseModel):
    """Complete execution log data."""

    execution_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = False
    error: str | None = None
    workflow_execution_id: str | None = None
    articles: list[ArticleLog] = Field(default_factory=list)
    prompt_sent: str = ""
    claude_response: str = ""
    timeline: list[StreamEvent] = Field(default_factory=list)
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)


class ExecutionDirectory:
    """
    Manages a single execution's log directory.

    Structure: logs/YYYY-MM-DD/HHMMSS_executionid/
    """

    def __init__(
        self,
        base_logs_dir: str,
        execution_id: str,
        timestamp: datetime | None = None,
    ) -> None:
        """Initialize execution directory.

        Args:
            base_logs_dir: Base logs directory (e.g., /app/logs)
            execution_id: Unique execution ID
            timestamp: Execution timestamp (defaults to now)
        """
        self.execution_id = execution_id
        self.timestamp = timestamp or datetime.now()
        self.base_dir = Path(base_logs_dir)

        # Create directory structure: logs/YYYY-MM-DD/HHMMSS_executionid/
        date_str = self.timestamp.strftime("%Y-%m-%d")
        time_str = self.timestamp.strftime("%H%M%S")
        self.folder_name = f"{time_str}_{execution_id}"
        self.exec_dir = self.base_dir / date_str / self.folder_name
        self.exec_dir.mkdir(parents=True, exist_ok=True)

        # Create raw subdirectory
        self.raw_dir = self.exec_dir / "raw"
        self.raw_dir.mkdir(exist_ok=True)

        # Update latest symlink
        self._update_latest_symlink()

    def _update_latest_symlink(self) -> None:
        """Update the 'latest' symlink to point to this execution."""
        latest_link = self.base_dir / "latest"
        try:
            if latest_link.is_symlink():
                latest_link.unlink()
            elif latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(self.exec_dir.relative_to(self.base_dir))
        except OSError:
            pass  # Symlinks may not work on all systems

    @property
    def path(self) -> Path:
        """Return the execution directory path."""
        return self.exec_dir

    @property
    def digest_path(self) -> Path:
        """Return path for digest.json."""
        return self.exec_dir / "digest.json"

    @property
    def research_path(self) -> Path:
        """Return path for research.md."""
        return self.exec_dir / "research.md"

    def save_digest(self, digest: dict) -> Path:
        """Save the digest JSON file."""
        path = self.digest_path
        with open(path, "w", encoding="utf-8") as f:
            json.dump(digest, f, indent=2, ensure_ascii=False)
        return path

    def save_workflow_log(self, workflow_log: WorkflowLog) -> Path:
        """Save workflow log as workflow.md."""
        path = self.exec_dir / "workflow.md"
        content = self._format_workflow_md(workflow_log)
        path.write_text(content, encoding="utf-8")
        return path

    def save_timeline(self, timeline: list[StreamEvent]) -> Path:
        """Save raw timeline to raw/timeline.json."""
        path = self.raw_dir / "timeline.json"
        data = [event.model_dump() for event in timeline]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def save_summary(
        self,
        execution_log: ExecutionLog,
        digest: dict | None = None,
        workflow_log: WorkflowLog | None = None,
    ) -> Path:
        """Generate and save SUMMARY.md."""
        path = self.exec_dir / "SUMMARY.md"
        content = self._format_summary(execution_log, digest, workflow_log)
        path.write_text(content, encoding="utf-8")
        return path

    def _format_summary(
        self,
        log: ExecutionLog,
        digest: dict | None,
        workflow: WorkflowLog | None,
    ) -> str:
        """Format the SUMMARY.md file."""
        status = "SUCCESS" if log.success else "FAILED"
        status_emoji = "✅" if log.success else "❌"

        # Format duration
        mins = int(log.metrics.duration_seconds // 60)
        secs = int(log.metrics.duration_seconds % 60)
        duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

        # Cost
        cost_str = f"${log.metrics.total_cost_usd:.2f}" if log.metrics.total_cost_usd > 0 else "N/A"

        # Pipeline status
        collect_status = "✅" if log.metrics.articles_received > 0 else "❌"
        claude_status = "✅" if log.success else "❌"
        discord_status = "✅" if workflow and workflow.discord_sent else "❌"

        # Digest stats
        headlines_count = len(digest.get("headlines", [])) if digest else 0
        research_count = len(digest.get("research", [])) if digest else 0
        industry_count = len(digest.get("industry", [])) if digest else 0
        watching_count = len(digest.get("watching", [])) if digest else 0
        total_news = headlines_count + research_count + industry_count + watching_count

        # Metadata from digest
        meta = digest.get("metadata", {}) if digest else {}
        web_searches = meta.get("web_searches", 0)
        fact_checks = meta.get("fact_checks", 0)
        deep_dives = meta.get("deep_dives", 0)

        # Top headlines
        top_headlines = ""
        if digest and digest.get("headlines"):
            for i, h in enumerate(digest["headlines"][:3], 1):
                top_headlines += f"{i}. {h.get('title', 'N/A')}\n"
        else:
            top_headlines = "*No headlines*\n"

        md = f"""# Execution {log.execution_id}

**Status:** {status_emoji} {status}
**Date:** {log.timestamp.strftime("%Y-%m-%d %H:%M")}
**Duration:** {duration_str} | **Cost:** {cost_str}

## Pipeline

| Step | Status |
|------|--------|
| n8n collect | {collect_status} {log.metrics.articles_received} articles |
| Claude analyze | {claude_status} {web_searches} searches, {deep_dives} deep-dives |
| Discord send | {discord_status} |

## Output ({total_news} news)

| Category | Count |
|----------|-------|
| 📰 Headlines | {headlines_count} |
| 🔬 Research | {research_count} |
| 💼 Industry | {industry_count} |
| 👀 Watching | {watching_count} |

## Top Stories

{top_headlines}
## Files

- [digest.json](./digest.json) - Final output
- [research.md](./research.md) - Research document
- [workflow.md](./workflow.md) - Workflow log
"""

        if log.error:
            md += f"""
## Error

```
{log.error}
```
"""

        return md

    def _format_workflow_md(self, log: WorkflowLog) -> str:
        """Format workflow log as Markdown."""
        status_emoji = "✅" if log.status == "success" else "❌"
        duration_str = f"{log.duration_seconds:.1f}s"

        # Nodes table
        nodes_lines = ["| Node | Status |", "|------|--------|"]
        for node in log.nodes_executed:
            s = "✅" if node.status == "success" else "❌"
            nodes_lines.append(f"| {node.name} | {s} |")
        nodes_table = "\n".join(nodes_lines)

        md = f"""# Workflow Log

**Status:** {status_emoji} {log.status.upper()}
**Duration:** {duration_str}
**Articles:** {log.articles_count}
**Discord:** {"✅ Sent" if log.discord_sent else "❌ Not sent"}

## Nodes

{nodes_table}
"""

        if log.error_message:
            md += f"""
## Error

Node: `{log.error_node}`

```
{log.error_message}
```
"""

        return md


class ExecutionLogger:
    """Manages execution logging with the new folder structure."""

    def __init__(self, logs_dir: str = "/app/logs") -> None:
        """Initialize the logger."""
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._current_dir: ExecutionDirectory | None = None

    def create_execution_dir(
        self,
        execution_id: str,
        timestamp: datetime | None = None,
    ) -> ExecutionDirectory:
        """Create a new execution directory."""
        self._current_dir = ExecutionDirectory(
            base_logs_dir=str(self.logs_dir),
            execution_id=execution_id,
            timestamp=timestamp,
        )
        return self._current_dir

    def get_execution_dir(self, execution_id: str) -> ExecutionDirectory | None:
        """Get existing execution directory by ID."""
        # Search in date folders
        for date_dir in sorted(self.logs_dir.iterdir(), reverse=True):
            if not date_dir.is_dir() or date_dir.name == "latest":
                continue
            for exec_dir in date_dir.iterdir():
                if exec_dir.is_dir() and execution_id in exec_dir.name:
                    return ExecutionDirectory(
                        base_logs_dir=str(self.logs_dir),
                        execution_id=execution_id,
                        timestamp=datetime.strptime(
                            f"{date_dir.name}_{exec_dir.name[:6]}",
                            "%Y-%m-%d_%H%M%S"
                        ),
                    )
        return None

    def save(
        self,
        execution_log: ExecutionLog,
        exec_dir: ExecutionDirectory | None = None,
        digest: dict | None = None,
        workflow_log: WorkflowLog | None = None,
    ) -> ExecutionDirectory:
        """Save all logs for an execution.

        Args:
            execution_log: The main execution log data
            exec_dir: Optional existing execution directory (reused if provided)
            digest: Optional digest data from MCP
            workflow_log: Optional workflow log from n8n

        Returns:
            The ExecutionDirectory containing all saved files
        """
        # Reuse existing directory or create new one
        if exec_dir is None:
            exec_dir = self.create_execution_dir(
                execution_id=execution_log.execution_id,
                timestamp=execution_log.timestamp,
            )

        # Save timeline to raw/
        if execution_log.timeline:
            exec_dir.save_timeline(execution_log.timeline)

        # Save digest if provided
        if digest:
            exec_dir.save_digest(digest)

        # Save workflow log if provided
        if workflow_log:
            exec_dir.save_workflow_log(workflow_log)

        # Always save summary last (it uses other data)
        exec_dir.save_summary(execution_log, digest, workflow_log)

        return exec_dir


class WorkflowLogger:
    """
    Handles workflow logs - saves to execution directory if available,
    otherwise creates standalone log.
    """

    def __init__(self, logs_dir: str = "/app/logs") -> None:
        """Initialize the workflow logger."""
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        workflow_log: WorkflowLog,
        execution_dir: ExecutionDirectory | None = None,
    ) -> Path:
        """Save workflow log.

        If execution_dir is provided, saves to that directory.
        Otherwise, searches for matching execution or creates standalone.
        """
        # If we have an execution directory, save there
        if execution_dir:
            return execution_dir.save_workflow_log(workflow_log)

        # Try to find matching execution directory by claude_execution_id
        if workflow_log.claude_execution_id:
            for date_dir in sorted(self.logs_dir.iterdir(), reverse=True):
                if not date_dir.is_dir() or date_dir.name in ("latest", "workflows", "digests", "research"):
                    continue
                for exec_dir in date_dir.iterdir():
                    if exec_dir.is_dir() and workflow_log.claude_execution_id in exec_dir.name:
                        # Found matching directory
                        path = exec_dir / "workflow.md"
                        content = self._format_workflow_md(workflow_log)
                        path.write_text(content, encoding="utf-8")

                        # Update summary if exists
                        summary_path = exec_dir / "SUMMARY.md"
                        if summary_path.exists():
                            self._update_summary_discord_status(summary_path, workflow_log.discord_sent)

                        return path

        # Fallback: create in legacy workflows/ folder
        legacy_dir = self.logs_dir / "workflows"
        legacy_dir.mkdir(exist_ok=True)
        ts = workflow_log.started_at.strftime("%Y-%m-%d_%H-%M-%S")
        path = legacy_dir / f"{ts}_{workflow_log.workflow_execution_id}.md"
        content = self._format_workflow_md(workflow_log)
        path.write_text(content, encoding="utf-8")
        return path

    def _format_workflow_md(self, log: WorkflowLog) -> str:
        """Format workflow log as Markdown."""
        status_emoji = "✅" if log.status == "success" else "❌"
        duration_str = f"{log.duration_seconds:.1f}s"

        nodes_lines = ["| Node | Status |", "|------|--------|"]
        for node in log.nodes_executed:
            s = "✅" if node.status == "success" else "❌"
            nodes_lines.append(f"| {node.name} | {s} |")
        nodes_table = "\n".join(nodes_lines)

        md = f"""# Workflow Log

**Status:** {status_emoji} {log.status.upper()}
**Workflow ID:** `{log.workflow_execution_id}`
**Claude ID:** `{log.claude_execution_id or 'N/A'}`
**Duration:** {duration_str}
**Articles:** {log.articles_count}
**Discord:** {"✅ Sent" if log.discord_sent else "❌ Not sent"}

## Nodes

{nodes_table}
"""

        if log.error_message:
            md += f"""
## Error

Node: `{log.error_node}`

```
{log.error_message}
```
"""

        return md

    def _update_summary_discord_status(self, summary_path: Path, discord_sent: bool) -> None:
        """Update Discord status in SUMMARY.md."""
        try:
            content = summary_path.read_text(encoding="utf-8")
            old_status = "| Discord send | ❌ |"
            new_status = "| Discord send | ✅ |" if discord_sent else "| Discord send | ❌ |"
            content = content.replace(old_status, new_status)
            summary_path.write_text(content, encoding="utf-8")
        except Exception:
            pass


def parse_stream_event(line: str, start_time: float) -> StreamEvent | None:
    """Parse a single line of stream-json output into a StreamEvent."""
    import time

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
            raw_data={"name": tool_name, "input": data.get("input", {})}
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
    workflow_execution_id: str | None = None,
    execution_id: str | None = None,
) -> ExecutionLog:
    """Factory function to create an ExecutionLog from raw data."""
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

    log_kwargs = {
        "success": success,
        "error": error,
        "workflow_execution_id": workflow_execution_id,
        "articles": article_logs,
        "prompt_sent": prompt,
        "claude_response": response,
        "timeline": timeline or [],
        "metrics": metrics,
    }
    if execution_id:
        log_kwargs["execution_id"] = execution_id

    return ExecutionLog(**log_kwargs)
