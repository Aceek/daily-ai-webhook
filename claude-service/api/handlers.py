#!/usr/bin/env python3
"""
Request handlers for Claude Service API.

Contains the business logic for each API endpoint.
"""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from api.converters import convert_workflow_request
from api.models import (
    AnalyzeWeeklyRequest,
    AnalyzeWeeklyResponse,
    CheckUrlsRequest,
    CheckUrlsResponse,
    ClaudeResult,
    SummarizeRequest,
    SummarizeResponse,
    WorkflowLogRequest,
    WorkflowLogResponse,
)
from config import Settings, validate_mission, validate_weekly_mission
from database import get_engine
from loggers.execution_logger import ExecutionLogger, create_execution_log
from loggers.workflow_logger import WorkflowLogger
from repositories.article_repository import check_duplicate_urls
from services.claude_service import call_claude_cli, write_articles_file
from services.digest_service import read_digest_file
from services.prompt_builder import build_prompt, build_weekly_prompt

if TYPE_CHECKING:
    from utils.execution_dir import ExecutionDirectory


logger = logging.getLogger("claude-service")


async def handle_summarize(
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

    # Write articles file and call Claude
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

    claude_result = await call_claude_cli(prompt, exec_dir, settings)
    duration = time.time() - start_time

    if claude_result.success:
        logger.info("Summary generated for mission '%s'", request.mission)
    else:
        logger.error("Claude CLI failed: %s", claude_result.error)

    # Read digest and build response
    digest = read_digest_file(exec_dir)
    return _build_summarize_response(
        request, claude_result, exec_dir, digest, duration,
        execution_id, execution_logger,
    )


def _build_summarize_response(
    request: SummarizeRequest,
    result: ClaudeResult,
    exec_dir: "ExecutionDirectory",
    digest: dict | None,
    duration: float,
    execution_id: str,
    execution_logger: ExecutionLogger,
) -> SummarizeResponse:
    """Build response for /summarize endpoint."""
    exec_log = create_execution_log(
        articles=list(request.articles),
        prompt="",
        response=result.response,
        duration=duration,
        success=result.success,
        error=result.error,
        timeline=result.timeline,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=result.cost_usd,
        workflow_execution_id=request.workflow_execution_id,
        execution_id=execution_id,
        mission=request.mission,
    )

    try:
        execution_logger.save(exec_log, exec_dir=exec_dir, digest=digest)
    except Exception as e:
        logger.error("Failed to save execution log: %s", e)

    # Determine success and error
    success, error, digest_id = _determine_result_status(result, digest)
    summary_text = json.dumps(digest, ensure_ascii=False) if digest else ""

    return SummarizeResponse(
        summary=summary_text,
        article_count=len(request.articles),
        success=success,
        error=error,
        execution_id=execution_id,
        log_file=str(exec_dir.path),
        mission=request.mission,
        workflow_execution_id=request.workflow_execution_id,
        digest=digest,
        digest_id=digest_id,
    )


async def handle_analyze_weekly(
    request: AnalyzeWeeklyRequest,
    settings: Settings,
    execution_logger: ExecutionLogger,
) -> AnalyzeWeeklyResponse:
    """Handle /analyze-weekly endpoint logic."""
    logger.info(
        "Weekly analysis: mission='%s', week=%s to %s",
        request.mission,
        request.week_start,
        request.week_end,
    )

    valid, error = validate_weekly_mission(request.mission, settings.missions_path)
    if not valid:
        return AnalyzeWeeklyResponse(
            success=False,
            error=error,
            mission=request.mission,
            week_start=request.week_start,
            week_end=request.week_end,
        )

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

    claude_result = await call_claude_cli(prompt, exec_dir, settings)
    duration = time.time() - start_time
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
    except Exception as e:
        logger.error("Failed to save execution log: %s", e)

    success, error, digest_id = _determine_result_status(
        claude_result, digest, weekly=True
    )

    return AnalyzeWeeklyResponse(
        success=success,
        error=error,
        execution_id=execution_id,
        log_file=str(exec_dir.path),
        mission=request.mission,
        week_start=request.week_start,
        week_end=request.week_end,
        theme=request.theme,
        workflow_execution_id=request.workflow_execution_id,
        digest=digest,
        digest_id=digest_id,
    )


def _determine_result_status(
    result: ClaudeResult,
    digest: dict | None,
    weekly: bool = False,
) -> tuple[bool, str | None, int | None]:
    """Determine final success status and error message.

    Returns:
        Tuple of (success, error_message, digest_id).
    """
    success = result.success and digest is not None
    error = None
    digest_id = digest.get("digest_id") if digest else None

    if success and digest_id is None:
        success = False
        error = "Digest created but not saved to database"

    if not success and error is None:
        if not result.success:
            error = result.error
        elif digest is None:
            tool = "submit_weekly_digest" if weekly else "submit_digest"
            error = f"Claude did not call {tool} tool"

    return success, error, digest_id


async def handle_log_workflow(
    request: WorkflowLogRequest,
    workflow_logger: WorkflowLogger,
) -> WorkflowLogResponse:
    """Handle /log-workflow endpoint logic."""
    source_type = "command" if request.source == "discord_command" else "workflow"
    logger.info("Logging %s: %s", source_type, request.workflow_execution_id)

    try:
        workflow_log = convert_workflow_request(request)
        log_path = workflow_logger.save(workflow_log)
        logger.info("Workflow log saved: %s", log_path)
        return WorkflowLogResponse(success=True, log_file=str(log_path))
    except Exception as e:
        logger.error("Failed to save workflow log: %s", e)
        return WorkflowLogResponse(success=False, error=str(e))


async def handle_check_urls(request: CheckUrlsRequest) -> CheckUrlsResponse:
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
