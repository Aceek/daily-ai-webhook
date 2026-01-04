#!/usr/bin/env python3
"""Summarize service for Claude Service."""

import json
import logging
import time
import uuid
from typing import TYPE_CHECKING

from api.models import (
    ClaudeResult,
    SummarizeRequest,
    SummarizeResponse,
)
from config import Settings, validate_mission
from loggers import UnifiedLogger, create_execution_log
from services.claude_service import call_claude_cli, write_articles_file
from services.digest_service import read_digest_file
from services.prompt_builder import build_prompt

if TYPE_CHECKING:
    from utils.execution_dir import ExecutionDirectory


logger = logging.getLogger("claude-service")


class SummarizeService:
    """Service for handling article summarization."""

    def __init__(self, settings: Settings, execution_logger: UnifiedLogger):
        """Initialize the summarize service.

        Args:
            settings: Application settings.
            execution_logger: Execution logger instance.
        """
        self.settings = settings
        self.execution_logger = execution_logger

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        """Process summarize request.

        Args:
            request: Summarize request data.

        Returns:
            SummarizeResponse with results.
        """
        logger.info(
            "Received %d articles for mission '%s'",
            len(request.articles),
            request.mission,
        )

        # Validate mission
        valid, error = validate_mission(request.mission, self.settings.missions_path)
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
        exec_dir = self.execution_logger.create_execution_dir(execution_id)
        logger.info("Created execution directory: %s", exec_dir.path)

        # Write articles file and call Claude
        from pathlib import Path
        articles_path = Path(self.settings.data_path) / "articles.json"
        write_articles_file(request.articles, articles_path)

        start_time = time.time()
        prompt = build_prompt(
            mission=request.mission,
            articles_path=str(articles_path),
            execution_id=execution_id,
            research_path=str(exec_dir.research_path),
            workflow_execution_id=request.workflow_execution_id,
        )

        claude_result = await call_claude_cli(prompt, exec_dir, self.settings)
        duration = time.time() - start_time

        if claude_result.success:
            logger.info("Summary generated for mission '%s'", request.mission)
        else:
            logger.error("Claude CLI failed: %s", claude_result.error)

        # Read digest and build response
        digest = read_digest_file(exec_dir)
        return self._build_response(
            request, claude_result, exec_dir, digest, duration, execution_id
        )

    def _build_response(
        self,
        request: SummarizeRequest,
        result: ClaudeResult,
        exec_dir: "ExecutionDirectory",
        digest: dict | None,
        duration: float,
        execution_id: str,
    ) -> SummarizeResponse:
        """Build response for /summarize endpoint.

        Args:
            request: Original request.
            result: Claude CLI result.
            exec_dir: Execution directory.
            digest: Digest data if available.
            duration: Execution duration in seconds.
            execution_id: Unique execution ID.

        Returns:
            Complete SummarizeResponse.
        """
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
            self.execution_logger.save(exec_log, exec_dir=exec_dir, digest=digest)
        except Exception as e:
            logger.error("Failed to save execution log: %s", e)

        # Determine success and error
        success, error, digest_id = self._determine_result_status(result, digest)
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
                error = "Claude did not call submit_digest tool"

        return success, error, digest_id
