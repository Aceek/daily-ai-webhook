# Output Schema - AI News

JSON soumis via `submit_digest`.

## Structure

```json
{
  "digest": {
    "date": "2024-12-22",
    "headline_count": 4,
    "categories": ["headlines", "research", "industry", "tools", "watching"]
  },
  "headlines": [{
    "title": "Titre concis",
    "summary": "Résumé factuel 2-3 phrases",
    "url": "https://source-primaire.com/article",
    "source": "Anthropic Blog",
    "category": "headlines",
    "confidence": "high",
    "emoji": "🚀",
    "importance": "major"
  }],
  "research": [{
    "title": "Titre paper",
    "summary": "Contribution expliquée",
    "url": "https://arxiv.org/abs/...",
    "source": "arXiv",
    "category": "research",
    "confidence": "high",
    "emoji": "🧠",
    "importance": "standard"
  }],
  "industry": [{
    "title": "News business",
    "summary": "Impact et contexte",
    "url": "https://...",
    "source": "Source",
    "category": "industry",
    "confidence": "medium",
    "emoji": "💼",
    "importance": "standard"
  }],
  "tools": [{
    "title": "Claude Code 2.1 released",
    "summary": "New features for agentic workflows",
    "url": "https://anthropic.com/...",
    "source": "Anthropic",
    "category": "tools",
    "confidence": "high",
    "emoji": "🛠️",
    "importance": "major"
  }],
  "watching": [{
    "title": "Tendance à suivre",
    "summary": "Pourquoi intéressant",
    "url": "https://...",
    "source": "Source",
    "category": "watching",
    "confidence": "medium",
    "emoji": "👀",
    "importance": "standard"
  }],
  "excluded": [{
    "url": "https://...",
    "title": "Article non sélectionné",
    "source": "Source",
    "category": "industry",
    "reason": "low_priority",
    "score": 4
  }],
  "metadata": {
    "execution_id": "abc123",
    "mission_id": "ai-news",
    "articles_analyzed": 30,
    "selected_count": 6,
    "excluded_count": 24
  }
}
```

## Champs selected item

| Champ | Contraintes |
|-------|-------------|
| `title` | Max 100 chars |
| `summary` | Max 300 chars, 2-3 phrases |
| `url` | URL source primaire |
| `source` | Nom lisible |
| `category` | `headlines`, `research`, `industry`, `tools`, `watching` |
| `confidence` | `high` (officiel) ou `medium` (réputé) |
| `emoji` | Un seul, représente le sujet |
| `importance` | `breaking`, `major`, `standard` |

## Champs excluded item

| Champ | Contraintes |
|-------|-------------|
| `url` | URL article |
| `title` | Titre |
| `source` | Optionnel, défaut "unknown" |
| `category` | Catégorie assignée |
| `reason` | `off_topic`, `duplicate`, `low_priority`, `outdated` |
| `score` | 1-10 (pertinence) |

## Exclusion reasons

| Raison | Usage |
|--------|-------|
| `off_topic` | Pas AI/ML |
| `duplicate` | Déjà couvert |
| `low_priority` | Pertinent mais mineur |
| `outdated` | >48h |

## Emoji par contexte

| Contexte | Exemples |
|----------|----------|
| Release | 🚀 🎉 ✨ |
| Research | 🧠 📊 🔬 |
| Business | 💰 💼 📈 |
| M&A | 🤝 🏢 |
| Régulation | ⚖️ 📜 🏛️ |
| Open source | 🌐 🔓 |
| Security | 🛡️ 🔒 |
| Agents | 🤖 🦾 |
| Tools | 🛠️ ⚙️ 🔧 |

## Validation

1. Au moins 1 item dans `headlines`
2. URLs valides, pas de doublons
3. TOUS articles soumis (selected + excluded)
4. `confidence: low` → exclure
5. `breaking` → max 1 par digest

## Volume

Pas de nombre fixe. Sélectionner **généreusement** tous les articles pertinents. Un digest avec 10-15 articles est parfaitement acceptable si le contenu est intéressant.
