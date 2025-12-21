# Intelligent News Agent - Vision Technique

> **Version:** 1.0
> **Date:** 22 décembre 2025
> **Statut:** Proposition validée, prête pour implémentation

---

## 1. Résumé Exécutif

### Objectif

Transformer le système de veille AI/ML d'un simple pipeline de résumé en un **agent de recherche intelligent** capable de :
- Analyser des sources primaires (RSS, Reddit, HN)
- Effectuer des recherches web complémentaires systématiques
- Déléguer à des sub-agents spécialisés (fact-checking, deep-dive)
- Produire un digest structuré avec traçabilité complète

### Avant / Après

| Aspect | MVP Actuel | Agent Intelligent |
|--------|------------|-------------------|
| Sources | 3 RSS passifs | 8+ RSS + Reddit + HN |
| Recherche | Aucune | WebSearch systématique |
| Vérification | Aucune | Sub-agent fact-checker |
| Approfondissement | Aucun | Sub-agent topic-diver |
| Traçabilité | Logs basiques | Document de recherche complet |
| Intelligence | Résumé simple | Orchestration conditionnelle |

---

## 2. Architecture Globale

### 2.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARCHITECTURE AGENT INTELLIGENT                       │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        n8n: COLLECTE PRIMAIRE                          │ │
│  │                                                                         │ │
│  │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │ │
│  │   │Anthropic│ │ OpenAI  │ │   HF    │ │   MIT   │ │The Batch│  RSS x8  │ │
│  │   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │ │
│  │        │           │           │           │           │                │ │
│  │        └───────────┴───────────┼───────────┴───────────┘                │ │
│  │                                │                                        │ │
│  │   ┌─────────┐ ┌─────────┐      │                                        │ │
│  │   │ Reddit  │ │   HN    │      │                                        │ │
│  │   │   API   │ │ Algolia │      │                                        │ │
│  │   └────┬────┘ └────┬────┘      │                                        │ │
│  │        │           │           │                                        │ │
│  │        └───────────┴───────────┤                                        │ │
│  │                                ▼                                        │ │
│  │                    ┌───────────────────────┐                            │ │
│  │                    │  Merge + Dedupe +     │                            │ │
│  │                    │  Filter (7 jours)     │                            │ │
│  │                    └───────────┬───────────┘                            │ │
│  └────────────────────────────────┼────────────────────────────────────────┘ │
│                                   │                                          │
│                                   ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                   CLAUDE-SERVICE (FastAPI)                              │ │
│  │                                                                         │ │
│  │   POST /summarize                                                       │ │
│  │   {                                                                     │ │
│  │     "articles": [...],           // Données n8n                         │ │
│  │     "workflow_execution_id": "..." // Corrélation                       │ │
│  │   }                                                                     │ │
│  │                                   │                                     │ │
│  │                                   ▼                                     │ │
│  │   ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │   │  claude -p "$PROMPT"                                            │  │ │
│  │   │    --allowedTools "WebSearch,WebFetch,Write,Task"               │  │ │
│  │   │    --output-format stream-json                                  │  │ │
│  │   └─────────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────┼────────────────────────────────────────┘ │
│                                   │                                          │
│                                   ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    CLAUDE CLI: AGENT PRINCIPAL                         │ │
│  │                                                                         │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │ PHASE 1: ANALYSE DES SOURCES PRIMAIRES                            │ │ │
│  │  │                                                                    │ │ │
│  │  │ • Parcourt tous les articles n8n                                  │ │ │
│  │  │ • Identifie les sujets majeurs                                    │ │ │
│  │  │ • Détecte les sources potentiellement douteuses                   │ │ │
│  │  │ • Repère les hot topics méritant approfondissement                │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                │                                        │ │
│  │                                ▼                                        │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │ PHASE 2: RECHERCHE WEB COMPLÉMENTAIRE (SYSTÉMATIQUE)              │ │ │
│  │  │                                                                    │ │ │
│  │  │ WebSearch() - TOUJOURS exécuté pour:                              │ │ │
│  │  │ • Découvrir breaking news non captées par RSS                     │ │ │
│  │  │ • Croiser/valider les informations des sources primaires          │ │ │
│  │  │ • Enrichir le contexte des sujets identifiés                      │ │ │
│  │  │                                                                    │ │ │
│  │  │ Limite: 3-5 recherches par exécution                              │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                │                                        │ │
│  │                                ▼                                        │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │ PHASE 3: SUB-AGENTS (CONDITIONNEL)                                │ │ │
│  │  │                                                                    │ │ │
│  │  │ ┌─────────────────────────────────────────────────────────────┐   │ │ │
│  │  │ │ Task(fact-checker)                                          │   │ │ │
│  │  │ │                                                              │   │ │ │
│  │  │ │ Déclenché SI:                                               │   │ │ │
│  │  │ │ • Source non reconnue/fiable                                │   │ │ │
│  │  │ │ • Information semble peu crédible                           │   │ │ │
│  │  │ │ • Contradiction entre sources                               │   │ │ │
│  │  │ │                                                              │   │ │ │
│  │  │ │ Action: Vérifie source primaire, retourne confiance         │   │ │ │
│  │  │ └─────────────────────────────────────────────────────────────┘   │ │ │
│  │  │                                                                    │ │ │
│  │  │ ┌─────────────────────────────────────────────────────────────┐   │ │ │
│  │  │ │ Task(topic-diver)                                           │   │ │ │
│  │  │ │                                                              │   │ │ │
│  │  │ │ Déclenché SI:                                               │   │ │ │
│  │  │ │ • Sujet majeur identifié (annonce importante)               │   │ │ │
│  │  │ │ • Tendance émergente détectée                               │   │ │ │
│  │  │ │ • Maximum 1-2 sujets par exécution                          │   │ │ │
│  │  │ │                                                              │   │ │ │
│  │  │ │ Action: Recherche contexte, réactions, implications         │   │ │ │
│  │  │ └─────────────────────────────────────────────────────────────┘   │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                │                                        │ │
│  │                                ▼                                        │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │ PHASE 4: DOCUMENTATION DE RECHERCHE                              │ │ │
│  │  │                                                                    │ │ │
│  │  │ Write("/app/logs/research/{timestamp}_{id}_research.md")          │ │ │
│  │  │                                                                    │ │ │
│  │  │ Contenu:                                                          │ │ │
│  │  │ • Articles analysés (nombre, sources)                             │ │ │
│  │  │ • Recherches web effectuées (queries, urls, raisons)              │ │ │
│  │  │ • Sub-agents appelés (lesquels, pourquoi, résultats)              │ │ │
│  │  │ • Décisions éditoriales (inclus/exclus avec justification)        │ │ │
│  │  │ • Niveau de confiance par news (high/medium/low)                  │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                │                                        │ │
│  │                                ▼                                        │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │ PHASE 5: RÉDACTION FINALE                                         │ │ │
│  │  │                                                                    │ │ │
│  │  │ Output JSON structuré selon editorial-guide.md                    │ │ │
│  │  │ Format optimisé pour embeds Discord riches                        │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────┼────────────────────────────────────────┘ │
│                                   │                                          │
│                                   ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         DISCORD                                        │ │
│  │                                                                         │ │
│  │   Embeds riches multi-catégories avec liens cliquables                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Séparation des Contextes Claude

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEUX INSTANCES CLAUDE DISTINCTES                          │
│                                                                              │
│   ┌─────────────────────────────────┐    ┌─────────────────────────────────┐│
│   │      CONTEXTE DÉVELOPPEMENT     │    │      CONTEXTE PRODUCTION        ││
│   │                                 │    │                                 ││
│   │   Emplacement: .claude/         │    │   Emplacement: claude-config/   ││
│   │                                 │    │   Monté dans Docker comme       ││
│   │   Usage: Développement local    │    │   /root/.claude                 ││
│   │   avec Claude Code CLI          │    │                                 ││
│   │                                 │    │   Usage: Exécution automatisée  ││
│   │   Agents:                       │    │   du workflow de veille         ││
│   │   - feature-planner             │    │                                 ││
│   │   - feature-implementer         │    │   Agents:                       ││
│   │   - senior-reviewer             │    │   - fact-checker                ││
│   │   - etc.                        │    │   - topic-diver                 ││
│   │                                 │    │                                 ││
│   │   ⚠️ NE PAS MÉLANGER            │    │   📁 Config dédiée au projet    ││
│   └─────────────────────────────────┘    └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Configuration Unifiée

