#!/usr/bin/env python3
"""
Claude Service - HTTP wrapper for Claude Code CLI.

Provides /summarize endpoint for n8n integration.
This service wraps Claude Code CLI to expose it as an HTTP API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import create_routers
from config import Settings, configure_logging, get_settings
from database import close_db, init_db, seed_missions
from loggers.execution_logger import ExecutionLogger
from loggers.workflow_logger import WorkflowLogger


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()
    logger = configure_logging(settings)

    # Initialize loggers
    execution_logger = ExecutionLogger(logs_dir=settings.logs_path)
    workflow_logger = WorkflowLogger(logs_dir=settings.logs_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan: init and cleanup."""
        # Startup
        if settings.database_url:
            await init_db(settings.database_url)
            await seed_missions()
            logger.info("Database connected and seeded")
        else:
            logger.warning("DATABASE_URL not set, running without database")

        yield

        # Shutdown
        if settings.database_url:
            await close_db()
            logger.info("Database connection closed")

    # Create FastAPI application
    app = FastAPI(
        title="Claude Service",
        description="HTTP wrapper for Claude Code CLI",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register routes
    api_router = create_routers(settings, execution_logger, workflow_logger)
    app.include_router(api_router)

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
