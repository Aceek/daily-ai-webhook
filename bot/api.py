"""
HTTP API for Discord bot.

Provides endpoints for external services to trigger digest publication.
"""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException

from services.models import (
    CallbackRequest,
    HealthResponse,
    PublishRequest,
    PublishResponse,
)

logger = logging.getLogger(__name__)

# FastAPI app instance (bot reference set at runtime)
app = FastAPI(
    title="AI News Discord Bot API",
    description="HTTP API for publishing digests to Discord",
    version="1.0.0",
)

# Reference to Discord bot (set by main.py via app.state)
_bot = None


def set_bot(bot) -> None:
    """Set the Discord bot reference for API handlers."""
    global _bot
    _bot = bot


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    if _bot is None:
        return HealthResponse(
            status="starting",
            discord_connected=False,
            guild_count=0,
        )

    return HealthResponse(
        status="healthy",
        discord_connected=_bot.is_ready(),
        guild_count=len(_bot.guilds) if _bot.is_ready() else 0,
    )


@app.post("/publish", response_model=PublishResponse)
async def publish_digest(request: PublishRequest) -> PublishResponse:
    """Publish a digest to Discord.

    Accepts both daily and weekly digest types.
    """
    if _bot is None or not _bot.is_ready():
        raise HTTPException(status_code=503, detail="Discord bot not ready")

    # Import here to avoid circular imports
    from services.publisher import publish_daily_digest, publish_weekly_digest

    try:
        if request.type == "daily":
            if not request.date:
                raise HTTPException(status_code=400, detail="date field required for daily digest")

            result = await publish_daily_digest(
                bot=_bot,
                digest_id=request.digest_id,
                content=request.content,
                digest_date=request.date,
                channel_id=request.channel_id,
            )
        elif request.type == "weekly":
            if not request.week_start or not request.week_end:
                raise HTTPException(
                    status_code=400,
                    detail="week_start and week_end required for weekly digest",
                )

            result = await publish_weekly_digest(
                bot=_bot,
                digest_id=request.digest_id,
                content=request.content,
                week_start=request.week_start,
                week_end=request.week_end,
                channel_id=request.channel_id,
                theme=request.theme,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown digest type: {request.type}")

        logger.info(
            "Published %s digest %d to channel %s",
            request.type,
            request.digest_id,
            result["channel_id"],
        )

        return PublishResponse(**result)

    except ValueError as e:
        logger.error("Publish error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Publish failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# In-memory callback storage (for async workflow integration)
_callbacks: dict[str, dict[str, Any]] = {}


@app.post("/callback")
async def receive_callback(request: CallbackRequest) -> dict[str, str]:
    """Receive async callback from external services."""
    logger.info(
        "Received callback for correlation_id=%s status=%s",
        request.correlation_id,
        request.status,
    )

    _callbacks[request.correlation_id] = {
        "status": request.status,
        "result": request.result,
        "error": request.error,
    }

    return {"status": "received", "correlation_id": request.correlation_id}


def get_callback(correlation_id: str) -> dict[str, Any] | None:
    """Get callback result by correlation ID.

    Returns None if not yet received.
    """
    return _callbacks.pop(correlation_id, None)
