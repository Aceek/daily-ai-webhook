# Roadmap: AI News Bot v2

> Document de suivi d'implémentation. Cocher [x] une fois complété.

## Phase 1: Archivage Complet ✅

### 1.1 Migration DB ✅
- [x] Ajouter colonne `status VARCHAR(20) DEFAULT 'selected'` à articles
- [x] Ajouter colonne `exclusion_reason VARCHAR(50)` à articles
- [x] Ajouter colonne `relevance_score SMALLINT` à articles
- [x] Créer script migration SQL
- [x] Exécuter migration sur postgres

**Fichiers:** `migrations/001_add_article_status.sql`

### 1.2 Modifier Models ✅
- [x] Mettre à jour `Article` dans `models.py` avec nouveaux champs
- [x] Ajouter enum/constantes pour `status` et `exclusion_reason`

**Fichier:** `claude-service/models.py`

### 1.3 Modifier MCP submit_digest ✅
- [x] Accepter nouveau format avec `selected` + `excluded`
- [x] Sauvegarder articles excluded avec status='excluded'
- [x] Sauvegarder exclusion_reason et relevance_score
- [x] Mettre à jour metadata dans digest

**Fichier:** `claude-service/mcp/server.py`

### 1.4 Modifier Output Schema ✅
- [x] Ajouter section `excluded` au schema
- [x] Documenter format minimal excluded (url, title, category, reason, score)
- [x] Ajouter `exclusion_breakdown` dans metadata

**Fichier:** `claude-service/missions/ai-news/output-schema.md`

### 1.5 Modifier Instructions Agent ✅
- [x] Mettre à jour protocole pour inclure excluded dans soumission
- [x] Documenter les raisons d'exclusion valides

**Fichier:** `claude-service/config/CLAUDE.md`

### 1.6 Tests Phase 1 ✅
- [x] Test syntaxe MCP server.py
- [x] Vérifier colonnes et contraintes en DB
- [x] Redémarrer claude-service avec succès

---

## Phase 2: Déduplication Hybride ✅

### 2.1 Nouveau MCP Tool ✅
- [x] Créer `get_recent_headlines(mission_id, days=3)`
- [x] Retourne: liste de {title, url, date, category} des articles sélectionnés
- [x] Limiter à 50 résultats max

**Fichier:** `claude-service/mcp/server.py`

### 2.2 Endpoint /check-urls ✅
- [x] Ajouter endpoint POST `/check-urls` dans claude-service
- [x] Reçoit liste d'URLs, retourne new_urls et duplicate_urls
- [x] Query articles des derniers N jours (default 7, max 30)

**Fichier:** `claude-service/main.py`

### 2.3 Modifier Instructions Agent ✅
- [x] Ajouter étape 1.6: appeler `get_recent_headlines` avant analyse
- [x] Instruction: "Ne pas sélectionner sujet déjà couvert sauf update significative"
- [x] Documenter exemples de déduplication
- [x] Ajouter get_recent_headlines à allowed_tools

**Fichier:** `claude-service/config/CLAUDE.md`

### 2.4 Tests Phase 2 ✅
- [x] Test: /check-urls retourne URLs correctement classées
- [x] Test: MCP server.py contient get_recent_headlines
- [x] Test: Query filtre par status='selected'

---

## Phase 3: Enrichissement Sources ✅

### 3.1 Vérifier Feeds Labs ✅
- [x] Vérifier RSS Anthropic → Pas de RSS officiel disponible
- [x] Vérifier RSS Meta AI → Pas de RSS officiel disponible
- [x] Vérifier RSS Mistral → Pas de RSS officiel disponible
- [x] Documenter: Labs majeurs n'ont pas de RSS publics (scraping futur si besoin)

### 3.2 Ajouter Sources Tier 1 (Labs) ⏭️ SKIPPED
- [x] Décision: Pas de RSS officiels disponibles pour Anthropic/Meta/Mistral
- [x] Alternative future: scraping ou monitoring manuel

### 3.3 Ajouter Sources Tier 2 (Research) ✅
- [x] Ajouter node RSS arXiv combiné `https://rss.arxiv.org/rss/cs.AI+cs.LG`
- [x] Format arXiv natif compatible Article standard
- [x] Connecter au Merge Articles

