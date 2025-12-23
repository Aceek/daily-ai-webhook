# MCP Tools Reference

## Daily Digest Workflow

### submit_digest (obligatoire)

Tu DOIS utiliser `submit_digest` pour soumettre le résultat final du daily digest.
NE JAMAIS retourner le JSON en texte libre.

```
submit_digest(
    execution_id: str,      # ID fourni dans les paramètres d'exécution
    headlines: list[dict],  # News majeures (au moins 1 requis)
    research: list[dict],   # Papers/recherches (peut être vide)
    industry: list[dict],   # Business/produits (peut être vide)
    watching: list[dict],   # Tendances à suivre (peut être vide)
    metadata: dict          # Métriques d'exécution
)
```

**Format news items:**

```json
{
    "title": "Titre concis (max 100 chars)",
    "summary": "Résumé factuel 2-3 phrases (max 300 chars)",
    "url": "https://source-primaire.com/article",
    "source": "Nom de la source",
    "category": "headlines|research|industry|watching",
    "confidence": "high|medium"
}
```

**Format metadata:**

```json
{
    "mission_id": "ai-news",
    "articles_analyzed": 24,
    "web_searches": 4,
    "fact_checks": 1,
    "deep_dives": 1,
    "research_doc": "/chemin/vers/research.md",
    "total_news_included": 6,
    "total_news_excluded": 4
}
```

---

## Database Query Tools

Ces outils permettent d'interroger la base de données des articles.
Utilise-les principalement pour les weekly digests.

### get_categories

Récupère les catégories existantes pour une mission.
**Utilise cet outil au début de l'analyse** pour réutiliser les catégories existantes.

```
get_categories(
    mission_id: str,           # ex: "ai-news"
    date_from: str | None,     # YYYY-MM-DD (optionnel)
    date_to: str | None        # YYYY-MM-DD (optionnel)
)
```

**Retour:**
```json
{
    "status": "success",
    "categories": [
        {"id": 1, "name": "LLM Models"},
        {"id": 2, "name": "AI Regulation"}
    ],
    "count": 2
}
```

### get_articles

Récupère des articles avec filtres optionnels.

```
get_articles(
    mission_id: str,              # ex: "ai-news"
    categories: list[str] | None, # noms de catégories (optionnel)
    date_from: str | None,        # YYYY-MM-DD (optionnel)
    date_to: str | None,          # YYYY-MM-DD (optionnel)
    limit: int = 100              # max 500
)
```

**Retour:**
```json
{
    "status": "success",
    "articles": [
        {
            "id": 123,
            "title": "GPT-5 Released",
            "url": "https://...",
            "source": "OpenAI",
            "category": "LLM Models",
            "pub_date": "2024-12-20"
        }
    ],
    "count": 45
}
```

### get_article_stats

Statistiques sur les articles dans une période.
**Utilise cet outil avant un weekly digest** pour comprendre le volume.

```
get_article_stats(
    mission_id: str,    # ex: "ai-news"
    date_from: str,     # YYYY-MM-DD (requis)
    date_to: str        # YYYY-MM-DD (requis)
)
```

**Retour:**
```json
{
    "status": "success",
    "total_articles": 156,
    "by_category": {
        "LLM Models": 45,
        "AI Regulation": 23
    },
    "by_source": {
        "TechCrunch": 34,
        "OpenAI": 12
    },
    "by_day": {
        "2024-12-16": 22,
        "2024-12-17": 28
    }
}
```

---

## Weekly Digest Workflow

### submit_weekly_digest

Soumet un digest hebdomadaire avec analyse de tendances.
Utilise les DB query tools pour récupérer les données avant d'analyser.

```
submit_weekly_digest(
    execution_id: str,
    mission_id: str,           # ex: "ai-news"
    week_start: str,           # YYYY-MM-DD
    week_end: str,             # YYYY-MM-DD
    summary: str,              # Résumé exécutif (2-3 paragraphes)
    trends: list[dict],        # Tendances identifiées
    top_stories: list[dict],   # Histoires clés de la semaine
    category_analysis: dict,   # Analyse par catégorie
    metadata: dict,
    is_standard: bool = True   # false si thème custom
)
```

**Format trends:**
```json
{
    "name": "Open-source AI acceleration",
    "description": "Major labs releasing more open models",
    "evidence": ["Article 1", "Article 2"],
    "direction": "rising"  // rising|stable|declining
}
```

**Format top_stories:**
```json
{
    "title": "OpenAI releases GPT-5",
    "summary": "The new model shows...",
    "url": "https://...",
    "impact": "Sets new benchmark for..."
}
```

---

## Workflow Complet

### Daily Digest

1. Analyse les articles fournis
2. Effectue recherches web complémentaires
3. Écris le document de recherche (Write)
4. Appelle `submit_digest` UNE SEULE FOIS

### Weekly Digest

1. `get_article_stats()` - comprendre le volume
2. `get_categories()` - voir les catégories existantes
3. `get_articles()` - récupérer les articles pertinents
4. Analyse les tendances et patterns
5. Appelle `submit_weekly_digest` UNE SEULE FOIS

---

## Erreurs Courantes

- Oublier un champ requis dans les items
- Ne pas appeler submit_digest (le workflow échoue)
- Appeler submit plusieurs fois (seul le dernier compte)
- Mettre confidence: "low" (interdit, exclure plutôt)
- Oublier mission_id dans metadata
