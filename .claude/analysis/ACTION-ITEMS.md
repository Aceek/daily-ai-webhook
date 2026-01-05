# Action Items - Post-Refactoring Cleanup

Date: 2026-01-05
Priority: Critical → High → Medium → Low

## Critical (Fix Now)

Aucun probleme critique bloquant. Le code est pret pour production.

## High (Fix This Week)

### H1. Supprimer ExecutionLogger duplique
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/loggers/execution_logger.py:1-322` - **DELETE FILE** - Completement duplique dans UnifiedLogger

**Fix:**
```bash
rm claude-service/loggers/execution_logger.py
# Mettre a jour imports si necessaire (verifier avec grep)
```

**Gain:** -321 LOC

---

### H2. Supprimer WorkflowLogger duplique
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/loggers/workflow_logger.py:1-146` - **DELETE FILE** - Toutes les methodes sont dans UnifiedLogger

**Fix:**
```bash
rm claude-service/loggers/workflow_logger.py
# UnifiedLogger.save_workflow() remplace WorkflowLogger.save()
```

**Gain:** -146 LOC

---

### H3. Supprimer ExecutionDirectory de loggers/
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/loggers/execution_logger.py:23-145` - ExecutionDirectory defini ici ET dans utils/execution_dir.py

**Fix:**
```python
# Garder seulement utils/execution_dir.py
# Supprimer de execution_logger.py (mais H1 supprime deja tout le fichier)
# Verifier que tous les imports utilisent:
from utils.execution_dir import ExecutionDirectory
```

**Gain:** -123 LOC (inclus dans H1)

---

### H4. Supprimer handlers.py (code mort)
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/api/handlers.py:1-317` - **DELETE FILE** - Remplace par SummarizeService et WeeklyService

**Fix:**
```bash
# Verifier qu'aucun import ne reference handlers.py
grep -r "from.*handlers import" claude-service/
# Si vide (sauf converters.py qui sera supprime), supprimer:
rm claude-service/api/handlers.py
```

**Gain:** -316 LOC

---

### H5. Supprimer converters.py (duplique dans routes.py)
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/api/converters.py:1-95` - **DELETE FILE** - Fonction `_convert_workflow_request()` dupliquee dans routes.py

**Fix:**
```bash
# La fonction est maintenant inline dans routes.py (lignes 157-254)
rm claude-service/api/converters.py
# Supprimer import dans handlers.py (mais handlers.py sera supprime)
```

**Gain:** -95 LOC

---

### H6. Ameliorer error handling - Database
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/database.py:114` - `except Exception:` trop large - Utiliser `SQLAlchemyError`
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/database.py:140` - `except Exception:` trop large - Utiliser `SQLAlchemyError`

**Fix:**
```python
# Ligne 114
except SQLAlchemyError:
    await session.rollback()
    raise
except Exception as e:
    await session.rollback()
    logger.error("Unexpected error in database session: %s", e)
    raise RuntimeError(f"Database session error: {e}") from e

# Ligne 140
except SQLAlchemyError:
    session.rollback()
    raise
except Exception as e:
    session.rollback()
    logger.error("Unexpected error in sync database session: %s", e)
    raise RuntimeError(f"Database session error: {e}") from e
```

---

### H7. Ameliorer error handling - MCP Services
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/mcp_tools/services/article_query.py:52` - `except Exception:` - Specifier `SQLAlchemyError, ValueError`
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/mcp_tools/services/article_query.py:101` - `except Exception:` - Specifier exceptions
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/mcp_tools/services/article_query.py:141` - `except Exception:` - Specifier exceptions
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/mcp_tools/services/article_query.py:182` - `except Exception:` - Specifier exceptions
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/mcp_tools/services/digest_submitter.py:198` - `except Exception:` - Specifier exceptions

**Fix template:**
```python
except (SQLAlchemyError, ValueError) as e:
    logger.error(f"Database query failed: {e}")
    return {"status": "error", "error": str(e), "categories": []}
```

---

### H8. Ameliorer error handling - Bot Cogs
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/cogs/daily.py:86` - `except Exception:` - Utiliser `discord.HTTPException, ValueError`
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/cogs/daily.py:93` - `except Exception:` - Utiliser `discord.HTTPException, ValueError`
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/cogs/weekly.py:91` - `except Exception:` - Specifier exceptions
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/cogs/weekly.py:98` - `except Exception:` - Specifier exceptions
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/cogs/weekly.py:186` - `except Exception:` - Specifier exceptions
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/cogs/weekly.py:221` - `except Exception:` - Specifier exceptions

