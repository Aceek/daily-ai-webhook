"""Centralized constants for claude-service."""

from enum import Enum


class Mission(str, Enum):
    """Available missions."""
    AI_NEWS = "ai-news"


class DigestCategory(str, Enum):
    """Digest article categories."""
    HEADLINES = "headlines"
    RESEARCH = "research"
    INDUSTRY = "industry"
    WATCHING = "watching"


class ExclusionReason(str, Enum):
    """Reasons for excluding articles."""
    OFF_TOPIC = "off_topic"
    DUPLICATE = "duplicate"
    LOW_PRIORITY = "low_priority"
    OUTDATED = "outdated"


class ConfidenceLevel(str, Enum):
    """Confidence levels for article classification."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Validation limits
MIN_HEADLINES = 1
MIN_SCORE = 1
MAX_SCORE = 10

# Required mission files
DAILY_MISSION_FILES = [
    "mission.md",
    "selection-rules.md",
    "editorial-guide.md",
    "output-schema.md",
]

WEEKLY_MISSION_FILES = [
    "mission.md",
    "analysis-rules.md",
    "output-schema.md",
]
