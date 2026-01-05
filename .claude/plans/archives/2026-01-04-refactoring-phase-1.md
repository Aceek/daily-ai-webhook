# Phase 1: Quick Wins - Plan d'Implementation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Débloquer l'architecture multi-mission et corriger les erreurs critiques de gestion d'exceptions.

**Architecture Impact:**

| Avant | Après |
|-------|-------|
| VALID_MISSIONS hardcodé | Auto-découverte depuis missions/ |
| allowed_tools hardcodé | Auto-généré depuis MCP server |
| `except Exception: pass` (silencieux) | Logging explicite avec contexte |
| mission_id implicite (metadata) | Paramètre explicite sur tous les tools |
| DEFAULT_MISSION hardcodé | Via variable d'environnement |

**Tech Stack:** Python 3.11+, FastMCP, Pydantic settings, pathlib

**Prerequisites:** Phase 0 complète (tests smoke fonctionnent)

---

## Task 1.1: VALID_MISSIONS dynamique

**Objectif:** Détecter automatiquement les missions depuis le filesystem

### Files

| Action | File |
|--------|------|
| Modify | `claude-service/config.py` |

### Steps

**Step 1.1.1:** Ajouter fonction `discover_missions()`

```python
def discover_missions(missions_path: str | None = None) -> list[str]:
    """Discover available missions from filesystem.

    Scans missions directory for valid mission folders.
    A valid mission must have mission.md file.
    """
    path = Path(missions_path or Settings().missions_path)
    if not path.exists():
        return []

    missions = []
    for item in path.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            if (item / "mission.md").exists():
                missions.append(item.name)
    return sorted(missions)
```

**Step 1.1.2:** Remplacer VALID_MISSIONS constant par fonction

```python
# Avant
VALID_MISSIONS: list[str] = ["ai-news"]

# Après
def get_valid_missions() -> list[str]:
    """Get list of valid missions (cached on first call)."""
    if not hasattr(get_valid_missions, "_cache"):
        get_valid_missions._cache = discover_missions()
    return get_valid_missions._cache
```

**Step 1.1.3:** Mettre à jour `validate_mission()` et `validate_weekly_mission()`

**Step 1.1.4:** Vérification

Run:
```bash
cd claude-service && python -c "
from config import discover_missions, get_valid_missions
print('Discovered:', discover_missions())
print('Valid:', get_valid_missions())
"
```

Expected:
```
Discovered: ['ai-news']
Valid: ['ai-news']
```

### Commit

```
fix(config): dynamic mission discovery from filesystem
```

---

## Task 1.2: allowed_tools auto-généré

**Objectif:** Générer la liste des outils MCP depuis le serveur

### Files

| Action | File |
|--------|------|
| Modify | `claude-service/config.py` |
| Modify | `claude-service/services/claude_service.py` |

### Steps

**Step 1.2.1:** Ajouter constantes pour outils de base

```python
BASE_TOOLS: list[str] = ["Read", "WebSearch", "WebFetch", "Write", "Task"]
MCP_SERVER_NAME: str = "submit-digest"
```

**Step 1.2.2:** Ajouter fonction `get_mcp_tool_names()`

```python
def get_mcp_tool_names() -> list[str]:
    """Get list of MCP tool names from server definition."""
    try:
        from mcp_tools.server import mcp
        tool_names = []
        if hasattr(mcp, "_tool_manager") and hasattr(mcp._tool_manager, "_tools"):
            for name in mcp._tool_manager._tools.keys():
                tool_names.append(f"mcp__{MCP_SERVER_NAME}__{name}")
        return tool_names
    except ImportError:
        return []
```

**Step 1.2.3:** Ajouter fonction `build_allowed_tools()`

```python
def build_allowed_tools() -> str:
    """Build allowed tools string for Claude CLI."""
    mcp_tools = get_mcp_tool_names()
    all_tools = BASE_TOOLS + mcp_tools
    return ",".join(all_tools)
```

**Step 1.2.4:** Modifier Settings pour utiliser get_allowed_tools()

**Step 1.2.5:** Vérification

Run:
```bash
cd claude-service && python -c "
from config import build_allowed_tools
print('All tools:', build_allowed_tools())
"
```

### Commit

```
feat(config): auto-generate allowed_tools from MCP server
```

---

## Task 1.3: Fix `except Exception: pass` dans workflow_logger.py

### Files

