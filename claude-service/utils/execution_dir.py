#!/usr/bin/env python3
"""
Execution Directory management for Claude Service.

Handles the folder-per-execution structure:
    logs/YYYY-MM-DD/HHMMSS_executionid/
        |- SUMMARY.md
        |- digest.json
        |- research.md
        |- workflow.md
        |- raw/timeline.json
"""

import json
from datetime import datetime
from pathlib import Path


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
