# Output Schema - Weekly Digest

Le JSON soumis via `submit_weekly_digest` doit respecter ce schéma.

## Structure complète

```json
{
  "summary": "Executive summary of the week (2-3 paragraphs)...",
  "trends": [
    {
      "name": "Open-source AI momentum",
      "description": "Major labs releasing more open-weight models",
      "evidence": ["Llama 3.1 release", "Gemma 2 open-sourced"],
      "direction": "rising"
    }
  ],
  "top_stories": [
    {
      "title": "OpenAI releases GPT-5",
      "summary": "New model features 1M context window...",
      "url": "https://openai.com/blog/gpt-5",
      "impact": "Sets new standard for context length",
      "emoji": "🚀"
    }
  ],
  "category_analysis": {
    "headlines": {
      "count": 12,
      "summary": "Dominated by GPT-5 announcement"
    },
    "research": {
      "count": 8,
      "summary": "Focus on efficiency and smaller models"
    }
  },
  "metadata": {
    "execution_id": "abc123",
    "mission_id": "ai-news",
    "week_start": "2024-12-16",
    "week_end": "2024-12-22",
    "articles_analyzed": 156,
    "web_searches": 2,
    "theme": null
  }
}
```

## Champs requis

### summary (string)

| Contrainte | Valeur |
|------------|--------|
| Min length | 100 caractères |
| Max length | 2000 caractères |
| Format | 2-3 paragraphes |
| Langue | Anglais |

### trends (array)

| Champ | Type | Contraintes |
|-------|------|-------------|
| `name` | string | Max 50 chars, court et descriptif |
| `description` | string | Max 200 chars, 1-2 phrases |
| `evidence` | array[string] | 2-5 items, titres d'articles |
| `direction` | string | `rising`, `stable`, ou `declining` |

**Contraintes array:**
- Minimum: 2 tendances
- Maximum: 5 tendances
- Recommandé: 3-4 tendances

### top_stories (array)

| Champ | Type | Contraintes |
|-------|------|-------------|
| `title` | string | Max 100 chars, factuel |
| `summary` | string | Max 300 chars, 2-3 phrases |
| `url` | string | URL valide, source primaire |
| `impact` | string | Max 200 chars, implications |
| `emoji` | string | Emoji unique représentant le sujet |

**Contraintes array:**
- Minimum: 3 stories
- Maximum: 5 stories
- Recommandé: 4-5 stories

**Emoji:** Choisis un emoji qui capture l'essence de la story (🚀 pour release, 💰 pour funding, ⚖️ pour régulation, etc.)

### category_analysis (object)

Clés attendues: `headlines`, `research`, `industry`, `watching`

Pour chaque catégorie:

| Champ | Type | Contraintes |
|-------|------|-------------|
| `count` | integer | Nombre d'articles dans la catégorie |
| `summary` | string | Max 150 chars, points clés |

**Note:** Seules les catégories avec articles sont requises.

### metadata (object)

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `execution_id` | string | Oui | ID fourni par le système |
| `mission_id` | string | Oui | Toujours "ai-news" |
| `week_start` | string | Oui | YYYY-MM-DD (lundi) |
| `week_end` | string | Oui | YYYY-MM-DD (dimanche) |
| `articles_analyzed` | integer | Oui | Total articles traités |
| `web_searches` | integer | Non | Recherches web effectuées |
| `theme` | string/null | Non | Thème si mode thématique |
| `data_source` | string | Thématique | Source des données (voir ci-dessous) |
| `db_articles_matched` | integer | Thématique | Nombre d'articles DB matchant le thème |

### data_source (mode thématique uniquement)

| Valeur | Signification | Quand l'utiliser |
|--------|---------------|------------------|
| `"database"` | Données uniquement de la DB | ≥3 articles DB matchent le thème |
| `"mixed"` | DB + recherche web | 1-2 articles DB matchent |
| `"web_search"` | Recherche web uniquement | 0 articles DB matchent |

**Important:** Si `theme` est fourni, `data_source` et `db_articles_matched` sont OBLIGATOIRES.

## Direction des tendances

| Valeur | Signification | Indicateurs |
|--------|---------------|-------------|
| `rising` | Tendance en hausse | Plus d'articles, plus d'intérêt |
| `stable` | Tendance constante | Volume similaire aux semaines précédentes |
| `declining` | Tendance en baisse | Moins de couverture, sujet qui s'essouffle |

## Règles de validation

