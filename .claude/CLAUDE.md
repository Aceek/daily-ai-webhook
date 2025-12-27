# AI News Bot

Système automatisé de veille AI/ML : n8n collecte → Claude analyse → PostgreSQL stocke → Discord publie.

## Stack

| Composant | Tech | Rôle |
|-----------|------|------|
| Database | PostgreSQL 16 | Stockage articles, digests, catégories |
| Orchestration | n8n (Docker) | Cron, RSS, merge, appel service |
| Intelligence | Claude Service (FastAPI) | Wrapper Claude CLI, MCP tools |
| Bot | discord.py + FastAPI | Commandes Discord + HTTP API publication |
| Output | Via Bot API | Publication automatique (n8n → bot → Discord) |

## Architecture

```
daily-ai-webhook/
├── docker-compose.yml           # postgres + n8n + claude-service + discord-bot
├── claude-service/
│   ├── main.py                  # FastAPI app init
│   ├── config.py                # Settings, VALID_MISSIONS
│   ├── models.py                # SQLModel: Mission, Category, Article, Digest
│   ├── database.py              # Async engine, session factory
│   ├── api/
│   │   ├── routes.py            # Route definitions
│   │   ├── handlers.py          # /summarize, /log-workflow, /check-urls
│   │   ├── models.py            # Pydantic request/response models
│   │   └── converters.py        # Data converters
│   ├── services/
│   │   ├── claude_service.py    # Claude CLI orchestration
│   │   ├── digest_service.py    # Digest file operations
│   │   └── prompt_builder.py    # Prompt construction
│   ├── repositories/
│   │   └── article_repository.py # URL deduplication queries
│   ├── loggers/
│   │   ├── execution_logger.py  # Per-execution logging
│   │   ├── workflow_logger.py   # n8n workflow logging
│   │   └── models.py            # Log data models
│   ├── formatters/
│   │   └── markdown_formatter.py # Summary/workflow MD generation
│   ├── utils/
│   │   └── execution_dir.py     # Execution directory management
│   ├── mcp/
│   │   ├── server.py            # MCP tools entry point
│   │   ├── models.py            # Pydantic models
│   │   ├── validators.py        # Input validation
│   │   ├── utils.py             # Helper functions
│   │   ├── logger.py            # MCPLogger
│   │   ├── repositories/        # DB queries (base, article, category, digest, stats)
│   │   └── services/            # Business logic (article_query, digest_submitter, weekly_digest)
│   ├── config/
│   │   ├── CLAUDE.md            # Instructions agent (production)
│   │   ├── .mcp.json            # Config MCP tools
│   │   └── agents/              # Sub-agents fact-checker, topic-diver
│   └── missions/
│       ├── _common/             # quality-rules, mcp-usage, research-template
│       └── ai-news/             # mission, selection, editorial, output-schema
├── bot/
│   ├── main.py                  # Discord bot + FastAPI entry point
│   ├── api.py                   # HTTP API endpoints (/publish, /health)
│   ├── config.py                # Bot configuration
│   ├── cogs/
│   │   ├── daily.py             # /daily command
│   │   ├── weekly.py            # /weekly command
│   │   └── admin.py             # /status, /stats commands
│   ├── services/
│   │   ├── models.py            # PublishRequest, DigestResult
│   │   ├── database.py          # Connection pool
│   │   ├── publisher.py         # Unified digest publication
│   │   ├── embed_builder.py     # Discord embed construction
│   │   ├── card_generator.py    # Image card generation
│   │   ├── image_renderer.py    # HTML to image rendering
│   │   ├── health_checker.py    # Health check utilities
│   │   ├── claude_client.py     # Claude API client
│   │   ├── command_logger.py    # Command logging
│   │   ├── formatters/          # Item formatting (item_formatter.py)
│   │   ├── repositories/        # DB queries (digest_repository.py)
│   │   └── utils/               # Helpers (date_utils.py)
│   └── Dockerfile
├── data/                        # articles.json (runtime)
└── logs/                        # Exécutions (gitignored)
```

