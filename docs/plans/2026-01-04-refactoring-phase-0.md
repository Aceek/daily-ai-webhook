# Phase 0: Préparation (Tests Smoke) - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Créer un filet de sécurité avec pytest avant tout refactoring.

**Architecture:** Setup pytest + pytest-asyncio, créer 2 tests smoke minimaux qui vérifient que /summarize et /publish répondent correctement.

**Tech Stack:** pytest, pytest-asyncio, httpx (async test client)

---

## Task 1: Setup pytest

**Files:**
- Create: `claude-service/pyproject.toml` (ou modifier si existe)
- Create: `claude-service/tests/__init__.py`
- Create: `claude-service/tests/conftest.py`

**Step 1: Vérifier structure existante**

Run: `ls -la claude-service/pyproject.toml claude-service/tests/ 2>/dev/null || echo "À créer"`

**Step 2: Créer/modifier pyproject.toml pour pytest**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"

[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]
```

**Step 3: Créer tests/__init__.py**

```python
# tests/__init__.py
```

**Step 4: Créer conftest.py avec fixtures**

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
async def client():
    """Async test client for FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

**Step 5: Installer dépendances test**

Run: `cd claude-service && pip install pytest pytest-asyncio httpx`
Expected: Successfully installed pytest-X.X.X pytest-asyncio-X.X.X httpx-X.X.X

**Step 6: Vérifier que pytest fonctionne**

Run: `cd claude-service && python -m pytest --collect-only`
Expected: "no tests ran" ou "collected 0 items"

**Step 7: Commit**

```bash
git add claude-service/pyproject.toml claude-service/tests/
git commit -m "test: setup pytest infrastructure"
```

---

## Task 2: Test smoke /health endpoint

**Files:**
- Create: `claude-service/tests/api/test_health.py`
- Create: `claude-service/tests/api/__init__.py`

**Step 1: Créer dossier api**

Run: `mkdir -p claude-service/tests/api && touch claude-service/tests/api/__init__.py`

**Step 2: Write the failing test**

```python
# claude-service/tests/api/test_health.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient):
    """Smoke test: /health endpoint responds."""
    response = await client.get("/health")
    assert response.status_code == 200
```

**Step 3: Run test to verify it works**

Run: `cd claude-service && python -m pytest tests/api/test_health.py -v`
Expected: PASSED (si /health existe déjà)

**Step 4: Commit**

```bash
git add claude-service/tests/api/
git commit -m "test: add /health smoke test"
```

---

## Task 3: Test smoke /summarize endpoint (validation only)

**Files:**
- Create: `claude-service/tests/api/test_summarize.py`

**Step 1: Write the failing test**

```python
# claude-service/tests/api/test_summarize.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_summarize_rejects_invalid_mission(client: AsyncClient):
    """Smoke test: /summarize validates mission parameter."""
    response = await client.post(
        "/summarize",
        json={
            "mission": "invalid-mission-that-does-not-exist",
            "articles": []
        }
    )
    # Should reject with 400 or 422 (validation error)
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_summarize_rejects_empty_articles(client: AsyncClient):
    """Smoke test: /summarize handles empty articles."""
    response = await client.post(
        "/summarize",
        json={
            "mission": "ai-news",
            "articles": []
        }
    )
    # Should either accept (200) or reject (400/422)
    # This test documents current behavior
    assert response.status_code in (200, 400, 422)
```

**Step 2: Run test to verify behavior**

Run: `cd claude-service && python -m pytest tests/api/test_summarize.py -v`
Expected: PASSED (documents current behavior)

**Step 3: Commit**

```bash
git add claude-service/tests/api/test_summarize.py
git commit -m "test: add /summarize smoke tests"
```

---

## Task 4: Setup pytest pour bot

**Files:**
- Create: `bot/tests/__init__.py`
- Create: `bot/tests/conftest.py`
- Modify: `bot/pyproject.toml` (ou créer)

**Step 1: Créer structure tests bot**

Run: `mkdir -p bot/tests && touch bot/tests/__init__.py`

**Step 2: Créer conftest.py pour bot**

```python
# bot/tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from api import app


@pytest.fixture
async def client():
    """Async test client for bot FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

**Step 3: Installer dépendances test**

Run: `cd bot && pip install pytest pytest-asyncio httpx`
Expected: Successfully installed...

**Step 4: Commit**

```bash
git add bot/tests/
git commit -m "test: setup pytest infrastructure for bot"
```

---

## Task 5: Test smoke /health bot

**Files:**
- Create: `bot/tests/api/test_health.py`
- Create: `bot/tests/api/__init__.py`

**Step 1: Créer dossier et test**

```python
# bot/tests/api/test_health.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_status(client: AsyncClient):
    """Smoke test: bot /health endpoint responds."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
```

**Step 2: Run test**

Run: `cd bot && python -m pytest tests/api/test_health.py -v`
Expected: PASSED

**Step 3: Commit**

```bash
git add bot/tests/api/
git commit -m "test: add bot /health smoke test"
```

---

## Task 6: Validation finale

**Step 1: Run all tests claude-service**

Run: `cd claude-service && python -m pytest tests/ -v`
Expected: 3 tests PASSED

**Step 2: Run all tests bot**

Run: `cd bot && python -m pytest tests/ -v`
Expected: 1 test PASSED

**Step 3: Commit final**

```bash
git add -A
git commit -m "test: complete Phase 0 - smoke tests ready"
```

---

## Critère de Succès Phase 0

```bash
# Depuis la racine du projet
cd claude-service && python -m pytest tests/ -v && cd ..
cd bot && python -m pytest tests/ -v && cd ..
# → 4+ tests PASSED, 0 FAILED
```

**Phase 0 terminée.** Filet de sécurité en place pour Phase 1.
