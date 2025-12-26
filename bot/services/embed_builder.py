"""
Centralized embed building utilities for Discord messages.

Provides consistent styling and formatting for daily and weekly digest embeds.
Follows DRY principles by extracting common embed building logic.
"""

from typing import Any, Callable

import discord


class EmbedColors:
    """Standard color palette for digest embeds."""

    HEADLINES = discord.Color.from_rgb(239, 68, 68)      # Red
    RESEARCH = discord.Color.from_rgb(34, 197, 94)       # Green
    INDUSTRY = discord.Color.from_rgb(99, 102, 241)      # Indigo
    WATCHING = discord.Color.from_rgb(234, 179, 8)       # Yellow/Amber
    TRENDS = discord.Color.from_rgb(168, 85, 247)        # Purple
    TOP_STORIES = discord.Color.from_rgb(245, 158, 11)   # Amber/Gold
    SUMMARY = discord.Color.from_rgb(59, 130, 246)       # Blue


class ConfidenceBadges:
    """Confidence level indicators."""

    HIGH = "🟢"
    MEDIUM = "🟡"
    LOW = "🔴"

    @classmethod
    def get(cls, level: str) -> str:
        """Get badge for confidence level."""
        return {
            "high": cls.HIGH,
            "medium": cls.MEDIUM,
            "low": cls.LOW,
        }.get(level.lower(), cls.MEDIUM)


class DirectionIndicators:
    """Trend direction indicators."""

    RISING = "📈"
    STABLE = "➡️"
    DECLINING = "📉"

    @classmethod
    def get(cls, direction: str) -> str:
        """Get indicator for trend direction."""
        return {
            "rising": cls.RISING,
            "stable": cls.STABLE,
            "declining": cls.DECLINING,
        }.get(direction.lower(), cls.STABLE)


def format_news_item(item: dict[str, Any]) -> tuple[str, str]:
    """Format a news item for embed field.

    Args:
        item: News item with title, summary, url, source, confidence, emoji

    Returns:
        Tuple of (field_name, field_value)
    """
    emoji = item.get("emoji", "📌")
    title = item.get("title", "")[:80]
    summary = item.get("summary", "")[:200]
    url = item.get("url", "")
    source = item.get("source", "")
    confidence = item.get("confidence", "medium")

    if len(item.get("summary", "")) > 200:
        summary += "..."

    conf_badge = ConfidenceBadges.get(confidence)

    field_name = f"{emoji} {title}"

    field_value = f"{summary}\n\n"
    if url:
        field_value += f"📎 **[Read article]({url})**\n"
    field_value += f"└ `{source}` {conf_badge} {confidence}"

    return field_name, field_value


def format_research_item(item: dict[str, Any]) -> tuple[str, str]:
    """Format a research item for embed field."""
    title = item.get("title", "")[:80]
    summary = item.get("summary", "")[:200]
    url = item.get("url", "")
    source = item.get("source", "")
    confidence = item.get("confidence", "medium")

    if len(item.get("summary", "")) > 200:
        summary += "..."

    conf_badge = ConfidenceBadges.get(confidence)

    field_name = f"📄 {title}"

    field_value = f"{summary}\n\n"
    if url:
        field_value += f"📎 **[Read more]({url})**\n"
    field_value += f"└ `{source}` {conf_badge} {confidence}"

    return field_name, field_value


def format_industry_item(item: dict[str, Any]) -> tuple[str, str]:
    """Format an industry item for embed field."""
    title = item.get("title", "")[:80]
    summary = item.get("summary", "")[:200]
    url = item.get("url", "")
    source = item.get("source", "")
    confidence = item.get("confidence", "medium")

    if len(item.get("summary", "")) > 200:
        summary += "..."

    conf_badge = ConfidenceBadges.get(confidence)

    field_name = f"💼 {title}"

    field_value = f"{summary}\n\n"
    if url:
        field_value += f"📎 **[Read more]({url})**\n"
    field_value += f"└ `{source}` {conf_badge} {confidence}"

    return field_name, field_value


