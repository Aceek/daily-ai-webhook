# Vision: AI News Bot v2

## Overview

Bot Discord interactif + automations n8n + Claude agentic + PostgreSQL.

## Architecture

```
discord-bot ←→ n8n ←→ claude-service ←→ PostgreSQL
     ↑                      ↑
     └──── callback ────────┘
```

### Containers (docker-compose)

| Service | Tech | Rôle |
|---------|------|------|
| postgres | PostgreSQL 16 | Stockage persistant |
| n8n | n8n 2.0.3 | Crons, RSS, orchestration workflows |
| claude-service | FastAPI + Claude CLI | Analyse agentic, MCP tools |
| discord-bot | discord.py | Commandes, publication, callback endpoint |

## Base de Données

### Schéma

```sql
missions (id PK string, name, description, created_at)

categories (id PK, mission_id FK, name, created_at)
  UNIQUE(mission_id, name)

articles (id PK, mission_id FK, category_id FK, title, url, source,
          description, pub_date, digest_id FK nullable, created_at)

daily_digests (id PK, mission_id FK, date UNIQUE/mission, content JSON,
               generated_at, posted_to_discord bool)

weekly_digests (id PK, mission_id FK, week_start, week_end, params JSON,
                content JSON, generated_at, is_standard bool)
```

### Catégories Dynamiques

- Liées à mission_id (multi-mission ready)
- Claude reçoit catégories existantes via MCP avant analyse
- Réutilise existantes, crée nouvelles si nécessaire
- `get_or_create(mission, name)` côté DB

## Discord Bot

### Commandes

| Commande | Action | Async |
|----------|--------|-------|
| `/daily` | Retourne dernier daily (DB cache) | Non |
| `/weekly` | Retourne dernier weekly standard (DB cache) | Non |
| `/weekly --theme X` | Génère analyse custom | Oui |
| `/weekly --from --to` | Analyse période custom | Oui |
| `/ask "question"` | Question libre sur DB (futur) | Oui |

### Publication Auto

- Chan dédié #daily-news pour daily
- Chan dédié #weekly-digest pour weekly
- Bot poste proactivement via crons n8n

### Callback Endpoint

```
POST /callback
Body: {correlation_id, result, status}
```

Bot expose HTTP pour recevoir résultats async de n8n/claude-service.

## Workflows n8n

### Daily (existant, étendu)

```
Cron 8h → RSS feeds → merge → POST /summarize
       → Store DB (articles + digest)
       → POST Discord via bot
```

### Weekly (nouveau)

```
Cron Lundi 9h → POST /analyze-weekly
             → Claude + MCP (query DB, analyse patterns)
             → Store DB (weekly_digest)
             → POST Discord via bot
```

### Webhook Triggers

Bot peut trigger workflows n8n via webhook pour commandes custom:
```
/weekly --theme X → Bot POST n8n webhook → workflow → callback bot
```

## MCP Tools (serveur unifié)

### Existants
- `submit_digest(execution_id, headlines, research, industry, watching, metadata)`

### Nouveaux DB Query
```python
get_categories(mission_id, date_from?, date_to?) → list[str]
get_articles(mission_id, categories?, date_from?, date_to?, limit?) → list[dict]
get_article_stats(mission_id, date_from, date_to) → dict
```

### Nouveaux Submit
```python
submit_daily_digest(execution_id, mission_id, date, ...) → confirmation
submit_weekly_digest(execution_id, mission_id, week_start, ...) → confirmation
```

### Usage Claude

1. `get_categories()` → voir existantes
2. Raisonner sur demande user (thème vague → catégories précises)
3. `get_articles()` → récupérer données
4. Analyser, détecter patterns
5. `submit_weekly_digest()` → sauvegarder

## Missions

### Structure

```
missions/
├── _common/
│   ├── quality-rules.md
│   ├── research-template.md
│   └── mcp-usage.md (étendre avec DB tools)
├── ai-news/
│   ├── mission.md
│   ├── selection-rules.md
│   ├── editorial-guide.md
│   ├── output-schema.md
│   └── weekly/
│       ├── mission.md
│       ├── analysis-rules.md
│       └── output-schema.md
```

### Multi-Mission Ready

- Chaque mission = folder isolé
- Catégories scopées par mission
- Articles scopés par mission
- Digests scopés par mission

## Communication Async

### Flow Commande Custom

```
1. User: /weekly --theme "openai"
2. Bot: génère correlation_id, répond "⏳ Génération..."
3. Bot: POST n8n webhook {correlation_id, mission, params}
4. n8n: workflow → claude-service
5. Claude: MCP get_categories → raisonne → get_articles → analyse
6. Claude: submit_weekly_digest
7. claude-service: POST callback bot {correlation_id, result}
8. Bot: édite message Discord avec résultat
```

## Stockage Résultats

| Type | Stocker | Raison |
|------|---------|--------|
| Daily standard | Oui | Référence quotidienne |
| Weekly standard | Oui | Référence hebdo |
| Weekly --theme | Optionnel | Réutilisable si redemandé |
| Weekly --dates custom | Non | One-shot |

## Tech Stack Final

| Composant | Choix |
|-----------|-------|
| Bot | discord.py |
| ORM | SQLModel |
| DB | PostgreSQL 16 |
| Async pattern | Callback webhook |
| MCP | Serveur unifié |
| Crons | n8n conservé |

## Ce qui ne change pas

- Logs folder-per-execution
- Format digest (headlines, research, industry, watching)
- Architecture agentic Claude CLI
- Système missions existant
