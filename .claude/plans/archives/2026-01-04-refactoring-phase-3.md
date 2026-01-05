# Phase 3: Unification

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Éliminer la duplication dans le codebase :
- 4 loggers → 1 logger unifié
- 3+ Article models → 1 model partagé
- 2 patterns DB (psycopg2 + asyncpg) → 1 pattern SQLAlchemy

**Architecture Cible:**

```
AVANT                                    APRÈS
------                                   ------
loggers/execution_logger.py              loggers/unified_logger.py
loggers/workflow_logger.py                   ├── log_execution()
mcp_tools/logger.py                          ├── log_workflow()
bot/services/command_logger.py               ├── log_mcp_operation()
                                             └── log_command() → HTTP

api/models.py:Article                    shared/models.py
mcp_tools/models.py:NewsItem                 ├── ArticleInput
loggers/models.py:ArticleLog                 ├── NewsItem
                                             └── ArticleLog

database.py (asyncpg)                    database.py (SQLAlchemy)
mcp_tools/repositories (psycopg2)            ├── async_session() - API
                                             └── sync_session() - MCP
```

**Tech Stack:** SQLAlchemy 2.0, Pydantic, SQLModel

**Prerequisites:** Phase 2 terminée

---

## Phase 3A: Unifier Loggers (4 → 1)

### Task 3A.1: Créer UnifiedLogger

**Files:**
- Create: `claude-service/loggers/unified_logger.py`

### Steps

**Step 3A.1.1:** Créer le logger unifié

```python
# claude-service/loggers/unified_logger.py
"""Unified Logger for Claude Service."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from loggers.models import ExecutionLog, WorkflowLog


class UnifiedLogger:
    """Unified logger managing all execution logging.

    Consolidates:
    - ExecutionLogger: Claude execution logs
    - WorkflowLogger: n8n workflow logs
    - MCPLogger: MCP tool operation logs
    """

    def __init__(self, logs_dir: str = "/app/logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._exec_dir: Path | None = None
        self._mcp_operations: list[dict[str, Any]] = []

    def create_execution_dir(self, execution_id: str, timestamp: datetime | None = None) -> Path:
        """Create execution directory structure."""
        ts = timestamp or datetime.now()
        date_str = ts.strftime("%Y-%m-%d")
        time_str = ts.strftime("%H%M%S")
        self._exec_dir = self.logs_dir / date_str / f"{time_str}_{execution_id}"
        self._exec_dir.mkdir(parents=True, exist_ok=True)
        (self._exec_dir / "raw").mkdir(exist_ok=True)
        return self._exec_dir

    def log_execution(self, execution_log: ExecutionLog, digest: dict | None = None) -> Path:
        """Save complete execution log."""
        # Save timeline, digest, summary
        ...

    def log_workflow(self, workflow_log: WorkflowLog, exec_dir: Path | None = None) -> Path:
        """Save workflow log."""
        ...

    def log_mcp_operation(self, name: str, status: str, details: str = "", **extra) -> None:
        """Log an MCP tool operation."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        entry = {"timestamp": timestamp, "name": name, "status": status, "details": details, **extra}
        self._mcp_operations.append(entry)

        symbol = "+" if status == "success" else "x" if status == "error" else "o"
        print(f"[{timestamp}] [MCP] {symbol} {name}", file=sys.stderr, flush=True)


# Global singleton
_logger: UnifiedLogger | None = None

def get_logger(logs_dir: str = "/app/logs") -> UnifiedLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = UnifiedLogger(logs_dir)
    return _logger
```

**Step 3A.1.2:** Vérification

Run:
```bash
cd claude-service && python -c "
from loggers.unified_logger import UnifiedLogger, get_logger
l = get_logger('/tmp/test')
print(l.create_execution_dir('test123'))
"
```

### Commit

```
refactor(loggers): create UnifiedLogger class
```

---

### Task 3A.2: Migrer ExecutionLogger → UnifiedLogger

**Files:**
- Modify: `claude-service/loggers/__init__.py`
- Modify: `claude-service/api/routes.py`

### Steps

**Step 3A.2.1:** Mettre à jour `loggers/__init__.py`

```python
from loggers.unified_logger import UnifiedLogger, get_logger

# Backward compatibility aliases
ExecutionLogger = UnifiedLogger
WorkflowLogger = UnifiedLogger
```

**Step 3A.2.2:** Mettre à jour imports

### Commit

```
refactor(loggers): migrate to UnifiedLogger
```

---

### Task 3A.3: Migrer MCPLogger → UnifiedLogger

**Files:**
- Modify: `claude-service/mcp_tools/server.py`
- Modify: `claude-service/mcp_tools/services/*.py`

### Steps

Remplacer:
```python
from ..logger import logger
logger.info("Message")
```

Par:
```python
from loggers import get_logger
logger = get_logger()
logger.log_mcp_operation("tool_name", "info", "Message")
```

### Commit

```
refactor(mcp): migrate MCPLogger to UnifiedLogger
```

---

### Task 3A.4: Supprimer fichiers obsolètes

**Files:**
- Delete: `claude-service/loggers/execution_logger.py`
- Delete: `claude-service/loggers/workflow_logger.py`
- Delete: `claude-service/mcp_tools/logger.py`

Run:
```bash
rm claude-service/loggers/execution_logger.py
rm claude-service/loggers/workflow_logger.py
rm claude-service/mcp_tools/logger.py
```

### Commit

```
refactor(loggers): remove obsolete logger files
```

---

## Phase 3B: Unifier Models (3 → 1)

