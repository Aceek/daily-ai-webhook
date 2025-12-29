FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies (including MCP)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "mcp>=0.5.0"

# Copy application code (refactored structure)
COPY main.py .
COPY config.py .
COPY database.py .
COPY models.py .
COPY api/ ./api/
COPY services/ ./services/
COPY repositories/ ./repositories/
COPY loggers/ ./loggers/
COPY formatters/ ./formatters/
COPY utils/ ./utils/

# Copy and setup entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create logs directories (will be mounted)
RUN mkdir -p /app/logs /app/logs/research /app/logs/digests

# Create mcp_tools directory (server.py will be mounted at runtime)
RUN mkdir -p /app/mcp_tools

# Copy MCP wrapper script to a location not affected by volume mount
# This script inherits parent env to work around Claude Code bug #1254
COPY mcp_tools/run_server.sh /usr/local/bin/mcp-run-server
RUN chmod +x /usr/local/bin/mcp-run-server

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Use entrypoint to fix permissions and set umask before starting
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
