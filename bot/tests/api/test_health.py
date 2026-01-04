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
