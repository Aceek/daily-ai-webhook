"""
Database connection and session management.

Provides async database engine and session factory for SQLModel.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from models import Article, Category, DailyDigest, Mission, WeeklyDigest  # noqa: F401

logger = logging.getLogger(__name__)

# Global engine instance (initialized on startup)
_engine = None
_async_session_factory = None


async def init_db(database_url: str) -> None:
    """Initialize database connection and create tables.

    Args:
        database_url: PostgreSQL connection string (asyncpg format).
    """
    global _engine, _async_session_factory

    logger.info("Initializing database connection")

    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    _async_session_factory = sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables if they don't exist
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database connection."""
    global _engine, _async_session_factory

    if _engine:
        logger.info("Closing database connection")
        await _engine.dispose()
        _engine = None
        _async_session_factory = None


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.

    Yields:
        AsyncSession for database operations.

    Raises:
        RuntimeError: If database is not initialized.
    """
    if _async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def seed_missions() -> None:
    """Seed default missions if they don't exist."""
    from sqlmodel import select

    async with get_session() as session:
        # Check if ai-news mission exists
        stmt = select(Mission).where(Mission.id == "ai-news")
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            mission = Mission(
                id="ai-news",
                name="AI News Daily Digest",
                description="Daily digest of AI/ML news for technical audience",
            )
            session.add(mission)
            await session.commit()
            logger.info("Seeded 'ai-news' mission")
        else:
            logger.info("Mission 'ai-news' already exists")
