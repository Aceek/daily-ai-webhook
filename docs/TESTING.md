# Testing Guide

## Running Tests

### Local (requires pytest)
```bash
cd claude-service
pip install pytest pytest-asyncio pytest-cov
PYTHONPATH=. pytest tests/ -v
```

### Docker
```bash
docker-compose exec claude-service pytest tests/ -v
```

### With Coverage
```bash
PYTHONPATH=. pytest tests/ -v --cov=. --cov-report=term-missing
```

## Test Structure

```
tests/
├── conftest.py              # Global fixtures
├── claude_service/
│   ├── conftest.py          # Service fixtures
│   ├── test_config.py       # Configuration tests
│   └── test_summarize_service.py  # Summarize tests
└── bot/                     # (future)
```

## Coverage Target

- Minimum: **60%**
- Goal: **80%**

## Writing Tests

- Use `pytest.mark.asyncio` for async tests
- Mock external dependencies (Claude CLI, database)
- Use fixtures from conftest.py
- Keep tests independent and fast