**Fix template:**
```python
except discord.HTTPException as e:
    await interaction.followup.send(f"Discord error: {e.text}", ephemeral=True)
except ValueError as e:
    await interaction.followup.send(f"Invalid input: {e}", ephemeral=True)
except Exception as e:
    logger.error(f"Unexpected error in command: {e}", exc_info=True)
    await interaction.followup.send("An unexpected error occurred.", ephemeral=True)
```

---

**Total Gain High Priority:** -878 LOC de cleanup + meilleure error handling

## Medium (Technical Debt - Fix This Month)

### M1. Ameliorer error handling - Services
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/services/digest_service.py:42` - `except Exception:` - Specifier `json.JSONDecodeError, IOError`
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/services/summarize_service.py:141` - `except Exception:` dans save log - Specifier exceptions
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/services/weekly_service.py:106` - `except Exception:` dans save log - Specifier exceptions

**Fix:**
```python
# digest_service.py:42
except (json.JSONDecodeError, IOError, OSError) as e:
    logger.error(f"Failed to read digest file: {e}")
    return None
```

---

### M2. Ameliorer error handling - Repositories
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/repositories/article_repository.py:66` - `except Exception:` - Utiliser `SQLAlchemyError`

**Fix:**
```python
except SQLAlchemyError as e:
    logger.error(f"Database error checking URLs: {e}")
    return urls, []  # Return all as new on error
```

---

### M3. Ameliorer error handling - Bot Services
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/services/publisher.py:135` - `except Exception:` dans card generation - Acceptable mais documenter
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/services/publisher.py:187` - `except Exception:` dans mark posted - Acceptable mais documenter
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/services/database.py:117` - `except Exception:` - Specifier `asyncpg.PostgresError`
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/services/database.py:137` - `except Exception:` - Specifier `asyncpg.PostgresError`
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/services/health_checker.py:57` - `except Exception:` - Acceptable pour health check

**Fix:**
```python
# database.py
import asyncpg

except asyncpg.PostgresError as e:
    logger.error(f"Database error: {e}")
    return None
```

---

### M4. Ameliorer error handling - Loggers
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/loggers/unified_logger.py:251` - `except Exception:` dans update summary - Specifier `IOError, OSError`
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/loggers/unified_logger.py:323` - `except Exception:` dans write MCP log - Specifier `IOError, OSError`
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/loggers/workflow_logger.py:136` - `except Exception:` - Specifier exceptions (si fichier pas supprime)

**Fix:**
```python
# unified_logger.py:323
except (IOError, OSError) as e:
    if not self._log_write_failed:
        self._log_write_failed = True
        logger.error(f"Failed to write MCP log: {e}")
```

---

### M5. Ameliorer error handling - API/Routes
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/api/routes.py:111` - `except Exception:` dans log workflow - OK mais specifier
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/api.py:110` - `except Exception:` dans publish - Specifie deja ValueError, garder Exception en dernier

**Fix:**
```python
# routes.py:111
except (ValueError, IOError) as e:
    logger.error(f"Failed to save workflow log: {e}")
    return WorkflowLogResponse(success=False, error=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return WorkflowLogResponse(success=False, error="Internal error")
```

---

### M6. Ajouter tests pour MCP tools
- [ ] `claude-service/tests/mcp_tools/test_digest_submitter.py` - **CREATE** - Tester validation, DB save, file write
- [ ] `claude-service/tests/mcp_tools/test_article_query.py` - **CREATE** - Tester queries, filters, stats

**Template:**
```python
# tests/mcp_tools/test_digest_submitter.py
import pytest
from mcp_tools.services.digest_submitter import DigestSubmitter

def test_submit_valid_digest():
    result = DigestSubmitter.submit(
        execution_id="test123",
        mission_id="ai-news",
        headlines=[{"title": "Test", "url": "http://test.com", ...}],
        ...
    )
    assert result["status"] == "success"
    assert result["digest_id"] is not None
```

---

### M7. Ajouter tests pour Bot publishers
- [ ] `bot/tests/services/test_publisher.py` - **CREATE** - Tester build_embeds, publish flow

---

### M8. Documenter globals mutables
- [ ] `/home/ilan/code/active/daily-ai-webhook/bot/api.py:29` - `_bot = None` - Ajouter docstring expliquant lifecycle
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/database.py:35` - Documenter pattern singleton

**Fix:**
```python
# Global singleton (initialized at app startup, immutable after)
# Set via set_bot() in main.py before starting FastAPI
_bot: discord.Bot | None = None
```

---

### M9. Verifier imports apres suppression fichiers
- [ ] Apres suppression de handlers.py, converters.py, execution_logger.py, workflow_logger.py - **VERIFY** - Lancer tests, verifier pas d'imports casses

**Command:**
```bash
# Chercher imports vers fichiers supprimes
grep -r "from.*execution_logger import" claude-service/
grep -r "from.*workflow_logger import" claude-service/
grep -r "from.*handlers import" claude-service/
grep -r "from.*converters import" claude-service/

