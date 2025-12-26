#!/usr/bin/env python3
"""
Request/Response converters for Claude Service API.

Converts between API models and internal domain models.
"""

from datetime import datetime

from api.models import WorkflowLogRequest
from loggers.models import (
    DiscordChannelLog,
    DiscordGuildLog,
    DiscordUserLog,
    NodeExecutionLog,
    WorkflowLog,
)


def convert_workflow_request(request: WorkflowLogRequest) -> WorkflowLog:
    """Convert API request to WorkflowLog model.

    Args:
        request: API workflow log request.

    Returns:
        Internal WorkflowLog model.
    """
    started_at = datetime.fromisoformat(request.started_at.replace("Z", "+00:00"))
    finished_at = datetime.fromisoformat(request.finished_at.replace("Z", "+00:00"))

    nodes = [
        NodeExecutionLog(name=n.name, status=n.status, error=n.error)
        for n in request.nodes_executed
    ]

    discord_user = _convert_discord_user(request)
    discord_guild = _convert_discord_guild(request)
    discord_channel = _convert_discord_channel(request)

    return WorkflowLog(
        workflow_execution_id=request.workflow_execution_id,
        workflow_name=request.workflow_name,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=(finished_at - started_at).total_seconds(),
        status=request.status,
        error_message=request.error_message,
        error_node=request.error_node,
        nodes_executed=nodes,
        articles_count=request.articles_count,
        claude_execution_id=request.claude_execution_id,
        discord_sent=request.discord_sent,
        discord_message_id=request.discord_message_id,
        discord_channel_id=request.discord_channel_id,
        digest_id=request.digest_id,
        db_saved=request.db_saved,
        articles_saved=request.articles_saved,
        source=request.source,
        discord_user=discord_user,
        discord_guild=discord_guild,
        discord_channel=discord_channel,
        command_args=request.command_args,
    )


def _convert_discord_user(request: WorkflowLogRequest) -> DiscordUserLog | None:
    """Convert Discord user from request."""
    if not request.discord_user:
        return None
    return DiscordUserLog(
        id=request.discord_user.id,
        name=request.discord_user.name,
    )


def _convert_discord_guild(request: WorkflowLogRequest) -> DiscordGuildLog | None:
    """Convert Discord guild from request."""
    if not request.discord_guild:
        return None
    return DiscordGuildLog(
        id=request.discord_guild.id,
        name=request.discord_guild.name,
    )


def _convert_discord_channel(request: WorkflowLogRequest) -> DiscordChannelLog | None:
    """Convert Discord channel from request."""
    if not request.discord_channel:
        return None
    return DiscordChannelLog(
        id=request.discord_channel.id,
        name=request.discord_channel.name,
    )
