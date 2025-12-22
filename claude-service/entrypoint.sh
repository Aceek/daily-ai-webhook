#!/bin/bash
set -e

# Set permissive umask for all files created by Claude CLI
# 002 = files: rw-rw-r--, dirs: rwxrwxr-x
umask 002

# Copy our config files to Claude CLI home directory
# Source: /app/config/ (mounted read-only from host)
# Destination: /root/.claude/ (named volume for runtime)
copy_config() {
    local src="/app/config"
    local dest="/root/.claude"

    echo "[entrypoint] Copying config files to $dest..."

    # Create destination if not exists
    mkdir -p "$dest"

    # Copy CLAUDE.md (main instructions)
    if [ -f "$src/CLAUDE.md" ]; then
        cp "$src/CLAUDE.md" "$dest/CLAUDE.md"
        echo "  - CLAUDE.md"
    fi

    # Copy credentials
    if [ -f "$src/.credentials.json" ]; then
        cp "$src/.credentials.json" "$dest/.credentials.json"
        echo "  - .credentials.json"
    fi

    # Copy agents directory
    if [ -d "$src/agents" ]; then
        mkdir -p "$dest/agents"
        cp -r "$src/agents/"* "$dest/agents/" 2>/dev/null || true
        echo "  - agents/"
    fi

    # Copy docs directory
    if [ -d "$src/docs" ]; then
        mkdir -p "$dest/docs"
        cp -r "$src/docs/"* "$dest/docs/" 2>/dev/null || true
        echo "  - docs/"
    fi

    # Copy MCP config to home directory (not inside .claude)
    if [ -f "$src/.mcp.json" ]; then
        cp "$src/.mcp.json" "/root/.mcp.json"
        echo "  - .mcp.json -> /root/.mcp.json"
    fi

    echo "[entrypoint] Config copy complete."
}

# Fix permissions on directories
fix_permissions() {
    local dir="$1"
    if [ -d "$dir" ]; then
        find "$dir" -type f -exec chmod 644 {} \; 2>/dev/null || true
        find "$dir" -type d -exec chmod 755 {} \; 2>/dev/null || true
    fi
}

# Copy config files from mounted read-only source to Claude home
copy_config

# Fix permissions on runtime directories
echo "[entrypoint] Fixing permissions on /root/.claude..."
fix_permissions "/root/.claude"

echo "[entrypoint] Fixing permissions on /app/logs..."
fix_permissions "/app/logs"

# Ensure logs directory exists (subdirectories created dynamically per execution)
mkdir -p /app/logs
echo "[entrypoint] Ensured /app/logs exists"

echo "[entrypoint] Starting uvicorn with umask 002..."
exec "$@"
