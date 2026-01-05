# Agent Multi-Mission

## Détection du type

| Paramètre | Type |
|-----------|------|
| `articles_path` présent | DAILY |
| `week_start` + `week_end` | WEEKLY |

---

## Protocole DAILY

### Paramètres
- `mission`, `articles_path`, `execution_id`

### Étapes

| # | Action | Obligatoire |
|---|--------|-------------|
| 1 | `Read(articles_path)` | ✓ |
| 2 | `Read` fichiers mission (voir ci-dessous) | ✓ |
| 3 | `get_categories(mission_id)` | ✓ |
| 4 | `get_recent_headlines(mission_id, days=3)` | ✓ |
| 5 | Analyser et classifier articles | ✓ |
| 6 | `submit_digest(...)` | ✓ |

### Fichiers mission à lire

```
/app/.claude/missions/_common/quality-rules.md
/app/.claude/missions/_common/mcp-usage.md
/app/.claude/missions/{mission}/mission.md
/app/.claude/missions/{mission}/selection-rules.md
/app/.claude/missions/{mission}/editorial-guide.md
/app/.claude/missions/{mission}/output-schema.md
```

### Classification

**get_categories** - Appeler AVANT de classifier:
- Réutiliser catégories existantes si le sujet correspond
- Ne créer une nouvelle que si aucune ne correspond

**get_recent_headlines** - Appeler AVANT de sélectionner:
- Ne pas sélectionner si même sujet couvert récemment
- Exception: mise à jour significative (nouvelle info)

### Output

**Selected**: Être GÉNÉREUX. Inclure tous les articles pertinents sans limite fixe. 10-15 articles acceptable si contenu intéressant.

**Excluded** (uniquement si vraiment pas pertinent):

| Raison | Usage |
|--------|-------|
| `off_topic` | Clairement pas AI/ML |
| `duplicate` | Exactement même sujet déjà couvert |
| `low_priority` | Très mineur, aucun intérêt |

Note: Ne PAS utiliser `outdated` - le filtre n8n gère déjà (<7 jours)

Score: 1-3 (off_topic), 4-5 (low), 6-7 (borderline), 8-10 (should be selected)

### Finalisation

```
submit_digest(
  execution_id,
  headlines=[...],
  research=[...],
  industry=[...],
  tools=[...],      # AI dev tools: Claude Code, Cursor, MCP, SDK
  watching=[...],
  excluded=[{url, title, source, category, reason, score}],
  metadata={mission_id, articles_analyzed, ...}
)
```

---

## Protocole WEEKLY

### Paramètres
- `mission`, `week_start`, `week_end`, `execution_id`
- `theme` (optionnel)

### Étapes

| # | Action |
|---|--------|
| 1 | `Read` fichiers weekly (voir ci-dessous) |
| 2 | `get_article_stats(mission_id, date_from, date_to)` |
| 3 | `get_categories(mission_id, date_from, date_to)` |
| 4 | `get_articles(mission_id, date_from, date_to, limit=200)` |
| 5 | Analyser tendances et patterns |
| 6 | `submit_weekly_digest(...)` |

### Fichiers weekly à lire

```
/app/.claude/missions/_common/mcp-usage.md
/app/.claude/missions/{mission}/weekly/mission.md
/app/.claude/missions/{mission}/weekly/analysis-rules.md
/app/.claude/missions/{mission}/weekly/output-schema.md
```

### Output weekly

- 3-5 tendances (name, description, evidence, direction)
- 3-5 top stories (title, summary, url, impact)
- Analyse par catégorie
- Résumé exécutif

---

## Outils MCP

| Outil | Daily | Weekly |
|-------|-------|--------|
| `get_categories` | ✓ | ✓ |
| `get_recent_headlines` | ✓ | - |
| `get_article_stats` | - | ✓ |
| `get_articles` | - | ✓ |
| `submit_digest` | ✓ | - |
| `submit_weekly_digest` | - | ✓ |

---

## Règles absolues

### Daily
1. Lire fichiers mission AVANT analyse
2. `get_categories` AVANT classification
3. `get_recent_headlines` AVANT sélection
4. Réutiliser catégories existantes
5. Ne pas dupliquer sujets récents
6. `submit_digest` pour finaliser
7. Soumettre TOUS articles (selected + excluded)

### Weekly
1. Utiliser MCP DB tools pour récupérer données
2. Identifier minimum 2 tendances
3. Inclure minimum 3 top stories
4. `submit_weekly_digest` (PAS submit_digest)
