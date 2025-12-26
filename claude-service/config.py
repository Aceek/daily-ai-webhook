#!/usr/bin/env python3
"""
Configuration module for Claude Service.

Centralizes all settings, constants, and environment variable loading.
"""

import logging
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables
    with the CLAUDE_ prefix.
    """

    model_config = SettingsConfigDict(env_prefix="CLAUDE_")

    # Claude CLI settings
    claude_model: str = "sonnet"
    claude_timeout: int = 600  # Increased for agentic workflow
    retry_count: int = 1

    # Path settings
    logs_path: str = "/app/logs"
    missions_path: str = "/app/missions"
    data_path: str = "/app/data"
    digests_path: str = "/app/logs/digests"

    # Logging
    log_level: str = "info"

    # Allowed tools for agentic workflow
    allowed_tools: str = (
        "Read,WebSearch,WebFetch,Write,Task,"
        "mcp__submit-digest__submit_digest,"
        "mcp__submit-digest__submit_weekly_digest,"
        "mcp__submit-digest__get_categories,"
        "mcp__submit-digest__get_articles,"
        "mcp__submit-digest__get_article_stats,"
        "mcp__submit-digest__get_recent_headlines"
    )

    # Database connection (uses DATABASE_URL without prefix)
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")


# Valid missions (extensible)
VALID_MISSIONS: list[str] = ["ai-news"]

# Application version
APP_VERSION: str = "1.0.0"


def get_settings() -> Settings:
    """Get the application settings singleton.

    Returns:
        Settings instance loaded from environment.
    """
    return Settings()


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure application logging.

    Args:
        settings: Application settings.

    Returns:
        Configured logger instance.
    """
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("claude-service")


def validate_mission(mission: str, missions_path: str) -> tuple[bool, str | None]:
    """Validate that mission exists and has required files.

    Args:
        mission: Name of the mission to validate.
        missions_path: Base path to missions directory.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if mission not in VALID_MISSIONS:
        return False, f"Unknown mission: {mission}. Valid missions: {VALID_MISSIONS}"

    mission_path = Path(missions_path) / mission
    required_files = [
        "mission.md",
        "selection-rules.md",
        "editorial-guide.md",
        "output-schema.md",
    ]

    for f in required_files:
        if not (mission_path / f).exists():
            return False, f"Missing mission file: {mission_path / f}"

    return True, None


def validate_weekly_mission(
    mission: str,
    missions_path: str,
) -> tuple[bool, str | None]:
    """Validate that mission exists and has weekly analysis files.

    Args:
        mission: Name of the mission to validate.
        missions_path: Base path to missions directory.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if mission not in VALID_MISSIONS:
        return False, f"Unknown mission: {mission}. Valid missions: {VALID_MISSIONS}"

    weekly_path = Path(missions_path) / mission / "weekly"
    required_files = ["mission.md", "analysis-rules.md", "output-schema.md"]

    for f in required_files:
        if not (weekly_path / f).exists():
            return False, f"Missing weekly mission file: {weekly_path / f}"

    return True, None
