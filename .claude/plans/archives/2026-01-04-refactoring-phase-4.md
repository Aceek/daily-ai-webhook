# Phase 4: Qualité

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Atteindre une couverture de tests > 60% et nettoyer le code.

**Tech Stack:** pytest, pytest-asyncio, pytest-cov, unittest.mock

**Prerequisites:** Phase 3 terminée

---

## Phase 4A: Tests

### Task 4A.1: test_summarize_service.py

**Effort:** 2h

**Files:**
- Create: `tests/claude_service/conftest.py`
- Create: `tests/claude_service/test_summarize_service.py`

### Steps

**Step 4A.1.1:** Créer conftest.py avec fixtures partagées

```python
# tests/claude_service/conftest.py
import pytest
from unittest.mock import MagicMock

from api.models import Article, SummarizeRequest, ClaudeResult
from config import Settings


@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=Settings)
    settings.claude_model = "sonnet"
    settings.logs_path = "/tmp/logs"
    return settings


@pytest.fixture
def sample_articles():
    return [
        Article(title="GPT-5", url="https://example.com/gpt5", source="TechCrunch"),
        Article(title="Gemini 2", url="https://example.com/gemini", source="The Verge"),
    ]


@pytest.fixture
def sample_summarize_request(sample_articles):
    return SummarizeRequest(articles=sample_articles, mission="ai-news")


@pytest.fixture
def mock_claude_result_success():
    return ClaudeResult(success=True, response="Summary generated", ...)


@pytest.fixture
def sample_digest():
    return {"digest_id": 42, "headlines": [...], ...}
```

**Step 4A.1.2:** Créer les tests

```python
# tests/claude_service/test_summarize_service.py
class TestHandleSummarize:
    @pytest.mark.asyncio
    async def test_summarize_success(self, sample_summarize_request, ...):
        """Test successful summarization flow."""
        ...

    @pytest.mark.asyncio
    async def test_summarize_invalid_mission(self, ...):
        """Test with invalid mission returns error."""
        ...

    @pytest.mark.asyncio
    async def test_summarize_claude_cli_failure(self, ...):
        """Test when Claude CLI fails."""
        ...
```

**Step 4A.1.3:** Run tests

Run:
```bash
PYTHONPATH=claude-service pytest tests/claude_service/test_summarize_service.py -v
```

Expected: 6 tests pass

### Commit

```
test(claude-service): add /summarize handler tests
```

---

### Task 4A.2: test_weekly_service.py

**Effort:** 1.5h

**Files:**
- Create: `tests/claude_service/test_weekly_service.py`

### Tests

- `test_weekly_success` - Successful weekly analysis
- `test_weekly_with_theme` - Weekly with theme parameter
- `test_weekly_invalid_mission` - Invalid mission error
- `test_weekly_no_digest` - No digest produced

### Commit

```
test(claude-service): add /analyze-weekly handler tests
```

---

### Task 4A.3: test_submit_digest.py

**Effort:** 1.5h

**Files:**
- Create: `tests/claude_service/test_submit_digest.py`

### Tests

```python
class TestValidateNewsItems:
    def test_valid_items(self, valid_headlines): ...
    def test_missing_required_field(self): ...

class TestValidateExcludedItems:
    def test_valid_excluded(self): ...
    def test_invalid_reason(self): ...
    def test_invalid_score_range(self): ...

class TestValidateDailyDigest:
    def test_valid_digest(self): ...
    def test_empty_headlines_required(self): ...

class TestDigestSubmitterSubmit:
    def test_submit_validation_error(self): ...
    def test_submit_db_connection_failure(self): ...
    def test_submit_success(self): ...
```

### Commit

```
test(mcp): add submit_digest validation and service tests
```

---

### Task 4A.4: test_daily_cog.py

**Effort:** 1h

**Files:**
- Create: `tests/bot/conftest.py`
- Create: `tests/bot/test_daily_cog.py`

### Tests

- `test_daily_latest_success` - Returns latest digest
- `test_daily_specific_date` - Returns digest for specific date
- `test_daily_invalid_date_format` - Error on invalid date
- `test_daily_no_digest_found` - No digest available
- `test_daily_card_generation_failure` - Continues when card fails

### Commit

```
test(bot): add /daily command tests
```

---

### Task 4A.5: test_weekly_cog.py

**Effort:** 1h

**Files:**
- Create: `tests/bot/test_weekly_cog.py`

### Tests

- `test_weekly_cached_success` - Returns cached digest
- `test_weekly_no_cached_digest` - No cache available
- `test_weekly_with_theme_generates` - Theme triggers generation
- `test_weekly_invalid_date_format` - Error on invalid dates
- `test_weekly_generation_failure` - Handles generation errors

### Commit

```
test(bot): add /weekly command tests
```

---

### Task 4A.6: test_embed_builder.py

**Effort:** 1h

**Files:**
- Create: `tests/bot/test_embed_builder.py`

### Tests

