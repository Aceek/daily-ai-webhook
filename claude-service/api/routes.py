#!/usr/bin/env python3
"""
FastAPI routes for Claude Service.

All HTTP endpoints are defined here.
"""

import logging

from fastapi import APIRouter

from api.models import (
    AnalyzeWeeklyRequest,
    AnalyzeWeeklyResponse,
    CheckUrlsRequest,
    CheckUrlsResponse,
    HealthResponse,
    SummarizeRequest,
    SummarizeResponse,
    WorkflowLogRequest,
    WorkflowLogResponse,
)
from config import APP_VERSION, Settings
from database import get_engine
from loggers import UnifiedLogger
from loggers.models import (
    DiscordChannelLog,
    DiscordGuildLog,
    DiscordUserLog,
    NodeExecutionLog,
    WorkflowLog,
)
from repositories.article_repository import check_duplicate_urls
from services.summarize_service import SummarizeService
from services.weekly_service import WeeklyService


logger = logging.getLogger("claude-service")


def create_routers(
    settings: Settings,
    execution_logger: UnifiedLogger,
    workflow_logger: UnifiedLogger,
) -> APIRouter:
    """Create API router with injected dependencies.

    Args:
        settings: Application settings.
        execution_logger: Execution logger instance.
        workflow_logger: Workflow logger instance.

    Returns:
        Configured APIRouter.
    """
    router = APIRouter()

    # Initialize services
    summarize_service = SummarizeService(settings, execution_logger)
    weekly_service = WeeklyService(settings, execution_logger)

    @router.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(status="healthy", version=APP_VERSION)

    @router.post("/summarize", response_model=SummarizeResponse)
    async def summarize(request: SummarizeRequest) -> SummarizeResponse:
        """Generate a news summary from articles using Claude CLI."""
        return await summarize_service.summarize(request)

    @router.post("/analyze-weekly", response_model=AnalyzeWeeklyResponse)
    async def analyze_weekly(request: AnalyzeWeeklyRequest) -> AnalyzeWeeklyResponse:
        """Generate a weekly digest by analyzing articles from database."""
        return await weekly_service.analyze_weekly(request)

    @router.post("/log-workflow", response_model=WorkflowLogResponse)
    async def log_workflow(request: WorkflowLogRequest) -> WorkflowLogResponse:
        """Log a workflow or Discord command execution."""
        return await _handle_log_workflow(request, workflow_logger)

    @router.post("/check-urls", response_model=CheckUrlsResponse)
    async def check_urls(request: CheckUrlsRequest) -> CheckUrlsResponse:
        """Check which URLs already exist in the database."""
        return await _handle_check_urls(request)

    return router


async def _handle_log_workflow(
    request: WorkflowLogRequest,
    workflow_logger: UnifiedLogger,
) -> WorkflowLogResponse:
    """Handle /log-workflow endpoint logic.

    Args:
        request: Workflow log request.
        workflow_logger: Workflow logger instance.

    Returns:
        WorkflowLogResponse with result.
    """
    source_type = "command" if request.source == "discord_command" else "workflow"
    logger.info("Logging %s: %s", source_type, request.workflow_execution_id)

    try:
        workflow_log = _convert_workflow_request(request)
        log_path = workflow_logger.save_workflow(workflow_log)
        logger.info("Workflow log saved: %s", log_path)
        return WorkflowLogResponse(success=True, log_file=str(log_path))
    except Exception as e:
        logger.error("Failed to save workflow log: %s", e)
        return WorkflowLogResponse(success=False, error=str(e))


async def _handle_check_urls(request: CheckUrlsRequest) -> CheckUrlsResponse:
    """Handle /check-urls endpoint logic.

    Args:
        request: Check URLs request.

    Returns:
        CheckUrlsResponse with results.
    """
    logger.info(
        "Checking %d URLs (mission=%s, days=%d)",
        len(request.urls),
        request.mission_id,
        request.days,
    )

    engine = get_engine()
    if not engine:
        logger.warning("Database not available, returning all URLs as new")
        return CheckUrlsResponse(
            new_urls=request.urls,
            duplicate_urls=[],
            total_checked=len(request.urls),
            duplicates_found=0,
        )

    new_urls, duplicate_urls = await check_duplicate_urls(
        engine,
        request.urls,
        request.mission_id,
        request.days,
    )

    return CheckUrlsResponse(
        new_urls=new_urls,
        duplicate_urls=duplicate_urls,
        total_checked=len(request.urls),
        duplicates_found=len(duplicate_urls),
    )


def _convert_workflow_request(request: WorkflowLogRequest) -> WorkflowLog:
    """Convert API request to WorkflowLog model.

    Args:
        request: API workflow log request.

    Returns:
        Internal WorkflowLog model.
    """
    from datetime import datetime

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
    """Convert Discord user from request.

    Args:
        request: Workflow log request.

    Returns:
        DiscordUserLog if present, None otherwise.
    """
    if not request.discord_user:
        return None
    return DiscordUserLog(
        id=request.discord_user.id,
        name=request.discord_user.name,
    )


def _convert_discord_guild(request: WorkflowLogRequest) -> DiscordGuildLog | None:
    """Convert Discord guild from request.

    Args:
        request: Workflow log request.

    Returns:
        DiscordGuildLog if present, None otherwise.
    """
    if not request.discord_guild:
        return None
    return DiscordGuildLog(
        id=request.discord_guild.id,
        name=request.discord_guild.name,
    )


def _convert_discord_channel(request: WorkflowLogRequest) -> DiscordChannelLog | None:
    """Convert Discord channel from request.

    Args:
        request: Workflow log request.

    Returns:
        DiscordChannelLog if present, None otherwise.
    """
    if not request.discord_channel:
        return None
    return DiscordChannelLog(
        id=request.discord_channel.id,
        name=request.discord_channel.name,
    )
