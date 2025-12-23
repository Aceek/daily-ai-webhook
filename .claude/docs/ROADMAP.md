# Roadmap: AI News Bot v2

## Phase 1: Infrastructure DB

### 1.1 PostgreSQL Setup
- [ ] Ajouter postgres à docker-compose.yml
- [ ] Variables env (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB)
- [ ] Volume persistant postgres-data
- [ ] Healthcheck

### 1.2 SQLModel Setup
- [ ] Dépendances: sqlmodel, asyncpg, psycopg2-binary
- [ ] models.py: Mission, Category, Article, DailyDigest, WeeklyDigest
- [ ] database.py: engine async, session factory
- [ ] Migrations initiales (ou create_all pour MVP)

### 1.3 Intégration claude-service
- [ ] DATABASE_URL env var
- [ ] Connexion DB au startup
- [ ] CRUD basique categories, articles

---

## Phase 2: MCP DB Tools

### 2.1 Extension mcp/server.py
- [ ] Tool `get_categories(mission_id, date_from?, date_to?)`
- [ ] Tool `get_articles(mission_id, categories?, date_from?, date_to?, limit?)`
- [ ] Tool `get_article_stats(mission_id, date_from, date_to)`
- [ ] Connexion DB dans MCP server

### 2.2 Mise à jour submit tools
- [ ] `submit_daily_digest` → sauvegarde DB + fichier
- [ ] `submit_weekly_digest` → nouveau, sauvegarde DB
- [ ] Auto-création catégories si nouvelles

### 2.3 Mise à jour _common/mcp-usage.md
- [ ] Documentation nouveaux tools
- [ ] Exemples d'usage pour Claude

---

## Phase 3: Discord Bot Base

### 3.1 Structure bot/
```
bot/
├── main.py          # Entry point, bot setup
├── cogs/
│   ├── daily.py     # /daily command
│   ├── weekly.py    # /weekly command
│   └── admin.py     # /status, /health (futur)
├── services/
│   ├── database.py  # DB queries
│   └── n8n.py       # n8n webhook triggers
├── models.py        # Shared with claude-service ou import
├── config.py        # Settings
├── Dockerfile
└── requirements.txt
```

### 3.2 Setup Discord
- [ ] Dockerfile bot
- [ ] Ajouter à docker-compose.yml
- [ ] DISCORD_TOKEN env var
- [ ] Bot permissions (send messages, slash commands)
- [ ] Intents configuration

### 3.3 Commande /daily
- [ ] Slash command registration
- [ ] Query DB: dernier daily_digest pour mission
- [ ] Format embed Discord
- [ ] Retourne résultat

### 3.4 Commande /weekly (cache only)
- [ ] Query DB: dernier weekly_digest standard
- [ ] Format embed Discord
- [ ] Retourne résultat

---

## Phase 4: Workflow Daily Étendu

### 4.1 Stockage articles en DB
- [ ] Après analyse Claude, stocker articles sélectionnés
- [ ] Lier aux catégories (get_or_create)
- [ ] Lier au daily_digest généré

### 4.2 Stockage daily_digest
- [ ] submit_daily_digest sauvegarde en DB
- [ ] Champs: mission_id, date, content, generated_at

### 4.3 Publication via Bot
- [ ] n8n appelle bot (ou bot poll) pour publier
- [ ] Bot poste dans chan #daily-news
- [ ] Update posted_to_discord = true

---

## Phase 5: Workflow Weekly

### 5.1 Mission weekly
- [ ] missions/ai-news/weekly/mission.md
- [ ] missions/ai-news/weekly/analysis-rules.md
- [ ] missions/ai-news/weekly/output-schema.md

### 5.2 Endpoint /analyze-weekly
- [ ] claude-service: nouveau endpoint
- [ ] Params: mission, date_from, date_to, theme?
- [ ] Appel Claude CLI avec mission weekly
- [ ] Claude utilise MCP DB tools

### 5.3 Workflow n8n weekly
- [ ] Cron Lundi 9h
- [ ] POST /analyze-weekly
- [ ] Callback ou direct publish

### 5.4 Stockage weekly_digest
- [ ] DB: week_start, week_end, content, is_standard=true
- [ ] Lien avec articles analysés (optionnel)

---

## Phase 6: Callback System

### 6.1 Bot callback endpoint
- [ ] FastAPI mini dans bot (ou Flask)
- [ ] POST /callback route
- [ ] Correlation ID tracking (dict in-memory ou Redis futur)

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

## Phase 7: Polish & Extensions

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

## Ordre d'Implémentation Recommandé

```
Phase 1 (Infrastructure)     ████████░░  Critique
Phase 2 (MCP DB)             ████████░░  Critique
Phase 3 (Bot Base)           ██████░░░░  Core feature
Phase 4 (Daily Étendu)       ██████░░░░  Core feature
Phase 5 (Weekly)             ████░░░░░░  Nouvelle feature
Phase 6 (Callback)           ████░░░░░░  Pour commandes async
Phase 7 (Polish)             ██░░░░░░░░  Nice to have
```

## MVP Minimal

Pour un premier déploiement fonctionnel:
1. Phase 1.1-1.2 (DB setup)
2. Phase 2.1-2.2 (MCP tools)
3. Phase 3.1-3.4 (Bot + /daily + /weekly cache)
4. Phase 4 (Daily stocke en DB)

= Bot fonctionnel avec /daily et /weekly qui retournent les caches.

## Dépendances

```
Phase 2 requires Phase 1
Phase 3 requires Phase 1
Phase 4 requires Phase 1, 2
Phase 5 requires Phase 1, 2, 4
Phase 6 requires Phase 3, 5
Phase 7 requires all above
```
