# Plan de Refactoring v2

Date: 2026-01-04
Objectif: Projet propre, extensible, maintenable

## Vue d'Ensemble

| Phase | Nom | Effort | Objectif |
|-------|-----|--------|----------|
| 0 | Préparation | 2h | Tests minimaux pour refacto safe |
| 1 | Quick Wins | 4h | Débloquer multi-mission + fix critiques |
| 2 | Simplification Layers | 8h | 5 layers → 3 layers |
| 3 | Unification | 6h | 4 loggers → 1, 3 models → 1 |
| 4 | Qualité | 8h | Tests complets + cleanup |

**Total estimé: 28h (~1 semaine)**

---

## Phase 0: Préparation

**Objectif:** Filet de sécurité avant modifications

### Tâches

| # | Tâche | Fichiers | Effort |
|---|-------|----------|--------|
| 0.1 | Setup pytest + pytest-asyncio | pyproject.toml, conftest.py | 30 min |
| 0.2 | Test smoke /summarize | tests/api/test_smoke.py | 45 min |
| 0.3 | Test smoke /publish | tests/bot/test_smoke.py | 45 min |

### Critère de Succès

```bash
pytest tests/ -v  # 2+ tests passent
```

### Dépendances

Aucune. Phase 0 doit être faite EN PREMIER.

---

## Phase 1: Quick Wins

**Objectif:** Débloquer multi-mission + corriger erreurs critiques

### Tâches

| # | Tâche | Fichier | Lignes | Effort |
|---|-------|---------|--------|--------|
| 1.1 | VALID_MISSIONS dynamique | claude-service/config.py | 54-60 | 30 min |
| 1.2 | allowed_tools auto-généré | claude-service/config.py | 39-47 | 1h |
| 1.3 | Fix `except Exception: pass` | claude-service/loggers/workflow_logger.py | 133 | 20 min |
| 1.4 | Fix `except Exception: pass` | claude-service/mcp_tools/logger.py | 61 | 20 min |
| 1.5 | Fix `except Exception:` broad | claude-service/database.py | 83 | 20 min |
| 1.6 | mission_id param explicite | claude-service/mcp_tools/server.py | 136-177 | 1h |
| 1.7 | Supprimer DEFAULT_MISSION hardcode | bot/config.py + mcp_tools/models.py | 25, 41 | 30 min |

### Critère de Succès

```bash
# Nouvelle mission sans toucher config.py
mkdir -p claude-service/missions/crypto-news
echo "# Crypto News" > claude-service/missions/crypto-news/mission.md
# → Mission détectée automatiquement
```

### Dépendances

- Phase 0 (tests smoke)

---

## Phase 2: Simplification Layers

**Objectif:** Réduire 5 layers → 3 layers

### Architecture Cible

```
AVANT                           APRÈS
──────                          ──────
routes.py                       routes.py
    ↓                               ↓
handlers.py     ─── SUPPRIMER       │
    ↓                               │
services/                       services/
    ↓                               ↓
repositories/                   repositories/
    ↓                               ↓
models.py                       models.py

converters.py   ─── SUPPRIMER
```

### Tâches

| # | Tâche | Action | Effort |
|---|-------|--------|--------|
| 2.1 | Fusionner handlers → services | Déplacer logique handle_summarize → SummarizeService | 2h |
| 2.2 | Fusionner handlers → services | Déplacer logique handle_weekly → WeeklyService | 1.5h |
| 2.3 | Supprimer api/handlers.py | Après 2.1 + 2.2 | 10 min |
| 2.4 | Inline converters | Intégrer dans services ou supprimer | 1h |
| 2.5 | Supprimer api/converters.py | Après 2.4 | 10 min |
| 2.6 | Simplifier ExecutionDirectory | Fonctions simples dans loggers/ | 1h |
| 2.7 | Supprimer utils/execution_dir.py | Après 2.6 | 10 min |
| 2.8 | Mettre à jour imports | Tous fichiers affectés | 1h |
| 2.9 | Tests de non-régression | pytest | 30 min |

### Critère de Succès

```bash
# Structure après Phase 2
claude-service/api/
├── routes.py      # Routes → appelle services directement
└── models.py      # Request/Response Pydantic

# Supprimés:
# - api/handlers.py
# - api/converters.py
# - utils/execution_dir.py
```

### Dépendances

- Phase 1 (multi-mission fonctionne)

---

## Phase 3: Unification

**Objectif:** Éliminer duplication (loggers, models, DB)

### 3A: Unifier Loggers

```
AVANT (4 loggers)               APRÈS (1 logger)
─────────────────               ────────────────
execution_logger.py             execution_logger.py
workflow_logger.py                  ├── log_execution()
mcp/logger.py                       ├── log_workflow()
bot/command_logger.py               ├── log_mcp_operation()
                                    └── log_command()
```

| # | Tâche | Effort |
|---|-------|--------|
| 3A.1 | Créer ExecutionLogger unifié | 2h |
| 3A.2 | Migrer workflow_logger → ExecutionLogger | 1h |
| 3A.3 | Migrer mcp/logger → ExecutionLogger | 1h |
| 3A.4 | Migrer command_logger → HTTP call | 30 min |
| 3A.5 | Supprimer fichiers obsolètes | 10 min |

