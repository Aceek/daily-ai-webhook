# Analysis: claude-service

## Violations Identifiées

| Fichier | Ligne | Violation | Sévérité |
|---------|-------|-----------|----------|
| main.py | 1-1171 | Fichier dépasse 300L (1171 lignes) | HIGH |
| main.py | 705-840 | Fonction `summarize` 136L - dépasse limite 30L, mélange SoC | HIGH |
| main.py | 843-975 | Fonction `analyze_weekly` 132L - dépasse limite 30L | HIGH |
| main.py | 519-591 | Fonction `call_claude_cli` 72L - dépasse limite 30L | HIGH |
| main.py | 117-189 | Models Pydantic dans routes - violates SoC | HIGH |
| main.py | 1088-1165 | SQL direct dans route `/check-urls` - violates SoC | HIGH |
| main.py | 393, 604, 826 | Imports `import json` répétés (3x) - violates DRY | MED |
| main.py | 69 | Hardcoded `VALID_MISSIONS` - pas extensible | MED |
| main.py | 548 | `import os` inline dans fonction | MED |
| main.py | 230-291 | Formatage Markdown mélangé à logique | MED |
| execution_logger.py | 1-753 | Fichier dépasse 300L (753 lignes) | HIGH |
| execution_logger.py | 230-345 | Méthode `_format_summary` 115L | HIGH |
| execution_logger.py | 521-589 | Méthode `_format_workflow_md` 68L | HIGH |
| execution_logger.py | 590-629 | Mélange regex + file I/O | MED |
| execution_logger.py | 131-228 | ExecutionDirectory multiuse - violates SoC | MED |
| execution_logger.py | 385-465 | ExecutionLogger et WorkflowLogger mélangés | MED |
| mcp/server.py | 1-968 | Fichier dépasse 300L (968 lignes) | HIGH |
| mcp/server.py | 535-793 | Fonction `submit_digest` 259L | HIGH |
| mcp/server.py | 797-963 | Fonction `submit_weekly_digest` 167L | HIGH |
| mcp/server.py | 29-90 | MCPLogger custom au lieu de logging standard | MED |
| mcp/server.py | 144-210 | Fonction `get_categories` 67L | MED |
| mcp/server.py | 214-300 | Fonction `get_articles` 87L | MED |
| mcp/server.py | 304-393 | Fonction `get_article_stats` 90L | MED |
| mcp/server.py | 14-20 | Globals: `db_url`, `sync_url` | MED |
| database.py | 20-21 | Globals `_engine`, `_async_session_factory` | LOW |
| models.py | ✅ | Fichier bien structuré (142L) | OK |

## Plan de Refactoring

### Phase 1: Separation of Concerns

- [ ] Créer `api/models.py` - Déplacer modèles Pydantic de main.py
- [ ] Créer `repositories/article_repository.py` - Extraire logique DB
- [ ] Créer `services/claude_service.py` - Extraire call_claude_cli, parse_stream_output
- [ ] Créer `services/digest_service.py` - Extraire read_digest_file
- [ ] Créer `api/handlers/` - Déplacer routes dans handlers dédiés

### Phase 2: Split fichiers longs

- [ ] **main.py → api/routes.py** (~100L)
- [ ] **execution_logger.py → loggers/** (split 3 modules):
  - `loggers/execution_logger.py`
  - `loggers/workflow_logger.py`
  - `formatters/markdown_formatter.py`
- [ ] **mcp/server.py → mcp/** (split 4 modules):
  - `mcp/database.py`
  - `mcp/submit.py`
  - `mcp/logger.py`
  - `mcp/server.py`

### Phase 3: DRY

- [ ] `utils/json_utils.py` - Consolidate json patterns
- [ ] `utils/db_utils.py` - Extract common DB patterns
- [ ] `validators/digest_validators.py` - Consolidate validators
- [ ] `config.py` - Centralize VALID_MISSIONS

### Phase 4: Type hints & documentation

- [ ] Add missing return type hints
- [ ] Add docstrings Google format
- [ ] Remove unused imports

### Phase 5: Security & patterns

- [ ] Make VALID_MISSIONS configurable
- [ ] Convert MCPLogger to standard logging
- [ ] Use dependency injection for database

## Nouvelle Structure Proposée

```
claude-service/
├── main.py                    # FastAPI init only (~50L)
├── config.py                  # Settings, constants
├── database.py               # (keep as-is)
├── models.py                 # (keep as-is)
├── api/
│   ├── models.py             # Pydantic models
│   └── routes.py             # All routes
├── services/
│   ├── claude_service.py     # CLI orchestration
│   └── digest_service.py     # Digest logic
├── repositories/
│   └── article_repository.py
├── loggers/
│   ├── execution_logger.py
│   └── workflow_logger.py
├── formatters/
│   └── markdown_formatter.py
├── utils/
│   ├── json_utils.py
│   └── execution_dir.py
└── mcp/
    ├── server.py             # Entry point (~80L)
    ├── database.py           # Query tools
    ├── submit.py             # Submit handlers
    └── logger.py             # MCPLogger
```

## Dépendances

**Ordre d'exécution:**
1. config.py (no deps)
2. api/models.py (pydantic only)
3. repositories/ (database.py)
4. utils/ (pure functions)
5. formatters/ (no deps)
6. services/ (repos, utils)
7. loggers/ (formatters, utils)
8. mcp/* (config, utils)
9. api/routes.py (all services)
10. main.py (routes, database)

## Métriques Cibles

| Fichier | Current | Target | Réduction |
|---------|---------|--------|-----------|
| main.py | 1171 | ~100 | -91% |
| execution_logger.py | 753 | ~380 (split) | -50% |
| mcp/server.py | 968 | ~480 (split) | -50% |
| **Total** | **3151** | **~2200** | **-30%** |
