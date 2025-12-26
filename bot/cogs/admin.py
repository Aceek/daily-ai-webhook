"""
Admin commands cog.

Provides administrative commands for monitoring and management.
All commands require Discord Administrator permission.
"""

import logging
from datetime import datetime
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from services.database import get_database_stats
from services.health_checker import check_claude_service_health, check_db_health

logger = logging.getLogger(__name__)


def build_status_embed(
    db_status: tuple[bool, str],
    claude_status: tuple[bool, str],
    guild_count: int,
) -> discord.Embed:
    """Build status embed with health check results.

    Args:
        db_status: (healthy, message) tuple for database
        claude_status: (healthy, message) tuple for claude-service
        guild_count: Number of Discord guilds

    Returns:
        Configured Discord embed
    """
    embed = discord.Embed(
        title="Service Status",
        color=discord.Color.blue(),
        timestamp=datetime.now(),
    )

    # PostgreSQL status
    db_healthy, db_message = db_status
    db_emoji = "\u2705" if db_healthy else "\u274c"
    embed.add_field(name=f"{db_emoji} PostgreSQL", value=db_message, inline=True)

    # Claude service status
    claude_healthy, claude_message = claude_status
    claude_emoji = "\u2705" if claude_healthy else "\u274c"
    embed.add_field(name=f"{claude_emoji} Claude Service", value=claude_message, inline=True)

    # Discord bot status (always OK if responding)
    embed.add_field(
        name="\u2705 Discord Bot",
        value=f"Online ({guild_count} guilds)",
        inline=True,
    )

    # Set color based on overall health
    all_healthy = db_healthy and claude_healthy
    embed.color = discord.Color.green() if all_healthy else discord.Color.red()
    footer_text = "All systems operational" if all_healthy else "Some services are degraded"
    embed.set_footer(text=footer_text)

    return embed


def build_stats_embed(stats: dict[str, Any]) -> discord.Embed:
    """Build statistics embed from database stats.

    Args:
        stats: Dictionary with database statistics

    Returns:
        Configured Discord embed
    """
    embed = discord.Embed(
        title="Database Statistics",
        color=discord.Color.blue(),
        timestamp=datetime.now(),
    )

    # Counts section
    embed.add_field(name="\U0001f4f0 Articles", value=f"{stats['articles']:,}", inline=True)
    embed.add_field(name="\U0001f3f7\ufe0f Categories", value=f"{stats['categories']:,}", inline=True)
    embed.add_field(name="\U0001f4c5 Daily Digests", value=f"{stats['daily_digests']:,}", inline=True)
    embed.add_field(name="\U0001f4ca Weekly Digests", value=f"{stats['weekly_digests']:,}", inline=True)
    embed.add_field(name="\U0001f4c8 Articles (7 days)", value=f"{stats['articles_last_7_days']:,}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)  # Alignment spacer

    # Latest dates section
    last_daily = stats["last_daily_date"]
    last_weekly = stats["last_weekly_date"]
    embed.add_field(name="Last Daily Digest", value=str(last_daily) if last_daily else "None", inline=True)
    embed.add_field(name="Last Weekly Digest", value=str(last_weekly) if last_weekly else "None", inline=True)

    embed.set_footer(text=f"Mission: {settings.default_mission}")

    return embed


class AdminCog(commands.Cog):
    """Administrative commands for bot management."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="status", description="Check service status (admin only)")
    @app_commands.default_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction) -> None:
        """Check the health status of all services."""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Status command invoked by %s (ID: %s) in guild %s",
            interaction.user.name,
            interaction.user.id,
            interaction.guild.name if interaction.guild else "DM",
        )

        db_health = await check_db_health()
        claude_health = await check_claude_service_health()

        embed = build_status_embed(
            db_status=(db_health.healthy, db_health.message),
            claude_status=(claude_health.healthy, claude_health.message),
            guild_count=len(self.bot.guilds),
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="Show database statistics (admin only)")
    @app_commands.default_permissions(administrator=True)
    async def stats(self, interaction: discord.Interaction) -> None:
        """Display database statistics."""
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Stats command invoked by %s (ID: %s) in guild %s",
            interaction.user.name,
            interaction.user.id,
            interaction.guild.name if interaction.guild else "DM",
        )

        stats = await get_database_stats()

        if stats is None:
            await interaction.followup.send(
                "\u274c Database unavailable. Cannot fetch statistics.",
                ephemeral=True,
            )
            return

        embed = build_stats_embed(stats)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @status.error
    @stats.error
    async def admin_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for admin commands."""
        if isinstance(error, app_commands.MissingPermissions):
            logger.warning(
                "Permission denied for %s (ID: %s) on command %s",
                interaction.user.name,
                interaction.user.id,
                interaction.command.name if interaction.command else "unknown",
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "\u274c You need Administrator permission to use this command.",
                    ephemeral=True,
                )
        else:
            logger.error("Admin command error: %s", error)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "\u274c An error occurred while processing the command.",
                    ephemeral=True,
                )


async def setup(bot: commands.Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(AdminCog(bot))
