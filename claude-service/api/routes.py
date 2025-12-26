#!/usr/bin/env python3
"""
FastAPI routes for Claude Service.

All HTTP endpoints are defined here.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter

from api.models import (
    AnalyzeWeeklyRequest,
    AnalyzeWeeklyResponse,
    CheckUrlsRequest,
    CheckUrlsResponse,
    ClaudeResult,
    HealthResponse,
    SummarizeRequest,
    SummarizeResponse,
    WorkflowLogRequest,
    WorkflowLogResponse,
)
from config import (
    APP_VERSION,
    Settings,
    validate_mission,
    validate_weekly_mission,
)
from database import get_engine
from loggers.execution_logger import ExecutionLogger, create_execution_log
from loggers.models import (
    DiscordChannelLog,
    DiscordGuildLog,
    DiscordUserLog,
    NodeExecutionLog,
    WorkflowLog,
)
from loggers.workflow_logger import WorkflowLogger
from repositories.article_repository import check_duplicate_urls
from services.claude_service import (
    build_prompt,
    build_weekly_prompt,
    call_claude_cli,
    write_articles_file,
)
from services.digest_service import read_digest_file


logger = logging.getLogger("claude-service")

router = APIRouter()


def create_routers(
    settings: Settings,
    execution_logger: ExecutionLogger,
    workflow_logger: WorkflowLogger,
) -> APIRouter:
    """Create API router with injected dependencies.

    Args:
        settings: Application settings.
        execution_logger: Execution logger instance.
        workflow_logger: Workflow logger instance.

    Returns:
        Configured APIRouter.
    """
    api_router = APIRouter()

    @api_router.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(status="healthy", version=APP_VERSION)

    @api_router.post("/summarize", response_model=SummarizeResponse)
    async def summarize(request: SummarizeRequest) -> SummarizeResponse:
        """Generate a news summary from articles using Claude CLI."""
        return await _handle_summarize(
            request, settings, execution_logger
        )

    @api_router.post("/analyze-weekly", response_model=AnalyzeWeeklyResponse)
    async def analyze_weekly(request: AnalyzeWeeklyRequest) -> AnalyzeWeeklyResponse:
        """Generate a weekly digest by analyzing articles from database."""
        return await _handle_analyze_weekly(
            request, settings, execution_logger
        )

    @api_router.post("/log-workflow", response_model=WorkflowLogResponse)
    async def log_workflow(request: WorkflowLogRequest) -> WorkflowLogResponse:
        """Log a workflow or Discord command execution."""
        return await _handle_log_workflow(request, workflow_logger)

    @api_router.post("/check-urls", response_model=CheckUrlsResponse)
    async def check_urls(request: CheckUrlsRequest) -> CheckUrlsResponse:
        """Check which URLs already exist in the database."""
        return await _handle_check_urls(request)

    return api_router


async def _handle_summarize(
    request: SummarizeRequest,
    settings: Settings,
    execution_logger: ExecutionLogger,
) -> SummarizeResponse:
    """Handle /summarize endpoint logic.

    Args:
        request: Summarize request data.
        settings: Application settings.
        execution_logger: Logger instance.

    Returns:
        SummarizeResponse with results.
    """
    logger.info(
        "Received %d articles for mission '%s'",
        len(request.articles),
        request.mission,
    )

    # Validate mission
    valid, error = validate_mission(request.mission, settings.missions_path)
    if not valid:
        logger.error("Invalid mission: %s", error)
        return SummarizeResponse(
            summary="",
            article_count=len(request.articles),
            success=False,
            error=error,
            mission=request.mission,
        )

    # Generate execution ID and create directory
    execution_id = uuid.uuid4().hex[:12]
    exec_dir = execution_logger.create_execution_dir(execution_id)
    logger.info("Created execution directory: %s", exec_dir.path)

    # Write articles file
    articles_path = Path(settings.data_path) / "articles.json"
    write_articles_file(request.articles, articles_path)

    start_time = time.time()
    prompt = build_prompt(
        mission=request.mission,
        articles_path=str(articles_path),
        execution_id=execution_id,
        research_path=str(exec_dir.research_path),
        workflow_execution_id=request.workflow_execution_id,
    )

    # Call Claude CLI
    claude_result = await call_claude_cli(prompt, exec_dir, settings)
    duration = time.time() - start_time

    if claude_result.success:
        logger.info("Summary generated successfully for mission '%s'", request.mission)
    else:
        logger.error("Claude CLI failed: %s", claude_result.error)

    # Read digest and build response
    digest = read_digest_file(exec_dir)
    response = _build_summarize_response(
        request, claude_result, exec_dir, digest, duration, execution_id,
        execution_logger,
    )

    return response


def _build_summarize_response(
    request: SummarizeRequest,
    claude_result: ClaudeResult,
    exec_dir,
    digest: dict | None,
    duration: float,
    execution_id: str,
    execution_logger: ExecutionLogger,
) -> SummarizeResponse:
    """Build response for /summarize endpoint.

    Args:
        request: Original request.
        claude_result: Result from Claude CLI.
        exec_dir: Execution directory.
        digest: Parsed digest data.
        duration: Execution duration.
        execution_id: Execution ID.
        execution_logger: Logger for saving.

    Returns:
        Populated SummarizeResponse.
    """
    # Create and save execution log
    exec_log = create_execution_log(
        articles=list(request.articles),
        prompt="",  # Omitted for brevity
        response=claude_result.response,
        duration=duration,
        success=claude_result.success,
        error=claude_result.error,
        timeline=claude_result.timeline,
        input_tokens=claude_result.input_tokens,
        output_tokens=claude_result.output_tokens,
        cost_usd=claude_result.cost_usd,
        workflow_execution_id=request.workflow_execution_id,
        execution_id=execution_id,
        mission=request.mission,
    )

    try:
        execution_logger.save(exec_log, exec_dir=exec_dir, digest=digest)
        logger.info("Execution logs saved to: %s", exec_dir.path)
    except Exception as log_error:
        logger.error("Failed to save execution log: %s", log_error)

    # Determine success
    final_success = claude_result.success and digest is not None
    final_error = None
    digest_db_id = digest.get("digest_id") if digest else None

    if final_success and digest_db_id is None:
        final_success = False
        final_error = "Digest created but not saved to database"
        logger.error("Digest validation failed: no digest_id")

    if not final_success and final_error is None:
        if not claude_result.success:
            final_error = claude_result.error
        elif digest is None:
            final_error = "Claude did not call submit_digest tool"

    summary_text = json.dumps(digest, ensure_ascii=False) if digest else ""

    return SummarizeResponse(
        summary=summary_text,
        article_count=len(request.articles),
        success=final_success,
        error=final_error,
        execution_id=execution_id,
        log_file=str(exec_dir.path),
        mission=request.mission,
        workflow_execution_id=request.workflow_execution_id,
        digest=digest,
        digest_id=digest_db_id,
    )


async def _handle_analyze_weekly(
    request: AnalyzeWeeklyRequest,
    settings: Settings,
    execution_logger: ExecutionLogger,
) -> AnalyzeWeeklyResponse:
    """Handle /analyze-weekly endpoint logic."""
    logger.info(
        "Weekly analysis: mission='%s', week=%s to %s, theme=%s",
        request.mission,
        request.week_start,
        request.week_end,
        request.theme,
    )

    # Validate mission
    valid, error = validate_weekly_mission(request.mission, settings.missions_path)
    if not valid:
        logger.error("Invalid weekly mission: %s", error)
        return AnalyzeWeeklyResponse(
            success=False,
            error=error,
            mission=request.mission,
            week_start=request.week_start,
            week_end=request.week_end,
        )

    # Generate execution ID and directory
    execution_id = f"weekly-{uuid.uuid4().hex[:8]}"
    exec_dir = execution_logger.create_execution_dir(execution_id)

    start_time = time.time()
    prompt = build_weekly_prompt(
        mission=request.mission,
        week_start=request.week_start,
        week_end=request.week_end,
        execution_id=execution_id,
        research_path=str(exec_dir.research_path),
        theme=request.theme,
        workflow_execution_id=request.workflow_execution_id,
    )

    # Call Claude CLI
    claude_result = await call_claude_cli(prompt, exec_dir, settings)
    duration = time.time() - start_time

    # Read digest and save logs
    digest = read_digest_file(exec_dir)

    exec_log = create_execution_log(
        articles=[],
        prompt=prompt,
        response=claude_result.response,
        duration=duration,
        success=claude_result.success,
        error=claude_result.error,
        timeline=claude_result.timeline,
        input_tokens=claude_result.input_tokens,
        output_tokens=claude_result.output_tokens,
        cost_usd=claude_result.cost_usd,
        workflow_execution_id=request.workflow_execution_id,
        execution_id=execution_id,
        mission=request.mission,
    )

    try:
        execution_logger.save(exec_log, exec_dir=exec_dir, digest=digest)
    except Exception as log_error:
        logger.error("Failed to save execution log: %s", log_error)

    # Determine success
    final_success = claude_result.success and digest is not None
    final_error = None
    digest_db_id = digest.get("digest_id") if digest else None

    if final_success and digest_db_id is None:
        final_success = False
        final_error = "Weekly digest created but not saved to database"

    if not final_success and final_error is None:
        if not claude_result.success:
            final_error = claude_result.error
        elif digest is None:
            final_error = "Claude did not call submit_weekly_digest tool"

    return AnalyzeWeeklyResponse(
        success=final_success,
        error=final_error,
        execution_id=execution_id,
        log_file=str(exec_dir.path),
        mission=request.mission,
        week_start=request.week_start,
        week_end=request.week_end,
        theme=request.theme,
        workflow_execution_id=request.workflow_execution_id,
        digest=digest,
        digest_id=digest_db_id,
    )


async def _handle_log_workflow(
    request: WorkflowLogRequest,
    workflow_logger: WorkflowLogger,
) -> WorkflowLogResponse:
    """Handle /log-workflow endpoint logic."""
    source_type = "command" if request.source == "discord_command" else "workflow"
    logger.info(
        "Logging %s execution: %s (status: %s)",
        source_type,
        request.workflow_execution_id,
        request.status,
    )

    try:
        # Parse timestamps
        started_at = datetime.fromisoformat(request.started_at.replace("Z", "+00:00"))
        finished_at = datetime.fromisoformat(request.finished_at.replace("Z", "+00:00"))
        duration_seconds = (finished_at - started_at).total_seconds()

        # Convert nodes
        nodes = [
            NodeExecutionLog(name=n.name, status=n.status, error=n.error)
            for n in request.nodes_executed
        ]

        # Convert Discord info
        discord_user = None
        discord_guild = None
        discord_channel = None

        if request.discord_user:
            discord_user = DiscordUserLog(
                id=request.discord_user.id,
                name=request.discord_user.name,
            )
        if request.discord_guild:
            discord_guild = DiscordGuildLog(
                id=request.discord_guild.id,
                name=request.discord_guild.name,
            )
        if request.discord_channel:
            discord_channel = DiscordChannelLog(
                id=request.discord_channel.id,
                name=request.discord_channel.name,
            )

        # Create workflow log
        workflow_log = WorkflowLog(
            workflow_execution_id=request.workflow_execution_id,
            workflow_name=request.workflow_name,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
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

        log_path = workflow_logger.save(workflow_log)
        logger.info("Workflow log saved: %s", log_path)

        return WorkflowLogResponse(success=True, log_file=str(log_path))

    except Exception as e:
        logger.error("Failed to save workflow log: %s", e)
        return WorkflowLogResponse(success=False, error=str(e))


async def _handle_check_urls(request: CheckUrlsRequest) -> CheckUrlsResponse:
    """Handle /check-urls endpoint logic."""
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
