"""
Claude service client for on-demand digest generation.

Provides async HTTP client for calling claude-service endpoints.
"""

import logging
from typing import Any

import aiohttp

from config import settings

logger = logging.getLogger(__name__)


class ClaudeServiceError(Exception):
    """Error from claude-service API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


async def generate_weekly_digest(
    mission: str,
    week_start: str,
    week_end: str,
    theme: str | None = None,
) -> dict[str, Any]:
    """Generate a weekly digest via claude-service.

    Args:
        mission: Mission ID (e.g., 'ai-news')
        week_start: Start of week (YYYY-MM-DD)
        week_end: End of week (YYYY-MM-DD)
        theme: Optional theme to focus the analysis on

    Returns:
        Response dict with success, digest, digest_id, etc.

    Raises:
        ClaudeServiceError: If the API call fails
    """
    url = f"{settings.claude_service_url}/analyze-weekly"

    payload = {
        "mission": mission,
        "week_start": week_start,
        "week_end": week_end,
        "theme": theme,
    }

    logger.info(
        "Requesting weekly digest: mission=%s, week=%s to %s, theme=%s",
        mission,
        week_start,
        week_end,
        theme,
    )

    timeout = aiohttp.ClientTimeout(total=settings.claude_service_timeout)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()

                if response.status != 200:
                    error_msg = data.get("detail", str(data))
                    logger.error(
                        "Claude service error: status=%d, error=%s",
                        response.status,
                        error_msg,
                    )
                    raise ClaudeServiceError(error_msg, response.status)

                if not data.get("success"):
                    error_msg = data.get("error", "Unknown error")
                    logger.error("Weekly digest generation failed: %s", error_msg)
                    raise ClaudeServiceError(error_msg)

                logger.info(
                    "Weekly digest generated: digest_id=%s, execution_id=%s",
                    data.get("digest_id"),
                    data.get("execution_id"),
                )

                return data

    except aiohttp.ClientError as e:
        logger.error("HTTP error calling claude-service: %s", e)
        raise ClaudeServiceError(f"Connection error: {e}") from e
    except TimeoutError as e:
        logger.error("Timeout calling claude-service after %ds", settings.claude_service_timeout)
        raise ClaudeServiceError(
            f"Request timed out after {settings.claude_service_timeout}s"
        ) from e