### 3.1 Structure du dossier `claude-config/`

```
claude-config/                      # Monté comme /root/.claude dans Docker
├── settings.json                   # Configuration Claude CLI
├── CLAUDE.md                       # Instructions système pour l'agent
├── agents/                         # Sub-agents disponibles
│   ├── fact-checker.md
│   └── topic-diver.md
└── docs/                           # Documentation de référence
    ├── editorial-guide.md          # Guide éditorial (déplacé depuis config/)
    ├── sources-reference.md        # Documentation des sources
    └── output-schema.md            # Schéma JSON de sortie
```

### 3.2 Fichier CLAUDE.md (Instructions Agent)

```markdown
# AI News Research Agent

Tu es un agent de veille AI/ML intelligent. Tu opères en mode autonome
pour produire un digest quotidien de qualité.

## Tes Capacités

| Outil | Usage |
|-------|-------|
| WebSearch | Recherche web (TOUJOURS utiliser) |
| WebFetch | Récupérer contenu d'une URL |
| Write | Écrire le document de recherche |
| Task | Déléguer aux sub-agents |

## Sub-Agents Disponibles

### fact-checker
- **Quand l'utiliser:** Source non reconnue, info peu crédible, contradiction
- **Ce qu'il fait:** Vérifie source primaire, retourne niveau de confiance

### topic-diver
- **Quand l'utiliser:** Sujet majeur, tendance émergente (max 1-2/run)
- **Ce qu'il fait:** Recherche contexte, réactions, implications

## Workflow Obligatoire

1. Analyse les articles reçus
2. Effectue 3-5 recherches web (OBLIGATOIRE)
3. Délègue aux sub-agents si nécessaire
4. Écris le document de recherche dans /app/logs/research/
5. Produis le JSON final

## Règles de Décision

- Fact-check si source non dans: [Anthropic, OpenAI, Google, Meta, HuggingFace, MIT, Stanford, arXiv]
- Deep-dive si annonce majeure (nouveau modèle, acquisition >$100M, régulation)
- Toujours croiser avec au moins une recherche web

## Output

Produis un JSON structuré selon docs/output-schema.md
```

