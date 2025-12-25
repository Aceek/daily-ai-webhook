"""
Discord bot configuration.

Settings loaded from environment variables.
"""

import os


class Settings:
    """Bot configuration from environment variables."""

    # Discord
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    guild_id: int | None = int(os.getenv("DISCORD_GUILD_ID", "0")) or None

    # Channels (optional, for proactive posting)
    daily_channel_id: int | None = int(os.getenv("DAILY_CHANNEL_ID", "0")) or None
    weekly_channel_id: int | None = int(os.getenv("WEEKLY_CHANNEL_ID", "0")) or None

    # Database
    database_url: str = os.getenv("DATABASE_URL", "")

    # Default mission
    default_mission: str = os.getenv("DEFAULT_MISSION", "ai-news")

    # Claude service (for on-demand generation)
    claude_service_url: str = os.getenv("CLAUDE_SERVICE_URL", "http://claude-service:8080")
    claude_service_timeout: int = int(os.getenv("CLAUDE_SERVICE_TIMEOUT", "660"))


settings = Settings()
