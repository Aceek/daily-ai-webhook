"""
Admin commands cog.

Provides administrative commands for monitoring and management.
All commands require Discord Administrator permission.
"""

import logging
from datetime import datetime

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from services.database import check_database_health, get_database_stats

logger = logging.getLogger(__name__)


class AdminCog(commands.Cog):
    """Administrative commands for bot management."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="status", description="Check service status (admin only)")
    @app_commands.default_permissions(administrator=True)
    async def status(self, interaction: discord.Interaction) -> None:
        """Check the health status of all services.

        Requires Administrator permission on the Discord server.

        Args:
            interaction: Discord interaction
        """
        await interaction.response.defer(ephemeral=True)

        logger.info(
            "Status command invoked by %s (ID: %s) in guild %s",
            interaction.user.name,
            interaction.user.id,
            interaction.guild.name if interaction.guild else "DM",
        )

        embed = discord.Embed(
            title="Service Status",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        # Check PostgreSQL
        db_healthy, db_message = await check_database_health()
        db_status = "OK" if db_healthy else "Down"
        db_emoji = "\u2705" if db_healthy else "\u274c"
        embed.add_field(
            name=f"{db_emoji} PostgreSQL",
            value=db_message,
            inline=True,
        )

        # Check claude-service
        claude_healthy = False
        claude_message = "Unknown"
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{settings.claude_service_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        claude_healthy = data.get("status") == "healthy"
                        claude_message = f"v{data.get('version', '?')}"
                    else:
                        claude_message = f"HTTP {response.status}"
        except aiohttp.ClientError as e:
            claude_message = f"Connection error"
            logger.warning("Claude service health check failed: %s", e)
        except Exception as e:
            claude_message = "Error"
            logger.error("Unexpected error checking claude-service: %s", e)

        claude_emoji = "\u2705" if claude_healthy else "\u274c"
        embed.add_field(
            name=f"{claude_emoji} Claude Service",
            value=claude_message,
            inline=True,
        )

        # Check Discord Bot (always OK if we're responding)
        embed.add_field(
            name="\u2705 Discord Bot",
            value=f"Online ({len(self.bot.guilds)} guilds)",
            inline=True,
        )

        # Overall status
        all_healthy = db_healthy and claude_healthy
        if all_healthy:
            embed.color = discord.Color.green()
            embed.set_footer(text="All systems operational")
        else:
            embed.color = discord.Color.red()
            embed.set_footer(text="Some services are degraded")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="stats", description="Show database statistics (admin only)")
    @app_commands.default_permissions(administrator=True)
    async def stats(self, interaction: discord.Interaction) -> None:
        """Display database statistics.

        Requires Administrator permission on the Discord server.

        Args:
            interaction: Discord interaction
        """
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

        embed = discord.Embed(
            title="Database Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        # Counts section
        embed.add_field(
            name="\U0001f4f0 Articles",
            value=f"{stats['articles']:,}",
            inline=True,
        )
        embed.add_field(
            name="\U0001f3f7\ufe0f Categories",
            value=f"{stats['categories']:,}",
            inline=True,
        )
        embed.add_field(
            name="\U0001f4c5 Daily Digests",
            value=f"{stats['daily_digests']:,}",
            inline=True,
        )
        embed.add_field(
            name="\U0001f4ca Weekly Digests",
            value=f"{stats['weekly_digests']:,}",
            inline=True,
        )
        embed.add_field(
            name="\U0001f4c8 Articles (7 days)",
            value=f"{stats['articles_last_7_days']:,}",
            inline=True,
        )

        # Add empty field for alignment
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Latest dates section
        last_daily = stats["last_daily_date"]
        last_weekly = stats["last_weekly_date"]

        embed.add_field(
            name="Last Daily Digest",
            value=str(last_daily) if last_daily else "None",
            inline=True,
        )
        embed.add_field(
            name="Last Weekly Digest",
            value=str(last_weekly) if last_weekly else "None",
            inline=True,
        )

        embed.set_footer(text=f"Mission: {settings.default_mission}")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @status.error
    @stats.error
    async def admin_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle errors for admin commands.

        Args:
            interaction: Discord interaction
            error: The error that occurred
        """
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