1. `summary` ne doit pas être vide
2. Au moins 2 tendances dans `trends`
3. Au moins 3 stories dans `top_stories`
4. Tous les URLs doivent être valides
5. `week_start` doit être antérieur à `week_end`
6. `week_start` doit être un lundi
7. `metadata.execution_id` ne doit pas être vide

## Exemple complet

```json
{
  "summary": "This week was dominated by OpenAI's surprise release of GPT-5, which sets a new standard for context length in commercial LLMs with its 1 million token window.\n\nKey developments included Google's rapid response with Gemini 2.0 announcement, the EU finalizing AI Act implementation dates for August 2025, and record funding rounds totaling $4.5B across the sector.\n\nThe open-source momentum continues unabated, with Meta, Mistral, and now Google contributing significant models to the community.",

  "trends": [
    {
      "name": "Context window race",
      "description": "Major LLM providers competing on context length, with GPT-5 reaching 1M tokens",
      "evidence": [
        "GPT-5 launches with 1M context",
        "Claude 3.5 Sonnet extended to 200K",
        "Gemini 2.0 promises 2M context"
      ],
      "direction": "rising"
    },
    {
      "name": "Open-source acceleration",
      "description": "More open-weight models from major labs, narrowing gap with proprietary offerings",
      "evidence": [
        "Meta Llama 3.1 405B release",
        "Google Gemma 2 open-sourced",
        "Mistral Large 2 weights released"
      ],
      "direction": "rising"
    },
    {
      "name": "Enterprise AI adoption",
      "description": "Fortune 500 companies accelerating AI integration across operations",
      "evidence": [
        "Microsoft 365 Copilot hits 1M enterprise users",
        "Salesforce Einstein AI expansion",
        "SAP announces AI-first strategy"
      ],
      "direction": "rising"
    }
  ],

  "top_stories": [
    {
      "title": "OpenAI releases GPT-5 with 1M token context window",
      "summary": "OpenAI announced GPT-5, featuring unprecedented 1 million token context and 40% improvement on MMLU benchmark. The model is available to Plus and Enterprise users.",
      "url": "https://openai.com/blog/gpt-5",
      "impact": "Sets new industry standard for context length, enabling full codebase and document analysis in single prompts",
      "emoji": "🚀"
    },
    {
      "title": "EU finalizes AI Act implementation timeline",
      "summary": "European Commission published final implementation schedule with high-risk AI systems requirements taking effect August 2025. Penalties can reach 7% of global revenue.",
      "url": "https://ec.europa.eu/ai-act-timeline",
      "impact": "Creates compliance urgency for global AI companies operating in EU market",
      "emoji": "⚖️"
    },
    {
      "title": "Anthropic closes $2.3B funding round",
      "summary": "Anthropic announced largest AI funding round of 2024, led by Google and Spark Capital. Valuation reaches $25B, funds earmarked for compute and safety research.",
      "url": "https://anthropic.com/news/series-d",
      "impact": "Solidifies Anthropic's position as leading AI safety-focused lab with resources to compete at frontier",
      "emoji": "💰"
    },
    {
      "title": "Google announces Gemini 2.0 with native multimodality",
      "summary": "Google unveiled next-generation Gemini with native image, audio, and video generation. Model available in early access to select partners.",
      "url": "https://blog.google/gemini-2",
      "impact": "Signals shift toward unified multimodal models rather than separate specialized systems",
      "emoji": "✨"
    }
  ],

  "category_analysis": {
    "headlines": {
      "count": 12,
      "summary": "Dominated by GPT-5 release and major funding announcements"
    },
    "research": {
      "count": 8,
      "summary": "Focus on efficiency with papers on distillation and quantization"
    },
    "industry": {
      "count": 15,
      "summary": "Strong funding week with 3 unicorn rounds; enterprise deals accelerating"
    },
    "watching": {
      "count": 5,
      "summary": "Growing focus on AI agents and autonomous systems"
    }
  },

  "metadata": {
    "execution_id": "weekly-2024-12-22-abc123",
    "mission_id": "ai-news",
    "week_start": "2024-12-16",
    "week_end": "2024-12-22",
    "articles_analyzed": 156,
    "web_searches": 2,
    "theme": null,
    "data_source": null,
    "db_articles_matched": null
  }
}
```

### Exemple avec thème (mode thématique)

```json
{
  "metadata": {
    "execution_id": "weekly-2024-12-22-xyz789",
    "mission_id": "ai-news",
    "week_start": "2024-12-16",
    "week_end": "2024-12-22",
    "articles_analyzed": 45,
    "web_searches": 3,
    "theme": "Open Source",
    "data_source": "mixed",
    "db_articles_matched": 2
  }
}
```
