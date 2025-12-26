"""Structured logger for MCP operations.

Writes to execution directory for debugging and stderr for real-time monitoring.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class MCPLogger:
    """Structured logger for MCP operations.

    Writes to mcp.log in the execution directory for persistent debugging.
    Also outputs to stderr for real-time monitoring.
    """

    def __init__(self) -> None:
        """Initialize the logger."""
        self.exec_dir = os.getenv("EXECUTION_DIR")
        self.log_file = Path(self.exec_dir) / "mcp.log" if self.exec_dir else None
        self.operations: list[dict[str, Any]] = []

    def _timestamp(self) -> str:
        """Get current timestamp string.

        Returns:
            Formatted timestamp.
        """
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def _write(
        self,
        level: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Write log entry to file and stderr.

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
        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(f"{log_line}\n")
                    if details:
                        for key, value in details.items():
                            f.write(f"         {key}: {value}\n")
            except Exception:
                pass  # Don't fail on logging errors

    def info(self, message: str, **details: Any) -> None:
        """Log info message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._write("INFO", message, details if details else None)

    def success(self, message: str, **details: Any) -> None:
        """Log success message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._write("OK", message, details if details else None)

    def error(self, message: str, **details: Any) -> None:
        """Log error message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._write("ERROR", message, details if details else None)

    def warn(self, message: str, **details: Any) -> None:
        """Log warning message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._write("WARN", message, details if details else None)

    def operation(self, name: str, status: str, details: str = "") -> None:
        """Record an operation for the summary.

        Args:
            name: Operation name.
            status: Operation status (success, error, or other).
            details: Additional details.
        """
        self.operations.append({
            "timestamp": self._timestamp(),
            "name": name,
            "status": status,
            "details": details,
        })
        symbol = "+" if status == "success" else "x" if status == "error" else "o"
        self._write(
            "OP",
            f"{symbol} {name}",
            {"details": details} if details else None,
        )

    def get_operations_summary(self) -> list[dict[str, Any]]:
        """Get list of operations for inclusion in response.

        Returns:
            Copy of operations list.
        """
        return self.operations.copy()

    def clear_operations(self) -> None:
        """Clear the operations list."""
        self.operations.clear()


# Global logger instance
logger = MCPLogger()
