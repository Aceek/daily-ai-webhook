# Post-Refactoring Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Supprimer 878 LOC de dead code et améliorer l'error handling (34 occurrences de `except Exception:`).

**Architecture:** Cleanup en 3 phases: (1) suppression fichiers morts, (2) error handling critique, (3) tests additionnels.

**Tech Stack:** Python 3.12, pytest, SQLAlchemy, discord.py

**Prerequisites:** Refactoring Phase 1-4 terminé, 33 tests passent.

---

## Phase 1: Dead Code Cleanup (-878 LOC)

### Task 1.1: Vérifier les imports avant suppression

**Files:**
- Analyze: `claude-service/` (grep imports)

**Step 1.1.1:** Chercher imports vers fichiers à supprimer

Run:
```bash
cd /home/ilan/code/active/daily-ai-webhook
grep -r "from.*execution_logger import" claude-service/ --include="*.py" | grep -v __pycache__
grep -r "from.*workflow_logger import" claude-service/ --include="*.py" | grep -v __pycache__
grep -r "from.*handlers import" claude-service/ --include="*.py" | grep -v __pycache__
grep -r "from.*converters import" claude-service/ --include="*.py" | grep -v __pycache__
```

Expected: Lister tous les imports à corriger avant suppression.

**Step 1.1.2:** Noter les fichiers à modifier

Document which files import from dead files and need updating.

---

### Task 1.2: Mettre à jour loggers/__init__.py

**Files:**
- Modify: `claude-service/loggers/__init__.py`

**Step 1.2.1:** Lire le fichier actuel

```bash
cat claude-service/loggers/__init__.py
```

**Step 1.2.2:** Supprimer imports vers fichiers morts

Le fichier doit seulement exporter depuis `unified_logger.py`:

```python
"""Logging utilities for Claude Service."""

from loggers.unified_logger import UnifiedLogger, get_logger
from loggers.models import ExecutionLog, WorkflowLog, StreamEvent

# Backward compatibility aliases
ExecutionLogger = UnifiedLogger
WorkflowLogger = UnifiedLogger

__all__ = [
    "UnifiedLogger",
    "ExecutionLogger",
    "WorkflowLogger",
    "get_logger",
    "ExecutionLog",
    "WorkflowLog",
    "StreamEvent",
]
```

**Step 1.2.3:** Vérifier syntaxe

Run:
```bash
cd /home/ilan/code/active/daily-ai-webhook/claude-service
python3 -m py_compile loggers/__init__.py && echo "OK"
```

Expected: `OK`

---

### Task 1.3: Supprimer execution_logger.py

**Files:**
- Delete: `claude-service/loggers/execution_logger.py`

**Step 1.3.1:** Supprimer le fichier

Run:
```bash
rm /home/ilan/code/active/daily-ai-webhook/claude-service/loggers/execution_logger.py
```

**Step 1.3.2:** Vérifier pas d'erreur d'import

Run:
```bash
cd /home/ilan/code/active/daily-ai-webhook/claude-service
python3 -c "from loggers import get_logger, ExecutionLogger; print('OK')"
```

Expected: `OK`

---

### Task 1.4: Supprimer workflow_logger.py

**Files:**
- Delete: `claude-service/loggers/workflow_logger.py`

**Step 1.4.1:** Supprimer le fichier

Run:
```bash
rm /home/ilan/code/active/daily-ai-webhook/claude-service/loggers/workflow_logger.py
```

**Step 1.4.2:** Vérifier pas d'erreur d'import

Run:
```bash
cd /home/ilan/code/active/daily-ai-webhook/claude-service
python3 -c "from loggers import get_logger, WorkflowLogger; print('OK')"
```

Expected: `OK`

---

### Task 1.5: Mettre à jour api/__init__.py

**Files:**
- Modify: `claude-service/api/__init__.py`

**Step 1.5.1:** Lire le fichier actuel

```bash
cat claude-service/api/__init__.py
```

**Step 1.5.2:** Supprimer imports vers handlers et converters

