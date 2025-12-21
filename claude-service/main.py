#!/usr/bin/env python3
"""
Claude Service - HTTP wrapper for Claude Code CLI.

Provides /summarize endpoint for n8n integration.
This service wraps Claude Code CLI to expose it as an HTTP API.
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from execution_logger import (
    ExecutionLogger,
    NodeExecutionLog,
    StreamEvent,
    WorkflowLog,
    WorkflowLogger,
    create_execution_log,
    parse_stream_event,
)


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables
    with the CLAUDE_ prefix.
    """

    claude_model: str = "sonnet"
    claude_timeout: int = 120
    retry_count: int = 1
    rules_path: str = "/app/config/rules.md"
    editorial_guide_path: str = "/app/config/editorial-guide.md"
    logs_path: str = "/app/logs"
    log_level: str = "info"

    class Config:
        """Pydantic settings configuration."""

        env_prefix = "CLAUDE_"


settings = Settings()

# Logging configuration
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("claude-service")

# Execution logger for detailed per-execution logs
execution_logger = ExecutionLogger(logs_dir=settings.logs_path)

# Workflow logger for n8n workflow execution logs
workflow_logger = WorkflowLogger(logs_dir=settings.logs_path)

# FastAPI application
app = FastAPI(
    title="Claude Service",
    description="HTTP wrapper for Claude Code CLI",
    version="1.0.0",
)


# Pydantic models
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
    workflow_execution_id: str | None = Field(
        default=None,
        description="ID of the n8n workflow execution for log correlation",
    )


class SummarizeResponse(BaseModel):
    """Response body for the /summarize endpoint."""

    summary: str
    article_count: int
    success: bool
    error: str | None = None
    execution_id: str | None = None
    log_file: str | None = None
    workflow_execution_id: str | None = Field(
        default=None,
        description="ID of the n8n workflow execution if provided",
    )


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str
    version: str


# Models for /log-workflow endpoint
class NodeExecution(BaseModel):
    """Represents a single node execution in an n8n workflow."""

    name: str
    status: Literal["success", "error", "skipped"]
    error: str | None = None


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


class WorkflowLogResponse(BaseModel):
    """Response body for the /log-workflow endpoint."""

    success: bool
    log_file: str | None = None
    error: str | None = None


class ClaudeResult(BaseModel):
    """Result from Claude CLI execution with full timeline."""

    response: str = ""
    timeline: list[StreamEvent] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    success: bool = False
    error: str | None = None


def load_file(path: str) -> str:
    """Load content from a file.

    Args:
        path: Path to the file to load.

    Returns:
        File content as string, or empty string if file not found.
    """
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("File not found: %s", path)
        return ""


def build_prompt(articles: list[Article]) -> str:
    """Build the prompt for Claude CLI.

    Constructs a complete prompt including selection rules,
    editorial guidelines, and the articles to analyze.

    Args:
        articles: List of articles to include in the prompt.

    Returns:
        Complete prompt string for Claude CLI.
    """
    rules = load_file(settings.rules_path)
    guide = load_file(settings.editorial_guide_path)

    articles_text = "\n---\n".join(
        [
            f"[{i + 1}] {a.title}\n"
            f"Source: {a.source}\n"
            f"URL: {a.url}\n"
            f"Date: {a.pub_date}\n"
            f"Summary: {a.description[:500]}"
            for i, a in enumerate(articles)
        ]
    )

    return f"""You are an AI/ML news editor. Your task is to analyze the following articles and produce a daily news summary.

=== SELECTION RULES ===
{rules}

=== EDITORIAL GUIDELINES ===
{guide}

=== ARTICLES TO ANALYZE ({len(articles)} articles) ===
{articles_text if articles else "No articles provided today."}

=== INSTRUCTIONS ===
1. Analyze all articles according to the selection rules
2. If no articles are relevant or provided, write a brief message explaining there's no significant AI news today
3. Select the most relevant and important news
4. Write the summary following the editorial guidelines exactly
5. Use the exact format specified (TOP HEADLINES, etc.)
6. Keep it under 2000 characters total
7. Output ONLY the formatted summary, nothing else

Generate the summary now:"""


async def call_claude_cli(prompt: str) -> ClaudeResult:
    """Call Claude Code CLI with the given prompt using stream-json format.

    Executes claude CLI as a subprocess with retry logic
    and timeout handling. Captures full execution timeline.

    Args:
        prompt: The prompt to send to Claude CLI.

    Returns:
        ClaudeResult with response, timeline, and metrics.
    """
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose"]

    for attempt in range(settings.retry_count + 1):
        try:
            logger.info("Calling Claude CLI (attempt %d)", attempt + 1)
            start_time = time.time()

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=settings.claude_timeout,
            )

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error("Claude CLI error: %s", error_msg)
                if attempt < settings.retry_count:
                    await asyncio.sleep(2)
                    continue
                return ClaudeResult(
                    success=False,
                    error=f"Claude CLI failed: {error_msg}",
                )

            # Parse stream-json output
            return parse_stream_output(stdout.decode(), start_time)

        except asyncio.TimeoutError:
            logger.error(
                "Claude CLI timeout after %ds", settings.claude_timeout
            )
            if attempt < settings.retry_count:
                continue
            return ClaudeResult(
                success=False,
                error=f"Claude CLI timeout after {settings.claude_timeout}s",
            )

    return ClaudeResult(success=False, error="All retry attempts failed")


