#!/bin/bash
# Wrapper script to launch MCP server with proper environment
# This works around Claude Code bug #1254 where env vars from .mcp.json
# are not properly passed to MCP subprocesses.

# The parent process (claude-service container) has DATABASE_URL set.
# This wrapper ensures it's inherited by the MCP server subprocess.

# Set PYTHONPATH for imports
export PYTHONPATH="${PYTHONPATH:-/app}"

# Ensure we're in the right directory
cd /app

# Run the MCP server
exec python /app/mcp/server.py
