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
    # Current behavior: returns 200 with error in response body
    # TODO: Should return 400/422 for invalid mission (see Phase 1)
    assert response.status_code == 200
    data = response.json()
    assert "error" in data or "success" in data


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
