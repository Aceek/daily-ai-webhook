"""
Publisher service for Discord digest publication.

Handles building embeds, generating card images, and publishing to Discord channels.
"""

import io
import logging
from datetime import datetime
from typing import Any

import discord

from config import settings
from services.card_generator import generate_daily_card_async, generate_weekly_card_async
from services.database import mark_daily_digest_posted, mark_weekly_digest_posted

logger = logging.getLogger(__name__)

# Visual constants
SECTION_EMOJIS = {
    "headlines": "📰",
    "research": "🔬",
    "industry": "🏢",
    "watching": "👀",
}

CONFIDENCE_BADGES = {
    "high": "🟢",
    "medium": "🟡",
}

DIRECTION_EMOJIS = {
    "rising": "📈",
    "stable": "➡️",
    "declining": "📉",
}

DEFAULT_ITEM_EMOJI = "📌"


def _format_news_item(item: dict[str, Any], show_summary: bool = True) -> str:
    """Format a single news item for display.

    Args:
        item: The news item dict
        show_summary: Whether to include the summary

    Returns:
        Formatted string for the item
    """
    emoji = item.get("emoji", DEFAULT_ITEM_EMOJI)
    confidence = item.get("confidence", "medium")
    confidence_badge = CONFIDENCE_BADGES.get(confidence, "")
    title = item.get("title", "")[:100]
    url = item.get("url", "")
    source = item.get("source", "")
    summary = item.get("summary", "")[:150]

    # Build the line
    if url:
        title_line = f"{confidence_badge} {emoji} **[{title}]({url})**"
    else:
        title_line = f"{confidence_badge} {emoji} **{title}**"

    if source:
        title_line += f" — *{source}*"

    if show_summary and summary:
        return f"{title_line}\n{summary}\n\n"
    else:
        return f"{title_line}\n"


