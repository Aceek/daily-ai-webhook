"""
Command logger for Discord bot commands.

Logs command executions and sends them to claude-service for unified logging.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiohttp
import discord

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class CommandLog:
    """Represents a Discord command execution log."""

    # Command identification
    command_id: str = field(default_factory=lambda: f"cmd-{uuid.uuid4().hex[:8]}")
    command: str = ""
    args: dict[str, Any] = field(default_factory=dict)

    # Discord context
    user_id: str = ""
    user_name: str = ""
    guild_id: str | None = None
    guild_name: str | None = None
    channel_id: str = ""
    channel_name: str | None = None

    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    duration_seconds: float | None = None

    # Result
    success: bool = False
    error: str | None = None

    # Correlation with claude-service
    claude_execution_id: str | None = None
    digest_id: int | None = None

    def finish(
        self,
        success: bool,
        error: str | None = None,
        claude_execution_id: str | None = None,
        digest_id: int | None = None,
    ) -> None:
        """Mark the command as finished."""
        self.finished_at = datetime.utcnow()
        self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        self.success = success
        self.error = error
        self.claude_execution_id = claude_execution_id
        self.digest_id = digest_id

    def to_workflow_log_payload(self) -> dict[str, Any]:
        """Convert to payload for /log-workflow endpoint."""
        return {
            "workflow_execution_id": self.command_id,
            "workflow_name": f"Discord Command: {self.command}",
            "started_at": self.started_at.isoformat() + "Z",
            "finished_at": (self.finished_at or datetime.utcnow()).isoformat() + "Z",
            "status": "success" if self.success else "error",
            "error_message": self.error,
            "error_node": None,
            "nodes_executed": [
                {"name": "Command received", "status": "success", "error": None},
                {
                    "name": "Claude analysis",
                    "status": "success" if self.success else "error",
                    "error": self.error if not self.success else None,
                },
            ],
            "articles_count": 0,
            "claude_execution_id": self.claude_execution_id,
            "discord_sent": self.success,
            "discord_message_id": None,
            "discord_channel_id": self.channel_id,
            "digest_id": self.digest_id,
            "db_saved": self.digest_id is not None,
            "articles_saved": 0,
            # Discord command specific fields
            "source": "discord_command",
            "discord_user": {
                "id": self.user_id,
                "name": self.user_name,
            },
            "discord_guild": {
                "id": self.guild_id,
                "name": self.guild_name,
            } if self.guild_id else None,
            "discord_channel": {
                "id": self.channel_id,
                "name": self.channel_name,
            },
            "command_args": self.args,
        }


def create_command_log(
    interaction: discord.Interaction,
    command: str,
    args: dict[str, Any],
) -> CommandLog:
    """Create a CommandLog from a Discord interaction.

    Args:
        interaction: The Discord interaction
        command: Command name (e.g., "/weekly")
        args: Command arguments

    Returns:
        Initialized CommandLog
    """
    guild_id = str(interaction.guild_id) if interaction.guild_id else None
    guild_name = interaction.guild.name if interaction.guild else None
    channel_name = None
    if isinstance(interaction.channel, discord.TextChannel):
        channel_name = interaction.channel.name

    return CommandLog(
        command=command,
        args=args,
        user_id=str(interaction.user.id),
        user_name=str(interaction.user),
        guild_id=guild_id,
        guild_name=guild_name,
        channel_id=str(interaction.channel_id),
        channel_name=channel_name,
    )


async def send_command_log(log: CommandLog) -> bool:
    """Send command log to claude-service.

    Args:
        log: The command log to send

    Returns:
        True if successfully sent, False otherwise
    """
    url = f"{settings.claude_service_url}/log-workflow"
    payload = log.to_workflow_log_payload()

    logger.info(
        "Sending command log: command_id=%s, command=%s, user=%s, success=%s",
        log.command_id,
        log.command,
        log.user_name,
        log.success,
    )

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        "Command log saved: command_id=%s, log_file=%s",
                        log.command_id,
                        data.get("log_file"),
                    )
                    return True
                else:
                    error = await response.text()
                    logger.warning(
                        "Failed to save command log: status=%d, error=%s",
                        response.status,
                        error,
                    )
                    return False

    except Exception as e:
        logger.warning("Error sending command log: %s", e)
        return False