### 3B: Unifier Models

```
AVANT (3 Article models)        APRÈS (1 model)
────────────────────            ───────────────
api/models.py:Article           shared/models.py:Article
mcp_tools/models.py:NewsItem        ├── title, url, source
bot/services:dict                   ├── description, pub_date
                                    ├── category, confidence
                                    └── relevance_score
```

| # | Tâche | Effort |
|---|-------|--------|
| 3B.1 | Créer shared/models.py avec Article unifié | 1h |
| 3B.2 | Migrer api/models.py → shared | 30 min |
| 3B.3 | Migrer mcp_tools/models.py → shared | 30 min |
| 3B.4 | Mettre à jour bot pour utiliser shared | 30 min |

### 3C: Unifier DB Connection

```
AVANT (2 patterns)              APRÈS (1 pattern)
──────────────────              ─────────────────
database.py (asyncpg)           database.py (SQLAlchemy)
mcp/repositories (psycopg2)         ├── async session (API)
                                    └── sync session (MCP)
```

| # | Tâche | Effort |
|---|-------|--------|
| 3C.1 | SQLAlchemy sync session pour MCP | 1h |
| 3C.2 | Migrer mcp/repositories → SQLAlchemy | 2h |
| 3C.3 | Supprimer psycopg2 raw queries | 30 min |

### Critère de Succès

```bash
# 1 seul logger
ls claude-service/loggers/
# → execution_logger.py (unifié)

# 1 seul Article model
grep -r "class Article" claude-service/
# → shared/models.py:class Article

# 1 seul pattern DB
grep -r "psycopg2" claude-service/
# → (aucun résultat)
```

### Dépendances

- Phase 2 (layers simplifiés)

---

## Phase 4: Qualité

**Objectif:** Tests complets + cleanup final

### 4A: Tests

| # | Test | Couverture | Effort |
|---|------|------------|--------|
| 4A.1 | test_summarize_service.py | /summarize complet | 2h |
| 4A.2 | test_weekly_service.py | /analyze-weekly | 1.5h |
| 4A.3 | test_submit_digest.py | MCP submit_digest | 1.5h |
| 4A.4 | test_daily_cog.py | /daily command | 1h |
| 4A.5 | test_weekly_cog.py | /weekly command | 1h |
| 4A.6 | test_embed_builder.py | Discord embeds | 1h |

### 4B: Cleanup

| # | Tâche | Effort |
|---|-------|--------|
| 4B.1 | Supprimer imports inutilisés | 30 min |
| 4B.2 | Centraliser constantes (constants.py) | 1h |
| 4B.3 | Remplacer magic strings par enums | 1h |
| 4B.4 | Documenter architecture finale | 1h |

### Critère de Succès

```bash
pytest tests/ -v --cov=claude-service --cov=bot
# Coverage > 60%
# 0 warnings
```

### Dépendances

- Phase 3 (unification terminée)

---

## Résumé Effort

| Phase | Heures | Livrables |
|-------|--------|-----------|
| 0 | 2h | pytest setup + 2 tests smoke |
| 1 | 4h | Multi-mission + fix critiques |
| 2 | 8h | 3 layers, -3 fichiers |
| 3 | 6h | 1 logger, 1 model, 1 DB pattern |
| 4 | 8h | Tests + cleanup |
| **Total** | **28h** | **Projet propre** |

---

## État Final Attendu

### Structure

```
claude-service/
├── main.py
├── config.py                    # VALID_MISSIONS dynamique
├── shared/
│   └── models.py                # Article unifié
├── api/
│   ├── routes.py                # Routes → services direct
│   └── models.py                # Request/Response
├── services/
│   ├── summarize_service.py     # Ex-handlers fusionné
│   ├── weekly_service.py
│   ├── claude_service.py
│   └── digest_service.py
├── repositories/
│   └── article_repository.py
├── loggers/
│   └── execution_logger.py      # Logger unifié
├── mcp_tools/
│   ├── server.py
│   ├── services/
│   └── repositories/            # SQLAlchemy (pas psycopg2)
└── missions/                    # Auto-découvert

bot/
├── main.py
├── api.py
├── cogs/
└── services/

tests/
├── api/
├── mcp/
└── bot/
```

### Métriques

| Métrique | Avant | Après |
|----------|-------|-------|
| LOC | 7700 | ~6000 |
| Fichiers Python | 62 | ~50 |
| Layers | 5 | 3 |
| Loggers | 4 | 1 |
| Article models | 3 | 1 |
| DB patterns | 2 | 1 |
| Tests | 0 | 15+ |
| Coverage | 0% | >60% |

---

## Fichiers de Plan Détaillé

Chaque phase aura son propre fichier:

```
.claude/plans/refactoring-v2/
├── MASTER-PLAN.md          # Ce fichier
├── PHASE-0-PREPARATION.md  # À créer
├── PHASE-1-QUICK-WINS.md   # À créer
├── PHASE-2-LAYERS.md       # À créer
├── PHASE-3-UNIFICATION.md  # À créer
└── PHASE-4-QUALITY.md      # À créer
```

---

## Prochaine Étape

Créer le plan détaillé pour **Phase 0: Préparation** puis l'implémenter.
