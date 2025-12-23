# AI News Bot

Système automatisé de veille AI/ML : n8n collecte → Claude analyse → Discord publie.

## Stack

| Composant | Tech | Rôle |
|-----------|------|------|
| Orchestration | n8n (Docker) | Cron, RSS, merge, appel service |
| Intelligence | Claude Service (FastAPI) | Wrapper Claude CLI, logs |
| Output | Discord Webhook | Publication digest |

## Architecture

```
daily-ai-webhook/
├── docker-compose.yml        # n8n + claude-service
├── claude-service/
│   ├── main.py               # FastAPI /summarize, /log-workflow
│   ├── execution_logger.py   # Logs folder-per-execution
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── config/
│   │   ├── CLAUDE.md         # Instructions agent (production)
│   │   ├── .mcp.json         # Config MCP submit_digest
│   │   └── agents/           # Sub-agents fact-checker, topic-diver
│   ├── mcp/server.py         # MCP submit_digest tool
│   └── missions/
│       ├── _common/          # Règles partagées
│       └── ai-news/          # Mission: selection, editorial, output-schema
├── data/                     # articles.json (runtime)
├── logs/                     # Exécutions (gitignored)
└── bot/                      # Discord bot (Phase 2)
```

**Contextes:** `.claude/` = dev local | `claude-service/` = production container

## Flux d'exécution

```
n8n (cron 8h) → RSS feeds → merge/dedup → POST /summarize
    ↓
claude-service: write articles.json → claude CLI (agentic) → read digest.json
    ↓
n8n → format embeds → Discord webhook → POST /log-workflow
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

**Consulter:**
```bash
cat logs/latest/SUMMARY.md              # Dernière exécution
ls logs/$(date +%Y-%m-%d)/              # Exécutions du jour
grep -l "FAILED" logs/*/SUMMARY.md      # Échecs
```

## Variables Environnement

| Variable | Description |
|----------|-------------|
| `N8N_USER`, `N8N_PASSWORD` | Auth n8n |
| `DISCORD_WEBHOOK_URL` | Publication |
| `CLAUDE_MODEL` | sonnet (défaut) |
| `CLAUDE_TIMEOUT` | 600s |

## Standards

**Code:** Type hints, docstrings, logging structuré (pas print), async pour I/O
**Bash:** `set -euo pipefail`, variables quotées
**Docker:** Versions explicites, healthchecks
**Git:** Conventional commits `type(scope): desc`, pas de mention Claude Code

## Fichiers Sensibles

Ne jamais commit: `.env`, `*.credentials.json`, `n8n-data/`, `logs/`
