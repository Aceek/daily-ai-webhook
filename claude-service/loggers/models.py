#!/usr/bin/env python3
"""
Logging models for Claude Service.

Pydantic models for execution and workflow logging.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared.models import ArticleLog


class StreamEvent(BaseModel):
    """Represents a single event from Claude CLI stream-json output."""

    timestamp: float = 0.0
    event_type: str
    content: str = ""
    raw_data: dict = Field(default_factory=dict)


class ExecutionMetrics(BaseModel):
    """Metrics captured during execution."""

    prompt_length: int = 0
    response_length: int = 0
    articles_received: int = 0
    duration_seconds: float = 0.0
    total_cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0


class NodeExecutionLog(BaseModel):
    """Represents the execution status of a single n8n workflow node."""

    name: str
    status: str
    error: str | None = None


class DiscordUserLog(BaseModel):
    """Discord user info for logging."""

    id: str
    name: str


class DiscordGuildLog(BaseModel):
    """Discord guild info for logging."""

    id: str
    name: str | None = None


class DiscordChannelLog(BaseModel):
    """Discord channel info for logging."""

    id: str
    name: str | None = None


class WorkflowLog(BaseModel):
    """Complete log data for an n8n workflow or Discord command execution."""

    workflow_execution_id: str
    workflow_name: str = "Unknown Workflow"
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime = Field(default_factory=datetime.now)
    duration_seconds: float = 0.0
    status: str = "success"
    error_message: str | None = None
    error_node: str | None = None
    nodes_executed: list[NodeExecutionLog] = Field(default_factory=list)
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
    source: str = "n8n_workflow"  # "n8n_workflow" or "discord_command"
    discord_user: DiscordUserLog | None = None
    discord_guild: DiscordGuildLog | None = None
    discord_channel: DiscordChannelLog | None = None
    command_args: dict | None = None


class ExecutionLog(BaseModel):
    """Complete execution log data."""

    execution_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: datetime = Field(default_factory=datetime.now)
    mission: str = "ai-news"
    success: bool = False
    error: str | None = None
    workflow_execution_id: str | None = None
    articles: list[ArticleLog] = Field(default_factory=list)
    prompt_sent: str = ""
    claude_response: str = ""
    timeline: list[StreamEvent] = Field(default_factory=list)
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)


def create_execution_log(
    articles: list[Any],
    prompt: str,
    response: str,
    duration: float,
    success: bool,
    error: str | None = None,
    timeline: list[StreamEvent] | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
    workflow_execution_id: str | None = None,
    execution_id: str | None = None,
    mission: str = "ai-news",
) -> ExecutionLog:
    """Factory function to create an ExecutionLog from raw data.

    Args:
        articles: List of articles processed.
        prompt: Prompt sent to Claude.
        response: Response from Claude.
        duration: Execution duration in seconds.
        success: Whether execution succeeded.
        error: Error message if failed.
        timeline: Stream events timeline.
        input_tokens: Input token count.
        output_tokens: Output token count.
        cost_usd: Cost in USD.
        workflow_execution_id: n8n workflow ID.
        execution_id: Unique execution ID.
        mission: Mission name.

    Returns:
        Populated ExecutionLog instance.
    """
    article_logs = [
        ArticleLog(
            title=a.title,
            url=a.url,
            source=a.source,
            pub_date=a.pub_date,
            description_preview=a.description[:100] if a.description else "",
        )
        for a in articles
    ]

    metrics = ExecutionMetrics(
        prompt_length=len(prompt),
        response_length=len(response),
        articles_received=len(articles),
        duration_seconds=duration,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_cost_usd=cost_usd,
    )

    log_kwargs: dict[str, Any] = {
        "success": success,
        "error": error,
        "workflow_execution_id": workflow_execution_id,
        "articles": article_logs,
        "prompt_sent": prompt,
        "claude_response": response,
        "timeline": timeline or [],
        "metrics": metrics,
        "mission": mission,
    }
    if execution_id:
        log_kwargs["execution_id"] = execution_id

    return ExecutionLog(**log_kwargs)
