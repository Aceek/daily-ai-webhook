# Architecture

## Structure

```
daily-ai-webhook/
├── docker-compose.yml
├── claude-service/          # FastAPI + Claude CLI + MCP
│   ├── main.py              # App init, lifespan
│   ├── config.py            # Settings, discover_missions()
│   ├── models.py            # SQLModel ORM
│   ├── database.py          # Async session factory
│   ├── api/
│   │   ├── routes.py        # Router + endpoint logic
│   │   └── models.py        # Pydantic I/O
│   ├── services/
│   │   ├── summarize_service.py # Daily digest orchestration
│   │   ├── weekly_service.py    # Weekly digest orchestration
│   │   ├── claude_service.py    # CLI invocation
│   │   ├── digest_service.py    # Digest file ops
│   │   └── prompt_builder.py    # Prompt construction
│   ├── repositories/
│   │   └── article_repository.py
│   ├── loggers/
│   │   ├── unified_logger.py    # Unified logging
│   │   └── models.py
│   ├── formatters/
│   │   └── markdown_formatter.py
│   ├── utils/
│   │   └── execution_dir.py
│   ├── mcp_tools/           # MCP server (FastMCP)
│   │   ├── server.py        # 6 tools
│   │   ├── models.py
│   │   ├── validators.py
│   │   ├── repositories/    # DB queries
│   │   └── services/        # Business logic
│   └── .claude/             # Agent config (read-only mount)
│       ├── CLAUDE.md        # Agent instructions
│       ├── .mcp.json        # MCP config
│       ├── .credentials.json
│       └── missions/
│           ├── _common/     # Shared rules
│           └── ai-news/     # Mission config
├── bot/                     # Discord bot
│   ├── main.py              # AINewsBot class
│   ├── api.py               # /publish, /health
│   ├── config.py
│   ├── cogs/
│   │   ├── daily.py         # /daily
│   │   ├── weekly.py        # /weekly
│   │   └── admin.py         # /status, /stats
│   ├── services/
│   │   ├── publisher.py     # Digest → Discord
│   │   ├── embed_builder.py # Embed construction
│   │   ├── card_generator.py
│   │   ├── image_renderer.py
│   │   ├── claude_client.py # /analyze-weekly client
│   │   └── repositories/
│   └── templates/           # HTML cards
├── data/                    # articles.json (runtime)
└── logs/                    # Execution logs
```

## Flux Daily

```
1. n8n cron 8h
2. RSS feeds (7 sources) → merge/dedup
3. POST /summarize {mission, articles}
4. claude-service:
   - write articles.json
   - claude CLI --allowedTools [MCP tools]
   - Claude: reads mission files
   - Claude: get_categories(), get_recent_headlines()
   - Claude: submit_digest() → DB insert
5. Response {success, digest_id, digest}
6. n8n: POST /publish {digest_id, content}
7. discord-bot: build embeds → Discord
8. n8n: POST /log-workflow
```

## Flux Weekly

```
1. n8n cron lundi 8h (ou /weekly command)
2. POST /analyze-weekly {mission, week_start, week_end, theme?}
3. claude-service:
   - get_article_stats() → volume
   - get_categories() → active cats
   - get_articles() → week's articles
   - Analyse trends + top stories
   - submit_weekly_digest() → DB
4. discord-bot: /weekly → embeds
```

## Services Docker

| Service | Image | Depends |
|---------|-------|---------|
| postgres | postgres:16-alpine | - |
| n8n | n8nio/n8n:2.0.3 | postgres |
| claude-service | ./claude-service | postgres (healthy) |
| discord-bot | ./bot | postgres |

## Logs Structure

```
logs/
├── YYYY-MM-DD/
│   └── HHMMSS_executionid/
│       ├── SUMMARY.md       # Status, pipeline
│       ├── digest.json      # Structured output
│       ├── workflow.md      # n8n log
│       ├── mcp.log          # MCP operations
│       └── raw/timeline.json
└── latest → symlink
```

## Patterns

| Pattern | Usage |
|---------|-------|
| Layered | api → services → repositories |
| DI | Settings, logger injection |
| Repository | DB abstraction |
| Factory | Session, logger creation |
| Strategy | Mission-specific rules |

## Extension: Nouvelle Mission

```bash
# 1. Créer mission files
mkdir -p claude-service/.claude/missions/{mission_id}
# mission.md, selection-rules.md, output-schema.md

# 2. Ajouter weekly/ si besoin
mkdir -p claude-service/.claude/missions/{mission_id}/weekly

# 3. POST /summarize avec mission={mission_id}
```
