"""
Shared Pydantic models for bot services.

Provides request/response models used across API and publisher services.
"""

from typing import Any

from pydantic import BaseModel, Field


class PublishRequest(BaseModel):
    """Request model for publishing any digest type."""

    type: str = Field(description="Digest type: 'daily' or 'weekly'")
    mission_id: str = Field(description="Mission identifier (e.g., 'ai-news')")
    digest_id: int = Field(description="Database ID of the digest")
    content: dict[str, Any] = Field(description="Digest content object")
    # Daily fields
    date: str | None = Field(default=None, description="Digest date (for daily)")
    # Weekly fields
    week_start: str | None = Field(default=None, description="Week start (for weekly)")
    week_end: str | None = Field(default=None, description="Week end (for weekly)")
    theme: str | None = Field(default=None, description="Theme (for weekly)")
    # Common optional
    channel_id: int | None = Field(default=None, description="Override channel ID")


class PublishResponse(BaseModel):
    """Response model for publish endpoints."""

    status: str
    message_id: str | None = None
    channel_id: str | None = None
    posted_to_discord: bool = False
    error: str | None = None


class DigestResult(BaseModel):
    """Result from digest publication."""

    success: bool
    digest_id: int
    message_id: str | None = None
    channel_id: str | None = None
    embed_count: int = 0


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    discord_connected: bool
    guild_count: int


class CallbackRequest(BaseModel):
    """Request model for async callback."""

    correlation_id: str = Field(description="Correlation ID from original request")
    status: str = Field(description="Status: 'success' or 'error'")
    result: dict[str, Any] | None = Field(default=None, description="Result payload")
    error: str | None = Field(default=None, description="Error message if failed")