def build_daily_embeds(content: dict[str, Any], digest_date: str) -> list[discord.Embed]:
    """Build Discord embeds from daily digest content.

    Args:
        content: The digest content (headlines, research, industry, watching, metadata)
        digest_date: The date string for the digest

    Returns:
        List of Discord embeds
    """
    embeds = []

    # Main embed
    main_embed = discord.Embed(
        title=f"📰 AI News Daily — {digest_date}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )

    # Add headlines section
    headlines = content.get("headlines", [])
    if headlines:
        headlines_text = ""
        for item in headlines[:5]:
            headlines_text += _format_news_item(item, show_summary=True)

        section_emoji = SECTION_EMOJIS.get("headlines", "📰")
        main_embed.add_field(
            name=f"{section_emoji} Headlines",
            value=headlines_text[:1024] or "No headlines",
            inline=False,
        )

    # Add research section
    research = content.get("research", [])
    if research:
        research_text = ""
        for item in research[:3]:
            research_text += _format_news_item(item, show_summary=False)

        section_emoji = SECTION_EMOJIS.get("research", "🔬")
        main_embed.add_field(
            name=f"{section_emoji} Research",
            value=research_text[:1024] or "No research items",
            inline=False,
        )

    # Add industry section
    industry = content.get("industry", [])
    if industry:
        industry_text = ""
        for item in industry[:3]:
            industry_text += _format_news_item(item, show_summary=False)

        section_emoji = SECTION_EMOJIS.get("industry", "🏢")
        main_embed.add_field(
            name=f"{section_emoji} Industry",
            value=industry_text[:1024] or "No industry items",
            inline=False,
        )

    # Add watching section
    watching = content.get("watching", [])
    if watching:
        watching_text = ""
        for item in watching[:3]:
            watching_text += _format_news_item(item, show_summary=False)

        section_emoji = SECTION_EMOJIS.get("watching", "👀")
        main_embed.add_field(
            name=f"{section_emoji} Watching",
            value=watching_text[:1024] or "No items to watch",
            inline=False,
        )

    # Footer with metadata
    metadata = content.get("metadata", {})
    articles_analyzed = metadata.get("articles_analyzed", 0)
    web_searches = metadata.get("web_searches", 0)
    main_embed.set_footer(
        text=f"🤖 Analyzed {articles_analyzed} articles | {web_searches} web searches"
    )

    embeds.append(main_embed)
    return embeds


def build_weekly_embeds(content: dict[str, Any], week_start: str, week_end: str) -> list[discord.Embed]:
    """Build Discord embeds from weekly digest content.

    Args:
        content: The digest content
        week_start: Start date string
        week_end: End date string

    Returns:
        List of Discord embeds
    """
    embeds = []

    # Main embed with summary
    main_embed = discord.Embed(
        title="📊 AI News Weekly",
        description=f"**{week_start} → {week_end}**",
        color=discord.Color.purple(),
        timestamp=datetime.utcnow(),
    )

    # Add summary
    summary = content.get("summary", "")
    if summary:
        if len(summary) > 1024:
            summary = summary[:1021] + "..."
        main_embed.add_field(
            name="📋 Executive Summary",
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
            direction_emoji = DIRECTION_EMOJIS.get(direction, "")
            description = trend.get("description", "")[:100]
            trends_text += f"{direction_emoji} **{name}**\n{description}\n\n"

        main_embed.add_field(
            name="📈 Key Trends",
            value=trends_text[:1024] or "No trends identified",
            inline=False,
        )

    embeds.append(main_embed)

    # Second embed for top stories
    top_stories = content.get("top_stories", [])
    if top_stories:
        stories_embed = discord.Embed(
            title="🏆 Top Stories of the Week",
            color=discord.Color.purple(),
        )

        for i, story in enumerate(top_stories[:5], 1):
            emoji = story.get("emoji", DEFAULT_ITEM_EMOJI)
            title = story.get("title", "")[:80]
            summary = story.get("summary", "")[:200]
            url = story.get("url", "")
            impact = story.get("impact", "")[:100]

            # Number emoji for ranking
            number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            number_emoji = number_emojis[i - 1] if i <= 5 else f"{i}."

            if url:
                field_name = f"{number_emoji} {emoji} [{title}]({url})"
            else:
                field_name = f"{number_emoji} {emoji} {title}"

            field_value = summary
            if impact:
                field_value += f"\n💡 *{impact}*"

            stories_embed.add_field(
                name=field_name[:256],
                value=field_value[:1024],
                inline=False,
            )

        embeds.append(stories_embed)

    # Add metadata footer to last embed
    metadata = content.get("metadata", {})
    articles_analyzed = metadata.get("articles_analyzed", 0)
    embeds[-1].set_footer(text=f"🤖 Based on {articles_analyzed} articles")

    return embeds


async def publish_daily_digest(
    bot: discord.Client,
    digest_id: int,
    content: dict[str, Any],
    digest_date: str,
    channel_id: int | None = None,
) -> dict[str, Any]:
    """Publish a daily digest to Discord.

    Args:
        bot: The Discord bot instance
        digest_id: Database ID of the digest
        content: The digest content
        digest_date: Date string for the digest
        channel_id: Override channel ID (uses config default if None)

    Returns:
        Publication result with message_id, channel_id, success status
    """
    target_channel_id = channel_id or settings.daily_channel_id

    if not target_channel_id:
        raise ValueError("No channel ID provided and DAILY_CHANNEL_ID not configured")

    channel = bot.get_channel(target_channel_id)
    if not channel:
        raise ValueError(f"Channel {target_channel_id} not found")

    if not isinstance(channel, discord.TextChannel):
        raise ValueError(f"Channel {target_channel_id} is not a text channel")

    # Generate card image
    card_file = None
    try:
        card_bytes = await generate_daily_card_async(content, digest_date)
        card_file = discord.File(io.BytesIO(card_bytes), filename="daily-digest.png")
        logger.info("Generated daily card image: %d bytes", len(card_bytes))
    except Exception as e:
        logger.warning("Failed to generate card image, continuing without: %s", e)

    embeds = build_daily_embeds(content, digest_date)

    # Send with card image if available
    if card_file:
        message = await channel.send(file=card_file, embeds=embeds)
    else:
        message = await channel.send(embeds=embeds)

    # Update database
    try:
        await mark_daily_digest_posted(digest_id)
        logger.info("Marked daily digest %d as posted", digest_id)
    except Exception as e:
        logger.warning("Failed to mark digest %d as posted: %s", digest_id, e)

    return {
        "status": "success",
        "message_id": str(message.id),
        "channel_id": str(channel.id),
        "posted_to_discord": True,
    }


async def publish_weekly_digest(
    bot: discord.Client,
    digest_id: int,
    content: dict[str, Any],
    week_start: str,
    week_end: str,
    channel_id: int | None = None,
) -> dict[str, Any]:
    """Publish a weekly digest to Discord.

    Args:
        bot: The Discord bot instance
        digest_id: Database ID of the digest
        content: The digest content
        week_start: Start date string
        week_end: End date string
        channel_id: Override channel ID (uses config default if None)

    Returns:
        Publication result with message_id, channel_id, success status
    """
    target_channel_id = channel_id or settings.weekly_channel_id

    if not target_channel_id:
        raise ValueError("No channel ID provided and WEEKLY_CHANNEL_ID not configured")

    channel = bot.get_channel(target_channel_id)
    if not channel:
        raise ValueError(f"Channel {target_channel_id} not found")

    if not isinstance(channel, discord.TextChannel):
        raise ValueError(f"Channel {target_channel_id} is not a text channel")

    # Generate card image
    card_file = None
    try:
        card_bytes = await generate_weekly_card_async(content, week_start, week_end)
        card_file = discord.File(io.BytesIO(card_bytes), filename="weekly-digest.png")
        logger.info("Generated weekly card image: %d bytes", len(card_bytes))
    except Exception as e:
        logger.warning("Failed to generate weekly card image, continuing without: %s", e)

    embeds = build_weekly_embeds(content, week_start, week_end)

    # Send with card image if available
    if card_file:
        message = await channel.send(file=card_file, embeds=embeds)
    else:
        message = await channel.send(embeds=embeds)

    # Update database
    try:
        await mark_weekly_digest_posted(digest_id)
        logger.info("Marked weekly digest %d as posted", digest_id)
    except Exception as e:
        logger.warning("Failed to mark weekly digest %d as posted: %s", digest_id, e)

    return {
        "status": "success",
        "message_id": str(message.id),
        "channel_id": str(channel.id),
        "posted_to_discord": True,
    }
