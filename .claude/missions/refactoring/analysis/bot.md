# Analysis: bot

## Violations Identifiées

| Fichier | Ligne | Violation | Sévérité |
|---------|-------|-----------|----------|
| card_generator.py | 28-342 | Fichier > 300 lignes (407 total) | HIGH |
| embed_builder.py | 59-156 | DRY: 4 format functions quasi-identiques (92L) | HIGH |
| embed_builder.py | 250-341 | Fichier > 300 lignes (341 total) | HIGH |
| publisher.py | 103-233 | DRY: publish_daily/weekly identiques (128L) | HIGH |
| api.py | 26-29 | Global mutable state (_bot) | MED |
| api.py | 174-176 | Global mutable dict (_callbacks) | MED |
| database.py | 45-117 | DRY: get_latest/get_by_date identiques (70L) | MED |
| database.py | 23-41 | Global mutable state (_pool) | LOW |
| card_generator.py | 31 | `__init__` sans return type | LOW |
| card_generator.py | 39-63 | Méthode `_get_hti` 25L | MED |
| cogs/weekly.py | 28-38 | `get_last_7_days()` hors module services | MED |
| cogs/admin.py | 30-106 | Méthode `status` 77L | HIGH |
| cogs/admin.py | 108-189 | Méthode `stats` 82L | HIGH |
| api.py | 115-172 | `publish_digest` 58L mélange routing + logique | MED |
| main.py | 98-107 | `run_api_server` sans DI | LOW |
| services/ | All | Logique d'affichage dans publisher/embeds | MED |
| card_generator.py | 138-145 | Import datetime local | LOW |

## Plan de Refactoring

### Phase 1: Extraction Models & SoC

- [ ] **1.1** Créer `services/models.py` - PublishRequest, PublishResponse, DigestResult
- [ ] **1.2** Créer `services/repositories/digest_repository.py` - queries
- [ ] **1.3** Créer `services/formatters/embed_formatters.py` - consolidate format_*_item
- [ ] **1.4** Créer `services/utils/date_utils.py` - get_last_7_days()

### Phase 2: Split Long Functions

- [ ] **2.1** card_generator.py: split `_render_html_to_image()`
- [ ] **2.2** cogs/admin.py: extraire `_check_db_health()`, `_check_claude_health()`
- [ ] **2.3** cogs/admin.py: extraire `_build_stats_embed()`
- [ ] **2.4** api.py: extraire logique vers services/publisher.py

### Phase 3: DRY - Consolidate Formatters

- [ ] **3.1** embed_builder.py: 4 `format_*_item()` → 1 générique
- [ ] **3.2** embed_builder.py: extraire `_build_category_list()` helper
- [ ] **3.3** publisher.py: consolidate publish_daily/weekly → `publish_digest(type)`

### Phase 4: DRY - Database Queries

- [ ] **4.1** Créer `_fetch_digest()` helper générique
- [ ] **4.2** Réduire get_latest/get_by_date à wrappers

### Phase 5: State Management

- [ ] **5.1** api.py: `global _bot` → FastAPI app.state
- [ ] **5.2** api.py: `global _callbacks` → proper store
- [ ] **5.3** database.py: documenter _pool pattern
- [ ] **5.4** card_generator.py: documenter singleton

### Phase 6: Type Hints & Docs

- [ ] **6.1** card_generator.py: `-> None` sur `__init__()`
- [ ] **6.2** card_generator.py: déplacer import datetime top-level
- [ ] **6.3** Vérifier 100% type hints functions publiques
- [ ] **6.4** Ajouter docstrings Google format

## Nouvelle Structure Proposée

```
bot/
├── main.py                          (155L) ✅
├── api.py                           (204L → 140L)
├── config.py                        (32L) ✅
├── cogs/
│   ├── daily.py                     (102L) ✅
│   ├── weekly.py                    (243L) ✅
│   └── admin.py                     (225L → 120L)
└── services/
    ├── database.py                  (254L → 180L)
    ├── publisher.py                 (232L → 150L)
    ├── card_generator.py            (407L → 300L)
    ├── embed_builder.py             (341L → 250L)
    ├── command_logger.py            (186L) ✅
    ├── claude_client.py             (98L) ✅
    ├── models.py                    📝 NEW
    ├── repositories/
    │   └── digest_repository.py     📝 NEW
    ├── formatters/
    │   └── embed_formatters.py      📝 NEW
    └── utils/
        └── date_utils.py            📝 NEW
```

## Dépendances

**Ordre d'exécution:**
1. Phase 1 (parallel): 1.1, 1.2, 1.3, 1.4
2. Phase 2.1, 2.2 (parallel)
3. Phase 2.3 (dépend 2.2)
4. Phase 2.4 (dépend 1.1)
5. Phase 3.1 (dépend 1.3)
6. Phase 3.2, 3.3 (dépend 3.1)
7. Phase 4 (dépend 1.2)
8. Phase 5, 6 (indépendant)

## Résumé Réductions

| Fichier | Avant | Après | Réduction |
|---------|-------|-------|-----------|
| embed_builder.py | 341 | 220 | -36% |
| card_generator.py | 407 | 320 | -21% |
| publisher.py | 232 | 120 | -48% |
| api.py | 204 | 120 | -41% |
| cogs/admin.py | 225 | 100 | -56% |
| database.py | 254 | 180 | -29% |
| **TOTAL** | **1663** | **1040** | **-37%** |
