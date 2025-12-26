#!/usr/bin/env python3
"""
API request and response models for Claude Service.

All Pydantic models used for HTTP request/response validation.
"""

from typing import Literal

from pydantic import BaseModel, Field

from loggers.models import StreamEvent


class Article(BaseModel):
    """Represents a news article to analyze."""

    title: str
    url: str
    description: str = ""
    pub_date: str = ""
    source: str = ""


class SummarizeRequest(BaseModel):
    """Request body for the /summarize endpoint."""

    articles: list[Article] = Field(..., min_length=0)
    mission: str = Field(
        default="ai-news",
        description="Mission to execute (e.g., 'ai-news', 'video-games')",
    )
    workflow_execution_id: str | None = Field(
        default=None,
        description="ID of the n8n workflow execution for log correlation",
    )


class AnalyzeWeeklyRequest(BaseModel):
    """Request body for the /analyze-weekly endpoint."""

    mission: str = Field(
        default="ai-news",
        description="Mission to execute",
    )
    week_start: str = Field(
        ...,
        description="Start of week (YYYY-MM-DD, should be Monday)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    week_end: str = Field(
        ...,
        description="End of week (YYYY-MM-DD, should be Sunday)",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    theme: str | None = Field(
        default=None,
        description="Optional theme to focus the analysis on",
    )
    workflow_execution_id: str | None = Field(
        default=None,
        description="ID of the n8n workflow execution for log correlation",
    )


class SummarizeResponse(BaseModel):
    """Response body for the /summarize endpoint."""

    summary: str  # Kept for backwards compatibility
    article_count: int
    success: bool
    error: str | None = None
    execution_id: str | None = None
    log_file: str | None = None
    mission: str = Field(
        default="ai-news",
        description="Mission that was executed",
    )
    workflow_execution_id: str | None = Field(
        default=None,
        description="ID of the n8n workflow execution if provided",
    )
    digest: dict | None = Field(
        default=None,
        description="Structured digest submitted via MCP submit_digest tool",
    )
    digest_id: int | None = Field(
        default=None,
        description="Database ID of the saved digest",
    )


class AnalyzeWeeklyResponse(BaseModel):
    """Response body for the /analyze-weekly endpoint."""

    success: bool
    error: str | None = None
    execution_id: str | None = None
    log_file: str | None = None
    mission: str = "ai-news"
    week_start: str = ""
    week_end: str = ""
    theme: str | None = None
    workflow_execution_id: str | None = None
    digest: dict | None = Field(
        default=None,
        description="Structured weekly digest submitted via MCP",
    )
    digest_id: int | None = Field(
        default=None,
        description="Database ID of the saved weekly digest",
    )


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str
    version: str


class NodeExecution(BaseModel):
    """Represents a single node execution in an n8n workflow."""

    name: str
    status: Literal["success", "error", "skipped"]
    error: str | None = None


class DiscordUser(BaseModel):
    """Discord user info for command logging."""

    id: str
    name: str


class DiscordGuild(BaseModel):
    """Discord guild info for command logging."""

    id: str
    name: str | None = None


class DiscordChannel(BaseModel):
    """Discord channel info for command logging."""

    id: str
    name: str | None = None


class WorkflowLogRequest(BaseModel):
    """Request body for the /log-workflow endpoint."""

    workflow_execution_id: str
    workflow_name: str
    started_at: str  # ISO format from n8n
    finished_at: str  # ISO format from n8n
    status: Literal["success", "error"]
    error_message: str | None = None
    error_node: str | None = None
    nodes_executed: list[NodeExecution] = Field(default_factory=list)
    articles_count: int = 0
    claude_execution_id: str | None = None
    discord_sent: bool = False
    # Discord publication details
    discord_message_id: str | None = None
    discord_channel_id: str | None = None
    # Database storage details
    digest_id: int | None = None
    db_saved: bool = False
    articles_saved: int = 0
    # Discord command specific fields
    source: Literal["n8n_workflow", "discord_command"] = "n8n_workflow"
    discord_user: DiscordUser | None = None
    discord_guild: DiscordGuild | None = None
    discord_channel: DiscordChannel | None = None
    command_args: dict | None = None


class WorkflowLogResponse(BaseModel):
    """Response body for the /log-workflow endpoint."""

    success: bool
    log_file: str | None = None
    error: str | None = None


class CheckUrlsRequest(BaseModel):
    """Request body for the /check-urls endpoint."""

    urls: list[str] = Field(
        ...,
        description="List of URLs to check for duplicates",
        min_length=1,
    )
    mission_id: str = Field(
        default="ai-news",
        description="Mission ID to check against",
    )
    days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of days to look back for duplicates",
    )


class CheckUrlsResponse(BaseModel):
    """Response body for the /check-urls endpoint."""

    new_urls: list[str] = Field(
        default_factory=list,
        description="URLs that don't exist in the database",
    )
    duplicate_urls: list[str] = Field(
        default_factory=list,
        description="URLs that already exist in the database",
    )
    total_checked: int = 0
    duplicates_found: int = 0


class ClaudeResult(BaseModel):
    """Result from Claude CLI execution with full timeline."""

    response: str = ""
    timeline: list[StreamEvent] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    success: bool = False
    error: str | None = None
