# Vision: AI News Bot v2

## Objectif
Transformer le bot de veille AI/ML en système d'archivage complet avec couverture exhaustive des sources.

## Changements Majeurs

### 1. Archivage Complet
**Problème:** Seuls les articles sélectionnés (~6/jour) sont archivés. Les ~24 exclus sont perdus.

**Solution:** Claude enrichit et soumet TOUS les articles analysés.

```
AVANT: 30 analysés → 6 selected → DB (24 perdus)
APRÈS: 50 analysés → 6 selected + 44 excluded → DB (tout archivé)
```

**Format sortie modifié:**
```json
{
  "selected": [{
    "title", "summary", "url", "source", "category",
    "confidence", "emoji", "importance"
  }],
  "excluded": [{
    "url", "title", "category", "reason", "score"
  }],
  "metadata": {
    "total_analyzed", "selected_count", "excluded_count",
    "exclusion_breakdown": {"off_topic", "duplicate", "low_priority", "outdated"}
  }
}
```

**Raisons exclusion (enum):** `off_topic`, `duplicate`, `low_priority`, `outdated`

**Schema DB articles (nouveaux champs):**
```sql
status VARCHAR(20) DEFAULT 'raw'  -- 'raw'|'selected'|'excluded'
exclusion_reason VARCHAR(50)      -- raison si excluded
relevance_score SMALLINT          -- 1-10
```

### 2. Déduplication Hybride
**Problème:** Même news peut être republiée plusieurs jours consécutifs.

**Solution 2 niveaux:**

| Niveau | Où | Quoi | Coût |
|--------|-----|------|------|
| Code | n8n/MCP | Skip si URL existe en DB (7j) | 0 tokens |
| Agentique | Claude | Contexte titres 3 derniers jours | ~500 tokens |

**Nouveau MCP tool:** `get_recent_headlines(days=3)` → liste titres récents

**Instruction Claude:** "Ne sélectionne pas sujet déjà couvert, sauf update significative."

### 3. Sources Enrichies (7→14)

**Retirée:** MIT Tech Review (trop de bruit non-AI)

**Ajoutées:**
| Source | Tier | Type |
|--------|------|------|
| Anthropic | 1-Labs | RSS/scraping |
| Meta AI | 1-Labs | RSS/scraping |
| Mistral | 1-Labs | RSS/scraping |
| arXiv cs.AI | 2-Research | RSS |
| arXiv cs.LG | 2-Research | RSS |
| The Verge AI | 3-Media | RSS |
| Ars Technica | 3-Media | RSS |
| r/LocalLLaMA | 4-Community | API |

**Config finale:**
```
Tier 1 (Labs): OpenAI, Google AI, HuggingFace, Anthropic, Meta AI, Mistral
Tier 2 (Research): arXiv cs.AI, arXiv cs.LG
Tier 3 (Media): TechCrunch AI, The Verge AI, Ars Technica
Tier 4 (Community): Hacker News (>40pts), r/MachineLearning, r/LocalLLaMA
```

## Ce qui NE change PAS
- Scoring: système actuel conservé
- Weekly: analyse sur articles sélectionnés uniquement
- Sub-agents: fact-checker et topic-diver disponibles
- Format Discord embeds
- Commandes bot (/daily, /weekly)

## Métriques Cibles

| Métrique | Avant | Après |
|----------|-------|-------|
| Sources | 7 | 14 |
| Articles analysés/jour | ~30 | ~50 |
| Articles archivés/jour | ~6 | ~50 |
| Couverture Labs | 3/6 | 6/6 |
| Couverture Research | 0 | arXiv |
| Couverture Open Source | Faible | r/LocalLLaMA |

## Flux Cible

```
14 sources → n8n collect → ~60 articles
                              ↓
                    Dedup URL (code) → ~50 articles
                              ↓
                    Claude + contexte 3j
                              ↓
              ┌───────────────┴───────────────┐
              ↓                               ↓
        6 selected                      44 excluded
        (full enrichment)               (minimal: category+reason+score)
              ↓                               ↓
              └───────────────┬───────────────┘
                              ↓
                     DB (tout archivé)
                              ↓
                    Discord publication
```
