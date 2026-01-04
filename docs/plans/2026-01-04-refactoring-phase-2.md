# Phase 2: Simplification Layers

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Réduire de 5 layers à 3 layers en éliminant `handlers.py` et `converters.py`.

**Architecture:**

```
AVANT (5 layers)                    APRÈS (3 layers)
----------------                    ----------------
routes.py                           routes.py
    │                                   │
handlers.py  ───► SUPPRIMER             │
    │                                   │
services/                           services/
    │                                   │
converters.py ──► SUPPRIMER             │
    │                                   │
repositories/                       repositories/
    │                                   │
models.py                           models.py

utils/execution_dir.py ──► INLINE dans loggers/
```

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest

**Prerequisites:** Phase 0 et Phase 1 complétées

---

## Task 2.1: Créer SummarizeService

**Objectif:** Déplacer la logique de `handle_summarize` vers un nouveau service dédié.

### Files

| Action | Path |
|--------|------|
| Create | `claude-service/services/summarize_service.py` |
| Modify | `claude-service/api/routes.py` |

### Steps

**Step 2.1.1:** Créer le fichier SummarizeService

```python
# claude-service/services/summarize_service.py
"""Summarize service for Claude Service."""

import logging
import time
import uuid
from pathlib import Path

from api.models import SummarizeRequest, SummarizeResponse, ClaudeResult
from config import Settings, validate_mission
from loggers.execution_logger import ExecutionLogger, create_execution_log
from services.claude_service import call_claude_cli, write_articles_file
from services.digest_service import read_digest_file
from services.prompt_builder import build_prompt


logger = logging.getLogger("claude-service")


class SummarizeService:
    """Service for handling article summarization."""

    def __init__(self, settings: Settings, execution_logger: ExecutionLogger):
        self.settings = settings
        self.execution_logger = execution_logger

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        """Process summarize request."""
        # Validate mission
        valid, error = validate_mission(request.mission, self.settings.missions_path)
        if not valid:
            return SummarizeResponse(success=False, error=error, ...)

        # Create execution dir, call Claude, build response
        # ... (logique extraite de handle_summarize)
```

**Step 2.1.2:** Mettre à jour routes.py

```python
# Remplacer import handlers par services
from services.summarize_service import SummarizeService

def create_routers(settings, execution_logger, workflow_logger):
    router = APIRouter()
    summarize_service = SummarizeService(settings, execution_logger)

    @router.post("/summarize")
    async def summarize(request: SummarizeRequest):
        return await summarize_service.summarize(request)
```

**Step 2.1.3:** Tester

Run:
```bash
cd claude-service && python -c "from services.summarize_service import SummarizeService; print('OK')"
```

### Commit

```
refactor(api): extract SummarizeService from handlers
```

---

## Task 2.2: Créer WeeklyService

**Objectif:** Déplacer la logique de `handle_analyze_weekly` vers un nouveau service.

### Files

| Action | Path |
|--------|------|
| Create | `claude-service/services/weekly_service.py` |
| Modify | `claude-service/api/routes.py` |

### Steps

**Step 2.2.1:** Créer le fichier WeeklyService

```python
# claude-service/services/weekly_service.py
"""Weekly analysis service for Claude Service."""

class WeeklyService:
    """Service for handling weekly analysis."""

    def __init__(self, settings: Settings, execution_logger: ExecutionLogger):
        self.settings = settings
        self.execution_logger = execution_logger

    async def analyze_weekly(self, request: AnalyzeWeeklyRequest) -> AnalyzeWeeklyResponse:
        """Process weekly analysis request."""
        # ... (logique extraite de handle_analyze_weekly)
```

**Step 2.2.2:** Mettre à jour routes.py

```python
from services.weekly_service import WeeklyService

weekly_service = WeeklyService(settings, execution_logger)

@router.post("/analyze-weekly")
async def analyze_weekly(request: AnalyzeWeeklyRequest):
    return await weekly_service.analyze_weekly(request)
```

### Commit

```
refactor(api): extract WeeklyService from handlers
```

---

## Task 2.3: Migrer handle_log_workflow et handle_check_urls

**Objectif:** Inliner les handlers restants dans routes.py.

### Files

| Action | Path |
|--------|------|
| Modify | `claude-service/api/routes.py` |

### Steps

**Step 2.3.1:** Inline handle_log_workflow

```python
def _convert_workflow_request(request: WorkflowLogRequest) -> WorkflowLog:
    """Convert API request to WorkflowLog model."""
    # ... conversion logic

@router.post("/log-workflow")
async def log_workflow(request: WorkflowLogRequest):
    workflow_log = _convert_workflow_request(request)
    log_path = workflow_logger.save(workflow_log)
    return WorkflowLogResponse(success=True, log_file=str(log_path))
```

