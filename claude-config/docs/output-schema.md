# Output Schema

Le JSON de sortie finale doit suivre exactement ce format.

## Structure

```json
{
  "digest": {
    "date": "2024-12-22",
    "headline_count": 4,
    "categories": ["headlines", "research", "industry", "watching"]
  },
  "headlines": [
    {
      "title": "Titre concis de la news",
      "summary": "Résumé factuel en 2-3 phrases. Focus sur le quoi et le pourquoi.",
      "url": "https://source-primaire.com/article",
      "source": "Nom de la source (ex: Anthropic Blog)",
      "category": "headlines",
      "confidence": "high",
      "deep_dive": null
    }
  ],
  "research": [
    {
      "title": "Titre du paper ou avancée technique",
      "summary": "Explication accessible de la contribution.",
      "url": "https://arxiv.org/abs/...",
      "source": "arXiv / Institution",
      "category": "research",
      "confidence": "high",
      "deep_dive": null
    }
  ],
  "industry": [
    {
      "title": "News business/produit",
      "summary": "Impact et contexte.",
      "url": "https://...",
      "source": "Source",
      "category": "industry",
      "confidence": "medium",
      "deep_dive": null
    }
  ],
  "watching": [
    {
      "title": "Tendance ou développement à suivre",
      "summary": "Pourquoi c'est intéressant.",
      "url": "https://...",
      "source": "Source",
      "category": "watching",
      "confidence": "medium",
      "deep_dive": null
    }
  ],
  "metadata": {
    "execution_id": "abc123",
    "articles_analyzed": 24,
    "web_searches": 4,
    "fact_checks": 1,
    "deep_dives": 1,
    "research_doc": "/app/logs/research/2024-12-22_08-00-00_abc123_research.md",
    "total_news_included": 6,
    "total_news_excluded": 4
  }
}
```

## Champs Requis

### Pour chaque news item

| Champ | Type | Description |
|-------|------|-------------|
| `title` | string | Titre court et factuel (max 100 chars) |
| `summary` | string | 2-3 phrases factuelles (max 300 chars) |
| `url` | string | URL de la source primaire |
| `source` | string | Nom lisible de la source |
| `category` | string | `headlines`, `research`, `industry`, ou `watching` |
| `confidence` | string | `high` ou `medium` (jamais `low` en production) |
| `deep_dive` | object/null | Résultat du topic-diver si applicable |

### Catégories

| Catégorie | Contenu |
|-----------|---------|
| `headlines` | News majeures du jour (annonces labs, régulation, acquisitions) |
| `research` | Papers, benchmarks, avancées techniques |
| `industry` | Produits, business, levées de fonds |
| `watching` | Tendances émergentes, choses à surveiller |

### Confidence Levels

| Niveau | Signification |
|--------|---------------|
| `high` | Source officielle ou fact-checkée |
| `medium` | Source réputée mais non vérifiée directement |

**Note:** Les news avec `confidence: low` ne doivent PAS apparaître dans le digest final.

## Deep Dive Format

Si un topic-diver a été utilisé, le champ `deep_dive` contient:

```json
{
  "background": "Contexte historique",
  "key_reactions": [...],
  "implications": [...],
  "what_matters": "Résumé de l'importance"
}
```

## Règles de Validation

1. Au moins 1 item dans `headlines`
2. `metadata.research_doc` doit pointer vers un fichier existant
3. Tous les URLs doivent être valides
4. Pas de doublons (même URL ou titre très similaire)
5. Total des items recommandé: 4-8
