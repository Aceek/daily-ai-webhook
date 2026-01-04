#!/usr/bin/env python3
"""Weekly analysis service for Claude Service."""

import logging
import time
import uuid
from typing import TYPE_CHECKING

from api.models import (
    AnalyzeWeeklyRequest,
    AnalyzeWeeklyResponse,
    ClaudeResult,
)
from config import Settings, validate_weekly_mission
from loggers import UnifiedLogger, create_execution_log
from services.claude_service import call_claude_cli
from services.digest_service import read_digest_file
from services.prompt_builder import build_weekly_prompt

if TYPE_CHECKING:
    pass


logger = logging.getLogger("claude-service")


class WeeklyService:
    """Service for handling weekly analysis."""

    def __init__(self, settings: Settings, execution_logger: UnifiedLogger):
        """Initialize the weekly service.

        Args:
            settings: Application settings.
            execution_logger: Execution logger instance.
        """
        self.settings = settings
        self.execution_logger = execution_logger

    async def analyze_weekly(
        self, request: AnalyzeWeeklyRequest
    ) -> AnalyzeWeeklyResponse:
        """Process weekly analysis request.

        Args:
            request: Weekly analysis request data.

        Returns:
            AnalyzeWeeklyResponse with results.
        """
        logger.info(
            "Weekly analysis: mission='%s', week=%s to %s",
            request.mission,
            request.week_start,
            request.week_end,
        )

        valid, error = validate_weekly_mission(
            request.mission, self.settings.missions_path
        )
        if not valid:
            return AnalyzeWeeklyResponse(
                success=False,
                error=error,
                mission=request.mission,
                week_start=request.week_start,
                week_end=request.week_end,
            )

        execution_id = f"weekly-{uuid.uuid4().hex[:8]}"
        exec_dir = self.execution_logger.create_execution_dir(execution_id)

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

        claude_result = await call_claude_cli(prompt, exec_dir, self.settings)
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
            self.execution_logger.save(exec_log, exec_dir=exec_dir, digest=digest)
        except Exception as e:
            logger.error("Failed to save execution log: %s", e)

        success, error, digest_id = self._determine_result_status(
            claude_result, digest
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

    @staticmethod
    def _determine_result_status(
        result: ClaudeResult,
        digest: dict | None,
    ) -> tuple[bool, str | None, int | None]:
        """Determine final success status and error message.

        Args:
            result: Claude CLI result.
            digest: Digest data if available.

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
                error = "Claude did not call submit_weekly_digest tool"

        return success, error, digest_id