Le fichier doit seulement exporter depuis `routes.py` et `models.py`.

---

### Task 1.6: Supprimer handlers.py

**Files:**
- Delete: `claude-service/api/handlers.py`

**Step 1.6.1:** Supprimer le fichier

Run:
```bash
rm /home/ilan/code/active/daily-ai-webhook/claude-service/api/handlers.py
```

**Step 1.6.2:** Vérifier pas d'erreur d'import

Run:
```bash
cd /home/ilan/code/active/daily-ai-webhook/claude-service
python3 -c "from api.routes import create_routers; print('OK')"
```

Expected: `OK`

---

### Task 1.7: Supprimer converters.py

**Files:**
- Delete: `claude-service/api/converters.py`

**Step 1.7.1:** Supprimer le fichier

Run:
```bash
rm /home/ilan/code/active/daily-ai-webhook/claude-service/api/converters.py
```

**Step 1.7.2:** Vérifier pas d'erreur d'import

Run:
```bash
cd /home/ilan/code/active/daily-ai-webhook/claude-service
python3 -c "from api.routes import create_routers; print('OK')"
```

Expected: `OK`

---

### Task 1.8: Lancer tous les tests

**Step 1.8.1:** Tests locaux

Run:
```bash
cd /home/ilan/code/active/daily-ai-webhook
docker-compose exec claude-service pytest tests/ -v --tb=short
```

Expected: 33 tests passent

**Step 1.8.2:** Commit Phase 1

Run:
```bash
git add -A
git commit -m "chore: remove dead code after refactoring

Delete obsolete files replaced by unified patterns:
- loggers/execution_logger.py (replaced by unified_logger.py)
- loggers/workflow_logger.py (replaced by unified_logger.py)
- api/handlers.py (replaced by services/)
- api/converters.py (inlined in routes.py)

Gain: -878 LOC"
```

---

## Phase 2: Error Handling - High Priority

### Task 2.1: Fix database.py error handling

**Files:**
- Modify: `claude-service/database.py:114,140`

**Step 2.1.1:** Lire le fichier

```bash
cat -n claude-service/database.py | head -150
```

**Step 2.1.2:** Remplacer `except Exception:` par exceptions spécifiques

Dans `get_async_session()` (ligne ~114):
```python
except SQLAlchemyError:
    await session.rollback()
    raise
```

Dans `get_sync_session()` (ligne ~140):
```python
except SQLAlchemyError:
    session.rollback()
    raise
```

**Step 2.1.3:** Vérifier l'import SQLAlchemyError existe

```python
from sqlalchemy.exc import SQLAlchemyError
```

**Step 2.1.4:** Vérifier syntaxe

Run:
```bash
python3 -m py_compile claude-service/database.py && echo "OK"
```

---

### Task 2.2: Fix MCP article_query.py error handling

**Files:**
- Modify: `claude-service/mcp_tools/services/article_query.py:52,101,141,182`

**Step 2.2.1:** Lire le fichier

```bash
cat -n claude-service/mcp_tools/services/article_query.py
```

**Step 2.2.2:** Remplacer chaque `except Exception:` par:

```python
except (SQLAlchemyError, ValueError) as e:
    logger.mcp_error(f"Query failed: {e}")
    return {"status": "error", "error": str(e), "data": []}
```

**Step 2.2.3:** Ajouter import si nécessaire

```python
from sqlalchemy.exc import SQLAlchemyError
```

**Step 2.2.4:** Vérifier syntaxe

Run:
```bash
python3 -m py_compile claude-service/mcp_tools/services/article_query.py && echo "OK"
```

---

### Task 2.3: Fix MCP digest_submitter.py error handling

**Files:**
- Modify: `claude-service/mcp_tools/services/digest_submitter.py:198`

**Step 2.3.1:** Lire le fichier

```bash
cat -n claude-service/mcp_tools/services/digest_submitter.py | tail -50
```

**Step 2.3.2:** Remplacer `except Exception:` par:

