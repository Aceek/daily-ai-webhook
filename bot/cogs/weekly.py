"""
Weekly digest command cog.

Provides /weekly command to retrieve or generate weekly digests.
- Without arguments: returns the latest cached digest from database
- With theme/dates: generates a new digest via claude-service
"""

import io
import logging
from datetime import datetime
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from services.card_generator import generate_weekly_card_async
from services.claude_client import ClaudeServiceError, generate_weekly_digest
from services.command_logger import CommandLog, create_command_log, send_command_log
from services.database import get_latest_weekly_digest
from services.publisher import build_weekly_embeds
from services.utils.date_utils import get_last_7_days

logger = logging.getLogger(__name__)


class WeeklyCog(commands.Cog):
    """Commands for weekly digest retrieval and generation."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="weekly", description="Get or generate AI news weekly digest")
    @app_commands.describe(
        theme="Focus analysis on a specific theme (e.g., 'openai', 'regulation')",
        week_start="Start date (YYYY-MM-DD). Defaults to last Monday",
        week_end="End date (YYYY-MM-DD). Defaults to last Sunday",
    )
    async def weekly(
        self,
        interaction: discord.Interaction,
        theme: str | None = None,
        week_start: str | None = None,
        week_end: str | None = None,
    ) -> None:
        """Get or generate a weekly digest.

        Without arguments: returns the latest cached digest from database.
        With theme or custom dates: generates a new digest on-demand.

        Args:
            interaction: Discord interaction
            theme: Optional theme to focus the analysis on
            week_start: Optional start date (YYYY-MM-DD)
            week_end: Optional end date (YYYY-MM-DD)
        """
        # If any generation parameter is provided, generate on-demand
        if theme or week_start or week_end:
            await self._generate_weekly(interaction, theme, week_start, week_end)
        else:
            await self._get_cached_weekly(interaction)

    async def _get_cached_weekly(self, interaction: discord.Interaction) -> None:
        """Get the latest weekly digest from database cache."""
        await interaction.response.defer()

        mission_id = settings.default_mission

        try:
            digest = await get_latest_weekly_digest(mission_id, standard_only=True)

            if not digest:
                await interaction.followup.send(
                    "No weekly digest available yet. Weekly digests are generated every Monday.\n"
                    "Use `/weekly theme:openai` to generate a custom analysis.",
                    ephemeral=True,
                )
                return

            content = digest["content"]
            week_start = str(digest["week_start"])
            week_end = str(digest["week_end"])

            # Generate card image
            try:
                card_bytes = await generate_weekly_card_async(content, week_start, week_end)
                card_file = discord.File(io.BytesIO(card_bytes), filename="ai-news-weekly.png")
                await interaction.followup.send(file=card_file)
            except Exception as e:
                logger.warning("Failed to generate weekly card image: %s", e)

            # Send detailed embeds
            embeds = build_weekly_embeds(content, week_start, week_end)
            await interaction.followup.send(embeds=embeds[:10])

        except Exception as e:
            logger.error("Error fetching weekly digest: %s", e)
            await interaction.followup.send(
                "An error occurred while fetching the weekly digest.",
                ephemeral=True,
            )

    async def _generate_weekly(
        self,
        interaction: discord.Interaction,
        theme: str | None,
        week_start: str | None,
        week_end: str | None,
    ) -> None:
        """Generate a new weekly digest on-demand via claude-service."""
        # Defer with a longer thinking message
        await interaction.response.defer()

        mission_id = settings.default_mission

        # Default dates: always use last 7 days if not specified
        if not week_start or not week_end:
            default_start, default_end = get_last_7_days()
            week_start = week_start or default_start
            week_end = week_end or default_end

        # Validate date format
        try:
            datetime.strptime(week_start, "%Y-%m-%d")
            datetime.strptime(week_end, "%Y-%m-%d")
        except ValueError:
            await interaction.followup.send(
                "Invalid date format. Please use YYYY-MM-DD (e.g., 2024-12-16).",
                ephemeral=True,
            )
            return

        # Create command log
        command_args: dict[str, Any] = {
            "theme": theme,
            "week_start": week_start,
            "week_end": week_end,
        }
        cmd_log = create_command_log(interaction, "/weekly", command_args)

        # Send initial status message
        theme_info = f" focused on **{theme}**" if theme else ""
        status_msg = await interaction.followup.send(
            f"Generating weekly digest for {week_start} to {week_end}{theme_info}...\n"
            "This may take a few minutes.",
            wait=True,
        )

        try:
            # Call claude-service
            result = await generate_weekly_digest(
                mission=mission_id,
                week_start=week_start,
                week_end=week_end,
                theme=theme,
            )

            digest = result.get("digest")
            if not digest:
                cmd_log.finish(
                    success=False,
                    error="No digest produced",
                    claude_execution_id=result.get("execution_id"),
                )
                await send_command_log(cmd_log)
                await status_msg.edit(
                    content="Generation completed but no digest was produced. Check logs for details."
                )
                return

            # Build card and embeds from the generated digest
            content = digest

            # Delete the status message
            await status_msg.delete()

            # Generate and send card image
            try:
                card_bytes = await generate_weekly_card_async(
                    content, week_start, week_end, theme
                )
                card_file = discord.File(io.BytesIO(card_bytes), filename="ai-news-weekly.png")
                await interaction.followup.send(file=card_file)
            except Exception as e:
                logger.warning("Failed to generate weekly card image: %s", e)

            # Send detailed embeds
            embeds = build_weekly_embeds(content, week_start, week_end)

            # Add theme indicator to first embed if thematic
            if theme and embeds:
                embeds[0].title = f"📊 AI News Weekly: {theme.title()}"

            await interaction.followup.send(embeds=embeds[:10])

            # Log success
            cmd_log.finish(
                success=True,
                claude_execution_id=result.get("execution_id"),
                digest_id=result.get("digest_id"),
            )
            await send_command_log(cmd_log)

            logger.info(
                "Generated weekly digest: theme=%s, week=%s to %s, digest_id=%s",
                theme,
                week_start,
                week_end,
                result.get("digest_id"),
            )

        except ClaudeServiceError as e:
            logger.error("Claude service error: %s", e)
            cmd_log.finish(success=False, error=str(e))
            await send_command_log(cmd_log)
            await status_msg.edit(
                content=f"Failed to generate digest: {e}\nPlease try again later."
            )
        except Exception as e:
            logger.error("Unexpected error generating weekly digest: %s", e, exc_info=True)
            cmd_log.finish(success=False, error=str(e))
            await send_command_log(cmd_log)
            await status_msg.edit(
                content="An unexpected error occurred. Please try again later."
            )

async def setup(bot: commands.Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(WeeklyCog(bot))
