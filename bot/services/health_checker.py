"""
Health check service for external dependencies.

Provides health check functions for database and claude-service.
"""

import logging
from dataclasses import dataclass

import aiohttp

from config import settings
from services.database import check_database_health

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health check result."""

    healthy: bool
    message: str


async def check_db_health() -> HealthStatus:
    """Check PostgreSQL database health.

    Returns:
        HealthStatus with connection status
    """
    is_healthy, message = await check_database_health()
    return HealthStatus(healthy=is_healthy, message=message)


async def check_claude_service_health() -> HealthStatus:
    """Check claude-service health.

    Returns:
        HealthStatus with service status
    """
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{settings.claude_service_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "healthy":
                        version = data.get("version", "?")
                        return HealthStatus(healthy=True, message=f"v{version}")
                    return HealthStatus(healthy=False, message="Unhealthy response")
                return HealthStatus(healthy=False, message=f"HTTP {response.status}")

    except aiohttp.ClientError as e:
        logger.warning("Claude service health check failed: %s", e)
        return HealthStatus(healthy=False, message="Connection error")
    except Exception as e:
        logger.error("Unexpected error checking claude-service: %s", e)
        return HealthStatus(healthy=False, message="Error")