```python
class TestEmbedColors:
    def test_colors_are_discord_colors(self): ...

class TestBuildCategoryEmbed:
    def test_headlines_embed(self): ...
    def test_research_embed(self): ...
    def test_field_truncation(self): ...

class TestBuildSummaryEmbed:
    def test_summary_embed(self): ...
    def test_long_summary_truncation(self): ...

class TestBuildTrendsEmbed:
    def test_trends_embed(self): ...

class TestFormatters:
    def test_confidence_badges(self): ...
    def test_direction_indicators(self): ...
```

### Commit

```
test(bot): add embed builder and formatter tests
```

---

## Phase 4B: Cleanup

### Task 4B.1: Remove Unused Imports

**Effort:** 30 min

### Steps

Run:
```bash
pip install autoflake
autoflake --in-place --recursive --remove-all-unused-imports claude-service/ bot/
```

### Commit

```
chore: remove unused imports across codebase
```

---

### Task 4B.2: Centralize Constants (constants.py)

**Effort:** 1h

**Files:**
- Create: `claude-service/constants.py`
- Create: `bot/constants.py`

### claude-service/constants.py

```python
"""Centralized constants for claude-service."""

from enum import Enum


class Mission(str, Enum):
    AI_NEWS = "ai-news"


class DigestCategory(str, Enum):
    HEADLINES = "headlines"
    RESEARCH = "research"
    INDUSTRY = "industry"
    WATCHING = "watching"


class ExclusionReason(str, Enum):
    OFF_TOPIC = "off_topic"
    DUPLICATE = "duplicate"
    LOW_PRIORITY = "low_priority"
    OUTDATED = "outdated"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Validation limits
MIN_HEADLINES = 1
MIN_SCORE = 1
MAX_SCORE = 10

# Required mission files
DAILY_MISSION_FILES = ["mission.md", "selection-rules.md", "editorial-guide.md", "output-schema.md"]
WEEKLY_MISSION_FILES = ["mission.md", "analysis-rules.md", "output-schema.md"]
```

### bot/constants.py

```python
"""Centralized constants for Discord bot."""

from enum import Enum
import discord


class EmbedColor(Enum):
    HEADLINES = discord.Color.from_rgb(239, 68, 68)
    RESEARCH = discord.Color.from_rgb(34, 197, 94)
    INDUSTRY = discord.Color.from_rgb(99, 102, 241)
    WATCHING = discord.Color.from_rgb(234, 179, 8)


class ConfidenceBadge(str, Enum):
    HIGH = "🟢"
    MEDIUM = "🟡"
    LOW = "🔴"


# Field limits
MAX_EMBED_TITLE = 256
MAX_EMBED_DESCRIPTION = 4096
MAX_FIELD_VALUE = 1024
```

### Commit

```
refactor: centralize constants in dedicated modules
```

---

### Task 4B.3: Replace Magic Strings with Enums

**Effort:** 1h

**Files:**
- Modify: `claude-service/mcp_tools/validators.py`
- Modify: `bot/services/embed_builder.py`
- Modify: `claude-service/config.py`

### Steps

Replace:
```python
# Avant
if reason not in ["off_topic", "duplicate", "low_priority", "outdated"]:
    ...

# Après
from constants import ExclusionReason
if reason not in [e.value for e in ExclusionReason]:
    ...
```

### Commit

```
refactor: replace magic strings with enums
```

---

### Task 4B.4: Document Final Architecture

**Effort:** 1h

**Files:**
- Update: `.claude/CLAUDE.md`
- Create: `docs/TESTING.md`

### docs/TESTING.md

```markdown
# Testing Guide

## Running Tests

```bash
# Claude Service
PYTHONPATH=claude-service pytest tests/claude_service/ -v

# Bot
PYTHONPATH=bot pytest tests/bot/ -v

# With coverage
pytest tests/ -v --cov=claude-service --cov=bot --cov-report=html
```

## Coverage Target

- Minimum: **60%**
- Goal: **80%**
```

### Commit

```
docs: document final architecture and testing guide
```

---

## Final Verification

Run:
```bash
# Full test suite with coverage
PYTHONPATH=claude-service:bot pytest tests/ -v \
  --cov=claude-service \
  --cov=bot \
  --cov-report=term-missing
```

Expected:
- 48+ tests pass
- Coverage > 60%
- 0 warnings

---

## Success Criteria

| Metric | Target | Verification |
|--------|--------|--------------|
| Tests passing | 100% | `pytest tests/ -v` |
| Coverage | > 60% | `pytest --cov` |
| Warnings | 0 | `pytest -W error` |
| Unused imports | 0 | `autoflake --check` |
| Magic strings | 0 | Manual review |

---

## Summary

| Task | Tests | Files |
|------|-------|-------|
| 4A.1 | 6 | test_summarize_service.py |
| 4A.2 | 4 | test_weekly_service.py |
| 4A.3 | 11 | test_submit_digest.py |
| 4A.4 | 5 | test_daily_cog.py |
| 4A.5 | 5 | test_weekly_cog.py |
| 4A.6 | 17 | test_embed_builder.py |
| 4B.1 | - | Cleanup imports |
| 4B.2 | - | constants.py x2 |
| 4B.3 | - | Use enums |
| 4B.4 | - | Documentation |
| **Total** | **48** | **~15 files** |

**Effort Total:** ~8h