### 3.3 Agent fact-checker.md

```markdown
---
name: fact-checker
description: Vérifie la véracité d'une information en croisant les sources.
  Utilisé quand une news provient d'une source non reconnue ou semble peu crédible.
tools: WebSearch, WebFetch
model: haiku
---

# Fact Checker Agent

Tu es un vérificateur de faits spécialisé AI/ML.

## Input

Tu reçois une affirmation à vérifier avec sa source.

## Process

1. Recherche la source primaire (blog officiel, communiqué de presse)
2. Cherche une confirmation indépendante
3. Évalue la crédibilité

## Output

Retourne un objet JSON:
```json
{
  "claim": "L'affirmation vérifiée",
  "verified": true|false,
  "confidence": "high|medium|low",
  "primary_source": "URL de la source primaire ou null",
  "secondary_sources": ["URLs de confirmation"],
  "notes": "Observations importantes"
}
```

## Règles

- Maximum 3 recherches par vérification
- Si aucune source primaire trouvée → confidence: "low"
- Si source primaire + confirmation → confidence: "high"
```

### 3.4 Agent topic-diver.md

```markdown
---
name: topic-diver
description: Approfondit un sujet "hot" pour enrichir le contexte.
  Utilisé pour les annonces majeures ou tendances émergentes (max 1-2/run).
tools: WebSearch, WebFetch
model: sonnet
---

# Topic Deep Diver Agent

Tu es un analyste spécialisé dans l'approfondissement de sujets AI/ML.

## Input

Tu reçois un sujet à approfondir avec le contexte initial.

## Process

1. Recherche le contexte et le background
2. Trouve les réactions de la communauté (Twitter, Reddit, HN)
3. Identifie les implications et perspectives
4. Synthétise les points clés

## Output

Retourne un objet JSON:
```json
{
  "topic": "Le sujet analysé",
  "background": "Contexte historique (2-3 phrases)",
  "key_reactions": [
    {"source": "Twitter/Reddit/HN", "summary": "Point clé"}
  ],
  "implications": ["Implication 1", "Implication 2"],
  "expert_quotes": ["Citation notable si trouvée"],
  "related_developments": ["Développement connexe"]
}
```

## Règles

- Maximum 5 recherches par sujet
- Focus sur les 24-48 dernières heures
- Privilégier les réactions d'experts reconnus
```

