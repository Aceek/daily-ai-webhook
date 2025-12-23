"""
HTTP API for Discord bot.

Provides endpoints for external services to trigger digest publication.
"""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# FastAPI app instance (bot reference set at runtime)
app = FastAPI(
    title="AI News Discord Bot API",
    description="HTTP API for publishing digests to Discord",
    version="1.0.0",
)

# Reference to Discord bot (set by main.py)
_bot = None


def set_bot(bot) -> None:
    """Set the Discord bot reference for API handlers."""
    global _bot
    _bot = bot


class DailyPublishRequest(BaseModel):
    """Request model for publishing a daily digest."""

    type: str = Field(default="daily", pattern="^daily$")
    mission_id: str = Field(description="Mission identifier (e.g., 'ai-news')")
    digest_id: int = Field(description="Database ID of the digest")
    content: dict[str, Any] = Field(description="Digest content object")
    date: str = Field(description="Digest date (YYYY-MM-DD)")
    channel_id: int | None = Field(default=None, description="Override channel ID")


class WeeklyPublishRequest(BaseModel):
    """Request model for publishing a weekly digest."""

    type: str = Field(default="weekly", pattern="^weekly$")
    mission_id: str = Field(description="Mission identifier")
    digest_id: int = Field(description="Database ID of the digest")
    content: dict[str, Any] = Field(description="Digest content object")
    week_start: str = Field(description="Week start date (YYYY-MM-DD)")
    week_end: str = Field(description="Week end date (YYYY-MM-DD)")
    channel_id: int | None = Field(default=None, description="Override channel ID")


class PublishRequest(BaseModel):
    """Union request model for publishing any digest type."""

    type: str = Field(description="Digest type: 'daily' or 'weekly'")
    mission_id: str = Field(description="Mission identifier (e.g., 'ai-news')")
    digest_id: int = Field(description="Database ID of the digest")
    content: dict[str, Any] = Field(description="Digest content object")
    # Daily fields
    date: str | None = Field(default=None, description="Digest date (for daily)")
    # Weekly fields
    week_start: str | None = Field(default=None, description="Week start (for weekly)")
    week_end: str | None = Field(default=None, description="Week end (for weekly)")
    # Common optional
    channel_id: int | None = Field(default=None, description="Override channel ID")


class PublishResponse(BaseModel):
    """Response model for publish endpoints."""

    status: str
    message_id: str | None = None
    channel_id: str | None = None
    posted_to_discord: bool = False
    error: str | None = None


class CallbackRequest(BaseModel):
    """Request model for async callback."""

    correlation_id: str = Field(description="Correlation ID from original request")
    status: str = Field(description="Status: 'success' or 'error'")
    result: dict[str, Any] | None = Field(default=None, description="Result payload")
    error: str | None = Field(default=None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    discord_connected: bool
    guild_count: int


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


# In-memory callback storage (for Phase 6)
_callbacks: dict[str, dict[str, Any]] = {}


@app.post("/callback")
async def receive_callback(request: CallbackRequest) -> dict[str, str]:
    """Receive async callback from external services.

    Used for Phase 6 async workflow integration.
    """
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
