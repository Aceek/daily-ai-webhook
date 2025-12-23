"""
Weekly digest command cog.

Provides /weekly command to retrieve the latest weekly digest.
For MVP, this only returns cached digests from the database.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from services.database import get_latest_weekly_digest

logger = logging.getLogger(__name__)


class WeeklyCog(commands.Cog):
    """Commands for weekly digest retrieval."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="weekly", description="Get the latest AI news weekly digest")
    async def weekly(self, interaction: discord.Interaction) -> None:
        """Get the weekly digest (cached from database).

        Args:
            interaction: Discord interaction
        """
        await interaction.response.defer()

        mission_id = settings.default_mission

        try:
            digest = await get_latest_weekly_digest(mission_id, standard_only=True)

            if not digest:
                await interaction.followup.send(
                    "No weekly digest available yet. Weekly digests are generated every Monday.",
                    ephemeral=True,
                )
                return

            # Build embed from digest content
            embeds = self._build_weekly_embeds(digest)
            await interaction.followup.send(embeds=embeds)

        except Exception as e:
            logger.error("Error fetching weekly digest: %s", e)
            await interaction.followup.send(
                "An error occurred while fetching the weekly digest.",
                ephemeral=True,
            )

    def _build_weekly_embeds(self, digest: dict) -> list[discord.Embed]:
        """Build Discord embeds from weekly digest data.

        Args:
            digest: The digest data from database

        Returns:
            List of Discord embeds
        """
        content = digest["content"]
        week_start = digest["week_start"]
        week_end = digest["week_end"]

        embeds = []

        # Main embed with summary
        main_embed = discord.Embed(
            title=f"AI News Weekly Digest",
            description=f"**{week_start} to {week_end}**",
            color=discord.Color.purple(),
            timestamp=digest["generated_at"],
        )

        # Add summary
        summary = content.get("summary", "")
        if summary:
            # Truncate summary if too long
            if len(summary) > 1024:
                summary = summary[:1021] + "..."
            main_embed.add_field(
                name="Executive Summary",
                value=summary,
                inline=False,
            )

        # Add trends
        trends = content.get("trends", [])
        if trends:
            trends_text = ""
            for trend in trends[:5]:
                name = trend.get("name", "")
                direction = trend.get("direction", "")
                direction_emoji = {"rising": "rising", "stable": "stable", "declining": "declining"}.get(
                    direction, ""
                )
                description = trend.get("description", "")[:100]
                trends_text += f"**{name}** ({direction_emoji})\n{description}\n\n"

            main_embed.add_field(
                name="Key Trends",
                value=trends_text[:1024] or "No trends identified",
                inline=False,
            )

        embeds.append(main_embed)

        # Second embed for top stories if we have them
        top_stories = content.get("top_stories", [])
        if top_stories:
            stories_embed = discord.Embed(
                title="Top Stories of the Week",
                color=discord.Color.purple(),
            )

            for i, story in enumerate(top_stories[:5], 1):
                title = story.get("title", "")[:100]
                summary = story.get("summary", "")[:200]
                url = story.get("url", "")
                impact = story.get("impact", "")[:100]

                if url:
                    field_name = f"{i}. [{title}]({url})"
                else:
                    field_name = f"{i}. {title}"

                field_value = summary
                if impact:
                    field_value += f"\n*Impact: {impact}*"

                stories_embed.add_field(
                    name=field_name[:256],
                    value=field_value[:1024],
                    inline=False,
                )

            embeds.append(stories_embed)

        # Add metadata footer to last embed
        metadata = content.get("metadata", {})
        articles_analyzed = metadata.get("articles_analyzed", 0)
        embeds[-1].set_footer(text=f"Based on {articles_analyzed} articles")

        return embeds


async def setup(bot: commands.Bot) -> None:
    """Setup function for the cog."""
    await bot.add_cog(WeeklyCog(bot))
