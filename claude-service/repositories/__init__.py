"""Repositories module - Database access layer."""

from repositories.article_repository import check_duplicate_urls

__all__ = [
    "check_duplicate_urls",
]
