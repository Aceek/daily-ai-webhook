# Recommandations Priorisées

Basé sur l'analyse critique du 2026-01-04.

## Quick Wins (< 2h chaque)

| Action | Fichier | Effort | Impact |
|--------|---------|--------|--------|
| Rendre VALID_MISSIONS dynamique | config.py:54 | 30 min | 🔴 Critique |
| Générer allowed_tools auto | config.py:39 | 1h | 🔴 Critique |
| Centraliser constantes | nouveau constants.py | 1h | 🟡 Moyen |
| Remplacer `except Exception: pass` | workflow_logger.py:133 | 30 min | 🔴 Critique |

## Refactoring Moyen Terme (1-2 jours)

### Supprimer Layers Inutiles

```python
# AVANT: 5 layers
routes.py → handlers.py → services/ → repositories/ → models.py
              ↓
          converters.py

# APRÈS: 3 layers
routes.py → services/ → repositories/
```

| Fichier à supprimer/fusionner | Action |
|-------------------------------|--------|
| api/handlers.py | Fusionner logique dans services/ |
| api/converters.py | Inline dans handlers ou supprimer |
| utils/execution_dir.py | Fonctions simples dans loggers/ |

### Unifier Loggers

```python
# AVANT: 4 loggers
execution_logger.py  # Dossiers d'exécution
workflow_logger.py   # Logs n8n
mcp/logger.py        # MCPLogger custom
command_logger.py    # Discord commands

# APRÈS: 1 logger
class ExecutionLogger:
    def log_execution(...)
    def log_workflow(...)
    def log_mcp_operation(...)
    def log_command(...)
```

### Unifier Models

```python
# AVANT: 3 Article models
api/models.py:       Article(title, url, description, pub_date, source)
mcp_tools/models.py: NewsItem(title, summary, url, source, category, confidence)
bot/services/:       dict[str, Any]  # pas de modèle

# APRÈS: 1 modèle partagé
shared/models.py:
    class Article(BaseModel):
        title: str
        url: str
        source: str
        description: str = ""
        pub_date: datetime | None = None
        category: str | None = None
        confidence: float | None = None
```

## Tests à Ajouter (Priorité Haute)

| Test | Fichier | Couverture |
|------|---------|------------|
| test_summarize_handler | tests/api/test_handlers.py | /summarize flow |
| test_submit_digest | tests/mcp/test_digest_submitter.py | MCP submit |
| test_daily_command | tests/bot/test_daily.py | /daily command |
| test_embed_builder | tests/bot/test_embed_builder.py | Discord embeds |

**Framework suggéré:**
```bash
pip install pytest pytest-asyncio pytest-cov
```

## Corrections Erreurs Critiques

### Remplacer Exception Broad

```python
# AVANT (workflow_logger.py:133)
except Exception:
    pass

# APRÈS
except (IOError, OSError) as e:
    logger.warning("Failed to update summary: %s", e)
```

### Supprimer Globals Mutables

```python
# AVANT (bot/api.py:29-35)
_bot = None
def set_bot(bot):
    global _bot
    _bot = bot

# APRÈS: Dependency Injection
class APIState:
    bot: AINewsBot | None = None

state = APIState()

@app.on_event("startup")
async def startup():
    state.bot = get_bot_instance()
```

## ROI Estimé

| Action | Effort | LOC Saved | Bugs Prevented |
|--------|--------|-----------|----------------|
| Unifier loggers | 4h | 300 | 2-3 |
| Supprimer handlers layer | 3h | 400 | 1-2 |
| Unifier models | 2h | 100 | 3-4 |
| Tests handlers | 8h | 0 | 5+ |
| Fix broad exceptions | 2h | 0 | 3-4 |

**Total: ~20h travail → -800 LOC, ~15 bugs évités**

## Ordre d'Exécution Recommandé

```
Semaine 1:
  1. VALID_MISSIONS dynamique (30 min)
  2. allowed_tools auto (1h)
  3. Fix except Exception (2h)
  4. Tests handlers basiques (4h)

Semaine 2:
  5. Unifier loggers (4h)
  6. Supprimer handlers layer (3h)
  7. Unifier models (2h)

Semaine 3:
  8. Tests MCP (4h)
  9. Tests Discord (4h)
  10. Cleanup dead code (2h)
```
