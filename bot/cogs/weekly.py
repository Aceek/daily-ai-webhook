"""
Weekly digest command cog.

Provides /weekly command to retrieve or generate weekly digests.
- Without arguments: returns the latest cached digest from database
- With theme/dates: generates a new digest via claude-service
"""

import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from services.claude_client import ClaudeServiceError, generate_weekly_digest
from services.database import get_latest_weekly_digest
from services.publisher import build_weekly_embeds

logger = logging.getLogger(__name__)


def get_previous_week_dates() -> tuple[str, str]:
    """Calculate previous week's Monday and Sunday dates.

    Returns:
        Tuple of (week_start, week_end) as YYYY-MM-DD strings
    """
    today = datetime.now()
    # Go back to last week's Monday
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)

    return last_monday.strftime("%Y-%m-%d"), last_sunday.strftime("%Y-%m-%d")


def get_current_week_dates() -> tuple[str, str]:
    """Calculate current week's Monday to today dates.

    Returns:
        Tuple of (week_start, week_end) as YYYY-MM-DD strings
    """
    today = datetime.now()
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)

    return monday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


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

            embeds = self._build_weekly_embeds(digest)
            await interaction.followup.send(embeds=embeds)

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

        # Default dates: use previous week if not specified, or current week for thematic
        if not week_start or not week_end:
            if theme:
                # For thematic analysis, default to current week (more relevant)
                default_start, default_end = get_current_week_dates()
            else:
                # For standard generation, use previous week
                default_start, default_end = get_previous_week_dates()

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
                await status_msg.edit(
                    content="Generation completed but no digest was produced. Check logs for details."
                )
                return

            # Build embeds from the generated digest
            content = digest
            embeds = build_weekly_embeds(content, week_start, week_end)

            # Add theme indicator to first embed if thematic
            if theme:
                embeds[0].title = f"AI News Weekly: {theme.title()}"

            # Edit the status message with the actual content
            await status_msg.edit(content=None, embeds=embeds)

            logger.info(
                "Generated weekly digest: theme=%s, week=%s to %s, digest_id=%s",
                theme,
                week_start,
                week_end,
                result.get("digest_id"),
            )

        except ClaudeServiceError as e:
            logger.error("Claude service error: %s", e)
            await status_msg.edit(
                content=f"Failed to generate digest: {e}\nPlease try again later."
            )
        except Exception as e:
            logger.error("Unexpected error generating weekly digest: %s", e, exc_info=True)
            await status_msg.edit(
                content="An unexpected error occurred. Please try again later."
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
            title="AI News Weekly Digest",
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
