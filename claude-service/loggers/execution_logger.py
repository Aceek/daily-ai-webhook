#!/usr/bin/env python3
"""
Execution Logger for Claude Service.

Manages execution logging with folder-per-execution structure.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from formatters.markdown_formatter import format_execution_summary
from loggers.models import (
    ArticleLog,
    ExecutionLog,
    ExecutionMetrics,
    StreamEvent,
    WorkflowLog,
)


class ExecutionDirectory:
    """Manages a single execution's log directory.

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

    @property
    def summary_path(self) -> Path:
        """Return path for SUMMARY.md."""
        return self.exec_dir / "SUMMARY.md"

    @property
    def workflow_path(self) -> Path:
        """Return path for workflow.md."""
        return self.exec_dir / "workflow.md"

    @property
    def timeline_path(self) -> Path:
        """Return path for raw/timeline.json."""
        return self.raw_dir / "timeline.json"

    def save_json(self, data: dict | list, path: Path) -> Path:
        """Save data as JSON to specified path.

        Args:
            data: Data to serialize as JSON.
            path: Path to write to.

        Returns:
            The path written to.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def save_text(self, content: str, path: Path) -> Path:
        """Save text content to specified path.

        Args:
            content: Text content to write.
            path: Path to write to.

        Returns:
            The path written to.
        """
        path.write_text(content, encoding="utf-8")
        return path

    def read_json(self, path: Path) -> dict | list | None:
        """Read JSON from specified path.

        Args:
            path: Path to read from.

        Returns:
            Parsed JSON data or None if file doesn't exist.
        """
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None


class ExecutionLogger:
    """Manages execution logging with the folder structure."""

    def __init__(self, logs_dir: str = "/app/logs") -> None:
        """Initialize the logger.

        Args:
            logs_dir: Base directory for logs.
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._current_dir: ExecutionDirectory | None = None

    def create_execution_dir(
        self,
        execution_id: str,
        timestamp: datetime | None = None,
    ) -> ExecutionDirectory:
        """Create a new execution directory.

        Args:
            execution_id: Unique execution ID.
            timestamp: Optional timestamp (defaults to now).

        Returns:
            New ExecutionDirectory instance.
        """
        self._current_dir = ExecutionDirectory(
            base_logs_dir=str(self.logs_dir),
            execution_id=execution_id,
            timestamp=timestamp,
        )
        return self._current_dir

    def get_execution_dir(self, execution_id: str) -> ExecutionDirectory | None:
        """Get existing execution directory by ID.

        Args:
            execution_id: Execution ID to search for.

        Returns:
            ExecutionDirectory if found, None otherwise.
        """
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
                            "%Y-%m-%d_%H%M%S",
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
            execution_log: The main execution log data.
            exec_dir: Optional existing execution directory.
            digest: Optional digest data from MCP.
            workflow_log: Optional workflow log from n8n.

        Returns:
            The ExecutionDirectory containing all saved files.
        """
        if exec_dir is None:
            exec_dir = self.create_execution_dir(
                execution_id=execution_log.execution_id,
                timestamp=execution_log.timestamp,
            )

        # Save timeline to raw/
        if execution_log.timeline:
            timeline_data = [event.model_dump() for event in execution_log.timeline]
            exec_dir.save_json(timeline_data, exec_dir.timeline_path)

        # Save digest if provided
        if digest:
            exec_dir.save_json(digest, exec_dir.digest_path)

        # Save workflow log if provided
        if workflow_log:
            from formatters.markdown_formatter import format_workflow_markdown
            content = format_workflow_markdown(workflow_log)
            exec_dir.save_text(content, exec_dir.workflow_path)

        # Save summary last (uses other data)
        summary_content = format_execution_summary(execution_log, digest, workflow_log)
        exec_dir.save_text(summary_content, exec_dir.summary_path)

        return exec_dir


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
    mission: str = "ai-news",
) -> ExecutionLog:
    """Factory function to create an ExecutionLog from raw data.

    Args:
        articles: List of articles processed.
        prompt: Prompt sent to Claude.
        response: Response from Claude.
        duration: Execution duration in seconds.
        success: Whether execution succeeded.
        error: Error message if failed.
        timeline: Stream events timeline.
        input_tokens: Input token count.
        output_tokens: Output token count.
        cost_usd: Cost in USD.
        workflow_execution_id: n8n workflow ID.
        execution_id: Unique execution ID.
        mission: Mission name.

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

    log_kwargs: dict[str, Any] = {
        "success": success,
        "error": error,
        "workflow_execution_id": workflow_execution_id,
        "articles": article_logs,
        "prompt_sent": prompt,
        "claude_response": response,
        "timeline": timeline or [],
        "metrics": metrics,
        "mission": mission,
    }
    if execution_id:
        log_kwargs["execution_id"] = execution_id

    return ExecutionLog(**log_kwargs)