**Fichier:** `workflows/daily-news-workflow.json`

### 3.4 Ajouter Sources Tier 3 (Media) ✅
- [x] Ajouter node RSS The Verge AI `theverge.com/rss/ai-artificial-intelligence/index.xml`
- [x] Ajouter node RSS Ars Technica AI `arstechnica.com/ai/feed/`
- [x] Connecter au Merge Articles

**Fichier:** `workflows/daily-news-workflow.json`

### 3.5 Ajouter Sources Tier 4 (Community) ✅
- [x] Ajouter node HTTP Reddit r/LocalLLaMA (JSON API)
- [x] Transformer format Reddit → format Article standard
- [x] Filtrer score > 100
- [x] Connecter au Merge Articles

**Fichier:** `workflows/daily-news-workflow.json`

### 3.6 Retirer/Modifier Sources ✅
- [x] Retirer node RSS MIT Tech Review (paywalled, limited AI coverage)
- [x] Modifier Hacker News: points > 40 (au lieu de 50)
- [x] Mettre à jour Merge Articles (10 inputs)
- [x] Augmenter limite dedup de 30 à 50 articles

**Fichier:** `workflows/daily-news-workflow.json`

### 3.7 Mise à jour Documentation ✅
- [x] Mettre à jour liste sources fiables dans `mission.md`
- [x] Ajouter The Verge AI, Ars Technica AI aux sources fiables
- [x] Ajouter section sources communautaires avec thresholds

**Fichier:** `claude-service/missions/ai-news/mission.md`

### 3.8 Tests Phase 3
- [ ] Test workflow avec toutes les sources
- [ ] Vérifier volume ~50-60 articles après dedup
- [ ] Vérifier qualité/pertinence nouvelles sources

---

## Ordre d'Implémentation Recommandé

```
Phase 1 (Archivage) ──────────────────────────────► FIRST
   │   Critique: fondation pour tout le reste
   │
Phase 2 (Dédup) ──────────────────────────────────► SECOND
   │   Dépend de Phase 1 (articles en DB)
   │
Phase 3 (Sources) ────────────────────────────────► THIRD
       Indépendant mais bénéficie de Phase 1+2
```

---

## Fichiers Impactés (Résumé)

| Fichier | Phase(s) |
|---------|----------|
| `claude-service/models.py` | 1 |
| `claude-service/database.py` | 1 |
| `claude-service/mcp/server.py` | 1, 2 |
| `claude-service/main.py` | 2 (optionnel) |
| `claude-service/config/CLAUDE.md` | 1, 2 |
| `claude-service/missions/ai-news/output-schema.md` | 1 |
| `claude-service/missions/ai-news/mission.md` | 3 |
| `workflows/daily-news-workflow.json` | 2, 3 |

---

## Notes d'Implémentation

### Format Exclusion Reasons
```python
EXCLUSION_REASONS = [
    "off_topic",      # Pas lié AI/ML
    "duplicate",      # Même sujet déjà couvert
    "low_priority",   # Pertinent mais pas assez important
    "outdated"        # >48h ou info dépassée
]
```

### Format get_recent_headlines Response
```json
{
  "status": "success",
  "headlines": [
    {"title": "...", "url": "...", "date": "2025-12-25"},
    ...
  ],
  "count": 18
}
```

### URLs Sources Vérifiées (Dec 2025)
```
# Labs (pas de RSS officiels)
Anthropic: ❌ Pas de RSS public
Meta AI: ❌ Pas de RSS public
Mistral: ❌ Pas de RSS public

# Research (implémenté)
arXiv AI+LG: https://rss.arxiv.org/rss/cs.AI+cs.LG ✅

# Media (implémenté)
The Verge AI: https://www.theverge.com/rss/ai-artificial-intelligence/index.xml ✅
Ars Technica AI: https://arstechnica.com/ai/feed/ ✅

# Community (implémenté)
Reddit r/MachineLearning: https://www.reddit.com/r/MachineLearning/hot.json ✅
Reddit r/LocalLLaMA: https://www.reddit.com/r/LocalLLaMA/hot.json ✅
Hacker News: Algolia API avec points > 40 ✅
```
