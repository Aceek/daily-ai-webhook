# Output Schema - AI News

Le JSON soumis via `submit_digest` doit respecter ce schéma.

## Structure complète

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
    "research_doc": "/path/to/research.md",
    "total_news_included": 6,
    "total_news_excluded": 4
  }
}
```

## Champs requis par news item

| Champ | Type | Contraintes |
|-------|------|-------------|
| `title` | string | Max 100 chars, factuel |
| `summary` | string | Max 300 chars, 2-3 phrases |
| `url` | string | URL valide, source primaire |
| `source` | string | Nom lisible |
| `category` | string | `headlines`, `research`, `industry`, ou `watching` |
| `confidence` | string | `high` ou `medium` uniquement |
| `deep_dive` | object/null | Résultat topic-diver si applicable |

## Catégories

| Catégorie | Contenu attendu |
|-----------|-----------------|
| `headlines` | News majeures (annonces labs, régulation, acquisitions) |
| `research` | Papers, benchmarks, avancées techniques |
| `industry` | Produits, business, levées de fonds |
| `watching` | Tendances émergentes, choses à surveiller |

## Confidence levels

| Niveau | Signification | Quand l'utiliser |
|--------|---------------|------------------|
| `high` | Source officielle ou fact-checkée | Blogs officiels, papers, sources vérifiées |
| `medium` | Source réputée non vérifiée directement | TechCrunch, Reddit populaire, etc. |

**Note:** Les news `confidence: low` ne doivent PAS apparaître dans le digest.

## Deep Dive format

Si un topic-diver a été utilisé :

```json
{
  "background": "Contexte historique",
  "key_reactions": [
    {"source": "Twitter", "summary": "Réaction notable"}
  ],
  "implications": ["Implication 1", "Implication 2"],
  "what_matters": "Résumé de l'importance"
}
```

## Règles de validation

1. Au moins 1 item dans `headlines`
2. `metadata.research_doc` doit pointer vers un fichier existant
3. Tous les URLs doivent être valides
4. Pas de doublons (même URL ou titre très similaire)
5. Total items recommandé: 4-8
