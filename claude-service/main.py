#!/usr/bin/env python3
"""
Claude Service - HTTP wrapper for Claude Code CLI.

Provides /summarize endpoint for n8n integration.
This service wraps Claude Code CLI to expose it as an HTTP API.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from database import close_db, init_db, seed_missions

from execution_logger import (
    ExecutionDirectory,
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

    model_config = SettingsConfigDict(env_prefix="CLAUDE_")

    claude_model: str = "sonnet"
    claude_timeout: int = 600  # Increased for agentic workflow
    retry_count: int = 1
    logs_path: str = "/app/logs"
    log_level: str = "info"

    # Multi-mission architecture paths
    missions_path: str = "/app/missions"
    data_path: str = "/app/data"

    # Digests directory (where MCP server writes the structured output)
    digests_path: str = "/app/logs/digests"

    # Allowed tools for agentic workflow
    # MCP tools: submit_digest, submit_weekly_digest, get_categories, get_articles, get_article_stats
    allowed_tools: str = "Read,WebSearch,WebFetch,Write,Task,mcp__submit-digest__submit_digest,mcp__submit-digest__submit_weekly_digest,mcp__submit-digest__get_categories,mcp__submit-digest__get_articles,mcp__submit-digest__get_article_stats"

    # Database connection (uses DATABASE_URL without prefix)
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")


# Valid missions (extensible)
VALID_MISSIONS = ["ai-news"]


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init and cleanup."""
    # Startup
    if settings.database_url:
        await init_db(settings.database_url)
        await seed_missions()
        logger.info("Database connected and seeded")
    else:
        logger.warning("DATABASE_URL not set, running without database")

    yield

    # Shutdown
    if settings.database_url:
        await close_db()
        logger.info("Database connection closed")


