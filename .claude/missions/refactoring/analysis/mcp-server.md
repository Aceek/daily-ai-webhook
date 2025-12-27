# Analysis: mcp-server

## Violations Identifiées

| Fichier | Ligne | Violation | Sévérité |
|---------|-------|-----------|----------|
| server.py | 1-968 | File exceeds 300-line limit (968 total) | HIGH |
| server.py | 535 | `submit_digest()`: 262 lines (max 30) | HIGH |
| server.py | 797 | `submit_weekly_digest()`: 172 lines (max 30) | HIGH |
| server.py | 304 | `get_article_stats()`: 93 lines (max 30) | HIGH |
| server.py | 214 | `get_articles()`: 90 lines (max 30) | HIGH |
| server.py | 397 | `get_recent_headlines()`: 70 lines (max 30) | HIGH |
| server.py | 145 | `get_categories()`: 69 lines (max 30) | HIGH |
| server.py | 64-74 | MCPLogger missing return type hints | MED |
| server.py | 169-210 | SQL embedded in `get_categories()` handler | MED |
| server.py | 244-300 | SQL embedded in `get_articles()` handler | MED |
| server.py | 328-393 | SQL embedded in `get_article_stats()` (4 queries) | MED |
| server.py | 424-459 | SQL embedded in `get_recent_headlines()` | MED |
| server.py | 656-752 | Mixed concerns in `submit_digest()` | MED |
| server.py | 692-735 | Duplicate article insert patterns | MED |
| server.py | 748 | Bare `except Exception` | LOW |
| server.py | 893-910 | Repeated DB ops from submit_digest | MED |
| server.py | 467-481 | Missing type hints on cursor param | LOW |
| server.py | 45 | `_write()` I/O nested in handler - poor SoC | MED |
| server.py | 6x | Connection lifecycle pattern duplicated | HIGH |

## Plan de Refactoring

### Phase 1: Extract Repositories

- [ ] **1.1** Create `repositories/base.py` - DatabaseConnection context manager
- [ ] **1.2** Create `repositories/category.py`
  - `get_categories_by_mission(mission_id, date_from, date_to) -> list[dict]`
  - `get_or_create_category(mission_id, category_name) -> int`
- [ ] **1.3** Create `repositories/article.py`
  - `get_articles(mission_id, categories, date_from, date_to, limit) -> list[dict]`
  - `get_recent_headlines(mission_id, days) -> list[dict]`
  - `insert_article(...) -> None`
  - `insert_excluded_article(...) -> None`
- [ ] **1.4** Create `repositories/stats.py`
  - `get_total_articles(mission_id, date_from, date_to) -> int`
  - `get_articles_by_category(...) -> dict`
  - `get_articles_by_source(...) -> dict`
  - `get_articles_by_day(...) -> dict`
- [ ] **1.5** Create `repositories/digest.py`
  - `insert_daily_digest(mission_id, date, content) -> int`
  - `insert_weekly_digest(...) -> int`
  - `batch_insert_articles(articles, excluded) -> tuple[int, int]`

### Phase 2: Extract Validation & Utils

- [ ] **2.1** Create `validators.py`
  - `DigestValidator.validate_daily_digest(...) -> list[str]`
  - `DigestValidator.validate_weekly_digest(...) -> list[str]`
- [ ] **2.2** Create `models.py` (Pydantic)
  - `NewsItemModel`, `ExcludedItemModel`
  - `DailyDigestModel`, `WeeklyDigestModel`
- [ ] **2.3** Create `utils.py`
  - `_compute_exclusion_breakdown()`
  - `get_output_dir()`
  - `build_digest_structure(...) -> dict`
  - `write_digest_to_file(...) -> Path`
- [ ] **2.4** Create `logger.py`
  - Extract MCPLogger class
  - Add type hints

### Phase 3: Refactor Tool Handlers

- [ ] **3.1** Create `DigestSubmitter` class
  - `submit_daily(...) -> dict` (10-15 lines)
  - `_validate_input()`, `_save_to_database()`, `_save_to_file()`
- [ ] **3.2** Create `WeeklyDigestSubmitter` class
  - `submit_weekly(...) -> dict`
- [ ] **3.3** Create `ArticleQueryService` class
  - `get_categories(...)`, `get_articles(...)`
  - `get_article_stats(...)`, `get_recent_headlines(...)`

### Phase 4: Update server.py

- [ ] **4.1** Restructure to entry point only (~150 lines)
  - Import dependencies
  - Register MCP tools as thin wrappers

### Phase 5: DRY

- [ ] **5.1** Consolidate article insert patterns
- [ ] **5.2** Create `DatabaseTransaction` context manager
- [ ] **5.3** Create `ResponseBuilder` class

### Phase 6: Security & Quality

- [ ] **6.1** Add return type hints to all methods
- [ ] **6.2** Replace bare exceptions with specific types
- [ ] **6.3** Add input validation
- [ ] **6.4** Verify SQL injection prevention

## Nouvelle Structure Proposée

```
claude-service/mcp/
├── server.py                    # Entry point (~150 lines)
├── logger.py                    # MCPLogger (~100 lines)
├── models.py                    # Pydantic models (~80 lines)
├── validators.py                # Validation logic (~100 lines)
├── utils.py                     # Helper functions (~80 lines)
├── services/
│   ├── article_query.py         # ArticleQueryService (~150 lines)
│   ├── digest_submitter.py      # DigestSubmitter (~100 lines)
│   └── weekly_digest.py         # WeeklyDigestSubmitter (~80 lines)
└── repositories/
    ├── base.py                  # DatabaseConnection (~80 lines)
    ├── category.py              # CategoryRepository (~60 lines)
    ├── article.py               # ArticleRepository (~200 lines)
    ├── stats.py                 # StatsRepository (~150 lines)
    └── digest.py                # DigestRepository (~120 lines)
```

## Dépendances

```
Phase 1 (repos/base.py)
    ↓
Phase 1 (all repositories) [parallel with Phase 2]
    ↓
Phase 2 (validators, models, utils)
    ↓
Phase 3 (services)
    ↓
Phase 4 (server.py refactor)
    ↓
Phase 5 & 6 (polish)
```

## Métriques Cibles

| File | Current | Target | Status |
|------|---------|--------|--------|
| server.py | 968 | 150 | -85% |
| repositories/* | - | 620 | NEW |
| services/* | - | 330 | NEW |
| validators.py | - | 100 | NEW |
| models.py | - | 80 | NEW |
| logger.py | 93 | 100 | MOVE |
| utils.py | - | 80 | NEW |
| **Total** | **968** | **~1,360** | Split into modules < 200L |
