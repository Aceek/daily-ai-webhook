"""
Formatters package for Discord message formatting.

Provides utilities for formatting digest items into Discord embed fields.
"""

from services.formatters.item_formatter import (
    CategoryConfig,
    format_category_item,
    format_ranked_story,
    format_trend_item,
)

__all__ = [
    "CategoryConfig",
    "format_category_item",
    "format_ranked_story",
    "format_trend_item",
]
