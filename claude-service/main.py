#!/usr/bin/env python3
"""
Claude Service - HTTP wrapper for Claude Code CLI.

Provides /summarize endpoint for n8n integration.
This service wraps Claude Code CLI to expose it as an HTTP API.
"""

import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


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


class SummarizeResponse(BaseModel):
    """Response body for the /summarize endpoint."""

    summary: str
    article_count: int
    success: bool
    error: str | None = None


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str
    version: str


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


async def call_claude_cli(prompt: str) -> str:
    """Call Claude Code CLI with the given prompt.

    Executes claude CLI as a subprocess with retry logic
    and timeout handling.

    Args:
        prompt: The prompt to send to Claude CLI.

    Returns:
        Claude's response as a string.

    Raises:
        RuntimeError: If all retry attempts fail or timeout occurs.
    """
    cmd = ["claude", "-p", prompt]

    for attempt in range(settings.retry_count + 1):
        try:
            logger.info("Calling Claude CLI (attempt %d)", attempt + 1)

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
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            return stdout.decode().strip()

        except asyncio.TimeoutError:
            logger.error(
                "Claude CLI timeout after %ds", settings.claude_timeout
            )
            if attempt < settings.retry_count:
                continue
            raise RuntimeError(
                f"Claude CLI timeout after {settings.claude_timeout}s"
            )

    raise RuntimeError("All retry attempts failed")


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

    try:
        prompt = build_prompt(request.articles)
        summary = await call_claude_cli(prompt)

        logger.info("Summary generated successfully")
        return SummarizeResponse(
            summary=summary,
            article_count=len(request.articles),
            success=True,
        )

    except Exception as e:
        logger.error("Error generating summary: %s", e)
        return SummarizeResponse(
            summary="",
            article_count=len(request.articles),
            success=False,
            error=str(e),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
