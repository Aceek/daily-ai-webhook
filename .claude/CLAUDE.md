# AI News Bot - Configuration Claude Code

## Projet

Système automatisé de veille AI/ML : collecte, analyse et publication Discord.

**Type:** Automatisation/Intégration (non-application)

## Stack

| Composant | Tech |
|-----------|------|
| Orchestration | n8n (Docker) |
| Intelligence | Claude Code CLI (agentic mode) |
| Messaging | Discord Webhook → Bot (Phase 2) |
| Config | Markdown (`claude-config/`) |

## Architecture

```
daily-ai-webhook/
├── docker-compose.yml        # n8n + claude-service containers
├── claude-service/           # HTTP wrapper pour Claude CLI
│   ├── main.py               # FastAPI avec /summarize endpoint
│   ├── execution_logger.py   # Système de logs détaillés
│   ├── entrypoint.sh         # Setup permissions et copie config
│   └── Dockerfile
├── claude-config/            # Config Claude CLI (monté read-only)
│   ├── CLAUDE.md             # Instructions agent principal
│   ├── .credentials.json     # Auth Anthropic (gitignored)
│   ├── agents/               # Sub-agents (fact-checker, topic-diver)
│   └── docs/                 # Schémas et guides éditoriaux
├── logs/                     # Logs d'exécution (gitignored)
│   ├── research/             # Documents de recherche générés
│   └── workflows/            # Logs workflow n8n
├── workflows/                # Exports n8n (backup)
└── bot/                      # Discord bot (Phase 2, Python)
```

**Séparation des contextes:**
- `.claude/` = Développement (Claude Code local)
- `claude-config/` = Production (Claude CLI dans Docker)

## Standards

### Bash/Scripts
- Shebang explicite (`#!/bin/bash`)
- Variables quotées (`"$VAR"`)
- `set -euo pipefail` en début de script
- Commentaires pour sections complexes

### Docker/Compose
- Versions explicites des images
- Healthchecks configurés
- Variables sensibles dans `.env` (jamais commit)

### Python (Bot Phase 2)
- Type hints obligatoires
- Docstrings pour fonctions publiques
- async/await pour discord.py
- Logging structuré (pas de print)

### Markdown (claude-config/)
- Structure cohérente entre fichiers
- Sections clairement délimitées
- Exemples concrets inclus

### Git
- Conventional Commits: `type(scope): description`
- Types: `feat`, `fix`, `refactor`, `docs`, `chore`
- Branches: `feature/`, `fix/`
- **Pas de mention Claude Code** dans les messages de commit

## Système de Logs

Deux types de logs sont générés pour chaque exécution du workflow.

### Structure des fichiers

```
logs/
├── 2024-12-21_08-00-00_abc123.md       # Log Claude (Markdown)
├── 2024-12-21_08-00-00_abc123.json     # Log Claude (JSON)
└── workflows/
    ├── 2024-12-21_08-00-00_wf-xxx.md   # Log Workflow (Markdown)
    └── 2024-12-21_08-00-00_wf-xxx.json # Log Workflow (JSON)
```

### Logs Claude (logs/)

Capturent l'exécution de Claude CLI via `/summarize`.

| Section | Description |
|---------|-------------|
| **Metadata** | ID, timestamp, status, durée, tokens, coût |
| **Timeline** | Événements Claude CLI (init, tool_use, result) |
| **Articles** | Liste des articles reçus |
| **Prompt** | Prompt complet envoyé à Claude |
| **Response** | Réponse générée |
| **Metrics** | Tokens in/out, coût USD, durée |
| **workflow_execution_id** | ID du workflow parent (corrélation) |

### Logs Workflow (logs/workflows/)

Capturent l'exécution du workflow n8n (succès ET échecs).

| Champ | Description |
|-------|-------------|
| **workflow_execution_id** | ID unique de l'exécution (format: `wf-{timestamp}-{random}`) |
| **workflow_name** | Nom du workflow n8n |
| **started_at** | Timestamp de début (ISO) |
| **finished_at** | Timestamp de fin (ISO) |
| **duration_seconds** | Durée totale de l'exécution |
| **status** | `success` ou `error` |
| **error_message** | Message d'erreur (si échec) |
| **error_node** | Node qui a échoué (si échec) |
| **nodes_executed** | Liste des nodes exécutés avec leur status |
| **articles_count** | Nombre d'articles traités |
| **claude_execution_id** | ID du log Claude correspondant (corrélation) |
| **discord_sent** | Boolean indiquant si le message Discord a été envoyé |

### Corrélation bidirectionnelle

Les logs sont liés par des IDs croisés :
- **Workflow log** contient `claude_execution_id` -> pointe vers le log Claude
- **Claude log** contient `workflow_execution_id` -> pointe vers le log Workflow

Cela permet de naviguer entre les deux types de logs pour une même exécution.

### Consulter les logs

```bash
# Dernier log Claude
ls -t logs/*.md | head -1 | xargs cat

# Logs Claude d'aujourd'hui
ls logs/$(date +%Y-%m-%d)*.md

# Dernier log workflow
ls -t logs/workflows/*.md | head -1 | xargs cat

# Workflows en erreur
grep -l '"status": "error"' logs/workflows/*.json

# Corrélation : trouver le log Claude d'un workflow
cat logs/workflows/2024-12-21_*.json | jq '.claude_execution_id'

# Corrélation : trouver le log workflow d'un log Claude
cat logs/2024-12-21_*.json | jq '.workflow_execution_id'
```

### Note

Les logs sont gitignored (données locales uniquement).

## Workflow Agentique

### Pour chaque feature:

```
1. DISCUSSION   → Analyse détaillée avec utilisateur
2. PLANNER      → Plan d'implémentation (.claude/plans/)
3. IMPLEMENTER  → Implémentation par étapes
4. REVIEWER     → Review avant commit
```

### Tâches simples (< 30min, < 3 fichiers):
Chat direct sans workflow complet.

## Phases Projet

| Phase | Statut | Description |
|-------|--------|-------------|
| MVP | ✅ TERMINÉ | n8n + 3 RSS + Claude CLI + Discord webhook + Logs |
| Enrichissement | - | Reddit, HN, embeds améliorés |
| Bot | - | discord.py, commandes slash |

## Docs Référence

- **Vision complète:** `docs/VISION.md`
- **Architecture n8n:** `.claude/docs/architecture.md`
- **Composants:** `.claude/docs/components.md`

## Fichiers Sensibles

Ne jamais commit: `.env`, `*.credentials.json`, `n8n-data/`, `logs/*`
