#!/usr/bin/env python3
"""
Configuration module for Claude Service.

Centralizes all settings, constants, and environment variable loading.
"""

import logging
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from constants import DAILY_MISSION_FILES, WEEKLY_MISSION_FILES


# Application version
APP_VERSION: str = "1.0.0"

# Base tools for Claude CLI (non-MCP)
BASE_TOOLS: list[str] = ["Read", "WebSearch", "WebFetch", "Write", "Task"]

# MCP server name
MCP_SERVER_NAME: str = "submit-digest"

# Default mission (configurable via environment)
DEFAULT_MISSION: str = os.getenv("DEFAULT_MISSION", "ai-news")


def get_mcp_tool_names() -> list[str]:
    """Get list of MCP tool names from server definition.

    Returns:
        List of fully-qualified MCP tool names.
    """
    try:
        from mcp_tools.server import mcp
        tool_names = []
        if hasattr(mcp, "_tool_manager") and hasattr(mcp._tool_manager, "_tools"):
            for name in mcp._tool_manager._tools.keys():
                tool_names.append(f"mcp__{MCP_SERVER_NAME}__{name}")
        return tool_names
    except ImportError:
        return []


def build_allowed_tools() -> str:
    """Build allowed tools string for Claude CLI.

    Returns:
        Comma-separated string of tool names.
    """
    mcp_tools = get_mcp_tool_names()
    all_tools = BASE_TOOLS + mcp_tools
    return ",".join(all_tools)


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

    # Database connection (uses DATABASE_URL without prefix)
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")

    @property
    def allowed_tools(self) -> str:
        """Get allowed tools string (dynamically generated).

        Returns:
            Comma-separated string of tool names.
        """
        return build_allowed_tools()


def discover_missions(missions_path: str | None = None) -> list[str]:
    """Discover available missions from filesystem.

    Scans missions directory for valid mission folders.
    A valid mission must have mission.md file.

    Args:
        missions_path: Optional path to missions directory.

    Returns:
        Sorted list of discovered mission names.
    """
    path = Path(missions_path or Settings().missions_path)
    if not path.exists():
        return []

    missions = []
    for item in path.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            if (item / "mission.md").exists():
                missions.append(item.name)
    return sorted(missions)


def get_valid_missions() -> list[str]:
    """Get list of valid missions (cached on first call).

    Returns:
        List of valid mission names.
    """
    if not hasattr(get_valid_missions, "_cache"):
        get_valid_missions._cache = discover_missions()
    return get_valid_missions._cache


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
    valid_missions = get_valid_missions()
    if mission not in valid_missions:
        return False, f"Unknown mission: {mission}. Valid missions: {valid_missions}"

    mission_path = Path(missions_path) / mission

    for f in DAILY_MISSION_FILES:
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
    valid_missions = get_valid_missions()
    if mission not in valid_missions:
        return False, f"Unknown mission: {mission}. Valid missions: {valid_missions}"

    weekly_path = Path(missions_path) / mission / "weekly"

    for f in WEEKLY_MISSION_FILES:
        if not (weekly_path / f).exists():
            return False, f"Missing weekly mission file: {weekly_path / f}"

    return True, None
