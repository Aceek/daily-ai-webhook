"""Pydantic models for MCP server.

Defines data structures for news items, digests, and API responses.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """A news item for digest publication."""

    title: str = Field(..., description="Article title")
    summary: str = Field(..., description="Brief summary")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="Source name")
    category: str = Field(..., description="Assigned category")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    relevance_score: int | None = Field(None, ge=1, le=10, description="Relevance 1-10")


class ExcludedItem(BaseModel):
    """An excluded article for archival."""

    url: str = Field(..., description="Article URL")
    title: str = Field(..., description="Article title")
    category: str = Field(..., description="Assigned category")
    reason: str = Field(
        ...,
        description="Exclusion reason: off_topic|duplicate|low_priority|outdated"
    )
    score: int = Field(..., ge=1, le=10, description="Relevance score 1-10")
    source: str | None = Field(None, description="Source name")


class DigestMetadata(BaseModel):
    """Metadata for digest submission."""

    mission_id: str = Field(default="ai-news", description="Mission identifier")
    articles_analyzed: int = Field(..., ge=0, description="Number of articles analyzed")
    web_searches: int = Field(default=0, ge=0, description="Number of web searches")
    fact_checks: int = Field(default=0, ge=0, description="Number of fact checks")
    deep_dives: int = Field(default=0, ge=0, description="Number of deep dives")
    research_doc: str = Field(..., description="Path to research document")


class DailyDigest(BaseModel):
    """Complete daily digest structure."""

    digest_id: int | None = Field(None, description="Database ID after save")
    date: date = Field(..., description="Digest date")
    headlines: list[dict[str, Any]] = Field(..., min_length=1)
    research: list[dict[str, Any]] = Field(default_factory=list)
    industry: list[dict[str, Any]] = Field(default_factory=list)
    watching: list[dict[str, Any]] = Field(default_factory=list)
    excluded: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=datetime.now)


class Trend(BaseModel):
    """A trend identified in weekly analysis."""

    name: str = Field(..., description="Trend name")
    description: str = Field(..., description="What's happening")
    evidence: list[str] = Field(default_factory=list, description="Supporting articles")
    direction: str = Field(..., description="rising|stable|declining")


class TopStory(BaseModel):
    """A top story from the week."""

    title: str = Field(..., description="Story title")
    summary: str = Field(..., description="Brief summary")
    url: str = Field(..., description="Primary source URL")
    impact: str | None = Field(None, description="Why this matters")


class WeeklyDigest(BaseModel):
    """Complete weekly digest structure."""

    digest_id: int | None = Field(None, description="Database ID after save")
    summary: str = Field(..., description="Executive summary")
    trends: list[dict[str, Any]] = Field(..., min_length=1)
    top_stories: list[dict[str, Any]] = Field(..., min_length=1)
    category_analysis: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)


class ToolResponse(BaseModel):
    """Standard response format for MCP tools."""

    status: str = Field(..., description="success or error")
    message: str | None = Field(None, description="Human-readable message")
    errors: list[str] | None = Field(None, description="Validation errors if any")


class DigestSubmitResponse(ToolResponse):
    """Response from submit_digest tool."""

    execution_id: str | None = None
    digest_id: int | None = None
    output_path: str | None = None
    selected_count: int = 0
    excluded_count: int = 0
    total_archived: int = 0
    db_saved: bool = False
    db_error: str | None = None
    exclusion_breakdown: dict[str, int] | None = None
    operations: list[dict[str, Any]] | None = None
