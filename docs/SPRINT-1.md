# Sprint 1 - MVP Fondations

> **Objectif:** Système fonctionnel de bout en bout : collecte RSS → analyse Claude → publication Discord

---

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                      SPRINT 1 - MVP                         │
│                                                             │
│  [n8n Docker] → [3 RSS Feeds] → [Claude CLI] → [Discord]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Critère de succès:** Recevoir un résumé AI quotidien sur Discord à 8h.

---

## Étapes

### 1.1 Structure du projet

Créer l'arborescence complète :

```
daily-ai-webhook/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── config/
│   ├── rules.md
│   ├── sources.md
│   └── editorial-guide.md
├── scripts/
│   └── summarize.sh
├── workflows/
│   └── .gitkeep
├── n8n-data/
│   └── .gitkeep
└── bot/
    └── .gitkeep
```

**Livrables:**
- [ ] Dossiers créés
- [ ] `.gitignore` configuré (exclut `.env`, `n8n-data/`)
- [ ] `.env.example` avec variables requises

---

### 1.2 Docker + n8n

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: ai-news-n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - GENERIC_TIMEZONE=Europe/Paris
      - TZ=Europe/Paris
    volumes:
      - ./n8n-data:/home/node/.n8n
      - ./config:/home/node/config:ro
      - ./scripts:/home/node/scripts:ro
```

**Livrables:**
- [ ] `docker-compose.yml` créé
- [ ] n8n accessible sur `http://localhost:5678`
- [ ] Authentification fonctionnelle

---

### 1.3 Webhook Discord

1. Discord → Serveur → Paramètres du channel
2. Intégrations → Webhooks → Nouveau webhook
3. Nommer "AI News Bot"
4. Copier l'URL → `.env`

**Test manuel:**
```bash
curl -X POST "$DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test webhook AI News Bot"}'
```

**Livrables:**
- [ ] Webhook créé sur Discord
- [ ] URL stockée dans `.env`
- [ ] Test curl réussi

---

### 1.4 Fichiers de configuration

#### config/rules.md
```markdown
# Règles de Sélection

## Priorité Haute
- Annonces labs majeurs (Anthropic, OpenAI, Google, Meta, Mistral)
- Nouvelles releases de modèles
- Papers avec impact significatif
- Régulations AI

## Priorité Moyenne
- Tutoriels populaires (>500 upvotes)
- Nouvelles fonctionnalités outils existants

## À Exclure
- Contenus promotionnels sans substance
- Rumeurs non sourcées
- Doublons
- Contenus > 48h
```

#### config/sources.md
```markdown
# Sources Actives

## RSS Feeds (Phase 1)
- https://www.anthropic.com/feed.xml
- https://openai.com/blog/rss/
- https://huggingface.co/blog/feed.xml
```

#### config/editorial-guide.md
```markdown
# Guide Éditorial

## Langue
Anglais

## Format
🔥 **TOP HEADLINES**
[2-3 actualités majeures, 1-2 phrases chacune]

📊 **INDUSTRY**
[Si pertinent]

💡 **WORTH WATCHING**
[Si pertinent]

## Règles
- Max 2000 caractères
- Source entre parenthèses
- Ton factuel, pas d'opinions
```

**Livrables:**
- [ ] `config/rules.md`
- [ ] `config/sources.md`
- [ ] `config/editorial-guide.md`

---

### 1.5 Workflow n8n

Créer le workflow avec les nodes suivants :

```
[Schedule Trigger] → [RSS Feed x3] → [Merge] → [Code: Dedup] → [Code: Format] → [HTTP: Discord]
                                                                      ↑
                                                            (Phase 1.6: Claude CLI)
```

**Nodes à configurer:**

| Node | Config |
|------|--------|
| Schedule Trigger | Cron: `0 8 * * *` (8h daily) |
| RSS Feed #1 | Anthropic blog |
| RSS Feed #2 | OpenAI blog |
| RSS Feed #3 | Hugging Face blog |
| Merge | Mode: Append |
| Code (Dedup) | JS: filtrer doublons par URL |
| Code (Format) | JS: formater pour Claude |

**Livrables:**
- [ ] Workflow créé dans n8n
- [ ] 3 sources RSS configurées
- [ ] Merge et dedup fonctionnels
- [ ] Export JSON dans `workflows/`

---

### 1.6 Intégration Claude Code

#### scripts/summarize.sh
```bash
#!/bin/bash
set -euo pipefail

ARTICLES_FILE="$1"
CONFIG_DIR="/home/node/config"

claude -p "
You are an AI/ML news editor.

=== SELECTION RULES ===
$(cat "$CONFIG_DIR/rules.md")

=== EDITORIAL GUIDELINES ===
$(cat "$CONFIG_DIR/editorial-guide.md")

=== ARTICLES ===
$(cat "$ARTICLES_FILE")

=== INSTRUCTIONS ===
1. Analyze articles according to selection rules
2. Write summary following editorial guidelines exactly
3. Output ONLY the formatted summary
"
```

**Dans n8n:**
- Node "Execute Command"
- Command: `/home/node/scripts/summarize.sh /tmp/articles.json`

**Livrables:**
- [ ] `scripts/summarize.sh` créé et exécutable
- [ ] Node Execute Command configuré
- [ ] Test manuel réussi

---

### 1.7 Test complet manuel

1. Déclencher le workflow manuellement dans n8n
2. Vérifier chaque étape :
   - RSS récupérés ?
   - Articles mergés ?
   - Dedup fonctionne ?
   - Claude génère un résumé ?
   - Discord reçoit le message ?

**Debug checklist:**
- [ ] Logs n8n sans erreurs
- [ ] Output Claude cohérent
- [ ] Message Discord bien formaté

---

### 1.8 Cron production

1. Activer le workflow dans n8n
2. Configurer le trigger sur 8h
3. Attendre le lendemain matin
4. Vérifier Discord

**Livrables:**
- [ ] Workflow activé
- [ ] Premier résumé automatique reçu
- [ ] MVP validé ✅

---

## Checklist finale Sprint 1

| Étape | Statut |
|-------|--------|
| 1.1 Structure projet | ⬜ |
| 1.2 Docker + n8n | ⬜ |
| 1.3 Webhook Discord | ⬜ |
| 1.4 Fichiers config | ⬜ |
| 1.5 Workflow n8n | ⬜ |
| 1.6 Intégration Claude | ⬜ |
| 1.7 Test manuel | ⬜ |
| 1.8 Cron production | ⬜ |

---

## Risques Sprint 1

| Risque | Mitigation |
|--------|------------|
| RSS feeds indisponibles | Avoir 3+ sources, retry policy |
| Claude CLI timeout | Timeout n8n à 5min |
| Discord rate limit | 1 message/jour = OK |

---

## Prochaines étapes (Sprint 2)

- Ajouter Reddit comme source
- Ajouter Hacker News
- Améliorer embeds Discord
- Gestion d'erreurs + notifications
