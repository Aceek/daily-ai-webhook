# MCP Tools Reference

## Query Tools

### get_categories(mission_id, date_from?, date_to?)

Récupère catégories existantes. **Appeler AVANT classification (Daily).**

```json
{"categories": [{"id": 1, "name": "LLM Models"}], "count": 2}
```

### get_recent_headlines(mission_id, days=3)

Headlines récentes pour déduplication. **Appeler AVANT sélection (Daily).**

```json
{"headlines": [{"title": "...", "url": "...", "date": "...", "category": "..."}]}
```

### get_articles(mission_id, categories?, date_from?, date_to?, limit=100)

Articles filtrés. **Weekly uniquement.**

```json
{"articles": [{"id": 1, "title": "...", "url": "...", "source": "...", "category": "...", "pub_date": "..."}], "count": 45}
```

### get_article_stats(mission_id, date_from, date_to)

Stats volume/distribution. **Weekly uniquement.**

```json
{"total_articles": 156, "by_category": {...}, "by_source": {...}, "by_day": {...}}
```

---

## Submit Tools

### submit_digest (Daily)

```
submit_digest(
  execution_id: str,
  headlines: list[dict],   # Au moins 1 requis
  research: list[dict],
  industry: list[dict],
  watching: list[dict],
  excluded: list[dict],    # Tous les non-sélectionnés
  metadata: dict
)
```

**Article:** `{title, summary, url, source, category, confidence: "high|medium"}`

**Excluded:** `{url, title, source, category, reason, score}`

**Metadata:** `{mission_id, articles_analyzed, selected_count, excluded_count}`

### submit_weekly_digest (Weekly)

```
submit_weekly_digest(
  execution_id, mission_id, week_start, week_end,
  summary, trends, top_stories, category_analysis,
  metadata, is_standard=true
)
```

**Trend:** `{name, description, evidence: [], direction: "rising|stable|declining"}`

**Top story:** `{title, summary, url, impact}`

---

## Erreurs courantes

| Erreur | Solution |
|--------|----------|
| Catégories dupliquées | Appeler `get_categories` AVANT classification |
| Articles dupliqués | Appeler `get_recent_headlines` AVANT sélection |
| Workflow échoue | Toujours appeler `submit_digest` |
| confidence: "low" | Exclure l'article plutôt |
