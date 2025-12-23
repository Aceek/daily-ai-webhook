"""
Daily digest command cog.

Provides /daily command to retrieve the latest daily digest.
"""

import logging
from datetime import date, datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from services.database import get_daily_digest_by_date, get_latest_daily_digest

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

            # Build embed from digest content
            embeds = self._build_digest_embeds(digest)
            await interaction.followup.send(embeds=embeds)

        except Exception as e:
            logger.error("Error fetching daily digest: %s", e)
            await interaction.followup.send(
                "An error occurred while fetching the digest.",
                ephemeral=True,
            )

    def _build_digest_embeds(self, digest: dict) -> list[discord.Embed]:
        """Build Discord embeds from digest data.

        Args:
            digest: The digest data from database

        Returns:
            List of Discord embeds
        """
        content = digest["content"]
        digest_date = digest["date"]

        embeds = []

        # Main embed with headlines
        main_embed = discord.Embed(
            title=f"AI News Daily Digest - {digest_date}",
            color=discord.Color.blue(),
            timestamp=digest["generated_at"],
        )

        # Add headlines
        headlines = content.get("headlines", [])
        if headlines:
            headlines_text = ""
            for item in headlines[:5]:  # Limit to 5 headlines
                title = item.get("title", "")[:100]
                summary = item.get("summary", "")[:150]
                url = item.get("url", "")
                if url:
                    headlines_text += f"**[{title}]({url})**\n{summary}\n\n"
                else:
                    headlines_text += f"**{title}**\n{summary}\n\n"

            main_embed.add_field(
                name="Headlines",
                value=headlines_text[:1024] or "No headlines",
                inline=False,
            )

        # Add research section
        research = content.get("research", [])
        if research:
            research_text = ""
            for item in research[:3]:
                title = item.get("title", "")[:80]
                url = item.get("url", "")
                if url:
                    research_text += f"- [{title}]({url})\n"
                else:
                    research_text += f"- {title}\n"

            main_embed.add_field(
                name="Research",
                value=research_text[:1024] or "No research items",
                inline=False,
            )

        # Add industry section
        industry = content.get("industry", [])
        if industry:
            industry_text = ""
            for item in industry[:3]:
                title = item.get("title", "")[:80]
                url = item.get("url", "")
                if url:
                    industry_text += f"- [{title}]({url})\n"
                else:
                    industry_text += f"- {title}\n"

            main_embed.add_field(
                name="Industry",
                value=industry_text[:1024] or "No industry items",
                inline=False,
            )

        # Add watching section
        watching = content.get("watching", [])
        if watching:
            watching_text = ""
            for item in watching[:3]:
                title = item.get("title", "")[:80]
                watching_text += f"- {title}\n"

            main_embed.add_field(
                name="Watching",
                value=watching_text[:1024] or "No items to watch",
                inline=False,
            )

        # Footer with metadata
        metadata = content.get("metadata", {})
        articles_analyzed = metadata.get("articles_analyzed", 0)
        web_searches = metadata.get("web_searches", 0)
        main_embed.set_footer(
            text=f"Analyzed {articles_analyzed} articles | {web_searches} web searches"
        )

        embeds.append(main_embed)
        return embeds


async def setup(bot: commands.Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(DailyCog(bot))
