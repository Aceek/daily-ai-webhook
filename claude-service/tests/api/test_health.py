# claude-service/tests/api/test_health.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient):
    """Smoke test: /health endpoint responds."""
    response = await client.get("/health")
    assert response.status_code == 200
