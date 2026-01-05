# Weekly Analysis Rules

## Tendances

### Critères

| Critère | Seuil |
|---------|-------|
| Articles liés | 3+ |
| Sources distinctes | 2+ |
| Jours couverts | 2+ |

### Directions

| Direction | Quand |
|-----------|-------|
| `rising` | Plus d'articles/intérêt |
| `stable` | Volume similaire |
| `declining` | Moins de couverture |

### Format

```json
{
  "name": "Open-source AI momentum",
  "description": "Major labs releasing more open-weight models",
  "evidence": ["Llama 3.1 release", "Gemma 2 open-sourced"],
  "direction": "rising"
}
```

## Top Stories

### Priorité

1. Impact majeur (industrie entière)
2. Source officielle (annonce directe)
3. Nouveauté (breakthrough)
4. Adoption large (millions users)
5. Régulation (force légale)

### Format

```json
{
  "title": "OpenAI releases GPT-5",
  "summary": "New model features 1M context window...",
  "url": "https://openai.com/blog/gpt-5",
  "impact": "Sets new standard for context length",
  "emoji": "🚀"
}
```

## Category Analysis

```json
{
  "headlines": {"count": 12, "summary": "Dominated by GPT-5 announcement"},
  "research": {"count": 8, "summary": "Focus on efficiency"}
}
```

## Executive Summary

Structure: Opening → Key developments → Trends → Looking ahead

- 2-3 paragraphes, 150-300 mots
- Factuel, chiffres et dates concrètes

## Métriques

| Métrique | Min | Recommandé |
|----------|-----|------------|
| Tendances | 2 | 3-5 |
| Top Stories | 3 | 4-5 |
| Summary | 100 mots | 150-250 |
