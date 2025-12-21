# AI News Bot - Document de Vision

> **Version:** 1.0
> **Date:** 21 décembre 2024
> **Statut:** En cours de définition

---

## 1. Présentation du Projet

### 1.1 Objectif Principal
Créer un système automatisé qui collecte, analyse et synthétise les actualités AI/ML quotidiennement, puis les publie sur un serveur Discord sous forme de résumé éditorialisé.

### 1.2 Proposition de Valeur
- **Gain de temps** : Plus besoin de parcourir 10+ sources manuellement
- **Qualité éditoriale** : Claude Code trie et priorise l'information, pas juste une agrégation brute
- **Personnalisable** : Règles et format modifiables sans toucher au code
- **Évolutif** : Architecture pensée pour ajouter des features (bot interactif, multi-thématiques)

### 1.3 Public Cible
- Serveur Discord personnel ou communautaire
- Personnes souhaitant suivre l'actualité AI sans y passer des heures

---

## 2. Fonctionnalités

### 2.1 Phase 1 - MVP (Minimum Viable Product)

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Collecte automatique | Récupération des articles via RSS, Reddit, Hacker News | Haute |
| Analyse intelligente | Claude Code évalue la pertinence selon des règles configurables | Haute |
| Recherche complémentaire | Claude peut effectuer des recherches web si les sources sont insuffisantes | Haute |
| Résumé quotidien | Publication formatée sur Discord à heure configurable | Haute |
| Configuration éditoriale | Fichiers .md pour définir les règles sans coder | Haute |

### 2.2 Phase 2 - Bot Interactif

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| `/news now` | Déclencher un résumé immédiat à la demande | Moyenne |
| `/news topic <sujet>` | Changer temporairement le sujet (crypto, gaming, etc.) | Moyenne |
| `/news sources` | Afficher la liste des sources actives | Basse |
| `/subscribe` | Notifications personnalisées par utilisateur | Basse |

### 2.3 Phase 3 - Extensions Futures

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Twitter/X | Intégration des comptes influents AI | À définir |
| Multi-thématiques | Plusieurs channels pour différents sujets | À définir |
| Dashboard web | Interface pour gérer sources et règles | À définir |
| Historique searchable | Retrouver les news passées | À définir |

---

## 3. Architecture Technique

### 3.1 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            INFRASTRUCTURE                                │
│                                                                          │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐    │
│   │   SOURCES    │     │     n8n      │     │     Claude Code      │    │
│   │              │     │              │     │                      │    │
│   │ • RSS Feeds  │────▶│ • Scheduler  │────▶│ • Analyse articles   │    │
│   │ • Reddit API │     │ • Collecte   │     │ • Recherche web      │    │
│   │ • HN API     │     │ • Merge      │     │ • Rédaction résumé   │    │
│   └──────────────┘     └──────────────┘     └──────────┬───────────┘    │
│                                                         │                │
│                              ┌───────────────────────────┘                │
│                              │                                           │
│                              ▼                                           │
│   ┌──────────────────────────────────────┐     ┌────────────────────┐   │
│   │         CONFIGURATION                 │     │      DISCORD       │   │
│   │                                       │     │                    │   │
│   │ • rules.md (critères sélection)      │     │ • Webhook (MVP)    │   │
│   │ • sources.md (liste feeds)           │     │ • Bot (Phase 2)    │   │
│   │ • editorial-guide.md (format/ton)    │     │                    │   │
│   └──────────────────────────────────────┘     └────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Stack Technologique

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| **Orchestration** | n8n (Docker) | Interface visuelle, scheduling intégré, gratuit en self-hosted |
| **Intelligence** | Claude Code CLI | Abonnement existant, capacité web search, puissant |
| **Messaging** | Discord Webhook → Bot | Webhook pour MVP (simple), Bot pour interactions |
| **Configuration** | Fichiers Markdown | Modifiables sans code, versionnables avec Git |
| **Hébergement** | Docker local | Gratuit, contrôle total, pas de dépendance cloud |

### 3.3 Structure des Fichiers

