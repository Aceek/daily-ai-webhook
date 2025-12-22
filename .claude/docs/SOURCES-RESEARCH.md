# Recherche Sources AI/ML - Phase 3

> **Date:** 22 décembre 2024
> **Objectif:** Identifier les meilleures sources gratuites et qualitatives pour enrichir le bot de veille

---

## 1. Sources Actuelles (MVP)

| Source | Type | URL |
|--------|------|-----|
| Anthropic Blog | RSS | https://www.anthropic.com/feed.xml |
| OpenAI Blog | RSS | https://openai.com/blog/rss/ |
| HuggingFace Blog | RSS | https://huggingface.co/blog/feed.xml |

---

## 2. Sources RSS Recommandées

### Tier 1: Labs Officiels (Haute priorité)

| Source | RSS URL | Justification |
|--------|---------|---------------|
| **Google AI Blog** | `https://blog.google/technology/ai/rss/` | Annonces Gemini, DeepMind, recherche |
| **Meta AI** | `https://ai.meta.com/blog/rss/` | Llama, recherche open-source |
| **Microsoft AI** | `https://blogs.microsoft.com/ai/feed/` | Azure AI, Copilot, partenariats |
| **DeepMind** | `https://deepmind.google/blog/rss.xml` | Recherche fondamentale |

### Tier 2: Newsletters & Agrégateurs (Moyenne priorité)

| Source | RSS URL | Justification |
|--------|---------|---------------|
| **The Batch (Andrew Ng)** | `https://www.deeplearning.ai/the-batch/feed/` | Curation hebdo de qualité |
| **MIT News AI** | `https://news.mit.edu/topic/artificial-intelligence2/feed` | Recherche académique |
| **Import AI** | `https://importai.substack.com/feed` | Newsletter influente (Jack Clark) |

### Tier 3: Tech News (Basse priorité - souvent redondant)

| Source | RSS URL | Note |
|--------|---------|------|
| VentureBeat AI | `https://venturebeat.com/category/ai/feed/` | Beaucoup de volume, qualité variable |
| TechCrunch AI | `https://techcrunch.com/category/artificial-intelligence/feed/` | Business focus |
| Ars Technica AI | `https://feeds.arstechnica.com/arstechnica/technology-lab` | Analyses techniques |

### Tier 4: Recherche (Pour deep-dives)

| Source | RSS URL | Note |
|--------|---------|------|
| arXiv cs.AI | `https://rss.arxiv.org/rss/cs.AI` | Volume élevé, filtrage nécessaire |
| arXiv cs.LG | `https://rss.arxiv.org/rss/cs.LG` | Machine Learning papers |
| BAIR Blog | `https://bair.berkeley.edu/blog/feed.xml` | Berkeley AI Research |

---

## 3. APIs Gratuites

### Hacker News (Algolia API)

**Statut:** Gratuit, pas de clé API requise

**Endpoint:** `https://hn.algolia.com/api/v1/search`

**Exemple pour AI news:**
```
https://hn.algolia.com/api/v1/search_by_date?query=AI OR LLM OR "machine learning"&tags=story&numericFilters=points>50,created_at_i>{timestamp_24h_ago}
```

**Paramètres utiles:**
- `query`: Recherche texte
- `tags=story`: Filtrer les stories uniquement
- `numericFilters=points>50`: Minimum 50 points
- `numericFilters=created_at_i>X`: Après timestamp X
- `hitsPerPage=25`: Nombre de résultats

**Avantages:**
- Gratuit et illimité (raisonnable)
- Contenu communautaire de qualité
- Discussions techniques approfondies

### Reddit API

**Statut:** Compliqué depuis 2023

**Changements 2023:**
- $0.24 / 1000 appels API pour usage commercial
- Gratuit pour usage académique/non-commercial
- Rate limit: 60 req/min

**Alternative - JSON public:**
```
https://www.reddit.com/r/MachineLearning/hot.json?limit=25
https://www.reddit.com/r/LocalLLaMA/hot.json?limit=25
```

**Subreddits pertinents:**
| Subreddit | Membres | Focus |
|-----------|---------|-------|
| r/MachineLearning | 3M+ | Recherche, papers, discussions |
| r/LocalLLaMA | 500K+ | LLMs open-source, fine-tuning |
| r/artificial | 700K+ | News générales AI |
| r/ChatGPT | 4M+ | ChatGPT spécifique |

**Risques:**
- Reddit peut bloquer les requêtes sans User-Agent
- ToS interdisent le scraping massif
- Qualité variable (beaucoup de bruit)

---

## 4. Recommandations d'Implémentation

### Configuration Recommandée

```
SOURCES PRIMAIRES (n8n - collecte passive)
├── RSS Labs (5 sources)
│   ├── Anthropic Blog ✓ (existant)
│   ├── OpenAI Blog ✓ (existant)
│   ├── HuggingFace Blog ✓ (existant)
│   ├── Google AI Blog (ajouter)
│   └── The Batch (ajouter)
│
├── API Hacker News (ajouter)
│   └── Query: AI/LLM/ML, points>50, last 24h
│
└── Reddit JSON (optionnel)
    └── r/MachineLearning hot, score>100

SOURCES SECONDAIRES (Claude WebSearch - enrichissement)
└── Recherches web systématiques (déjà configuré)
```

### Priorité d'Implémentation

| Priorité | Source | Effort | Valeur |
|----------|--------|--------|--------|
| 1 | **Hacker News API** | Faible | Haute |
| 2 | **Google AI Blog RSS** | Très faible | Haute |
| 3 | **The Batch RSS** | Très faible | Moyenne |
| 4 | Reddit r/MachineLearning | Moyen | Moyenne |
| 5 | MIT News AI | Très faible | Basse |

### Ce que je NE recommande PAS

1. **arXiv RSS directement** - Trop de volume (100+ papers/jour), mieux géré par WebSearch si besoin
2. **VentureBeat/TechCrunch** - Redondant avec WebSearch, souvent du contenu sponsorisé
3. **Twitter/X API** - Payant et complexe
4. **Reddit API officielle** - Risque légal/ToS pour un bot automatisé

---

## 5. Plan d'Action Phase 3

### Étape 1: Ajouter Hacker News (prioritaire)
- Node HTTP Request vers Algolia API
- Filtrer: query AI/LLM, points>50, last 24h
- Transformer en format Article

### Étape 2: Ajouter 2 RSS
- Google AI Blog
- The Batch (Andrew Ng)

### Étape 3: (Optionnel) Reddit
- r/MachineLearning via JSON public
- User-Agent approprié
- Filtrer score>100

---

## Sources de cette Recherche

- [GitHub - allainews_sources](https://github.com/foorilla/allainews_sources)
- [Top 100 AI RSS Feeds - Feedspot](https://rss.feedspot.com/ai_rss_feeds/)
- [HN Algolia API Documentation](https://hn.algolia.com/api)
- [Reddit API Guide - Zuplo](https://zuplo.com/learning-center/reddit-api-guide)
- [Best AI Subreddits - YourDreamAI](https://yourdreamai.com/best-ai-subreddits/)