---

## 4. Système de Logs Enrichi

### 4.1 Structure des logs

```
logs/
├── 2024-12-22_08-00-00_abc123.md       # Log Claude (existant)
├── 2024-12-22_08-00-00_abc123.json     # Log Claude JSON (existant)
├── workflows/
│   ├── 2024-12-22_08-00-00_wf-xxx.md   # Log Workflow (existant)
│   └── 2024-12-22_08-00-00_wf-xxx.json # Log Workflow JSON (existant)
└── research/                            # NOUVEAU
    ├── 2024-12-22_08-00-00_abc123_research.md
    └── 2024-12-22_08-00-00_abc123_research.json
```

### 4.2 Format du Document de Recherche

```markdown
# Research Document - 2024-12-22 08:00:00

## Execution Info
- **Execution ID:** abc123
- **Workflow ID:** wf-xxx
- **Duration:** 8m 32s
- **Cost:** $0.18

## Phase 1: Sources Primaires Analysées

| # | Source | Title | Relevance |
|---|--------|-------|-----------|
| 1 | Anthropic Blog | Claude 3.5 Update | High |
| 2 | Reddit r/LocalLLaMA | New Llama weights | Medium |
| ... | ... | ... | ... |

**Total:** 24 articles analysés

## Phase 2: Recherches Web Effectuées

| Query | Raison | Résultats Utiles |
|-------|--------|------------------|
| "OpenAI GPT-5 announcement december 2024" | Rumeur dans article Reddit | 2 sources confirmées |
| "AI regulation EU december 2024" | Compléter couverture | 3 articles pertinents |
| ... | ... | ... |

**Total:** 4 recherches effectuées

## Phase 3: Sub-Agents Utilisés

### fact-checker (1 appel)
- **Sujet:** "Mistral AI acquiert Hugging Face"
- **Raison:** Source non reconnue (blog personnel)
- **Résultat:** NOT VERIFIED (confidence: low)
- **Action:** Exclu du digest

### topic-diver (1 appel)
- **Sujet:** "Claude 3.5 Update"
- **Raison:** Annonce majeure Anthropic
- **Résultat:** Contexte enrichi avec réactions communauté

## Phase 4: Décisions Éditoriales

### Inclus dans le digest
| News | Catégorie | Confiance | Justification |
|------|-----------|-----------|---------------|
| Claude 3.5 Update | Headlines | High | Source officielle + deep-dive |
| EU AI Act implementation | Regulation | High | Multiple sources confirmées |
| ... | ... | ... | ... |

### Exclus du digest
| News | Raison |
|------|--------|
| Mistral acquiert HF | Non vérifié (fact-check failed) |
| GPT-5 leak | Rumeur non confirmée |
| ... | ... |

## Métriques

| Métrique | Valeur |
|----------|--------|
| Articles analysés | 24 |
| Recherches web | 4 |
| Fact-checks | 1 |
| Deep-dives | 1 |
| News incluses | 6 |
| News exclues | 4 |

---
*Document généré automatiquement par l'agent de recherche*
```

### 4.3 Corrélation Tri-directionnelle

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Workflow Log   │────▶│   Claude Log    │────▶│  Research Doc   │
│                 │     │                 │     │                 │
│ workflow_id     │     │ execution_id    │     │ execution_id    │
│ claude_exec_id ─┼────▶│ workflow_id ────┼────▶│ workflow_id     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 5. Sources Enrichies

### 5.1 Sources RSS (n8n)

