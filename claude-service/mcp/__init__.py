"""MCP Server package for AI News Digest.

This package provides MCP tools for:
- Querying the database (categories, articles, stats)
- Submitting daily and weekly digests

Note: The server module imports the external 'mcp' package (fastmcp),
so we don't auto-import it here to avoid circular import issues.
Import directly with: from mcp.server import mcp
"""

__all__ = ["server", "logger", "utils", "validators", "models", "repositories", "services"]