```
daily-ai-webhook/
│
├── docker-compose.yml              # Configuration Docker (n8n)
├── .env                            # Variables d'environnement
│
├── n8n-data/                       # Volume persistant n8n
│   └── .n8n/                       # Données n8n (auto-généré)
│
├── config/                         # Configuration éditoriale
│   ├── rules.md                    # Critères de sélection des news
│   ├── sources.md                  # Liste des sources (RSS, Reddit, etc.)
│   └── editorial-guide.md          # Guide de style et format
│
├── scripts/                        # Scripts utilitaires
│   └── summarize.sh                # Wrapper pour appeler Claude Code
│
├── workflows/                      # Exports des workflows n8n
│   └── daily-news-workflow.json    # Workflow principal (backup)
│
├── bot/                            # Bot Discord (Phase 2)
│   ├── bot.py                      # Code du bot
│   ├── requirements.txt            # Dépendances Python
│   └── Dockerfile                  # Container pour le bot
│
├── docs/                           # Documentation
│   └── VISION.md                   # Ce document
│
└── README.md                       # Documentation du projet
```

---

## 4. Sources de Données

### 4.1 Sources Phase 1 (Gratuites)

#### Flux RSS
| Source | URL Feed | Type de contenu |
|--------|----------|-----------------|
| Anthropic Blog | anthropic.com/feed | Annonces officielles, recherche |
| OpenAI Blog | openai.com/blog/rss | Annonces, releases |
| Google AI Blog | blog.google/technology/ai/rss | Recherche, produits |
| Hugging Face Blog | huggingface.co/blog/feed.xml | Open source, modèles |
| MIT Tech Review AI | technologyreview.com/feed (filtré AI) | Analyses, tendances |
| The Batch | deeplearning.ai/the-batch/feed | Newsletter hebdo |

#### APIs Gratuites
| Source | Endpoint | Limite |
|--------|----------|--------|
| Reddit | `reddit.com/r/{subreddit}/hot.json` | ~60 req/min sans auth |
| Hacker News | `hn.algolia.com/api/v1/search?query=AI` | Illimité |

#### Subreddits Ciblés
- r/MachineLearning - Recherche et discussions techniques
- r/LocalLLaMA - LLMs open source, fine-tuning
- r/artificial - News générales AI
- r/singularity - Tendances long-terme

### 4.2 Sources Phase 3 (Optionnelles)

| Source | Difficulté | Coût |
|--------|------------|------|
| Twitter/X | Élevée (API restrictive) | $100+/mois ou alternatives |
| NewsAPI | Faible | 100 req/jour gratuit |
| Arxiv | Faible | Gratuit (API officielle) |

---

## 5. Configuration Éditoriale

### 5.1 rules.md - Critères de Sélection

```markdown
# Règles de Sélection des News

## Priorité Haute (À inclure systématiquement)
- Annonces officielles des labs majeurs (Anthropic, OpenAI, Google, Meta, Mistral)
- Nouvelles releases de modèles (GPT-x, Claude x, Gemini, Llama, etc.)
- Papers avec impact significatif (nouveaux benchmarks battus, nouvelles architectures)
- Régulations et législations AI (EU AI Act, décisions gouvernementales)
- Acquisitions et levées de fonds majeures (>$100M)

## Priorité Moyenne (Inclure si pertinent)
- Tutoriels et guides techniques populaires (>500 upvotes Reddit)
- Nouvelles fonctionnalités d'outils existants
- Interviews de chercheurs/leaders du domaine
- Analyses de tendances par des sources réputées

## Priorité Basse (Inclure si espace disponible)
- Projets open source intéressants
- Discussions communautaires notables
- Événements et conférences à venir

## À Exclure
- Contenus purement promotionnels sans substance
- Rumeurs non sourcées
- Articles clickbait sans information concrète
- Doublons (même info de sources différentes)
- Contenus datant de plus de 48h

## Recherche Web Complémentaire
Déclencher une recherche web si:
- Moins de 5 articles pertinents après filtrage
- Une actualité majeure est mentionnée mais manque de détails
- Besoin de contexte sur une annonce importante
```

### 5.2 editorial-guide.md - Guide de Style

```markdown
# Guide Éditorial

## Langue
- Anglais

## Ton
- Professionnel et accessible
- Factuel, pas d'opinions personnelles
- Concis, aller à l'essentiel

## Structure du Résumé

### Format Standard
🔥 **TOP 3 HEADLINES**
[Les 3 actualités les plus importantes]

📊 **INDUSTRY & PRODUCTS**
[Annonces produits, business news - si pertinent]

🔬 **RESEARCH SPOTLIGHT**
[Papers ou avancées techniques notables - si pertinent]

💡 **WORTH WATCHING**
[Tendances émergentes, à surveiller - si pertinent]

### Règles de Formatage
- Chaque item: 1-2 phrases maximum
- Inclure le nom de la source entre parenthèses
- Utiliser des liens quand disponibles
- Maximum 2000 caractères total

## Exemples

### Bon ✓
"🔥 OpenAI releases GPT-5 with native multimodal capabilities and 1M context window. Available today for Plus subscribers. (OpenAI Blog)"

### Mauvais ✗
"OpenAI just dropped something HUGE! GPT-5 is here and it's absolutely insane, you won't believe what it can do..."
```

