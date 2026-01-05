# AI News Bot

Veille AI/ML automatisée : n8n → Claude → PostgreSQL → Discord

## Stack

| Service | Tech | Port |
|---------|------|------|
| Database | PostgreSQL 16 | 5433 |
| Orchestration | n8n | 5678 |
| Intelligence | FastAPI + Claude CLI + MCP | 8080 |
| Bot | discord.py + FastAPI | 8000 |

## Commandes

| Action | Commande |
|--------|----------|
| Dev | `docker-compose up -d` |
| Logs | `docker-compose logs -f claude-service` |
| Rebuild | `docker-compose up -d --build claude-service` |
| DB shell | `docker exec -it postgres psql -U ainews` |

## Flux

```
n8n cron 8h → RSS (7 feeds) → POST /summarize
  → Claude CLI agentic (MCP tools + WebSearch)
  → submit_digest → PostgreSQL
  → POST /publish → Discord embeds
```

## Endpoints

| Service | Endpoint | Usage |
|---------|----------|-------|
| claude-service | `POST /summarize` | Daily digest |
| claude-service | `POST /analyze-weekly` | Weekly digest |
| claude-service | `POST /check-urls` | Dedup URLs |
| discord-bot | `POST /publish` | Publie digest |

## Discord

| Commande | Effet |
|----------|-------|
| `/daily` | Dernier digest |
| `/daily date:2024-12-20` | Digest spécifique |
| `/weekly` | Weekly cached |
| `/weekly theme:openai` | Weekly thématique |
| `/status` | Health check |

## Conventions

- Layered: `api/` → `services/` → `repositories/`
- Fichiers < 300 lignes, fonctions < 30 lignes
- Type hints, async I/O, logging structuré
- Commits: `type(scope): desc` (anglais)

## Fichiers sensibles

Ne jamais commit: `.env`, `n8n-data/`, `logs/`, `*.credentials.json`

## Contextes

| Contexte | Chemin | Usage |
|----------|--------|-------|
| Dev local | `.claude/` | Cette doc |
| Production | `claude-service/config/CLAUDE.md` | Agent instructions |
| Missions | `claude-service/missions/` | Mission definitions |

## Documentation détaillée

- [Architecture](docs/ARCHITECTURE.md) - Structure, flux, composants
- [API](docs/API.md) - Endpoints, MCP tools, schemas
- [Database](docs/DATABASE.md) - Schema, migrations, queries

## Refactoring (2026-01)

- [Post-Refactoring Review](analysis/POST-REFACTORING-REVIEW.md) - État actuel après refactoring
- [Action Items](analysis/ACTION-ITEMS.md) - Améliorations restantes
- [Plans d'exécution](../../docs/plans/) - Phases 0-4 + cleanup
