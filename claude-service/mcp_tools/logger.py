"""Structured logger for MCP operations.

Compatibility wrapper for UnifiedLogger with MCP-specific interface.
"""

import os
from typing import Any

from loggers import get_logger


class MCPLogger:
    """MCP-specific logger interface wrapping UnifiedLogger.

    Provides backward-compatible API for MCP tools.
    """

    def __init__(self) -> None:
        """Initialize the logger."""
        # Get execution directory from environment
        exec_dir = os.getenv("EXECUTION_DIR")

        # Get the unified logger instance
        self._unified = get_logger()

        # Setup execution directory if provided
        if exec_dir:
            # Extract execution_id from EXECUTION_DIR path
            # Format: /app/logs/YYYY-MM-DD/HHMMSS_executionid
            import re
            match = re.search(r'/(\d{6})_([^/]+)$', exec_dir)
            if match:
                execution_id = match.group(2)
                # Note: UnifiedLogger will handle the directory setup
                # We just need to ensure the log file is set
                from pathlib import Path
                self._unified._log_file = Path(exec_dir) / "mcp.log"

    def info(self, message: str, **details: Any) -> None:
        """Log info message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._unified.mcp_info(message, **details)

    def success(self, message: str, **details: Any) -> None:
        """Log success message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._unified.mcp_success(message, **details)

    def error(self, message: str, **details: Any) -> None:
        """Log error message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._unified.mcp_error(message, **details)

    def warn(self, message: str, **details: Any) -> None:
        """Log warning message.

        Args:
            message: Log message.
            **details: Key-value details to log.
        """
        self._unified.mcp_warn(message, **details)

    def operation(self, name: str, status: str, details: str = "") -> None:
        """Record an operation for the summary.

        Args:
            name: Operation name.
            status: Operation status (success, error, or other).
            details: Additional details.
        """
        self._unified.log_mcp_operation(name, status, details)

    def get_operations_summary(self) -> list[dict[str, Any]]:
        """Get list of operations for inclusion in response.

        Returns:
            Copy of operations list.
        """
        return self._unified.get_mcp_operations_summary()

    def clear_operations(self) -> None:
        """Clear the operations list."""
        self._unified.clear_mcp_operations()


# Global logger instance
logger = MCPLogger()