**Contextes:** `.claude/` = dev local | `claude-service/` = production container

## Flux d'exécution

```
n8n (cron 8h) → RSS feeds → merge/dedup → POST /summarize
    ↓
claude-service: write articles.json → claude CLI (agentic)
    ↓
Claude: WebSearch + analyse → MCP submit_digest
    ↓
MCP: sauvegarde PostgreSQL (articles, catégories, digest) + digest.json
    ↓
n8n → POST http://discord-bot:8000/publish
    ↓
discord-bot: build embeds → Discord API → update posted_to_discord
    ↓
n8n → POST /log-workflow
    ↓
discord-bot: /daily, /weekly → query PostgreSQL → embeds
```

## MCP Tools

| Tool | Usage |
|------|-------|
| `get_categories` | Liste catégories existantes |
| `get_articles` | Query articles avec filtres |
| `get_article_stats` | Stats par période |
| `get_recent_headlines` | Titres récents (dédup) |
| `submit_digest` | Sauvegarde daily + articles en DB |
| `submit_weekly_digest` | Sauvegarde weekly en DB |

## Base de Données

```sql
missions (id PK, name, description)
categories (id PK, mission_id FK, name) UNIQUE(mission_id, name)
articles (id PK, mission_id FK, category_id FK, title, url UNIQUE, source, ...)
daily_digests (id PK, mission_id FK, date, content JSON) UNIQUE(mission_id, date)
weekly_digests (id PK, mission_id FK, week_start, week_end, content JSON)
```

## Logs (folder-per-execution)

```
logs/
├── YYYY-MM-DD/
│   └── HHMMSS_executionid/
│       ├── SUMMARY.md      # Vue rapide: status, pipeline, top stories
│       ├── digest.json     # Output structuré pour Discord
│       ├── research.md     # Document recherche Claude
│       ├── workflow.md     # Log n8n nodes
│       └── raw/timeline.json
└── latest -> symlink
```

## Variables Environnement

| Variable | Description |
|----------|-------------|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Auth PostgreSQL |
| `N8N_USER`, `N8N_PASSWORD` | Auth n8n |
| `DISCORD_WEBHOOK_URL` | Backup (non utilisé si bot disponible) |
| `DISCORD_TOKEN` | Bot interactif |
| `DISCORD_GUILD_ID` | Optionnel: sync rapide commands |
| `CLAUDE_MODEL` | sonnet (défaut) |
| `CLAUDE_TIMEOUT` | 600s |

## Commandes Discord

| Commande | Description |
|----------|-------------|
| `/daily` | Dernier daily digest |
| `/daily date:2024-12-20` | Daily spécifique |
| `/weekly` | Dernier weekly digest (cached) |
| `/weekly theme:openai` | Génère analyse thématique on-demand |
| `/weekly week_start:2024-12-16 week_end:2024-12-22` | Analyse période custom |
| `/status` | État des services (DB, Claude) |
| `/stats` | Statistiques articles/digests |

## Standards

**Architecture:**
- Layered: api/ → services/ → repositories/
- Fichiers < 300 lignes, fonctions < 30 lignes
- SoC: models/, services/, repositories/, utils/ séparés
- DRY: pas de code dupliqué

**Code:** Type hints, docstrings, logging structuré (pas print), async pour I/O
**Bash:** `set -euo pipefail`, variables quotées
**Docker:** Versions explicites, healthchecks
**Git:** Conventional commits `type(scope): desc`, pas de mention Claude Code

## Fichiers Sensibles

Ne jamais commit: `.env`, `*.credentials.json`, `n8n-data/`, `logs/`

## Documentation

- `.claude/missions/refactoring/roadmap.md` - Historique refactoring
- `.claude/missions/refactoring/VERIFICATION.md` - Rapport conformité
