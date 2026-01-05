"""Shared fixtures for claude-service tests."""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from api.models import Article, SummarizeRequest
from config import Settings


@pytest.fixture
def mock_settings():
    """Mock Settings object."""
    settings = MagicMock(spec=Settings)
    settings.claude_model = "sonnet"
    settings.logs_path = "/tmp/logs"
    settings.missions_path = "/tmp/missions"
    settings.data_path = "/tmp/data"
    settings.digests_path = "/tmp/digests"
    settings.database_url = "postgresql://test:test@localhost/test"
    settings.allowed_tools = "Read,WebSearch,Write,mcp__submit-digest__submit_digest"
    settings.claude_timeout = 600
    settings.retry_count = 1
    settings.log_level = "info"
    return settings


@pytest.fixture
def sample_articles():
    """Sample articles for testing."""
    return [
        Article(
            title="GPT-5 Released",
            url="https://example.com/gpt5",
            source="TechCrunch",
            description="OpenAI releases GPT-5",
            pub_date="2024-01-01",
        ),
        Article(
            title="Gemini 2 Update",
            url="https://example.com/gemini",
            source="The Verge",
            description="Google updates Gemini",
            pub_date="2024-01-02",
        ),
    ]


@pytest.fixture
def sample_summarize_request(sample_articles):
    """Sample summarize request."""
    return SummarizeRequest(
        articles=sample_articles,
        mission="ai-news",
        workflow_execution_id="test-workflow-123",
    )


@pytest.fixture
def mock_logger():
    """Mock UnifiedLogger."""
    logger = MagicMock()

    # Mock ExecutionDirectory
    exec_dir = MagicMock()
    exec_dir.path = Path("/tmp/test-exec")
    exec_dir.logs_path = Path("/tmp/test-exec/logs")

    logger.create_execution_dir = MagicMock(return_value=exec_dir)
    logger.save = MagicMock()
    logger.log_mcp_operation = MagicMock()

    return logger


@pytest.fixture
def mock_exec_dir():
    """Mock ExecutionDirectory."""
    exec_dir = MagicMock()
    exec_dir.path = Path("/tmp/test-exec")
    exec_dir.logs_path = Path("/tmp/test-exec/logs")
    exec_dir.digest_path = Path("/tmp/test-exec/digest.json")
    return exec_dir