| Action | File |
|--------|------|
| Modify | `claude-service/loggers/workflow_logger.py` |

### Steps

**Step 1.3.1:** Remplacer `except Exception: pass`

```python
# Avant
except Exception:
    pass

# Après
except Exception as e:
    logger.warning(
        "Failed to update SUMMARY.md storage status: %s (file: %s)",
        e,
        summary_path,
    )
```

### Commit

```
fix(logger): log workflow_logger exceptions instead of silent pass
```

---

## Task 1.4: Fix `except Exception: pass` dans mcp_tools/logger.py

### Files

| Action | File |
|--------|------|
| Modify | `claude-service/mcp_tools/logger.py` |

### Steps

**Step 1.4.1:** Ajouter tracking des erreurs

```python
def __init__(self) -> None:
    # ...
    self._log_write_failed: bool = False
```

**Step 1.4.2:** Remplacer `except Exception: pass`

```python
except Exception as e:
    if not self._log_write_failed:
        self._log_write_failed = True
        print(f"[MCP] [WARN] Failed to write to log file: {e}", file=sys.stderr)
```

### Commit

```
fix(mcp-logger): log file write errors instead of silent pass
```

---

## Task 1.5: Fix `except Exception:` broad dans database.py

### Files

| Action | File |
|--------|------|
| Modify | `claude-service/database.py` |

### Steps

**Step 1.5.1:** Ajouter import SQLAlchemyError

```python
from sqlalchemy.exc import SQLAlchemyError
```

**Step 1.5.2:** Spécialiser l'exception

```python
except SQLAlchemyError:
    await session.rollback()
    raise
except Exception as e:
    await session.rollback()
    logger.error("Unexpected error in database session: %s", e)
    raise
```

### Commit

```
fix(database): catch specific SQLAlchemyError instead of broad Exception
```

---

## Task 1.6: mission_id param explicite sur MCP tools

### Files

| Action | File |
|--------|------|
| Modify | `claude-service/mcp_tools/server.py` |
| Modify | `claude-service/mcp_tools/services/digest_submitter.py` |

### Steps

**Step 1.6.1:** Ajouter mission_id explicite dans server.py

```python
@mcp.tool()
def submit_digest(
    execution_id: str,
    mission_id: str,  # Nouveau param explicite
    headlines: list[dict],
    # ...
```

**Step 1.6.2:** Mettre à jour DigestSubmitter.submit()

**Step 1.6.3:** Vérification

Run:
```bash
cd claude-service && python -c "
from mcp_tools.server import submit_digest
import inspect
params = list(inspect.signature(submit_digest).parameters.keys())
assert 'mission_id' in params
print('mission_id at position:', params.index('mission_id'))
"
```

### Commit

```
refactor(mcp): make mission_id explicit param on submit_digest
```

---

## Task 1.7: Supprimer DEFAULT_MISSION hardcode

### Files

| Action | File |
|--------|------|
| Modify | `claude-service/config.py` |
| Modify | `claude-service/mcp_tools/models.py` |

### Steps

**Step 1.7.1:** Ajouter constante dans config.py

```python
DEFAULT_MISSION: str = os.getenv("DEFAULT_MISSION", "ai-news")
```

**Step 1.7.2:** Rendre mission_id required dans models.py

```python
# Avant
mission_id: str = Field(default="ai-news", ...)

# Après
mission_id: str = Field(..., description="Mission identifier")  # Required
```

### Commit

```
refactor(config): centralize DEFAULT_MISSION from environment
```

---

## Final Verification

```bash
# Test multi-mission discovery
mkdir -p claude-service/missions/test-mission
echo "# Test" > claude-service/missions/test-mission/mission.md

cd claude-service && python -c "
from config import discover_missions
missions = discover_missions()
assert 'test-mission' in missions
print('SUCCESS: Multi-mission discovery works!')
"

rm -rf claude-service/missions/test-mission
```

---

## Success Criteria

| Critère | Vérification |
|---------|--------------|
| Missions auto-découvertes | `discover_missions()` retourne les missions |
| allowed_tools auto-généré | `build_allowed_tools()` inclut les MCP tools |
| Pas de `except Exception: pass` | `grep -r "except Exception:" \| grep pass` = 0 |
| mission_id explicite | Paramètre en position 2 de submit_digest |
| DEFAULT_MISSION configurable | Variable d'environnement respectée |
| Tests Phase 0 passent | `pytest tests/ -v` OK |
