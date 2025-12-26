"""
Publisher service for Discord digest publication.

Handles building embeds, generating card images, and publishing to Discord channels.
"""

import io
import logging
from dataclasses import dataclass
from enum import Enum
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


class DigestType(str, Enum):
    """Digest type enumeration."""

    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class DigestConfig:
    """Configuration for digest publication."""

    digest_type: DigestType
    digest_id: int
    content: dict[str, Any]
    channel_id: int | None = None
    # Daily-specific
    digest_date: str | None = None
    # Weekly-specific
    week_start: str | None = None
    week_end: str | None = None
    theme: str | None = None


def build_daily_embeds(content: dict[str, Any]) -> list[discord.Embed]:
    """Build detailed Discord embeds from daily digest content.

    Args:
        content: The digest content (headlines, research, industry, watching, metadata)

    Returns:
        List of Discord embeds (one per category)
    """
    embeds = []

    for category, builder in [
        ("headlines", build_headlines_embed),
        ("research", build_research_embed),
        ("industry", build_industry_embed),
        ("watching", build_watching_embed),
    ]:
        items = content.get(category, [])
        if items:
            embeds.append(builder(items))

    return embeds


def build_weekly_embeds(content: dict[str, Any]) -> list[discord.Embed]:
    """Build Discord embeds from weekly digest content.

    Args:
        content: The digest content (summary, trends, top_stories, metadata)

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


async def _generate_card(config: DigestConfig) -> discord.File | None:
    """Generate card image for a digest.

    Args:
        config: Digest configuration

    Returns:
        Discord File with card image, or None if generation failed
    """
    try:
        if config.digest_type == DigestType.DAILY:
            card_bytes = await generate_daily_card_async(config.content, config.digest_date)
            filename = "ai-news-daily.png"
        else:
            card_bytes = await generate_weekly_card_async(
                config.content, config.week_start, config.week_end, config.theme
            )
            filename = "ai-news-weekly.png"

        logger.info("Generated %s card image: %d bytes", config.digest_type.value, len(card_bytes))
        return discord.File(io.BytesIO(card_bytes), filename=filename)

    except Exception as e:
        logger.warning("Failed to generate card image: %s", e)
        return None


async def _get_channel(bot: discord.Client, config: DigestConfig) -> discord.TextChannel:
    """Get the target channel for publication.

    Args:
        bot: Discord bot instance
        config: Digest configuration

    Returns:
        Discord TextChannel

    Raises:
        ValueError: If channel not found or invalid
    """
    if config.digest_type == DigestType.DAILY:
        default_channel = settings.daily_channel_id
        channel_name = "DAILY_CHANNEL_ID"
    else:
        default_channel = settings.weekly_channel_id
        channel_name = "WEEKLY_CHANNEL_ID"

    target_channel_id = config.channel_id or default_channel

    if not target_channel_id:
        raise ValueError(f"No channel ID provided and {channel_name} not configured")

    channel = bot.get_channel(target_channel_id)
    if not channel:
        raise ValueError(f"Channel {target_channel_id} not found")

    if not isinstance(channel, discord.TextChannel):
        raise ValueError(f"Channel {target_channel_id} is not a text channel")

    return channel


async def _mark_posted(config: DigestConfig) -> None:
    """Mark digest as posted in database.

    Args:
        config: Digest configuration
    """
    try:
        if config.digest_type == DigestType.DAILY:
            await mark_daily_digest_posted(config.digest_id)
        else:
            await mark_weekly_digest_posted(config.digest_id)
        logger.info("Marked %s digest %d as posted", config.digest_type.value, config.digest_id)
    except Exception as e:
        logger.warning("Failed to mark digest %d as posted: %s", config.digest_id, e)


async def publish_digest(bot: discord.Client, config: DigestConfig) -> dict[str, Any]:
    """Publish a digest to Discord.

    Unified function for publishing both daily and weekly digests.

    Args:
        bot: The Discord bot instance
        config: Digest configuration

    Returns:
        Publication result with message_id, channel_id, success status
    """
    channel = await _get_channel(bot, config)

    # Generate and send card image
    card_file = await _generate_card(config)
    if card_file:
        await channel.send(file=card_file)

    # Build and send embeds
    if config.digest_type == DigestType.DAILY:
        embeds = build_daily_embeds(config.content)
    else:
        embeds = build_weekly_embeds(config.content)

    message = await channel.send(embeds=embeds[:10])

    # Update database
    await _mark_posted(config)

    return {
        "status": "success",
        "message_id": str(message.id),
        "channel_id": str(channel.id),
        "posted_to_discord": True,
    }


# Convenience functions for backward compatibility

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
    config = DigestConfig(
        digest_type=DigestType.DAILY,
        digest_id=digest_id,
        content=content,
        digest_date=digest_date,
        channel_id=channel_id,
    )
    return await publish_digest(bot, config)


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
    config = DigestConfig(
        digest_type=DigestType.WEEKLY,
        digest_id=digest_id,
        content=content,
        week_start=week_start,
        week_end=week_end,
        channel_id=channel_id,
        theme=theme,
    )
    return await publish_digest(bot, config)
