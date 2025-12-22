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

    claude_model: str = "sonnet"
    claude_timeout: int = 600  # Increased for agentic workflow
    retry_count: int = 1
    logs_path: str = "/app/logs"
    log_level: str = "info"

    # Claude config paths (mounted from claude-config/)
    claude_instructions_path: str = "/root/.claude/CLAUDE.md"
    selection_rules_path: str = "/root/.claude/docs/selection-rules.md"
    editorial_guide_path: str = "/root/.claude/docs/editorial-guide.md"
    output_schema_path: str = "/root/.claude/docs/output-schema.md"
    research_template_path: str = "/root/.claude/docs/research-template.md"

    # Digests directory (where MCP server writes the structured output)
    digests_path: str = "/app/logs/digests"

    # Allowed tools for agentic workflow (mcp__submit-digest__submit_digest is auto-added via MCP)
    allowed_tools: str = "WebSearch,WebFetch,Write,Task,mcp__submit-digest__submit_digest"

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

    summary: str  # Kept for backwards compatibility, contains stringified digest
    article_count: int
    success: bool
    error: str | None = None
    execution_id: str | None = None
    log_file: str | None = None
    workflow_execution_id: str | None = Field(
        default=None,
        description="ID of the n8n workflow execution if provided",
    )
    # New: structured digest from MCP server
    digest: dict | None = Field(
        default=None,
        description="Structured digest submitted via MCP submit_digest tool",
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


def build_prompt(
    articles: list[Article],
    execution_id: str,
    exec_dir: ExecutionDirectory,
    workflow_execution_id: str | None = None,
) -> str:
    """Build the enriched prompt for agentic Claude CLI.

    Constructs a complete prompt including agent instructions,
    selection rules, editorial guidelines, output schema,
    and the articles to analyze.

    Args:
        articles: List of articles to include in the prompt.
        execution_id: Unique execution ID for this run.
        exec_dir: The execution directory for this run.
        workflow_execution_id: Optional n8n workflow execution ID.

    Returns:
        Complete prompt string for Claude CLI.
    """
    # Load all configuration files
    instructions = load_file(settings.claude_instructions_path)
    selection_rules = load_file(settings.selection_rules_path)
    editorial_guide = load_file(settings.editorial_guide_path)
    output_schema = load_file(settings.output_schema_path)

    # Format articles
    articles_text = "\n---\n".join(
        [
            f"[{i + 1}] {a.title}\n"
            f"Source: {a.source}\n"
            f"URL: {a.url}\n"
            f"Date: {a.pub_date}\n"
            f"Description: {a.description[:500] if a.description else 'N/A'}"
            for i, a in enumerate(articles)
        ]
    )

    # Use the execution directory for research document
    research_path = str(exec_dir.research_path)

    return f"""{instructions}

=== SELECTION RULES ===
{selection_rules}

=== EDITORIAL GUIDELINES ===
{editorial_guide}

=== OUTPUT SCHEMA ===
{output_schema}

=== ARTICLES TO ANALYZE ({len(articles)} articles) ===
{articles_text if articles else "No articles provided by primary sources today."}

=== EXECUTION PARAMETERS ===
- Execution ID: {execution_id}
- Workflow ID: {workflow_execution_id or "standalone"}
- Research Document Path: {research_path}
- Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

=== FINAL INSTRUCTIONS ===

1. Analyze all articles above following the selection rules
2. Perform 3-5 web searches to complement/validate (MANDATORY)
3. Use sub-agents if necessary (fact-checker for dubious sources, topic-diver for major announcements)
4. Write the research document to: {research_path}
5. Return the final JSON according to the output schema

IMPORTANT:
- The research document MUST be written BEFORE your final response
- Your final response must be ONLY the structured JSON
- If no significant news today, still produce a valid JSON with empty arrays and a note in metadata
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

    Args:
        request: Request containing articles to summarize.

    Returns:
        Summary response with success status and generated content.
    """
    import uuid

    logger.info("Received %d articles to summarize", len(request.articles))

    # Generate execution ID early
    execution_id = uuid.uuid4().hex[:12]

    # Create execution directory immediately (new folder structure)
    exec_dir = execution_logger.create_execution_dir(execution_id)
    logger.info("Created execution directory: %s", exec_dir.path)

    start_time = time.time()
    prompt = ""
    claude_result: ClaudeResult | None = None

    try:
        prompt = build_prompt(
            articles=request.articles,
            execution_id=execution_id,
            exec_dir=exec_dir,
            workflow_execution_id=request.workflow_execution_id,
        )
        claude_result = await call_claude_cli(prompt, exec_dir)

        if claude_result.success:
            logger.info("Summary generated successfully")
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
    )

    # Save all logs to the execution directory (reuse existing exec_dir)
    try:
        execution_logger.save(exec_log, exec_dir=exec_dir, digest=digest)
        logger.info(
            "Execution logs saved to: %s (id: %s, duration: %.2fs)",
            exec_dir.path,
            exec_log.execution_id,
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

    return SummarizeResponse(
        summary=summary_text,
        article_count=len(request.articles),
        success=final_success,
        error=final_error,
        execution_id=exec_log.execution_id,
        log_file=str(exec_dir.path),
        workflow_execution_id=request.workflow_execution_id,
        digest=digest,
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