```python
except (SQLAlchemyError, ValidationError, IOError) as e:
    logger.mcp_error(f"Digest submission failed: {e}")
    return {"status": "error", "error": str(e)}
```

**Step 2.3.3:** Vérifier syntaxe

Run:
```bash
python3 -m py_compile claude-service/mcp_tools/services/digest_submitter.py && echo "OK"
```

---

### Task 2.4: Fix bot cogs error handling

**Files:**
- Modify: `bot/cogs/daily.py:86,93`
- Modify: `bot/cogs/weekly.py:91,98,186,221`

**Step 2.4.1:** Lire daily.py

```bash
cat -n bot/cogs/daily.py
```

**Step 2.4.2:** Remplacer `except Exception:` par pattern:

```python
except discord.HTTPException as e:
    logger.error(f"Discord API error: {e}")
    await interaction.followup.send(f"Discord error: {e.text}", ephemeral=True)
except ValueError as e:
    logger.error(f"Value error: {e}")
    await interaction.followup.send(f"Invalid input: {e}", ephemeral=True)
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    await interaction.followup.send("An unexpected error occurred.", ephemeral=True)
```

**Step 2.4.3:** Appliquer même pattern à weekly.py

**Step 2.4.4:** Vérifier syntaxe

Run:
```bash
python3 -m py_compile bot/cogs/daily.py bot/cogs/weekly.py && echo "OK"
```

---

### Task 2.5: Commit Phase 2

Run:
```bash
git add claude-service/database.py claude-service/mcp_tools/services/*.py bot/cogs/*.py
git commit -m "fix: improve error handling with specific exceptions

Replace broad 'except Exception:' with specific exception types:
- database.py: SQLAlchemyError for DB operations
- article_query.py: SQLAlchemyError, ValueError for queries
- digest_submitter.py: SQLAlchemyError, ValidationError, IOError
- daily.py, weekly.py: discord.HTTPException, ValueError

Improves debugging and error tracking."
```

---

## Phase 3: Tests et Vérification Finale

### Task 3.1: Rebuild et test complet

**Step 3.1.1:** Rebuild Docker

Run:
```bash
cd /home/ilan/code/active/daily-ai-webhook
docker-compose up -d --build claude-service
```

**Step 3.1.2:** Attendre healthy

Run:
```bash
sleep 15 && docker-compose ps
```

Expected: All services healthy

**Step 3.1.3:** Lancer tests

Run:
```bash
docker-compose exec claude-service pytest tests/ -v
```

Expected: 33+ tests passent

---

### Task 3.2: Vérifier API endpoints

**Step 3.2.1:** Health check

Run:
```bash
curl -s http://localhost:8080/health | jq .
```

Expected: `{"status": "healthy", ...}`

**Step 3.2.2:** Vérifier logs

Run:
```bash
docker-compose logs claude-service --tail 20 | grep -i error || echo "No errors"
```

Expected: `No errors`

---

### Task 3.3: Commit final et push

Run:
```bash
git status
git log --oneline -5
```

Si tout est OK:
```bash
git push origin main
```

---

## Success Criteria

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Dead code files | 4 | 0 | 0 |
| LOC removed | 0 | 878 | 878 |
| Broad exceptions | 34 | ~15 | <20 |
| Tests passing | 33 | 33+ | 33+ |
| Services healthy | Yes | Yes | Yes |

---

## Rollback Plan

Si problème après suppression:

```bash
git checkout HEAD~1 -- claude-service/loggers/execution_logger.py
git checkout HEAD~1 -- claude-service/loggers/workflow_logger.py
git checkout HEAD~1 -- claude-service/api/handlers.py
git checkout HEAD~1 -- claude-service/api/converters.py
```

---

## Summary

| Phase | Tasks | Effort | Impact |
|-------|-------|--------|--------|
| Phase 1 | 1.1-1.8 | 30 min | -878 LOC |
| Phase 2 | 2.1-2.5 | 45 min | 15+ fixes |
| Phase 3 | 3.1-3.3 | 15 min | Validation |
| **Total** | **16 tasks** | **~1.5h** | **Clean codebase** |