# FastAPI application
app = FastAPI(
    title="Claude Service",
    description="HTTP wrapper for Claude Code CLI",
    version="1.0.0",
    lifespan=lifespan,
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
    mission: str = Field(
        default="ai-news",
        description="Mission to execute (e.g., 'ai-news', 'video-games')",
    )
    workflow_execution_id: str | None = Field(
        default=None,
        description="ID of the n8n workflow execution for log correlation",
    )


class SummarizeResponse(BaseModel):
    """Response body for the /summarize endpoint."""

    summary: str  # Kept for backwards compatibility, contains stringified digest
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
    # New: structured digest from MCP server
    digest: dict | None = Field(
        default=None,
        description="Structured digest submitted via MCP submit_digest tool",
    )
    # Database ID of the saved digest (for /publish endpoint)
    digest_id: int | None = Field(
        default=None,
        description="Database ID of the saved digest",
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


def validate_mission(mission: str) -> tuple[bool, str | None]:
    """Validate that mission exists and has required files.

    Args:
        mission: Name of the mission to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if mission not in VALID_MISSIONS:
        return False, f"Unknown mission: {mission}. Valid missions: {VALID_MISSIONS}"

    mission_path = Path(settings.missions_path) / mission
    required_files = ["mission.md", "selection-rules.md", "editorial-guide.md", "output-schema.md"]

    for f in required_files:
        if not (mission_path / f).exists():
            return False, f"Missing mission file: {mission_path / f}"

    return True, None


def write_articles_file(articles: list[Article], path: Path) -> None:
    """Write articles to JSON file for Claude to read.

    Args:
        articles: List of articles to write.
        path: Path to write the JSON file.
    """
    import json

    data = [
        {
            "title": a.title,
            "url": a.url,
            "description": a.description[:500] if a.description else "",
            "pub_date": a.pub_date,
            "source": a.source,
        }
        for a in articles
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Wrote %d articles to %s", len(articles), path)


def build_prompt(
    mission: str,
    articles_path: str,
    execution_id: str,
    research_path: str,
    workflow_execution_id: str | None = None,
) -> str:
    """Build minimal prompt for multi-mission architecture.

    Claude will read mission files itself based on CLAUDE.md instructions.

    Args:
        mission: Name of the mission to execute.
        articles_path: Path to the articles JSON file.
        execution_id: Unique execution ID for this run.
        research_path: Path where Claude should write the research document.
        workflow_execution_id: Optional n8n workflow execution ID.

    Returns:
        Minimal prompt string for Claude CLI.
    """
    return f"""=== EXECUTION PARAMETERS ===

mission: {mission}
articles_path: {articles_path}
execution_id: {execution_id}
research_path: {research_path}
workflow_id: {workflow_execution_id or "standalone"}
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

=== INSTRUCTIONS ===

Suis le protocole de démarrage de ton CLAUDE.md.
Lis les fichiers de mission dans l'ordre indiqué avant de commencer ton analyse.

Remplace {{mission}} par: {mission}
"""


async def call_claude_cli(prompt: str, exec_dir: ExecutionDirectory) -> ClaudeResult:
    """Call Claude Code CLI with agentic capabilities.

    Executes claude CLI as a subprocess with retry logic
    and timeout handling. Enables WebSearch, WebFetch, Write,
    and Task tools for intelligent news research.

    Args:
        prompt: The prompt to send to Claude CLI.
        exec_dir: The execution directory for this run.

    Returns:
        ClaudeResult with response, timeline, and metrics.
    """
    cmd = [
        "claude",
        "-p", prompt,
        "--model", settings.claude_model,
        "--allowedTools", settings.allowed_tools,
        "--output-format", "stream-json",
        "--verbose",
    ]

    for attempt in range(settings.retry_count + 1):
        try:
            logger.info("Calling Claude CLI (attempt %d)", attempt + 1)
            start_time = time.time()

            import os
            env = os.environ.copy()
            # Pass execution directory to MCP server via environment variable
            env["EXECUTION_DIR"] = str(exec_dir.path)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=settings.claude_timeout,
            )

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                stdout_msg = stdout.decode().strip()[-2000:]  # Last 2000 chars
                logger.error("Claude CLI error (code %d): stderr=%s, stdout=%s",
                           process.returncode, error_msg, stdout_msg)
                if attempt < settings.retry_count:
                    await asyncio.sleep(2)
                    continue
                return ClaudeResult(
                    success=False,
                    error=f"Claude CLI failed (code {process.returncode}): {error_msg or stdout_msg}",
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


def read_digest_file(exec_dir: ExecutionDirectory) -> dict | None:
    """Read the digest JSON file created by the MCP submit_digest tool.

    Args:
        exec_dir: The execution directory containing the digest file.

    Returns:
        Parsed digest dict if file exists, None otherwise.
    """
    import json

    digest_path = exec_dir.digest_path

    if not digest_path.exists():
        logger.warning("Digest file not found: %s", digest_path)
        return None

    try:
        with open(digest_path, encoding="utf-8") as f:
            digest = json.load(f)
        logger.info("Read digest from %s", digest_path)
        return digest
    except json.JSONDecodeError as e:
        logger.error("Failed to parse digest file %s: %s", digest_path, e)
        return None
    except Exception as e:
        logger.error("Failed to read digest file %s: %s", digest_path, e)
        return None


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

    Uses multi-mission architecture: Claude reads mission files itself.

    Args:
        request: Request containing articles and mission to execute.

    Returns:
        Summary response with success status and generated content.
    """
    import uuid

    logger.info(
        "Received %d articles for mission '%s'",
        len(request.articles),
        request.mission,
    )

    # Validate mission before proceeding
    valid, error = validate_mission(request.mission)
    if not valid:
        logger.error("Invalid mission: %s", error)
        return SummarizeResponse(
            summary="",
            article_count=len(request.articles),
            success=False,
            error=error,
            mission=request.mission,
        )

    # Generate execution ID early
    execution_id = uuid.uuid4().hex[:12]

    # Create execution directory immediately (new folder structure)
    exec_dir = execution_logger.create_execution_dir(execution_id)
    logger.info("Created execution directory: %s", exec_dir.path)

    # Write articles to file for Claude to read
    articles_path = Path(settings.data_path) / "articles.json"
    write_articles_file(request.articles, articles_path)

    start_time = time.time()
    prompt = ""
    claude_result: ClaudeResult | None = None

    try:
        prompt = build_prompt(
            mission=request.mission,
            articles_path=str(articles_path),
            execution_id=execution_id,
            research_path=str(exec_dir.research_path),
            workflow_execution_id=request.workflow_execution_id,
        )
        claude_result = await call_claude_cli(prompt, exec_dir)

        if claude_result.success:
            logger.info("Summary generated successfully for mission '%s'", request.mission)
        else:
            logger.error("Claude CLI failed: %s", claude_result.error)

    except Exception as e:
        logger.error("Error generating summary: %s", e)
        claude_result = ClaudeResult(success=False, error=str(e))

    # Calculate duration
    duration = time.time() - start_time

    # Read the digest file created by MCP submit_digest tool
    digest = read_digest_file(exec_dir)

    # Create execution log
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
        execution_id=execution_id,
        mission=request.mission,
    )

    # Save all logs to the execution directory (reuse existing exec_dir)
    try:
        execution_logger.save(exec_log, exec_dir=exec_dir, digest=digest)
        logger.info(
            "Execution logs saved to: %s (id: %s, mission: %s, duration: %.2fs)",
            exec_dir.path,
            exec_log.execution_id,
            request.mission,
            duration,
        )
    except Exception as log_error:
        logger.error("Failed to save execution log: %s", log_error)

    # Determine success: we need both Claude CLI success AND a valid digest
    final_success = (claude_result.success if claude_result else False) and digest is not None
    final_error = None

    if not final_success:
        if claude_result and not claude_result.success:
            final_error = claude_result.error
        elif digest is None:
            final_error = "Claude did not call submit_digest tool - no digest file found"

    # For summary field: use stringified digest for backwards compatibility
    import json as json_module
    summary_text = json_module.dumps(digest, ensure_ascii=False) if digest else ""

    # Extract digest_id from digest (added by MCP submit_digest)
    digest_db_id = digest.get("digest_id") if digest else None

    return SummarizeResponse(
        summary=summary_text,
        article_count=len(request.articles),
        success=final_success,
        error=final_error,
        execution_id=exec_log.execution_id,
        log_file=str(exec_dir.path),
        mission=request.mission,
        workflow_execution_id=request.workflow_execution_id,
        digest=digest,
        digest_id=digest_db_id,
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
        "Logging workflow execution: %s (status: %s, claude_id: %s)",
        request.workflow_execution_id,
        request.status,
        request.claude_execution_id,
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

        # Save the workflow log (will find matching execution directory if available)
        log_path = workflow_logger.save(workflow_log)
        logger.info(
            "Workflow log saved: %s (duration: %.2fs, nodes: %d)",
            log_path,
            duration_seconds,
            len(nodes),
        )

        return WorkflowLogResponse(
            success=True,
            log_file=str(log_path),
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