def format_watching_item(item: dict[str, Any]) -> tuple[str, str]:
    """Format a watching item for embed field."""
    title = item.get("title", "")[:80]
    summary = item.get("summary", "")[:200]
    url = item.get("url", "")
    source = item.get("source", "")
    confidence = item.get("confidence", "medium")

    if len(item.get("summary", "")) > 200:
        summary += "..."

    conf_badge = ConfidenceBadges.get(confidence)

    field_name = f"🔍 {title}"

    field_value = f"{summary}\n\n"
    if url:
        field_value += f"📎 **[Read more]({url})**\n"
    field_value += f"└ `{source}` {conf_badge} {confidence}"

    return field_name, field_value


def format_trend_item(item: dict[str, Any]) -> tuple[str, str]:
    """Format a trend item for embed field.

    Args:
        item: Trend with name, direction, description

    Returns:
        Tuple of (field_name, field_value)
    """
    name = item.get("name", "")
    direction = item.get("direction", "stable")
    description = item.get("description", "")[:300]

    if len(item.get("description", "")) > 300:
        description += "..."

    direction_emoji = DirectionIndicators.get(direction)

    field_name = f"{direction_emoji} {name}"
    field_value = description if description else "*No description available*"

    return field_name, field_value


def format_ranked_story(item: dict[str, Any], rank: int) -> tuple[str, str]:
    """Format a ranked story for embed field.

    Args:
        item: Story with title, summary, url, emoji, impact
        rank: Story rank (1-5)

    Returns:
        Tuple of (field_name, field_value)
    """
    emoji = item.get("emoji", "📌")
    title = item.get("title", "")[:80]
    summary = item.get("summary", "")[:200]
    url = item.get("url", "")
    impact = item.get("impact", "")[:100]

    if len(item.get("summary", "")) > 200:
        summary += "..."

    # Number emoji for ranking
    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    number_emoji = number_emojis[rank - 1] if 1 <= rank <= 5 else f"{rank}."

    if url:
        field_name = f"{number_emoji} {emoji} [{title}]({url})"
    else:
        field_name = f"{number_emoji} {emoji} {title}"

    field_value = summary
    if impact:
        field_value += f"\n💡 *{impact}*"

    return field_name, field_value


def build_category_embed(
    title: str,
    description: str,
    items: list[dict[str, Any]],
    color: discord.Color,
    item_formatter: Callable[[dict[str, Any]], tuple[str, str]],
) -> discord.Embed:
    """Build a category embed with consistent styling.

    Args:
        title: Embed title
        description: Embed description
        items: List of items to format
        color: Embed color
        item_formatter: Function to format each item into (name, value) tuple

    Returns:
        Configured Discord embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
    )

    for item in items:
        name, value = item_formatter(item)
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
    return build_category_embed(
        title="📰 Headlines",
        description="Top AI/ML news stories of the day",
        items=headlines,
        color=EmbedColors.HEADLINES,
        item_formatter=format_news_item,
    )


def build_research_embed(research: list[dict[str, Any]]) -> discord.Embed:
    """Build research embed for daily digest."""
    return build_category_embed(
        title="🔬 Research & Development",
        description="Latest papers and technical announcements",
        items=research,
        color=EmbedColors.RESEARCH,
        item_formatter=format_research_item,
    )


def build_industry_embed(industry: list[dict[str, Any]]) -> discord.Embed:
    """Build industry embed for daily digest."""
    return build_category_embed(
        title="🏢 Industry News",
        description="Business moves, acquisitions, and market updates",
        items=industry,
        color=EmbedColors.INDUSTRY,
        item_formatter=format_industry_item,
    )


def build_watching_embed(watching: list[dict[str, Any]]) -> discord.Embed:
    """Build watching embed for daily digest."""
    return build_category_embed(
        title="👀 Worth Watching",
        description="Emerging trends and stories to follow",
        items=watching,
        color=EmbedColors.WATCHING,
        item_formatter=format_watching_item,
    )


# Weekly digest embed builders

def build_trends_embed(trends: list[dict[str, Any]]) -> discord.Embed:
    """Build trends embed for weekly digest."""
    return build_category_embed(
        title="📈 Key Trends",
        description="Emerging patterns and developments this week",
        items=trends,
        color=EmbedColors.TRENDS,
        item_formatter=format_trend_item,
    )


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