| Source | URL | Priorité |
|--------|-----|----------|
| Anthropic Blog | https://www.anthropic.com/feed.xml | High |
| OpenAI Blog | https://openai.com/blog/rss/ | High |
| HuggingFace Blog | https://huggingface.co/blog/feed.xml | High |
| Google AI Blog | https://blog.google/technology/ai/rss/ | High |
| The Batch (Andrew Ng) | https://www.deeplearning.ai/the-batch/feed/ | High |
| MIT Tech Review AI | https://www.technologyreview.com/topic/artificial-intelligence/feed | Medium |
| Papers With Code | https://paperswithcode.com/rss | Medium |
| BAIR Blog | https://bair.berkeley.edu/blog/feed.xml | Medium |

### 5.2 APIs (n8n)

| Source | Endpoint | Paramètres |
|--------|----------|------------|
| Reddit | `https://www.reddit.com/r/MachineLearning/hot.json` | `limit=25` |
| Reddit | `https://www.reddit.com/r/LocalLLaMA/hot.json` | `limit=25` |
| Hacker News | `https://hn.algolia.com/api/v1/search` | `query=AI, tags=story, last 24h` |

### 5.3 Recherche Web Complémentaire (Claude CLI)

- **Systématique:** 3-5 recherches par exécution
- **Objectifs:**
  - Breaking news non captées par RSS
  - Validation/croisement des sources primaires
  - Enrichissement contextuel

---

## 6. Modifications Techniques

### 6.1 docker-compose.yml

```yaml
services:
  claude-service:
    build: ./claude-service
    volumes:
      # Config Claude dédiée au projet (remplace CLAUDE_HOME personnel)
      - ./claude-config:/root/.claude
      # Logs avec nouveau dossier research/
      - ./logs:/app/logs
    environment:
      - CLAUDE_ALLOWED_TOOLS=WebSearch,WebFetch,Write,Task
```

### 6.2 main.py - Appel Claude CLI enrichi

```python
cmd = [
    "claude",
    "-p", prompt,
    "--allowedTools", "WebSearch,WebFetch,Write,Task",
    "--output-format", "stream-json",
    "--verbose"
]
```

### 6.3 Nouveau prompt (build_prompt)

Le prompt doit référencer les instructions complètes de `CLAUDE.md` et inclure le chemin pour le document de recherche.

---

## 7. Estimations

### 7.1 Coûts

| Composant | Coût/exécution | Coût/mois (30 runs) |
|-----------|----------------|---------------------|
| Sources n8n | $0 | $0 |
| Claude CLI principal | ~$0.10-0.20 | ~$3-6 |
| WebSearch (3-5) | $0 (inclus) | $0 |
| fact-checker (haiku) | ~$0.01-0.02 | ~$0.30-0.60 |
| topic-diver (sonnet) | ~$0.03-0.05 | ~$0.90-1.50 |
| **Total** | **~$0.15-0.30** | **~$4.50-9.00** |

### 7.2 Temps d'exécution

| Phase | Durée estimée |
|-------|---------------|
| n8n collecte | ~30s |
| Analyse sources | ~30s |
| Recherches web | ~2-3 min |
| Sub-agents | ~1-2 min |
| Rédaction | ~30s |
| **Total** | **~5-7 min** |

---

## 8. Risques et Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| WebSearch non pertinent | Moyenne | Faible | Limiter à 5 recherches, instructions précises |
| Sub-agent dérive | Faible | Moyen | Modèle haiku pour fact-checker, instructions strictes |
| Timeout | Faible | Moyen | Augmenter CLAUDE_TIMEOUT à 300s |
| Coût explosif | Faible | Élevé | Limites dans les instructions, monitoring |
| Boucle infinie | Très faible | Élevé | Pas de récursion dans les sub-agents |

---

## 9. Critères de Succès

| Critère | Mesure | Objectif |
|---------|--------|----------|
| Couverture | News majeures captées | >90% |
| Qualité | News vérifiées incluses | 100% |
| Temps | Durée totale workflow | <10 min |
| Coût | Coût mensuel | <$15 |
| Traçabilité | Décisions documentées | 100% |

---

## 10. Prochaines Étapes

Voir le document **IMPLEMENTATION-ROADMAP.md** pour le plan d'implémentation détaillé.

---

*Document créé le 22 décembre 2025*
