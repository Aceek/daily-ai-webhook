#!/usr/bin/env python3
"""
AI News Discord Bot.

Interactive bot for retrieving daily and weekly AI news digests.
"""

import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands

from config import settings
from services.database import close_db, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("discord-bot")

# Reduce discord.py noise
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("discord.http").setLevel(logging.WARNING)


class AINewsBot(commands.Bot):
    """Custom bot class with database lifecycle management."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            description="AI News Bot - Daily and weekly AI/ML news digests",
        )

    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        logger.info("Bot setup starting...")

        # Initialize database
        await init_db()

        # Load cogs
        cogs = ["cogs.daily", "cogs.weekly"]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info("Loaded cog: %s", cog)
            except Exception as e:
                logger.error("Failed to load cog %s: %s", cog, e)

        # Sync slash commands
        if settings.guild_id:
            # Sync to specific guild (faster for development)
            guild = discord.Object(id=settings.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("Synced commands to guild %s", settings.guild_id)
        else:
            # Sync globally (takes up to 1 hour to propagate)
            await self.tree.sync()
            logger.info("Synced commands globally")

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info("Bot is ready!")
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        logger.info("Connected to %d guilds", len(self.guilds))

        # Set presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="AI news",
            )
        )

    async def close(self) -> None:
        """Called when the bot is shutting down."""
        logger.info("Bot shutting down...")
        await close_db()
        await super().close()


async def main() -> None:
    """Main entry point."""
    if not settings.discord_token:
        logger.error("DISCORD_TOKEN not set")
        sys.exit(1)

    bot = AINewsBot()

    try:
        await bot.start(settings.discord_token)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
