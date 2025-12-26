"""
Item formatter for Discord embed fields.

Provides generic formatting functions for digest items with configurable emojis.
Consolidates format_news_item, format_research_item, format_industry_item, format_watching_item
into a single generic function with emoji configuration.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class CategoryConfig:
    """Configuration for category item formatting."""

    emoji: str
    link_text: str = "Read more"


# Predefined category configurations
CATEGORY_CONFIGS = {
    "headlines": CategoryConfig(emoji="", link_text="Read article"),  # Uses item emoji
    "research": CategoryConfig(emoji="📄", link_text="Read more"),
    "industry": CategoryConfig(emoji="💼", link_text="Read more"),
    "watching": CategoryConfig(emoji="🔍", link_text="Read more"),
}


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


def format_category_item(
    item: dict[str, Any],
    config: CategoryConfig | None = None,
    category: str | None = None,
) -> tuple[str, str]:
    """Format a category item for embed field.

    Generic formatter that replaces format_news_item, format_research_item,
    format_industry_item, and format_watching_item.

    Args:
        item: Item with title, summary, url, source, confidence, emoji
        config: Optional CategoryConfig for emoji and link text
        category: Optional category name to lookup config

    Returns:
        Tuple of (field_name, field_value)
    """
    # Get config from category name if provided
    if config is None and category:
        config = CATEGORY_CONFIGS.get(category, CategoryConfig(emoji="📌"))
    elif config is None:
        config = CategoryConfig(emoji="📌")

    # Extract item data with truncation
    title = item.get("title", "")[:80]
    summary = item.get("summary", "")[:200]
    url = item.get("url", "")
    source = item.get("source", "")
    confidence = item.get("confidence", "medium")

    # Add ellipsis if truncated
    if len(item.get("summary", "")) > 200:
        summary += "..."

    # Use item emoji for headlines, config emoji for others
    if config.emoji == "":  # headlines use item's own emoji
        emoji = item.get("emoji", "📌")
    else:
        emoji = config.emoji

    conf_badge = ConfidenceBadges.get(confidence)

    field_name = f"{emoji} {title}"

    field_value = f"{summary}\n\n"
    if url:
        field_value += f"📎 **[{config.link_text}]({url})**\n"
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