def parse_stream_output(output: str, start_time: float) -> ClaudeResult:
    """Parse stream-json output from Claude CLI.

    Args:
        output: Raw stdout from Claude CLI with stream-json format.
        start_time: Start time for calculating relative timestamps.

    Returns:
        ClaudeResult with parsed data.
    """
    import json

    timeline: list[StreamEvent] = []
    response_text = ""
    input_tokens = 0
    output_tokens = 0
    cost_usd = 0.0

    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        # Parse the event
        event = parse_stream_event(line, start_time)
        if event:
            timeline.append(event)

            # Extract final response text from result event
            if event.event_type == "result":
                result_data = event.raw_data
                # Extract response from result
                response_text = result_data.get("result", "")
                # Extract cost (correct field name)
                cost_usd = result_data.get("total_cost_usd", 0.0)
                # Extract tokens from usage dict
                usage = result_data.get("usage", {})
                if usage:
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    # Add cache tokens to input count for full picture
                    cache_creation = usage.get("cache_creation_input_tokens", 0)
                    cache_read = usage.get("cache_read_input_tokens", 0)
                    input_tokens += cache_creation + cache_read

            # Also extract text from assistant messages as backup
            elif event.event_type == "assistant" and not response_text:
                message = event.raw_data.get("message", {})
                contents = message.get("content", [])
                for c in contents:
                    if isinstance(c, dict) and c.get("type") == "text":
                        response_text = c.get("text", "")

    logger.info(
        "Parsed %d events, %d input tokens, %d output tokens, $%.4f",
        len(timeline),
        input_tokens,
        output_tokens,
        cost_usd,
    )

    return ClaudeResult(
        response=response_text,
        timeline=timeline,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        success=True,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status and version information.
    """
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    """Generate a news summary from articles using Claude CLI.

    Args:
        request: Request containing articles to summarize.

    Returns:
        Summary response with success status and generated content.
    """
    logger.info("Received %d articles to summarize", len(request.articles))

    start_time = time.time()
    prompt = ""
    claude_result: ClaudeResult | None = None

    try:
        prompt = build_prompt(request.articles)
        claude_result = await call_claude_cli(prompt)

        if claude_result.success:
            logger.info("Summary generated successfully")
        else:
            logger.error("Claude CLI failed: %s", claude_result.error)

    except Exception as e:
        logger.error("Error generating summary: %s", e)
        claude_result = ClaudeResult(success=False, error=str(e))

    # Calculate duration
    duration = time.time() - start_time

    # Create and save execution log with full timeline
    exec_log = create_execution_log(
        articles=list(request.articles),
        prompt=prompt,
        response=claude_result.response if claude_result else "",
        duration=duration,
        success=claude_result.success if claude_result else False,
        error=claude_result.error if claude_result else "Unknown error",
        timeline=claude_result.timeline if claude_result else [],
        input_tokens=claude_result.input_tokens if claude_result else 0,
        output_tokens=claude_result.output_tokens if claude_result else 0,
        cost_usd=claude_result.cost_usd if claude_result else 0.0,
        workflow_execution_id=request.workflow_execution_id,
    )

    try:
        md_path, json_path = execution_logger.save(exec_log)
        logger.info(
            "Execution log saved: %s (id: %s, duration: %.2fs, events: %d)",
            md_path.name,
            exec_log.execution_id,
            duration,
            len(exec_log.timeline),
        )
    except Exception as log_error:
        logger.error("Failed to save execution log: %s", log_error)
        md_path = None

    return SummarizeResponse(
        summary=claude_result.response if claude_result else "",
        article_count=len(request.articles),
        success=claude_result.success if claude_result else False,
        error=claude_result.error if claude_result else "Unknown error",
        execution_id=exec_log.execution_id,
        log_file=md_path.name if md_path else None,
        workflow_execution_id=request.workflow_execution_id,
    )


@app.post("/log-workflow", response_model=WorkflowLogResponse)
async def log_workflow(request: WorkflowLogRequest) -> WorkflowLogResponse:
    """Log an n8n workflow execution.

    Receives workflow execution data from n8n and saves it as a structured log.
    This enables correlation between workflow executions and Claude CLI calls.

    Args:
        request: Request containing workflow execution details.

    Returns:
        Response with success status and log file name.
    """
    logger.info(
        "Logging workflow execution: %s (status: %s)",
        request.workflow_execution_id,
        request.status,
    )

    try:
        # Parse ISO timestamps to datetime
        started_at = datetime.fromisoformat(request.started_at.replace("Z", "+00:00"))
        finished_at = datetime.fromisoformat(request.finished_at.replace("Z", "+00:00"))

        # Calculate duration
        duration_seconds = (finished_at - started_at).total_seconds()

        # Convert NodeExecution to NodeExecutionLog
        nodes = [
            NodeExecutionLog(
                name=node.name,
                status=node.status,
                error=node.error,
            )
            for node in request.nodes_executed
        ]

        # Create WorkflowLog from request
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
        )

        # Save the workflow log
        md_path, json_path = workflow_logger.save(workflow_log)
        logger.info(
            "Workflow log saved: %s (duration: %.2fs, nodes: %d)",
            md_path.name,
            duration_seconds,
            len(nodes),
        )

        return WorkflowLogResponse(
            success=True,
            log_file=md_path.name,
        )

    except Exception as e:
        logger.error("Failed to save workflow log: %s", e)
        return WorkflowLogResponse(
            success=False,
            error=str(e),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