### Task 3B.1: Créer shared/models.py

**Files:**
- Create: `claude-service/shared/__init__.py`
- Create: `claude-service/shared/models.py`

### Steps

**Step 3B.1.1:** Créer le répertoire

```bash
mkdir -p claude-service/shared
touch claude-service/shared/__init__.py
```

**Step 3B.1.2:** Créer le modèle unifié

```python
# claude-service/shared/models.py
"""Shared models for the entire application."""

from pydantic import BaseModel, Field


class ArticleInput(BaseModel):
    """Article received from RSS/API input."""
    title: str
    url: str
    source: str = ""
    description: str = ""
    pub_date: str = ""


class NewsItem(BaseModel):
    """Article selected for digest publication."""
    title: str
    summary: str
    url: str
    source: str
    category: str
    confidence: float
    relevance_score: int | None = None


class ExcludedItem(BaseModel):
    """Article excluded from digest."""
    url: str
    title: str
    category: str
    reason: str
    score: int
    source: str | None = None


class ArticleLog(BaseModel):
    """Article data for logging purposes."""
    title: str
    url: str
    source: str
    pub_date: str = ""
    description_preview: str = ""

    @classmethod
    def from_input(cls, article: ArticleInput) -> "ArticleLog":
        return cls(
            title=article.title,
            url=article.url,
            source=article.source,
            pub_date=article.pub_date,
            description_preview=article.description[:100] if article.description else "",
        )
```

### Commit

```
refactor(models): create shared/models.py with unified Article
```

---

### Task 3B.2-4: Migrer imports vers shared

**Files:**
- Modify: `claude-service/api/models.py`
- Modify: `claude-service/mcp_tools/models.py`
- Modify: `claude-service/loggers/models.py`

### Steps

```python
# api/models.py
from shared.models import ArticleInput as Article

# mcp_tools/models.py
from shared.models import NewsItem, ExcludedItem

# loggers/models.py
from shared.models import ArticleLog
```

### Commit

```
refactor(models): migrate imports to shared/models.py
```

---

## Phase 3C: Unifier DB Connection (2 → 1)

### Task 3C.1: Ajouter sync session à database.py

**Files:**
- Modify: `claude-service/database.py`

### Steps

**Step 3C.1.1:** Ajouter support sync session

```python
# claude-service/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager

_sync_engine = None
_sync_session_factory = None

async def init_db(database_url: str) -> None:
    """Initialize database connections (async + sync)."""
    global _async_engine, _sync_engine, ...

    # Async engine (for FastAPI)
    _async_engine = create_async_engine(database_url, ...)

    # Sync engine (for MCP subprocess)
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    _sync_engine = create_engine(sync_url, ...)
    _sync_session_factory = sessionmaker(bind=_sync_engine, class_=Session)

@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Get a sync database session (for MCP subprocess)."""
    session = _sync_session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### Commit

```
feat(database): add sync session support for MCP
```

---

### Task 3C.2: Migrer MCP repositories → SQLAlchemy

**Files:**
- Modify: `claude-service/mcp_tools/repositories/base.py`
- Modify: `claude-service/mcp_tools/repositories/article.py`
- Modify: `claude-service/mcp_tools/repositories/category.py`
- Modify: `claude-service/mcp_tools/repositories/digest.py`

### Steps

**Step 3C.2.1:** Modifier base.py

```python
# mcp_tools/repositories/base.py
from database import get_sync_session

@contextmanager
def get_session():
    """Get a sync database session."""
    from database import get_sync_session
    with get_sync_session() as session:
        yield session
```

**Step 3C.2.2:** Convertir raw SQL en SQLAlchemy ORM

```python
# Avant (psycopg2)
cursor.execute("SELECT * FROM articles WHERE mission_id = %s", (mission_id,))

# Après (SQLAlchemy)
from sqlalchemy import select
result = session.execute(select(Article).where(Article.mission_id == mission_id))
```

### Commit

```
refactor(mcp): migrate repositories from psycopg2 to SQLAlchemy
```

---

### Task 3C.3: Supprimer psycopg2

**Files:**
- Modify: `claude-service/requirements.txt` (retirer psycopg2-binary)

### Steps

Run:
```bash
grep -r "psycopg2" claude-service/ --include="*.py"
# → (aucun résultat)
```

### Commit

```
chore: remove psycopg2 dependency
```

---

## Success Criteria

```bash
# 1. Un seul logger unifié
ls claude-service/loggers/*.py
# → __init__.py, models.py, unified_logger.py

# 2. Models unifiés dans shared/
ls claude-service/shared/
# → __init__.py, models.py

# 3. Pas de psycopg2
grep -r "psycopg2" claude-service/
# → (vide)

# 4. Tests passent
pytest tests/ -v

# 5. Service démarre
cd claude-service && python -c "
from loggers import get_logger
from shared.models import ArticleInput, NewsItem
from database import get_sync_session
print('Phase 3 complete!')
"
```

## Summary

| Task | Fichiers | Effort |
|------|----------|--------|
| 3A.1 | Create unified_logger.py | 1h |
| 3A.2 | Migrate ExecutionLogger | 30 min |
| 3A.3 | Migrate MCPLogger | 30 min |
| 3A.4 | Delete obsolete files | 10 min |
| 3B.1 | Create shared/models.py | 45 min |
| 3B.2-4 | Migrate imports | 30 min |
| 3C.1 | Add sync session | 45 min |
| 3C.2 | Migrate repositories | 1.5h |
| 3C.3 | Remove psycopg2 | 10 min |
| **Total** | | **~6h** |
