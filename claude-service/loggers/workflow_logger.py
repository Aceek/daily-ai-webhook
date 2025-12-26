#!/usr/bin/env python3
"""
Workflow Logger for Claude Service.

Handles workflow logs - saves to execution directory if available,
otherwise creates standalone log.
"""

import re
from pathlib import Path

from formatters.markdown_formatter import format_workflow_markdown
from loggers.models import WorkflowLog


class WorkflowLogger:
    """Handles workflow logs with smart directory matching."""

    def __init__(self, logs_dir: str = "/app/logs") -> None:
        """Initialize the workflow logger.

        Args:
            logs_dir: Base directory for logs.
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def save(
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
        return self._save_standalone(workflow_log)

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

    def _save_standalone(self, workflow_log: WorkflowLog) -> Path:
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
        except Exception:
            pass

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
