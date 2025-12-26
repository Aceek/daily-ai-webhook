"""Validation logic for digest submissions.

Provides validation functions for news items and excluded items.
"""

from typing import Any

# Valid exclusion reasons
VALID_EXCLUSION_REASONS = frozenset([
    "off_topic",
    "duplicate",
    "low_priority",
    "outdated",
])

# Required fields for news items
NEWS_ITEM_REQUIRED_FIELDS = frozenset([
    "title",
    "summary",
    "url",
    "source",
    "category",
    "confidence",
])

# Required fields for excluded items
EXCLUDED_ITEM_REQUIRED_FIELDS = frozenset([
    "url",
    "title",
    "category",
    "reason",
    "score",
])


def validate_news_items(items: list[dict[str, Any]], section_name: str) -> list[str]:
    """Validate news items have required fields.

    Args:
        items: List of news item dicts.
        section_name: Name of the section for error messages.

    Returns:
        List of validation error messages.
    """
    errors = []
    for i, item in enumerate(items or []):
        for field in NEWS_ITEM_REQUIRED_FIELDS:
            if field not in item:
                errors.append(f"{section_name}[{i}]: missing '{field}'")
    return errors


def validate_excluded_items(items: list[dict[str, Any]]) -> list[str]:
    """Validate excluded items have required fields.

    Args:
        items: List of excluded item dicts.

    Returns:
        List of validation error messages.
    """
    errors = []

    for i, item in enumerate(items or []):
        # Check required fields
        for field in EXCLUDED_ITEM_REQUIRED_FIELDS:
            if field not in item:
                errors.append(f"excluded[{i}]: missing '{field}'")

        # Validate reason value
        if "reason" in item and item["reason"] not in VALID_EXCLUSION_REASONS:
            valid_list = list(VALID_EXCLUSION_REASONS)
            errors.append(
                f"excluded[{i}]: invalid reason '{item['reason']}', "
                f"must be one of {valid_list}"
            )

        # Validate score range
        if "score" in item:
            score = item["score"]
            if not isinstance(score, (int, float)) or score < 1 or score > 10:
                errors.append(f"excluded[{i}]: score must be between 1 and 10")

    return errors


def validate_daily_digest(
    headlines: list[dict[str, Any]],
    research: list[dict[str, Any]],
    industry: list[dict[str, Any]],
    watching: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[str]:
    """Validate a complete daily digest submission.

    Args:
        headlines: List of headline items.
        research: List of research items.
        industry: List of industry items.
        watching: List of watching items.
        excluded: List of excluded items.
        metadata: Submission metadata.

    Returns:
        List of validation error messages.
    """
    errors = []

    # Validate headlines (required, at least 1)
    if not headlines or len(headlines) == 0:
        errors.append("headlines: at least 1 item required")

    # Validate each section
    errors.extend(validate_news_items(headlines, "headlines"))
    errors.extend(validate_news_items(research, "research"))
    errors.extend(validate_news_items(industry, "industry"))
    errors.extend(validate_news_items(watching, "watching"))

    # Validate excluded items
    errors.extend(validate_excluded_items(excluded))

    # Validate metadata
    required_meta = ["articles_analyzed", "web_searches", "research_doc"]
    for field in required_meta:
        if field not in metadata:
            errors.append(f"metadata: missing '{field}'")

    return errors


def validate_weekly_digest(
    summary: str,
    trends: list[dict[str, Any]],
    top_stories: list[dict[str, Any]],
) -> list[str]:
    """Validate a weekly digest submission.

    Args:
        summary: Executive summary text.
        trends: List of trend dicts.
        top_stories: List of top story dicts.

    Returns:
        List of validation error messages.
    """
    errors = []

    if not summary:
        errors.append("summary: required")
    if not trends:
        errors.append("trends: at least 1 trend required")
    if not top_stories:
        errors.append("top_stories: at least 1 story required")

    # Validate trends
    for i, trend in enumerate(trends or []):
        for field in ["name", "description", "direction"]:
            if field not in trend:
                errors.append(f"trends[{i}]: missing '{field}'")

    # Validate top_stories
    for i, story in enumerate(top_stories or []):
        for field in ["title", "summary", "url"]:
            if field not in story:
                errors.append(f"top_stories[{i}]: missing '{field}'")

    return errors
