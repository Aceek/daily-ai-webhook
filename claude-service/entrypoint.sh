#!/bin/bash
set -e

# Set permissive umask for all files created by Claude CLI
umask 002

# Setup Claude CLI config
# Copy config files to /root/.claude (not symlink) so Claude CLI can write runtime data
# without polluting the mounted /app/.claude directory
setup_claude_config() {
    echo "[entrypoint] Setting up Claude CLI config..."

    # Prepare /root/.claude directory
    # If it's a volume mount, clear contents; otherwise recreate
    if mountpoint -q /root/.claude 2>/dev/null; then
        # It's a mount point, just clear contents (preserve runtime data like credentials)
        find /root/.claude -mindepth 1 -maxdepth 1 -name "missions" -o -name "CLAUDE.md" -o -name "docs" | xargs rm -rf 2>/dev/null || true
    else
        rm -rf /root/.claude
        mkdir -p /root/.claude
    fi

    # Copy config files from mounted volume
    if [ -d "/app/.claude" ]; then
        # Copy CLAUDE.md
        [ -f "/app/.claude/CLAUDE.md" ] && cp /app/.claude/CLAUDE.md /root/.claude/

        # Copy missions directory
        [ -d "/app/.claude/missions" ] && cp -r /app/.claude/missions /root/.claude/

        # Copy docs directory if exists
        [ -d "/app/.claude/docs" ] && cp -r /app/.claude/docs /root/.claude/

        # Copy credentials if exists
        [ -f "/app/.claude/.credentials.json" ] && cp /app/.claude/.credentials.json /root/.claude/

        echo "  - Copied config files to /root/.claude"
    fi

    # Copy .mcp.json to locations where Claude CLI looks for it
    if [ -f "/app/.claude/.mcp.json" ]; then
        cp /app/.claude/.mcp.json /root/.claude/.mcp.json
        cp /app/.claude/.mcp.json /root/.mcp.json
        cp /app/.claude/.mcp.json /app/.mcp.json
        echo "  - Copied .mcp.json to /root/.claude/, /root/ and /app/"
    fi

    echo "[entrypoint] Config setup complete (runtime data will stay in container)."
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
