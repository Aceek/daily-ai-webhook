# Research Document Template

Utilise ce template pour créer le document de recherche.

## Format

```markdown
# Research Document - {DATE} {TIME}

## Execution Info

| Field | Value |
|-------|-------|
| **Execution ID** | {execution_id} |
| **Workflow ID** | {workflow_execution_id} |
| **Mission** | {mission} |
| **Date** | {date} |

## Phase 1: Sources Primaires Analysées

| # | Source | Title | Relevance | Notes |
|---|--------|-------|-----------|-------|
| 1 | {source} | {title} | High/Medium/Low | {brief note} |
| ... | ... | ... | ... | ... |

**Total:** {n} articles analysés

## Phase 2: Recherches Web Effectuées

| # | Query | Raison | Résultats Utiles |
|---|-------|--------|------------------|
| 1 | "{search query}" | {why this search} | {n} sources pertinentes |
| ... | ... | ... | ... |

**Total:** {n} recherches effectuées

## Phase 3: Sub-Agents Utilisés

### fact-checker ({n} appels)

#### Vérification 1
- **Claim:** "{claim to verify}"
- **Source originale:** {original source}
- **Raison:** {why fact-check needed}
- **Résultat:** VERIFIED / NOT VERIFIED (confidence: high/medium/low)
- **Action:** Inclus / Exclu du digest

### topic-diver ({n} appels)

#### Deep-dive 1
- **Sujet:** "{topic}"
- **Raison:** {why deep-dive needed}
- **Résultat:** Contexte enrichi - {brief summary}

## Phase 4: Décisions Éditoriales

### Inclus dans le digest

| News | Catégorie | Confiance | Justification |
|------|-----------|-----------|---------------|
| {title} | headlines/research/industry/watching | high/medium | {why included} |
| ... | ... | ... | ... |

### Exclus du digest

| News | Raison |
|------|--------|
| {title} | {why excluded: non vérifié, doublon, hors scope, trop ancien, etc.} |
| ... | ... |

## Métriques Finales

| Métrique | Valeur |
|----------|--------|
| Articles analysés | {n} |
| Recherches web | {n} |
| Fact-checks effectués | {n} |
| Deep-dives effectués | {n} |
| News incluses | {n} |
| News exclues | {n} |

---
*Document généré automatiquement par l'agent de recherche*
```

## Instructions

1. Remplace tous les `{placeholders}` par les valeurs réelles
2. Supprime les sections non utilisées (ex: si pas de fact-check)
3. Sois concis mais précis
4. Le document doit permettre de comprendre POURQUOI chaque décision a été prise
