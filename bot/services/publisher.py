"""
Publisher service for Discord digest publication.

Handles building embeds, generating card images, and publishing to Discord channels.
"""

import io
import logging
from typing import Any

import discord

from config import settings
from services.card_generator import generate_daily_card_async, generate_weekly_card_async
from services.database import mark_daily_digest_posted, mark_weekly_digest_posted
from services.embed_builder import (
    build_headlines_embed,
    build_industry_embed,
    build_research_embed,
    build_summary_embed,
    build_top_stories_embed,
    build_trends_embed,
    build_watching_embed,
)

logger = logging.getLogger(__name__)


def build_daily_embeds(content: dict[str, Any], digest_date: str) -> list[discord.Embed]:
    """Build detailed Discord embeds from daily digest content.

    Creates separate embeds for each category with full article details.
    Uses embed_builder module for consistent styling.

    Args:
        content: The digest content (headlines, research, industry, watching, metadata)
        digest_date: The date string for the digest (unused, kept for API compatibility)

    Returns:
        List of Discord embeds (one per category)
    """
    embeds = []

    headlines = content.get("headlines", [])
    if headlines:
        embeds.append(build_headlines_embed(headlines))

    research = content.get("research", [])
    if research:
        embeds.append(build_research_embed(research))

    industry = content.get("industry", [])
    if industry:
        embeds.append(build_industry_embed(industry))

    watching = content.get("watching", [])
    if watching:
        embeds.append(build_watching_embed(watching))

    return embeds


def build_weekly_embeds(content: dict[str, Any], week_start: str, week_end: str) -> list[discord.Embed]:
    """Build Discord embeds from weekly digest content.

    Creates separate embeds for summary, trends, and top stories.
    Uses embed_builder module for consistent styling.

    Args:
        content: The digest content (summary, trends, top_stories, metadata)
        week_start: Start date string (unused, kept for API compatibility)
        week_end: End date string (unused, kept for API compatibility)

    Returns:
        List of Discord embeds
    """
    embeds = []

    # Summary embed (if available)
    summary = content.get("summary", "")
    if summary:
        embeds.append(build_summary_embed(summary))

    # Trends embed
    trends = content.get("trends", [])
    if trends:
        embeds.append(build_trends_embed(trends))

    # Top stories embed
    top_stories = content.get("top_stories", [])
    if top_stories:
        embeds.append(build_top_stories_embed(top_stories))

    # Add metadata footer to last embed
    if embeds:
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
        card_file = discord.File(io.BytesIO(card_bytes), filename="ai-news-daily.png")
        logger.info("Generated daily card image: %d bytes", len(card_bytes))
    except Exception as e:
        logger.warning("Failed to generate card image, continuing without: %s", e)

    embeds = build_daily_embeds(content, digest_date)

    # Send card image first (if available), then embeds separately
    if card_file:
        await channel.send(file=card_file)

    # Send detailed embeds (Discord allows max 10 embeds per message)
    message = await channel.send(embeds=embeds[:10])

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
    theme: str | None = None,
) -> dict[str, Any]:
    """Publish a weekly digest to Discord.

    Args:
        bot: The Discord bot instance
        digest_id: Database ID of the digest
        content: The digest content
        week_start: Start date string
        week_end: End date string
        channel_id: Override channel ID (uses config default if None)
        theme: Optional theme for thematic digests

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
        card_bytes = await generate_weekly_card_async(content, week_start, week_end, theme)
        card_file = discord.File(io.BytesIO(card_bytes), filename="ai-news-weekly.png")
        logger.info("Generated weekly card image: %d bytes", len(card_bytes))
    except Exception as e:
        logger.warning("Failed to generate weekly card image, continuing without: %s", e)

    embeds = build_weekly_embeds(content, week_start, week_end)

    # Send card image first (if available), then embeds separately
    if card_file:
        await channel.send(file=card_file)

    # Send detailed embeds (Discord allows max 10 embeds per message)
    message = await channel.send(embeds=embeds[:10])

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
