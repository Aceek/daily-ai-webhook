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
      "emoji": "🚀",
      "importance": "major",
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
      "emoji": "🧠",
      "importance": "standard",
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
      "emoji": "💼",
      "importance": "standard",
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
      "emoji": "👀",
      "importance": "standard",
      "deep_dive": null
    }
  ],
  "excluded": [
    {
      "url": "https://...",
      "title": "Article non sélectionné",
      "source": "Source",
      "category": "industry",
      "reason": "low_priority",
      "score": 4
    }
  ],
  "metadata": {
    "execution_id": "abc123",
    "articles_analyzed": 30,
    "web_searches": 4,
    "fact_checks": 1,
    "deep_dives": 1,
    "research_doc": "/path/to/research.md",
    "selected_count": 6,
    "excluded_count": 24,
    "exclusion_breakdown": {
      "off_topic": 10,
      "duplicate": 2,
      "low_priority": 8,
      "outdated": 4
    }
  }
}
```

## Champs requis par news item (selected)

| Champ | Type | Contraintes |
|-------|------|-------------|
| `title` | string | Max 100 chars, factuel |
| `summary` | string | Max 300 chars, 2-3 phrases |
| `url` | string | URL valide, source primaire |
| `source` | string | Nom lisible |
| `category` | string | Catégorie existante ou nouvelle |
| `confidence` | string | `high` ou `medium` uniquement |
| `emoji` | string | Emoji unique représentant le sujet |
| `importance` | string | `breaking`, `major`, ou `standard` |
| `deep_dive` | object/null | Résultat topic-diver si applicable |

## Champs requis par excluded item

| Champ | Type | Contraintes |
|-------|------|-------------|
| `url` | string | URL de l'article |
| `title` | string | Titre de l'article |
| `source` | string | Nom de la source (optionnel, défaut: "unknown") |
| `category` | string | Catégorie assignée |
| `reason` | string | `off_topic`, `duplicate`, `low_priority`, ou `outdated` |
| `score` | int | Score de pertinence 1-10 |

## Exclusion Reasons

| Raison | Signification | Quand l'utiliser |
|--------|---------------|------------------|
| `off_topic` | Pas lié AI/ML | Article généraliste tech, crypto, gaming non-AI |
| `duplicate` | Sujet déjà couvert | Même news d'une autre source, update mineure |
| `low_priority` | Pertinent mais pas assez important | News mineure, pas d'impact significatif |
| `outdated` | >48h ou info dépassée | Vieille news, info déjà obsolète |

## Catégories (sections du digest)

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

## Emoji

Choisis un emoji unique qui représente le sujet de la news. L'emoji sera affiché devant le titre dans Discord.

| Contexte | Exemples d'emojis |
|----------|-------------------|
| Nouveau modèle/release | 🚀 🎉 ✨ |
| Recherche/paper | 🧠 📊 🔬 |
| Financement/business | 💰 💼 📈 |
| Acquisition/M&A | 🤝 🏢 |
| Régulation/légal | ⚖️ 📜 🏛️ |
| Open source | 🌐 🔓 |
| Sécurité/safety | 🛡️ 🔒 |
| Infrastructure | ⚡ 🖥️ 🌍 |
| Agents/autonomie | 🤖 🦾 |

**Règle:** Un seul emoji par news. Choisis celui qui capture le mieux l'essence du sujet.

## Importance

Indique le niveau d'importance de la news pour aider au formatage visuel.

| Niveau | Signification | Quand l'utiliser |
|--------|---------------|------------------|
| `breaking` | Breaking news majeure | Annonces inattendues, changements majeurs de l'industrie |
| `major` | News importante | Releases de modèles, acquisitions significatives, régulations |
| `standard` | News régulière | Mises à jour produit, papers, tendances |

**Note:** Utilise `breaking` avec parcimonie (0-1 par digest max).

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
5. Volume adapté au cycle d'actualités (1-3 jour calme, 4-8 normal, 10+ breaking news)
6. **TOUS les articles analysés doivent être soumis** (selected OU excluded)
7. Chaque excluded item doit avoir une `reason` valide et un `score` 1-10