### 5.3 sources.md - Liste des Sources

```markdown
# Sources Actives

## RSS Feeds
- https://www.anthropic.com/feed.xml
- https://openai.com/blog/rss/
- https://blog.google/technology/ai/rss/
- https://huggingface.co/blog/feed.xml
- https://www.technologyreview.com/topic/artificial-intelligence/feed

## Reddit (JSON API)
- r/MachineLearning - hot, limit 25
- r/LocalLLaMA - hot, limit 15
- r/artificial - hot, limit 10

## Hacker News
- Query: "artificial intelligence OR machine learning OR LLM OR GPT"
- Filter: last 24 hours
- Limit: 20 stories

## Notes
- Ajouter/retirer des sources en modifiant ce fichier
- Les sources RSS sont prioritaires (plus fiables)
- Reddit/HN pour l'info "chaude" et discussions
```

---

## 6. Workflow Détaillé

### 6.1 Flux d'Exécution Quotidien

```
┌─────────────────────────────────────────────────────────────────────┐
│ 08:00 - DÉCLENCHEMENT                                               │
│ └── Cron Trigger n8n                                                │
├─────────────────────────────────────────────────────────────────────┤
│ 08:01 - COLLECTE (parallèle)                                        │
│ ├── RSS Feed Node ×6 sources                                        │
│ ├── HTTP Request: Reddit (3 subreddits)                            │
│ └── HTTP Request: Hacker News API                                   │
├─────────────────────────────────────────────────────────────────────┤
│ 08:02 - PRÉTRAITEMENT                                               │
│ ├── Merge: Combiner tous les résultats                             │
│ ├── Dedup: Supprimer doublons (par URL/titre)                      │
│ └── Filter: Garder uniquement dernières 24h                        │
├─────────────────────────────────────────────────────────────────────┤
│ 08:03 - FORMATAGE                                                   │
│ └── Construire le payload texte pour Claude                        │
├─────────────────────────────────────────────────────────────────────┤
│ 08:04 - ANALYSE CLAUDE CODE                                         │
│ ├── Lecture des fichiers config (rules.md, editorial-guide.md)     │
│ ├── Évaluation de la pertinence                                    │
│ ├── Recherche web complémentaire (si nécessaire)                   │
│ └── Génération du résumé formaté                                   │
├─────────────────────────────────────────────────────────────────────┤
│ 08:06 - PUBLICATION                                                 │
│ └── HTTP Request: Discord Webhook                                   │
├─────────────────────────────────────────────────────────────────────┤
│ 08:06 - LOGGING                                                     │
│ └── Enregistrement du statut dans n8n                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Script d'Appel Claude Code

```bash
#!/bin/bash
# scripts/summarize.sh

ARTICLES_FILE=$1
CONFIG_DIR="./config"

# Construire le prompt avec la documentation
claude -p "
You are an AI/ML news editor.

=== SELECTION RULES ===
$(cat $CONFIG_DIR/rules.md)

=== EDITORIAL GUIDELINES ===
$(cat $CONFIG_DIR/editorial-guide.md)

=== ARTICLES TO ANALYZE ===
$(cat $ARTICLES_FILE)

=== INSTRUCTIONS ===
1. Analyze all articles according to the selection rules
2. If fewer than 5 relevant articles, perform a web search for today's AI news
3. Write the summary following the editorial guidelines exactly
4. Output ONLY the formatted summary, nothing else
"
```

---

## 7. Configuration Discord

### 7.1 Création du Webhook (Phase 1)

1. Ouvrir Discord → Serveur → Paramètres du channel
2. Intégrations → Webhooks → Nouveau webhook
3. Nommer "AI News Bot" + choisir avatar
4. Copier l'URL du webhook
5. Stocker dans `.env` : `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...`

### 7.2 Format du Message Discord

```json
{
  "embeds": [{
    "title": "🤖 Daily AI/ML News Digest",
    "description": "[Contenu généré par Claude]",
    "color": 5814783,
    "timestamp": "2024-12-21T08:00:00.000Z",
    "footer": {
      "text": "Powered by Claude Code | Sources: RSS, Reddit, HN"
    }
  }]
}
```

---

## 8. Installation et Déploiement

### 8.1 Prérequis

- Docker et Docker Compose installés
- Claude Code CLI installé et configuré (abonnement actif)
- Compte Discord avec accès admin au serveur cible

### 8.2 docker-compose.yml

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    container_name: n8n
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

### 8.3 Étapes d'Installation

```bash
# 1. Cloner le repo
git clone git@github.com:Aceek/daily-ai-webhook.git
cd daily-ai-webhook

