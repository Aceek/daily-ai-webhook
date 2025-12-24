# Roadmap: AI News Bot v2

## Phase 1: Infrastructure DB ✅

### 1.1 PostgreSQL Setup ✅
- [x] Ajouter postgres à docker-compose.yml
- [x] Variables env (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)
- [x] Volume persistant postgres-data
- [x] Healthcheck

### 1.2 SQLModel Setup ✅
- [x] Dépendances: sqlmodel, asyncpg, psycopg2-binary
- [x] models.py: Mission, Category, Article, DailyDigest, WeeklyDigest
- [x] database.py: engine async, session factory
- [x] Migrations initiales (create_all au startup)

### 1.3 Intégration claude-service ✅
- [x] DATABASE_URL env var
- [x] Connexion DB au startup (lifespan)
- [x] Auto-seed mission 'ai-news'

**Commit:** `feat(db): add PostgreSQL infrastructure with SQLModel`

---

## Phase 2: MCP DB Tools ✅

### 2.1 Extension mcp/server.py ✅
- [x] Tool `get_categories(mission_id, date_from?, date_to?)`
- [x] Tool `get_articles(mission_id, categories?, date_from?, date_to?, limit?)`
- [x] Tool `get_article_stats(mission_id, date_from, date_to)`
- [x] Connexion DB dans MCP server (psycopg2 sync)

### 2.2 Mise à jour submit tools ✅
- [x] `submit_digest` → sauvegarde DB + fichier
- [x] `submit_weekly_digest` → nouveau, sauvegarde DB
- [x] Auto-création catégories si nouvelles (get_or_create)

### 2.3 Mise à jour documentation ✅
- [x] _common/mcp-usage.md avec tous les tools
- [x] Exemples d'usage pour Claude
- [x] allowed_tools mis à jour dans main.py

**Commit:** `feat(mcp): add database query and submit tools`

---

## Phase 3: Discord Bot Base ✅

### 3.1 Structure bot/ ✅
```
bot/
├── main.py              # Entry point (discord.py + FastAPI)
├── api.py               # HTTP API endpoints
├── config.py            # Settings
├── cogs/
│   ├── daily.py         # /daily command
│   └── weekly.py        # /weekly command
├── services/
│   ├── database.py      # DB queries (asyncpg)
│   └── publisher.py     # Digest publication logic
├── Dockerfile
└── requirements.txt
```

### 3.2 Setup Discord ✅
- [x] Dockerfile bot
- [x] Ajouter à docker-compose.yml
- [x] DISCORD_TOKEN env var
- [x] Intents configuration

### 3.3 Commande /daily ✅
- [x] Slash command registration
- [x] Query DB: dernier daily_digest pour mission
- [x] Format embed Discord
- [x] Support date optionnelle

### 3.4 Commande /weekly (cache only) ✅
- [x] Query DB: dernier weekly_digest standard
- [x] Format embed Discord avec trends et top stories

**Commit:** `feat(bot): add Discord bot with /daily and /weekly commands`

---

## Phase 4: Workflow Daily Étendu ✅ (via Phase 2)

### 4.1 Stockage articles en DB ✅
- [x] Après analyse Claude, stocker articles sélectionnés (via submit_digest)
- [x] Lier aux catégories (get_or_create pattern)
- [x] Lier au daily_digest généré

### 4.2 Stockage daily_digest ✅
- [x] submit_digest sauvegarde en DB avec ON CONFLICT
- [x] Champs: mission_id, date, content JSON, generated_at

### 4.3 Publication via Bot ✅
- [x] Bot HTTP API (FastAPI + uvicorn alongside discord.py)
- [x] Endpoints: POST /publish, POST /callback, GET /health
- [x] Publisher service with embed building logic
- [x] n8n workflow updated to POST to `http://discord-bot:8000/publish`
- [x] Update posted_to_discord = true after successful publication
- [x] Docker healthcheck on bot API

**Commit:** `feat(bot): add HTTP API for digest publication`

**Architecture:**
```
n8n ────────────────┐
                    │  POST http://discord-bot:8000/publish
                    ▼
claude-service ───► discord-bot:8000 ───► Discord API
                         │
                         └─► UPDATE posted_to_discord = true
```

