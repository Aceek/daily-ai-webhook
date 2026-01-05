# Mission: AI News Weekly Digest

Analyse hebdomadaire des tendances AI/ML.

## Différence Daily vs Weekly

| Aspect | Daily | Weekly |
|--------|-------|--------|
| Source | Articles RSS | Database (articles stockés) |
| Focus | Breaking news | Tendances |
| Output | Liste de news | Analyse structurée |

## Domaine

Même que Daily: Labs, modèles, research, régulation, M&A, open source.

## Mode thématique

Si `theme` fourni:

### Protocole

| Articles DB matchant | Action | data_source |
|---------------------|--------|-------------|
| ≥3 | DB uniquement | `"database"` |
| 1-2 | DB + contexte | `"mixed"` |
| 0 | Contexte uniquement | `"web_search"` |

### Summary obligatoire

- `database`: "Based on X articles from our database..."
- `mixed`: "Based on X database articles, supplemented with..."
- `web_search`: "No matching articles found in database..."

### Metadata thématique

```json
{
  "theme": "Open Source",
  "data_source": "mixed",
  "db_articles_matched": 2
}
```

## Langue

Anglais, ton analytique.
