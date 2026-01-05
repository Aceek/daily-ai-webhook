# Output Schema - Weekly Digest

JSON soumis via `submit_weekly_digest`.

## Structure

```json
{
  "summary": "Executive summary (2-3 paragraphes)...",
  "trends": [{
    "name": "Open-source momentum",
    "description": "Major labs releasing open-weight models",
    "evidence": ["Llama 3.1", "Gemma 2"],
    "direction": "rising"
  }],
  "top_stories": [{
    "title": "OpenAI releases GPT-5",
    "summary": "New model features 1M context...",
    "url": "https://openai.com/blog/gpt-5",
    "impact": "Sets new standard",
    "emoji": "🚀"
  }],
  "category_analysis": {
    "headlines": {"count": 12, "summary": "Dominated by GPT-5"},
    "research": {"count": 8, "summary": "Focus on efficiency"}
  },
  "metadata": {
    "execution_id": "abc123",
    "mission_id": "ai-news",
    "week_start": "2024-12-16",
    "week_end": "2024-12-22",
    "articles_analyzed": 156,
    "theme": null
  }
}
```

## Champs

### summary

| Contrainte | Valeur |
|------------|--------|
| Min | 100 chars |
| Max | 2000 chars |
| Format | 2-3 paragraphes, anglais |

### trends (2-5 items)

| Champ | Contraintes |
|-------|-------------|
| `name` | Max 50 chars |
| `description` | Max 200 chars |
| `evidence` | 2-5 items |
| `direction` | `rising`, `stable`, `declining` |

### top_stories (3-5 items)

| Champ | Contraintes |
|-------|-------------|
| `title` | Max 100 chars |
| `summary` | Max 300 chars |
| `url` | URL source primaire |
| `impact` | Max 200 chars |
| `emoji` | Un seul |

### category_analysis

Clés: `headlines`, `research`, `industry`, `watching`

| Champ | Type |
|-------|------|
| `count` | integer |
| `summary` | Max 150 chars |

### metadata

| Champ | Requis | Description |
|-------|--------|-------------|
| `execution_id` | Oui | ID système |
| `mission_id` | Oui | "ai-news" |
| `week_start` | Oui | YYYY-MM-DD (lundi) |
| `week_end` | Oui | YYYY-MM-DD (dimanche) |
| `articles_analyzed` | Oui | Total traités |
| `theme` | Non | Si mode thématique |
| `data_source` | Thématique | `database`, `mixed`, `web_search` |
| `db_articles_matched` | Thématique | Articles DB matchant |

## Validation

1. `summary` non vide
2. 2+ tendances
3. 3+ top stories
4. URLs valides
5. `week_start` < `week_end`, lundi
