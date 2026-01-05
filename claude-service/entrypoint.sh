#!/bin/bash
set -e

# Set permissive umask for all files created by Claude CLI
# 002 = files: rw-rw-r--, dirs: rwxrwxr-x
umask 002

# Setup Claude CLI config
# .claude/ is now mounted directly from host to /app/.claude/
# We need to symlink it to /root/.claude for Claude CLI to find it
setup_claude_config() {
    echo "[entrypoint] Setting up Claude CLI config..."

    # Create symlink from /root/.claude to /app/.claude
    if [ -d "/app/.claude" ]; then
        # Remove existing /root/.claude if it exists
        rm -rf /root/.claude
        ln -sf /app/.claude /root/.claude
        echo "  - Symlinked /app/.claude -> /root/.claude"
    fi

    # Copy .mcp.json to locations where Claude CLI looks for it
    if [ -f "/app/.claude/.mcp.json" ]; then
        cp /app/.claude/.mcp.json /root/.mcp.json
        cp /app/.claude/.mcp.json /app/.mcp.json
        echo "  - Copied .mcp.json to /root/ and /app/"
    fi

    echo "[entrypoint] Config setup complete."
}

# Fix permissions on directories
fix_permissions() {
    local dir="$1"
    if [ -d "$dir" ]; then
        find "$dir" -type f -exec chmod 644 {} \; 2>/dev/null || true
        find "$dir" -type d -exec chmod 755 {} \; 2>/dev/null || true
    fi
}

# Setup config
setup_claude_config

# Fix permissions on runtime directories
echo "[entrypoint] Fixing permissions on /app/logs..."
fix_permissions "/app/logs"

# Ensure logs directory exists
mkdir -p /app/logs
echo "[entrypoint] Ensured /app/logs exists"

echo "[entrypoint] Starting uvicorn with umask 002..."
exec "$@"