---

## Phase 4.5: Reliability & Observability ✅

### 4.5.1 MCP Environment Fix ✅
- [x] Workaround bug Claude Code #1254 (env vars non passées aux subprocess MCP)
- [x] Créé `mcp/run_server.sh` - wrapper bash héritant l'environnement parent
- [x] Installation dans `/usr/local/bin/mcp-run-server` (hors volume mount)
- [x] Mise à jour `.mcp.json` pour utiliser le wrapper

### 4.5.2 DB Constraints Fix ✅
- [x] Fix INSERT daily_digests (ajout `posted_to_discord=False`)
- [x] Fix INSERT categories (ajout `created_at`)
- [x] Fix INSERT articles (ajout `created_at`)
- [x] Fix INSERT weekly_digests (ajout `posted_to_discord=False`)

### 4.5.3 MCP Structured Logging ✅
- [x] Classe `MCPLogger` avec niveaux (INFO, OK, ERROR, WARN, OP)
- [x] Écriture vers `mcp.log` dans dossier exécution
- [x] Tracking opérations DB avec statut (✓/✗)
- [x] Erreurs détaillées dans réponse MCP (`db_error`, `operations`)

### 4.5.4 Pipeline Status Updates ✅
- [x] SUMMARY.md mis à jour après publication Discord
- [x] Référence `mcp.log` ajoutée dans SUMMARY.md

**Commits:**
- `fix(mcp): resolve DB save failures and add structured logging`
- `fix(mcp): add created_at to categories and articles INSERT statements`
- `fix(logs): update Pipeline Discord status in SUMMARY.md after publication`

---

## Phase 5: Workflow Weekly ✅

### 5.1 Mission weekly ✅
- [x] missions/ai-news/weekly/mission.md
- [x] missions/ai-news/weekly/analysis-rules.md
- [x] missions/ai-news/weekly/output-schema.md

### 5.2 Endpoint /analyze-weekly ✅
- [x] claude-service: nouveau endpoint
- [x] Params: mission, week_start, week_end, theme
- [x] Appel Claude CLI avec mission weekly
- [x] Claude utilise MCP DB tools pour query articles
- [x] validate_weekly_mission() pour vérifier fichiers

### 5.3 Workflow n8n weekly ✅
- [x] Cron Lundi 9h (Europe/Paris)
- [x] Calcul dates semaine précédente (Mon-Sun)
- [x] POST /analyze-weekly
- [x] Format Bot Payload pour weekly
- [x] Publish via Bot (type: weekly)
- [x] Error handling avec Error Trigger

### 5.4 Stockage weekly_digest ✅
- [x] DB model et submit tool ready (Phase 2)
- [x] Intégration end-to-end

**Commits:**
- `feat(weekly): add weekly mission files for ai-news`
- `feat(weekly): add /analyze-weekly endpoint for weekly digest generation`
- `feat(weekly): add n8n workflow for weekly digest generation`

---

## Phase 6: Callback System 🔶

### 6.1 Bot callback endpoint ✅
- [x] FastAPI intégré dans bot (avec discord.py)
- [x] POST /callback route
- [x] Correlation ID tracking (dict in-memory)

**Note:** Endpoint prêt via Phase 4.3, reste à intégrer avec n8n.

### 6.2 Intégration n8n
- [ ] Workflow envoie callback en fin
- [ ] Payload: {correlation_id, status, result}

### 6.3 /weekly --theme (async)
- [ ] Parse args (theme, from, to)
- [ ] Génère correlation_id
- [ ] Répond "⏳ Génération..."
- [ ] Trigger n8n webhook avec params
- [ ] Attend callback
- [ ] Edit message avec résultat

---

## Phase 7: Polish & Extensions 🔲

### 7.1 Catégories intelligentes
- [ ] Claude reçoit catégories existantes avant chaque analyse
- [ ] Test: nouvelles catégories créées correctement
- [ ] Test: réutilisation catégories existantes

### 7.2 Commande /ask (futur)
- [ ] Question libre sur articles DB
- [ ] Claude query intelligent
- [ ] Réponse formatée

