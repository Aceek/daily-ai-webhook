# AI News Bot

Automated AI/ML news digest: n8n collects → Claude analyzes → PostgreSQL stores → Discord publishes.

## Stack

| Component | Tech | Role |
|-----------|------|------|
| Database | PostgreSQL 16 | Articles, digests, categories |
| Orchestration | n8n | Cron, RSS feeds, workflow |
| Intelligence | Claude Service (FastAPI) | Claude CLI wrapper, MCP tools |
| Bot | discord.py + FastAPI | Discord commands + HTTP API |

## Quick Start

```bash
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d
```

Access n8n at `http://localhost:5678`

## Architecture

```
├── claude-service/          # FastAPI + Claude CLI
│   ├── api/                 # Routes, handlers, models
│   ├── services/            # Business logic
│   ├── repositories/        # Database queries
│   ├── mcp/                 # MCP tools (DB access for Claude)
│   └── loggers/             # Execution logging
├── bot/                     # Discord bot
│   ├── cogs/                # Commands (/daily, /weekly, /status)
│   └── services/            # Publisher, embeds, cards
└── docker-compose.yml
```

## Flow

```
n8n (cron) → RSS feeds → POST /summarize
    ↓
claude-service → Claude CLI (agentic) → MCP submit_digest
    ↓
PostgreSQL ← articles + digest saved
    ↓
n8n → POST /publish → Discord bot → Discord channel
```

## Discord Commands

| Command | Description |
|---------|-------------|
| `/daily` | Latest daily digest |
| `/daily date:2024-12-20` | Specific date |
| `/weekly` | Weekly analysis |
| `/status` | Service health |

## Environment Variables

```bash
# Database
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

# Discord
DISCORD_TOKEN=
DISCORD_GUILD_ID=      # Optional

# n8n
N8N_USER=
N8N_PASSWORD=
```

## License

MIT
