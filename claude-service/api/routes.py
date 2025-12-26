#!/usr/bin/env python3
"""
FastAPI routes for Claude Service.

All HTTP endpoints are defined here.
"""

from fastapi import APIRouter

from api.handlers import (
    handle_analyze_weekly,
    handle_check_urls,
    handle_log_workflow,
    handle_summarize,
)
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
from loggers.execution_logger import ExecutionLogger
from loggers.workflow_logger import WorkflowLogger


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
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(status="healthy", version=APP_VERSION)

    @router.post("/summarize", response_model=SummarizeResponse)
    async def summarize(request: SummarizeRequest) -> SummarizeResponse:
        """Generate a news summary from articles using Claude CLI."""
        return await handle_summarize(request, settings, execution_logger)

    @router.post("/analyze-weekly", response_model=AnalyzeWeeklyResponse)
    async def analyze_weekly(request: AnalyzeWeeklyRequest) -> AnalyzeWeeklyResponse:
        """Generate a weekly digest by analyzing articles from database."""
        return await handle_analyze_weekly(request, settings, execution_logger)

    @router.post("/log-workflow", response_model=WorkflowLogResponse)
    async def log_workflow(request: WorkflowLogRequest) -> WorkflowLogResponse:
        """Log a workflow or Discord command execution."""
        return await handle_log_workflow(request, workflow_logger)

    @router.post("/check-urls", response_model=CheckUrlsResponse)
    async def check_urls(request: CheckUrlsRequest) -> CheckUrlsResponse:
        """Check which URLs already exist in the database."""
        return await handle_check_urls(request)

    return router