# 2. Créer les fichiers de config
mkdir -p config scripts n8n-data workflows bot docs

# 3. Créer le .env
cp .env.example .env
# Éditer .env avec vos valeurs

# 4. Lancer n8n
docker-compose up -d

# 5. Accéder à n8n
# Ouvrir http://localhost:5678
```

---

## 9. Plan d'Implémentation

### 9.1 Sprint 1 - Fondations (MVP)

| Étape | Tâche | Statut |
|-------|-------|--------|
| 1.1 | Créer la structure du projet | ⬜ |
| 1.2 | Configurer Docker + n8n | ⬜ |
| 1.3 | Créer le webhook Discord et tester | ⬜ |
| 1.4 | Écrire les fichiers config (rules.md, etc.) | ⬜ |
| 1.5 | Créer le workflow n8n avec 3 sources RSS | ⬜ |
| 1.6 | Intégrer Claude Code via Execute Command | ⬜ |
| 1.7 | Tester le flux complet manuellement | ⬜ |
| 1.8 | Configurer le cron et tester en conditions réelles | ⬜ |

### 9.2 Sprint 2 - Enrichissement

| Étape | Tâche | Statut |
|-------|-------|--------|
| 2.1 | Ajouter Reddit comme source | ⬜ |
| 2.2 | Ajouter Hacker News comme source | ⬜ |
| 2.3 | Affiner les prompts Claude | ⬜ |
| 2.4 | Améliorer le formatage Discord (embeds) | ⬜ |
| 2.5 | Ajouter gestion d'erreurs et notifications | ⬜ |

### 9.3 Sprint 3 - Bot Discord

| Étape | Tâche | Statut |
|-------|-------|--------|
| 3.1 | Créer le bot Discord (discord.py) | ⬜ |
| 3.2 | Implémenter `/news now` | ⬜ |
| 3.3 | Implémenter `/news sources` | ⬜ |
| 3.4 | Intégrer avec n8n ou remplacer le scheduler | ⬜ |

---

## 10. Risques et Mitigations

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| API Reddit rate-limitée | Moyen | Moyenne | Utiliser auth Reddit, caching |
| Claude Code CLI indisponible | Élevé | Faible | Fallback sur API directe |
| Sources RSS changent d'URL | Faible | Moyenne | Monitoring + alertes |
| Résumés de mauvaise qualité | Moyen | Moyenne | Itérer sur les prompts |
| Docker/n8n crash | Élevé | Faible | Restart policies, backups |

---

## 11. Métriques de Succès

| Métrique | Objectif | Comment mesurer |
|----------|----------|-----------------|
| Fiabilité | >95% d'envois réussis | Logs n8n |
| Pertinence | Feedback positif utilisateurs | Réactions Discord |
| Timing | Envoi à ±5min de l'heure configurée | Timestamps |
| Couverture | Pas de news majeure manquée | Vérification manuelle hebdo |

---

## 12. Évolutions Possibles

- **Multi-channels** : Un channel par thématique (AI, Crypto, Gaming)
- **Personnalisation** : Chaque utilisateur configure ses centres d'intérêt
- **Historique** : Base de données des news passées, recherchable
- **Analytics** : Dashboard des tendances sur le temps
- **Multi-plateformes** : Slack, Telegram, email en plus de Discord

---

## Annexes

### A. Ressources Utiles

- [Documentation n8n](https://docs.n8n.io/)
- [Discord Webhooks Guide](https://discord.com/developers/docs/resources/webhook)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [discord.py Documentation](https://discordpy.readthedocs.io/)

### B. Contacts et Support

- Projet géré via Claude Code
- Issues et améliorations trackées dans le repo

---

*Document généré avec Claude Code - Décembre 2024*
