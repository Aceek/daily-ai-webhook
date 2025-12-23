#!/usr/bin/env python3
"""
AI News Discord Bot.

Interactive bot for retrieving daily and weekly AI news digests.
Also runs an HTTP API for external services to trigger digest publication.
"""

import asyncio
import logging
import sys

import discord
import uvicorn
from discord.ext import commands

from api import app as fastapi_app
from api import set_bot
from config import settings
from services.database import close_db, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("discord-bot")

# Reduce discord.py and uvicorn noise
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("discord.http").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


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


async def run_api_server() -> None:
    """Run the FastAPI server."""
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    """Main entry point."""
    if not settings.discord_token:
        logger.error("DISCORD_TOKEN not set")
        sys.exit(1)

    bot = AINewsBot()

    # Set bot reference for API handlers
    set_bot(bot)

    # Create tasks for both bot and API server
    bot_task = asyncio.create_task(bot.start(settings.discord_token))
    api_task = asyncio.create_task(run_api_server())

    logger.info("Starting Discord bot and HTTP API server...")

    try:
        # Wait for either task to complete (or fail)
        done, pending = await asyncio.wait(
            [bot_task, api_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # If one task completed, cancel the other
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Check for exceptions
        for task in done:
            if task.exception():
                logger.error("Task failed: %s", task.exception())

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