### 7.3 Admin commands
- [ ] /status - état des services
- [ ] /stats - metrics (articles count, digests count)
- [ ] /force-daily - trigger manuel

### 7.4 Multi-channel
- [ ] Config channels par mission
- [ ] #ai-news-daily, #ai-news-weekly
- [ ] Futur: autres missions, autres channels

---

## État Actuel

```
Phase 1 (Infrastructure)     ██████████  DONE
Phase 2 (MCP DB)             ██████████  DONE
Phase 3 (Bot Base)           ██████████  DONE
Phase 4 (Daily Étendu)       ██████████  DONE (incl. Bot as Hub)
Phase 4.5 (Reliability)      ██████████  DONE (MCP logging, DB fixes)
Phase 5 (Weekly)             ██████████  DONE (endpoint + workflow + mission)
─────────────────────────────────────────────── Feature Complete
Phase 6 (Callback)           ██░░░░░░░░  PARTIAL (/callback endpoint ready)
Phase 7 (Polish)             ░░░░░░░░░░  TODO
```

## MVP Fonctionnel

Le MVP est **opérationnel** avec:

1. **PostgreSQL** pour stockage persistant
2. **MCP Tools** pour query/submit vers DB
3. **Discord Bot** avec `/daily` et `/weekly` commands
4. **Daily workflow** collecte RSS → Claude → DB → Discord
5. **Weekly workflow** analyse DB → Claude → trends → Discord
6. **Bot HTTP API** pour publication centralisée (n8n → bot → Discord)
7. **MCP Logging** pour observabilité des opérations DB

### Structure Logs

```
logs/YYYY-MM-DD/HHMMSS_execid/
├── SUMMARY.md       # Vue rapide: status, pipeline, top stories
├── mcp.log          # Log structuré opérations MCP (Phase 4.5)
├── digest.json      # Output structuré pour Discord
├── research.md      # Document recherche Claude
├── workflow.md      # Log n8n nodes
└── raw/timeline.json
```

### Ports exposés

| Service | Port | Usage |
|---------|------|-------|
| PostgreSQL | 5432 | Database |
| n8n | 5678 | Workflow UI |
| claude-service | 8080 | Claude API |
| discord-bot | 8000 | Publication API |

### Pour tester le MVP

```bash
# 1. Configurer .env (copier depuis .env.example)
cp .env.example .env
# Éditer avec vos valeurs

# 2. Démarrer les services
docker-compose up -d

# 3. Vérifier les services
curl http://localhost:8080/health  # claude-service
curl http://localhost:8000/health  # discord-bot

# 4. Tester le bot Discord
# - Inviter le bot sur votre serveur
# - Utiliser /daily ou /weekly
```

## Dépendances

```
Phase 2 requires Phase 1
Phase 3 requires Phase 1
Phase 4 requires Phase 1, 2
Phase 4.5 requires Phase 4
Phase 5 requires Phase 1, 2, 4, 4.5
Phase 6 requires Phase 3, 5
Phase 7 requires all above
```

---

## Notes Techniques

### Bug Claude Code #1254: MCP Environment Variables

**Problème:** Les variables `env` définies dans `.mcp.json` ne sont pas passées aux subprocess MCP par Claude CLI.

```json
// .mcp.json - les env vars ne fonctionnent PAS
{
  "mcpServers": {
    "db-tools": {
      "command": "python",
      "args": ["mcp/server.py"],
      "env": {
        "DATABASE_URL": "..."  // ❌ Non passé au subprocess
      }
    }
  }
}
```

**Workaround:** Wrapper bash qui hérite l'environnement parent.

```bash
# mcp/run_server.sh
#!/bin/bash
exec python /app/mcp/server.py "$@"
```

```json
// .mcp.json - utilise le wrapper
{
  "mcpServers": {
    "db-tools": {
      "command": "/usr/local/bin/mcp-run-server"
    }
  }
}
```

**Important:** Le wrapper doit être dans un path non affecté par les volume mounts Docker (`/usr/local/bin/` et non `/app/mcp/`).

**Référence:** https://github.com/anthropics/claude-code/issues/1254
