#!/usr/bin/env python3
"""Unified Logger for Claude Service.

Consolidates:
- ExecutionLogger: Claude execution logs
- WorkflowLogger: n8n workflow logs
- MCPLogger: MCP tool operation logs
"""

import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from formatters.markdown_formatter import format_execution_summary, format_workflow_markdown
from loggers.models import ExecutionLog, WorkflowLog
from utils.execution_dir import ExecutionDirectory


logger = logging.getLogger(__name__)


class UnifiedLogger:
    """Unified logger managing all execution logging.

    Consolidates:
    - ExecutionLogger: Claude execution logs
    - WorkflowLogger: n8n workflow logs
    - MCPLogger: MCP tool operation logs
    """

    def __init__(self, logs_dir: str = "/app/logs") -> None:
        """Initialize the logger.

        Args:
            logs_dir: Base directory for logs.
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._current_dir: ExecutionDirectory | None = None
        self._mcp_operations: list[dict[str, Any]] = []
        self._log_file: Path | None = None
        self._log_write_failed: bool = False

    # =========================================================================
    # ExecutionLogger methods
    # =========================================================================

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
        # Setup MCP log file for this execution
        self._log_file = self._current_dir.path / "mcp.log"
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
            content = format_workflow_markdown(workflow_log)
            exec_dir.save_text(content, exec_dir.workflow_path)

        # Save summary last (uses other data)
        summary_content = format_execution_summary(execution_log, digest, workflow_log)
        exec_dir.save_text(summary_content, exec_dir.summary_path)

        return exec_dir

    # =========================================================================
    # WorkflowLogger methods
    # =========================================================================

    def save_workflow(
        self,
        workflow_log: WorkflowLog,
        execution_dir: Path | None = None,
    ) -> Path:
        """Save workflow log.

        If execution_dir is provided, saves to that directory.
        Otherwise, searches for matching execution or creates standalone.

        Args:
            workflow_log: The workflow log to save.
            execution_dir: Optional execution directory path.

        Returns:
            Path where the log was saved.
        """
        if execution_dir:
            path = execution_dir / "workflow.md"
            content = format_workflow_markdown(workflow_log)
            path.write_text(content, encoding="utf-8")
            return path

        # Try to find matching execution directory
        if workflow_log.claude_execution_id:
            matched_path = self._find_execution_dir(workflow_log.claude_execution_id)
            if matched_path:
                path = matched_path / "workflow.md"
                content = format_workflow_markdown(workflow_log)
                path.write_text(content, encoding="utf-8")
                self._update_summary_storage_status(matched_path, workflow_log)
                return path

        # Fallback: create in legacy workflows/ folder
        return self._save_standalone_workflow(workflow_log)

    def _find_execution_dir(self, execution_id: str) -> Path | None:
        """Find execution directory by Claude execution ID.

        Args:
            execution_id: Claude execution ID to search for.

        Returns:
            Path to execution directory if found, None otherwise.
        """
        skip_dirs = {"latest", "workflows", "digests", "research"}
        for date_dir in sorted(self.logs_dir.iterdir(), reverse=True):
            if not date_dir.is_dir() or date_dir.name in skip_dirs:
                continue
            for exec_dir in date_dir.iterdir():
                if exec_dir.is_dir() and execution_id in exec_dir.name:
                    return exec_dir
        return None

    def _save_standalone_workflow(self, workflow_log: WorkflowLog) -> Path:
        """Save as standalone log in workflows/ directory.

        Args:
            workflow_log: The workflow log to save.

        Returns:
            Path where the log was saved.
        """
        legacy_dir = self.logs_dir / "workflows"
        legacy_dir.mkdir(exist_ok=True)
        ts = workflow_log.started_at.strftime("%Y-%m-%d_%H-%M-%S")
        path = legacy_dir / f"{ts}_{workflow_log.workflow_execution_id}.md"
        content = format_workflow_markdown(workflow_log)
        path.write_text(content, encoding="utf-8")
        return path

    def _update_summary_storage_status(
        self,
        exec_dir: Path,
        workflow_log: WorkflowLog,
    ) -> None:
        """Update Storage and Pipeline sections in SUMMARY.md.

        Args:
            exec_dir: Execution directory containing SUMMARY.md.
            workflow_log: Workflow log with updated status.
        """
        summary_path = exec_dir / "SUMMARY.md"
        if not summary_path.exists():
            return

        try:
            content = summary_path.read_text(encoding="utf-8")

            # Update Pipeline Discord status
            if workflow_log.discord_sent:
                content = re.sub(
                    r"\| Discord send \| \[x\] \|",
                    "| Discord send | [+] |",
                    content,
                )

            # Build new storage lines
            storage_lines = self._build_storage_update(workflow_log)
            storage_pattern = (
                r"\| Database \| [^\|]+ \| [^\|]* \|\n\| Discord \| [^\|]+ \| [^\|]* \|"
            )
            content = re.sub(storage_pattern, storage_lines, content)

            summary_path.write_text(content, encoding="utf-8")
        except Exception as e:
            logger.warning(
                "Failed to update SUMMARY.md storage status: %s (file: %s)",
                e,
                summary_path,
            )

    def _build_storage_update(self, workflow_log: WorkflowLog) -> str:
        """Build storage section update lines.

        Args:
            workflow_log: Workflow log with storage status.

        Returns:
            Formatted storage table rows.
        """
        if workflow_log.db_saved:
            db_line = (
                f"| Database | [+] | "
                f"digest_id={workflow_log.digest_id}, "
                f"{workflow_log.articles_saved} articles |"
            )
        else:
            db_line = "| Database | [x] | Not saved |"

        if workflow_log.discord_sent:
            details = f"msg={workflow_log.discord_message_id}" if workflow_log.discord_message_id else "Sent"
            discord_line = f"| Discord | [+] | {details} |"
        else:
            discord_line = "| Discord | [x] | Not sent |"

        return f"{db_line}\n{discord_line}"

    # =========================================================================
    # MCPLogger methods
    # =========================================================================

    def _timestamp(self) -> str:
        """Get current timestamp string.

        Returns:
            Formatted timestamp.
        """
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _write_mcp_log(
        self,
        level: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Write MCP log entry to file and stderr.

        Args:
            level: Log level (INFO, OK, ERROR, WARN, OP).
            message: Log message.
            details: Optional key-value details.
        """
        timestamp = self._timestamp()
        log_line = f"[{timestamp}] [{level}] {message}"

        # Always write to stderr (may be captured by parent)
        print(f"[MCP] {log_line}", file=sys.stderr, flush=True)

        # Write to file if execution directory is set
        if self._log_file:
            try:
                with open(self._log_file, "a") as f:
                    f.write(f"{log_line}\n")
                    if details:
                        for key, value in details.items():
                            f.write(f"         {key}: {value}\n")
            except Exception as e:
                if not self._log_write_failed:
                    self._log_write_failed = True
                    print(f"[MCP] [WARN] Failed to write to log file: {e}", file=sys.stderr)

    def log_mcp_operation(
        self,
        name: str,
        status: str,
        details: str = "",
        **extra: Any,
    ) -> None:
        """Log an MCP tool operation.

        Args:
            name: Operation name.
            status: Operation status (success, error, info, warn).
            details: Additional details.
            **extra: Additional key-value pairs to log.
        """
        timestamp = self._timestamp()
        entry = {
            "timestamp": timestamp,
            "name": name,
            "status": status,
            "details": details,
            **extra,
        }
        self._mcp_operations.append(entry)

        # Map status to symbol and level
        if status == "success":
            symbol = "+"
            level = "OK"
        elif status == "error":
            symbol = "x"
            level = "ERROR"
        elif status == "warn":
            symbol = "!"
            level = "WARN"
        else:
            symbol = "o"
            level = "INFO"

        # Log to file and stderr
        self._write_mcp_log(
            level,
            f"{symbol} {name}",
            {"details": details, **extra} if (details or extra) else None,
        )

    def mcp_info(self, message: str, **details: Any) -> None:
        """Log MCP info message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._write_mcp_log("INFO", message, details if details else None)

    def mcp_success(self, message: str, **details: Any) -> None:
        """Log MCP success message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._write_mcp_log("OK", message, details if details else None)

    def mcp_error(self, message: str, **details: Any) -> None:
        """Log MCP error message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._write_mcp_log("ERROR", message, details if details else None)

    def mcp_warn(self, message: str, **details: Any) -> None:
        """Log MCP warning message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._write_mcp_log("WARN", message, details if details else None)

    def get_mcp_operations_summary(self) -> list[dict[str, Any]]:
        """Get list of MCP operations for inclusion in response.

        Returns:
            Copy of operations list.
        """
        return self._mcp_operations.copy()

    def clear_mcp_operations(self) -> None:
        """Clear the MCP operations list."""
        self._mcp_operations.clear()


# =============================================================================
# Global singleton
# =============================================================================

_logger: UnifiedLogger | None = None


def get_logger(logs_dir: str = "/app/logs") -> UnifiedLogger:
    """Get or create the global logger instance.

    Args:
        logs_dir: Base directory for logs.

    Returns:
        The global UnifiedLogger instance.
    """
    global _logger
    if _logger is None:
        _logger = UnifiedLogger(logs_dir)
    return _logger
