"""
Centralized embed building utilities for Discord messages.

Provides consistent styling and formatting for daily and weekly digest embeds.
Follows DRY principles by using generic formatters from formatters module.
"""

from typing import Any

import discord

from services.formatters import (
    CategoryConfig,
    format_category_item,
    format_ranked_story,
    format_trend_item,
)


class EmbedColors:
    """Standard color palette for digest embeds."""

    HEADLINES = discord.Color.from_rgb(239, 68, 68)      # Red
    RESEARCH = discord.Color.from_rgb(34, 197, 94)       # Green
    INDUSTRY = discord.Color.from_rgb(99, 102, 241)      # Indigo
    WATCHING = discord.Color.from_rgb(234, 179, 8)       # Yellow/Amber
    TRENDS = discord.Color.from_rgb(168, 85, 247)        # Purple
    TOP_STORIES = discord.Color.from_rgb(245, 158, 11)   # Amber/Gold
    SUMMARY = discord.Color.from_rgb(59, 130, 246)       # Blue


# Category configuration mapping
CATEGORY_EMBED_CONFIG = {
    "headlines": {
        "title": "📰 Headlines",
        "description": "Top AI/ML news stories of the day",
        "color": EmbedColors.HEADLINES,
        "formatter_config": CategoryConfig(emoji="", link_text="Read article"),
    },
    "research": {
        "title": "🔬 Research & Development",
        "description": "Latest papers and technical announcements",
        "color": EmbedColors.RESEARCH,
        "formatter_config": CategoryConfig(emoji="📄", link_text="Read more"),
    },
    "industry": {
        "title": "🏢 Industry News",
        "description": "Business moves, acquisitions, and market updates",
        "color": EmbedColors.INDUSTRY,
        "formatter_config": CategoryConfig(emoji="💼", link_text="Read more"),
    },
    "watching": {
        "title": "👀 Worth Watching",
        "description": "Emerging trends and stories to follow",
        "color": EmbedColors.WATCHING,
        "formatter_config": CategoryConfig(emoji="🔍", link_text="Read more"),
    },
}


def build_category_embed(
    category: str,
    items: list[dict[str, Any]],
) -> discord.Embed:
    """Build a category embed with consistent styling.

    Args:
        category: Category name (headlines, research, industry, watching)
        items: List of items to format

    Returns:
        Configured Discord embed
    """
    config = CATEGORY_EMBED_CONFIG.get(category)
    if not config:
        raise ValueError(f"Unknown category: {category}")

    embed = discord.Embed(
        title=config["title"],
        description=config["description"],
        color=config["color"],
    )

    for item in items:
        name, value = format_category_item(item, config=config["formatter_config"])
        embed.add_field(name=name[:256], value=value[:1024], inline=False)

    return embed


def build_summary_embed(summary: str, title: str = "📋 Executive Summary") -> discord.Embed:
    """Build a summary embed.

    Args:
        summary: The summary text
        title: Optional custom title

    Returns:
        Summary embed
    """
    if len(summary) > 4000:
        summary = summary[:3997] + "..."

    return discord.Embed(
        title=title,
        description=summary,
        color=EmbedColors.SUMMARY,
    )


# Daily digest embed builders

def build_headlines_embed(headlines: list[dict[str, Any]]) -> discord.Embed:
    """Build headlines embed for daily digest."""
    return build_category_embed("headlines", headlines)


def build_research_embed(research: list[dict[str, Any]]) -> discord.Embed:
    """Build research embed for daily digest."""
    return build_category_embed("research", research)


def build_industry_embed(industry: list[dict[str, Any]]) -> discord.Embed:
    """Build industry embed for daily digest."""
    return build_category_embed("industry", industry)


def build_watching_embed(watching: list[dict[str, Any]]) -> discord.Embed:
    """Build watching embed for daily digest."""
    return build_category_embed("watching", watching)


# Weekly digest embed builders

def build_trends_embed(trends: list[dict[str, Any]]) -> discord.Embed:
    """Build trends embed for weekly digest."""
    embed = discord.Embed(
        title="📈 Key Trends",
        description="Emerging patterns and developments this week",
        color=EmbedColors.TRENDS,
    )

    for trend in trends:
        name, value = format_trend_item(trend)
        embed.add_field(name=name[:256], value=value[:1024], inline=False)

    return embed


def build_top_stories_embed(stories: list[dict[str, Any]]) -> discord.Embed:
    """Build top stories embed for weekly digest."""
    embed = discord.Embed(
        title="🏆 Top Stories of the Week",
        description="Most significant developments",
        color=EmbedColors.TOP_STORIES,
    )

    for i, story in enumerate(stories[:5], 1):
        name, value = format_ranked_story(story, i)
        embed.add_field(name=name[:256], value=value[:1024], inline=False)

    return embed