# Lancer tests
pytest claude-service/tests/
pytest bot/tests/
```

## Low (Nice to Have - Backlog)

### L1. Eliminer magic strings
- [ ] Chercher `"daily"`, `"weekly"` hardcodes - Remplacer par `DigestType.DAILY`, `DigestType.WEEKLY`
- [ ] Chercher `"off_topic"`, `"duplicate"` - Remplacer par `ExclusionReason.*`
- [ ] Chercher `"headlines"`, `"research"` - Remplacer par `DigestCategory.*`

**Command:**
```bash
grep -r '"daily"' claude-service/ bot/ --include="*.py" | grep -v test | grep -v comment
# Evaluer chaque occurence
```

---

### L2. Extraire fonctions longues
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/services/claude_service.py:163-203` - `parse_stream_output()` 40 lignes - Acceptable mais pourrait extraire `_extract_event_data()`

**Note:** Deja bien decompose avec `_parse_stream_event()`, `_extract_event_data()`, etc. Pas prioritaire.

---

### L3. Ajouter type hints manquants
- [ ] Verifier que tous les parametres de fonctions ont type hints - **AUDIT** - Semble deja bien fait

**Command:**
```bash
# Trouver fonctions sans type hints
grep -r "def.*(" claude-service/ --include="*.py" | grep -v " -> " | head -20
```

---

### L4. Optimiser imports
- [ ] `/home/ilan/code/active/daily-ai-webhook/claude-service/services/summarize_service.py:74` - Import `from pathlib import Path` inline - Deplacer en haut

**Fix:**
```python
# Ligne 1
from pathlib import Path

# Supprimer ligne 74: from pathlib import Path
```

---

### L5. Ajouter docstrings manquantes
- [ ] Verifier que toutes les classes publiques ont docstrings - **AUDIT** - Semble bien documente

---

### L6. Standardiser logging format
- [ ] Verifier coherence des messages de log - **AUDIT** - Format structlog dans MCP, format standard ailleurs

**Note:** Acceptable d'avoir 2 formats (MCP vs API) vu les contextes differents.

---

### L7. Ajouter pre-commit hooks
- [ ] **CREATE** `.pre-commit-config.yaml` - black, ruff, mypy

**Template:**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## Summary Stats

### Cleanup Impact

| Action | LOC Saved | Files Deleted |
|--------|-----------|---------------|
| Supprimer execution_logger.py | -321 | 1 |
| Supprimer workflow_logger.py | -146 | 1 |
| Supprimer handlers.py | -316 | 1 |
| Supprimer converters.py | -95 | 1 |
| **TOTAL** | **-878 LOC** | **4 files** |

### Error Handling Improvements

| Category | Occurrences | Priority |
|----------|-------------|----------|
| Database (claude-service) | 4 | High |
| MCP Services | 5 | High |
| Bot Cogs | 6 | High |
| Services | 3 | Medium |
| Repositories | 1 | Medium |
| Bot Services | 5 | Medium |
| Loggers | 3 | Medium |
| API/Routes | 2 | Medium |
| Other | 5 | Low |
| **TOTAL** | **34** | **Mix** |

### Test Coverage Goals

| Module | Current Tests | Target Tests | Priority |
|--------|---------------|--------------|----------|
| API endpoints | 2 files | ✓ Complete | Done |
| Config | 1 file | ✓ Complete | Done |
| MCP tools | 0 files | 2 files | High |
| Bot publishers | 0 files | 1 file | Medium |
| Repositories | 0 files | 2 files | Medium |
| Services | 1 file | 4 files | Medium |

## Execution Plan

### Week 1: Cleanup (4h)
1. Day 1 (2h): Supprimer 4 fichiers dupliques, verifier imports
2. Day 2 (1h): Lancer tests, fixer imports casses
3. Day 3 (1h): Commit, push, verifier CI

### Week 2: Error Handling (6h)
1. Day 1 (2h): Fixer database + MCP services (H6, H7)
2. Day 2 (2h): Fixer bot cogs (H8)
3. Day 3 (2h): Review + tests

### Week 3-4: Tests (12h)
1. Week 3 (6h): Tests MCP tools (M6)
2. Week 4 (6h): Tests bot publishers (M7)

### Ongoing: Low Priority (backlog)
- Magic strings cleanup
- Pre-commit hooks
- Documentation improvements

---

**Note:** Ces actions sont basees sur l'analyse du 2026-01-05. Verifier que le code n'a pas change avant d'appliquer les fixes.
