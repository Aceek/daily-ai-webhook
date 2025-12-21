# AI News Bot - Configuration Claude Code

## Projet

Système automatisé de veille AI/ML : collecte, analyse et publication Discord.

**Type:** Automatisation/Intégration (non-application)

## Stack

| Composant | Tech |
|-----------|------|
| Orchestration | n8n (Docker) |
| Intelligence | Claude Code CLI |
| Messaging | Discord Webhook → Bot (Phase 2) |
| Config | Markdown (`config/`) |

## Architecture

```
daily-ai-webhook/
├── docker-compose.yml        # n8n + claude-service containers
├── claude-service/           # HTTP wrapper pour Claude CLI
│   ├── main.py               # FastAPI avec /summarize endpoint
│   ├── execution_logger.py   # Système de logs détaillés
│   ├── Dockerfile
│   └── config.yaml
├── config/                   # PRODUCTION: règles éditoriales
│   ├── rules.md
│   ├── sources.md
│   └── editorial-guide.md
├── logs/                     # Logs d'exécution (1 fichier/run, gitignored)
├── workflows/                # Exports n8n (backup)
└── bot/                      # Discord bot (Phase 2, Python)
```

**Séparation des contextes:**
- `.claude/` = Développement (toi + agents)
- `config/` = Production (n8n → Claude CLI automatisé)

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

### Markdown (config/)
- Structure cohérente entre fichiers
- Sections clairement délimitées
- Exemples concrets inclus

### Git
- Conventional Commits: `type(scope): description`
- Types: `feat`, `fix`, `refactor`, `docs`, `chore`
- Branches: `feature/`, `fix/`
- **Pas de mention Claude Code** dans les messages de commit

## Système de Logs

Chaque exécution du workflow génère des logs détaillés dans `logs/`.

### Fichiers générés

```
logs/
├── 2024-12-21_08-00-00_abc123.md    # Lisible (Markdown)
└── 2024-12-21_08-00-00_abc123.json  # Parsable (JSON)
```

### Contenu capturé

| Section | Description |
|---------|-------------|
| **Metadata** | ID, timestamp, status, durée, tokens, coût |
| **Timeline** | Événements Claude CLI (init, tool_use, result) |
| **Articles** | Liste des articles reçus |
| **Prompt** | Prompt complet envoyé à Claude |
| **Response** | Réponse générée |
| **Metrics** | Tokens in/out, coût USD, durée |

### Consulter les logs

```bash
# Dernier log
ls -t logs/*.md | head -1 | xargs cat

# Logs d'aujourd'hui
ls logs/$(date +%Y-%m-%d)*.md
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
