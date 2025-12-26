"""
Daily digest command cog.

Provides /daily command to retrieve the latest daily digest.
"""

import io
import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from services.card_generator import generate_daily_card_async
from services.database import get_daily_digest_by_date, get_latest_daily_digest
from services.publisher import build_daily_embeds

logger = logging.getLogger(__name__)


class DailyCog(commands.Cog):
    """Commands for daily digest retrieval."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Get the latest AI news daily digest")
    @app_commands.describe(
        date_str="Optional date (YYYY-MM-DD) to get a specific day's digest"
    )
    async def daily(
        self,
        interaction: discord.Interaction,
        date_str: str | None = None,
    ) -> None:
        """Get the daily digest.

        Args:
            interaction: Discord interaction
            date_str: Optional date string (YYYY-MM-DD)
        """
        await interaction.response.defer()

        mission_id = settings.default_mission

        try:
            if date_str:
                # Parse date and fetch specific digest
                try:
                    digest_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    await interaction.followup.send(
                        "Invalid date format. Please use YYYY-MM-DD.",
                        ephemeral=True,
                    )
                    return

                digest = await get_daily_digest_by_date(mission_id, digest_date)
                if not digest:
                    await interaction.followup.send(
                        f"No digest found for {date_str}.",
                        ephemeral=True,
                    )
                    return
            else:
                # Get latest digest
                digest = await get_latest_daily_digest(mission_id)
                if not digest:
                    await interaction.followup.send(
                        "No daily digest available yet.",
                        ephemeral=True,
                    )
                    return

            # Build card and embeds from digest content
            content = digest["content"]
            digest_date = str(digest["date"])

            # Generate card image
            try:
                card_bytes = await generate_daily_card_async(content, digest_date)
                card_file = discord.File(io.BytesIO(card_bytes), filename="ai-news-daily.png")
                await interaction.followup.send(file=card_file)
            except Exception as e:
                logger.warning("Failed to generate card image: %s", e)

            # Send detailed embeds
            embeds = build_daily_embeds(content, digest_date)
            await interaction.followup.send(embeds=embeds[:10])

        except Exception as e:
            logger.error("Error fetching daily digest: %s", e)
            await interaction.followup.send(
                "An error occurred while fetching the digest.",
                ephemeral=True,
            )

async def setup(bot: commands.Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(DailyCog(bot))
