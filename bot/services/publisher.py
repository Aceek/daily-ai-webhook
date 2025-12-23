"""
Publisher service for Discord digest publication.

Handles building embeds and publishing to Discord channels.
"""

import logging
from datetime import datetime
from typing import Any

import discord

from config import settings
from services.database import mark_daily_digest_posted, mark_weekly_digest_posted

logger = logging.getLogger(__name__)


def build_daily_embeds(content: dict[str, Any], digest_date: str) -> list[discord.Embed]:
    """Build Discord embeds from daily digest content.

    Args:
        content: The digest content (headlines, research, industry, watching, metadata)
        digest_date: The date string for the digest

    Returns:
        List of Discord embeds
    """
    embeds = []

    # Main embed with headlines
    main_embed = discord.Embed(
        title=f"AI News Daily Digest - {digest_date}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )

    # Add headlines
    headlines = content.get("headlines", [])
    if headlines:
        headlines_text = ""
        for item in headlines[:5]:
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
        title="AI News Weekly Digest",
        description=f"**{week_start} to {week_end}**",
        color=discord.Color.purple(),
        timestamp=datetime.utcnow(),
    )

    # Add summary
    summary = content.get("summary", "")
    if summary:
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

    # Second embed for top stories
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

    embeds = build_daily_embeds(content, digest_date)
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

    embeds = build_weekly_embeds(content, week_start, week_end)
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
