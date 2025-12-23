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
├── main.py          # Entry point, bot setup
├── cogs/
│   ├── daily.py     # /daily command
│   └── weekly.py    # /weekly command
├── services/
│   └── database.py  # DB queries (asyncpg)
├── config.py        # Settings
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

### 4.3 Publication via Bot
- [ ] n8n appelle bot endpoint pour publier (optionnel)
- [ ] Bot poste dans chan #daily-news
- [ ] Update posted_to_discord = true

**Note:** La publication continue via webhook Discord existant. Le bot permet les queries à la demande.

---

## Phase 5: Workflow Weekly 🔲

### 5.1 Mission weekly
- [ ] missions/ai-news/weekly/mission.md
- [ ] missions/ai-news/weekly/analysis-rules.md
- [ ] missions/ai-news/weekly/output-schema.md

### 5.2 Endpoint /analyze-weekly
- [ ] claude-service: nouveau endpoint
- [ ] Params: mission, date_from, date_to, theme?
- [ ] Appel Claude CLI avec mission weekly
- [ ] Claude utilise MCP DB tools pour query articles

### 5.3 Workflow n8n weekly
- [ ] Cron Lundi 9h
- [ ] POST /analyze-weekly
- [ ] Callback ou direct publish

### 5.4 Stockage weekly_digest
- [x] DB model et submit tool ready
- [ ] Test end-to-end

---

## Phase 6: Callback System 🔲

### 6.1 Bot callback endpoint
- [ ] FastAPI mini dans bot (ou aiohttp)
- [ ] POST /callback route
- [ ] Correlation ID tracking (dict in-memory)

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
Phase 4 (Daily Étendu)       ████████░░  DONE (via Phase 2)
─────────────────────────────────────────────── MVP Ready
Phase 5 (Weekly)             ░░░░░░░░░░  TODO
Phase 6 (Callback)           ░░░░░░░░░░  TODO
Phase 7 (Polish)             ░░░░░░░░░░  TODO
```

## MVP Fonctionnel

Le MVP est **opérationnel** avec:

1. **PostgreSQL** pour stockage persistant
2. **MCP Tools** pour query/submit vers DB
3. **Discord Bot** avec `/daily` et `/weekly` (cache)
4. **Daily workflow** stocke articles et digests en DB

### Pour tester le MVP

```bash
# 1. Configurer .env (copier depuis .env.example)
cp .env.example .env
# Éditer avec vos valeurs

# 2. Démarrer les services
docker-compose up -d

# 3. Vérifier les logs
docker-compose logs -f

# 4. Tester le bot Discord
# - Inviter le bot sur votre serveur
# - Utiliser /daily ou /weekly
```

## Dépendances

```
Phase 2 requires Phase 1
Phase 3 requires Phase 1
Phase 4 requires Phase 1, 2
Phase 5 requires Phase 1, 2, 4
Phase 6 requires Phase 3, 5
Phase 7 requires all above
```
