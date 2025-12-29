"""Base database connection utilities.

Provides a context manager for database connections and common utilities.
Uses synchronous psycopg2 for MCP server operations.
"""

import os
from contextlib import contextmanager
from typing import Any, Generator

import psycopg2
from psycopg2.extras import RealDictCursor


def get_database_url() -> str | None:
    """Get the database URL from environment.

    Returns:
        Database URL or None if not set.
    """
    return os.getenv("DATABASE_URL")


def get_sync_url(db_url: str) -> str:
    """Convert asyncpg URL to psycopg2 format.

    Args:
        db_url: Database URL (possibly with asyncpg prefix).

    Returns:
        URL compatible with psycopg2.
    """
    return db_url.replace("postgresql+asyncpg://", "postgresql://")


def get_db_connection() -> tuple[Any | None, str | None]:
    """Get a synchronous database connection.

    Returns:
        Tuple of (connection, error_message).
        Connection is None if unavailable, with error_message explaining why.
    """
    db_url = get_database_url()

    if not db_url:
        return None, "DATABASE_URL not set"

    sync_url = get_sync_url(db_url)

    try:
        conn = psycopg2.connect(sync_url, cursor_factory=RealDictCursor)
        return conn, None
    except Exception as e:
        return None, f"Connection failed: {e}"


@contextmanager
def DatabaseConnection() -> Generator[Any, None, None]:
    """Context manager for database connections.

    Automatically handles connection lifecycle and error reporting.

    Yields:
        Database connection with RealDictCursor.

    Raises:
        ConnectionError: If database connection fails.

    Example:
        with DatabaseConnection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    """
    conn, error = get_db_connection()

    if not conn:
        raise ConnectionError(error or "Failed to connect to database")

    try:
        yield conn
    finally:
        conn.close()


class DatabaseTransaction:
    """Context manager for database transactions with auto-commit/rollback.

    Usage:
        with DatabaseTransaction() as (conn, cur):
            cur.execute("INSERT INTO ...")
            # Auto-commits on success, rolls back on exception
    """

    def __init__(self) -> None:
        """Initialize transaction manager."""
        self._conn: Any = None
        self._cursor: Any = None

    def __enter__(self) -> tuple[Any, Any]:
        """Enter transaction context.

        Returns:
            Tuple of (connection, cursor).

        Raises:
            ConnectionError: If database connection fails.
        """
        conn, error = get_db_connection()
        if not conn:
            raise ConnectionError(error or "Failed to connect to database")

        self._conn = conn
        self._cursor = conn.cursor()
        return self._conn, self._cursor

    def __exit__(self, exc_type: type | None, exc_val: Exception | None,
                 exc_tb: Any) -> None:
        """Exit transaction context.

        Commits on success, rolls back on exception.
        """
        if self._cursor:
            self._cursor.close()

        if self._conn:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
            self._conn.close()