**Step 2.3.2:** Inline handle_check_urls

```python
@router.post("/check-urls")
async def check_urls(request: CheckUrlsRequest):
    engine = get_engine()
    if not engine:
        return CheckUrlsResponse(new_urls=request.urls, duplicate_urls=[], ...)
    new_urls, duplicates = await check_duplicate_urls(engine, request.urls, ...)
    return CheckUrlsResponse(new_urls=new_urls, duplicate_urls=duplicates, ...)
```

### Commit

```
refactor(api): inline remaining handlers into routes
```

---

## Task 2.4: Supprimer handlers.py

### Files

| Action | Path |
|--------|------|
| Delete | `claude-service/api/handlers.py` |

### Steps

**Step 2.4.1:** Vérifier qu'aucun import ne reste

Run:
```bash
grep -r "from api.handlers" claude-service/ --include="*.py"
```

Expected: Aucun résultat

**Step 2.4.2:** Supprimer le fichier

Run:
```bash
rm claude-service/api/handlers.py
```

### Commit

```
refactor(api): remove obsolete handlers.py
```

---

## Task 2.5: Supprimer converters.py

### Files

| Action | Path |
|--------|------|
| Delete | `claude-service/api/converters.py` |

### Steps

**Step 2.5.1:** Vérifier qu'aucun import ne reste

Run:
```bash
grep -r "from api.converters" claude-service/ --include="*.py"
```

**Step 2.5.2:** Supprimer le fichier

Run:
```bash
rm claude-service/api/converters.py
```

### Commit

```
refactor(api): remove obsolete converters.py
```

---

## Task 2.6: Simplifier ExecutionDirectory

**Objectif:** Intégrer ExecutionDirectory dans execution_logger.py.

### Files

| Action | Path |
|--------|------|
| Modify | `claude-service/loggers/execution_logger.py` |
| Modify | `claude-service/services/claude_service.py` |
| Modify | `claude-service/services/digest_service.py` |

### Steps

**Step 2.6.1:** Copier ExecutionDirectory dans execution_logger.py

**Step 2.6.2:** Mettre à jour les imports

```python
# Avant
from utils.execution_dir import ExecutionDirectory

# Après
from loggers.execution_logger import ExecutionDirectory
```

### Commit

```
refactor(loggers): inline ExecutionDirectory into execution_logger
```

---

## Task 2.7: Supprimer utils/execution_dir.py

### Files

| Action | Path |
|--------|------|
| Delete | `claude-service/utils/execution_dir.py` |

### Steps

Run:
```bash
rm claude-service/utils/execution_dir.py
```

### Commit

```
refactor(utils): remove obsolete execution_dir.py
```

---

## Task 2.8: Mettre à jour tous les imports

### Steps

**Step 2.8.1:** Vérifier imports cassés

Run:
```bash
cd claude-service && python -c "
from api.routes import create_routers
from services.summarize_service import SummarizeService
from services.weekly_service import WeeklyService
from loggers.execution_logger import ExecutionLogger, ExecutionDirectory
print('All imports OK')
"
```

### Commit

```
refactor(imports): update all imports after layer simplification
```

---

## Task 2.9: Tests de non-régression

### Steps

**Step 2.9.1:** Exécuter tous les tests

Run:
```bash
pytest tests/ -v --tb=short
```

Expected: Tous les tests passent

**Step 2.9.2:** Vérifier la structure finale

Run:
```bash
ls -la claude-service/api/
# → __init__.py  models.py  routes.py
# (PAS de handlers.py ni converters.py)

ls -la claude-service/services/
# → summarize_service.py  weekly_service.py  ...
```

### Commit

```
test: verify phase 2 refactoring complete
```

---

## Success Criteria

```bash
# Structure après Phase 2
ls claude-service/api/
# → __init__.py  models.py  routes.py

# Fichiers supprimés
ls claude-service/api/handlers.py 2>&1 | grep "No such file"
ls claude-service/api/converters.py 2>&1 | grep "No such file"
ls claude-service/utils/execution_dir.py 2>&1 | grep "No such file"

# Tests passent
pytest tests/ -v
```

## Files Summary

| Action | Fichier | Raison |
|--------|---------|--------|
| Create | `services/summarize_service.py` | Nouveau service pour /summarize |
| Create | `services/weekly_service.py` | Nouveau service pour /analyze-weekly |
| Modify | `api/routes.py` | Appelle services directement |
| Modify | `loggers/execution_logger.py` | Intègre ExecutionDirectory |
| Delete | `api/handlers.py` | Logique déplacée vers services |
| Delete | `api/converters.py` | Logique inlinée dans routes |
| Delete | `utils/execution_dir.py` | Déplacé vers loggers |

**Effort Total:** ~8h
