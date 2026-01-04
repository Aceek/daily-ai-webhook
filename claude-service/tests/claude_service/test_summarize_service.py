"""Tests for SummarizeService."""

import pytest
from unittest.mock import patch

from services.summarize_service import SummarizeService
from api.models import SummarizeRequest, Article, ClaudeResult


class TestSummarizeService:
    """Tests for SummarizeService class."""

    @pytest.fixture
    def service(self, mock_settings, mock_logger):
        """Create SummarizeService instance."""
        return SummarizeService(mock_settings, mock_logger)

    @pytest.mark.asyncio
    async def test_summarize_invalid_mission(self, service):
        """Test summarize with invalid mission returns error."""
        request = SummarizeRequest(
            articles=[Article(title="Test", url="http://test.com", source="Test")],
            mission="invalid-mission",
        )

        with patch("services.summarize_service.validate_mission") as mock_validate:
            mock_validate.return_value = (False, "Mission not found")
            response = await service.summarize(request)

        assert response.success is False
        assert "Mission not found" in response.error
        assert response.article_count == 1
        assert response.mission == "invalid-mission"

    @pytest.mark.asyncio
    async def test_summarize_empty_articles(self, service, mock_logger):
        """Test summarize with empty articles list."""
        request = SummarizeRequest(articles=[], mission="ai-news")

        # Mock all dependencies
        with patch("services.summarize_service.validate_mission") as mock_validate, \
             patch("services.summarize_service.write_articles_file") as mock_write, \
             patch("services.summarize_service.call_claude_cli") as mock_claude, \
             patch("services.summarize_service.build_prompt") as mock_prompt, \
             patch("services.summarize_service.read_digest_file") as mock_digest:

            mock_validate.return_value = (True, None)
            mock_prompt.return_value = "test prompt"
            mock_claude.return_value = ClaudeResult(
                response="Test response",
                success=True,
                timeline=[],
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
            )
            mock_digest.return_value = {
                "digest_id": 123,
                "mission": "ai-news",
                "content": "test digest",
            }

            response = await service.summarize(request)

        # Should handle empty articles gracefully
        assert response is not None
        assert response.article_count == 0
        assert response.success is True
        assert response.digest_id == 123

    @pytest.mark.asyncio
    async def test_summarize_success_with_digest(self, service, mock_logger, sample_articles):
        """Test successful summarize with digest saved."""
        request = SummarizeRequest(
            articles=sample_articles,
            mission="ai-news",
            workflow_execution_id="test-123",
        )

        digest_data = {
            "digest_id": 456,
            "mission": "ai-news",
            "title": "Daily Digest",
            "articles": [],
        }

        with patch("services.summarize_service.validate_mission") as mock_validate, \
             patch("services.summarize_service.write_articles_file") as mock_write, \
             patch("services.summarize_service.call_claude_cli") as mock_claude, \
             patch("services.summarize_service.build_prompt") as mock_prompt, \
             patch("services.summarize_service.read_digest_file") as mock_digest:

            mock_validate.return_value = (True, None)
            mock_prompt.return_value = "test prompt"
            mock_claude.return_value = ClaudeResult(
                response="Successfully created digest",
                success=True,
                timeline=[],
                input_tokens=200,
                output_tokens=100,
                cost_usd=0.02,
            )
            mock_digest.return_value = digest_data

            response = await service.summarize(request)

        assert response.success is True
        assert response.digest_id == 456
        assert response.digest == digest_data
        assert response.article_count == 2
        assert response.mission == "ai-news"
        assert response.workflow_execution_id == "test-123"
        assert response.error is None

    @pytest.mark.asyncio
    async def test_summarize_claude_failure(self, service, sample_articles):
        """Test summarize when Claude CLI fails."""
        request = SummarizeRequest(articles=sample_articles, mission="ai-news")

        with patch("services.summarize_service.validate_mission") as mock_validate, \
             patch("services.summarize_service.write_articles_file") as mock_write, \
             patch("services.summarize_service.call_claude_cli") as mock_claude, \
             patch("services.summarize_service.build_prompt") as mock_prompt, \
             patch("services.summarize_service.read_digest_file") as mock_digest:

            mock_validate.return_value = (True, None)
            mock_prompt.return_value = "test prompt"
            mock_claude.return_value = ClaudeResult(
                response="",
                success=False,
                error="Claude API timeout",
                timeline=[],
            )
            mock_digest.return_value = None

            response = await service.summarize(request)

        assert response.success is False
        assert "Claude API timeout" in response.error
        assert response.digest is None
        assert response.digest_id is None

    @pytest.mark.asyncio
    async def test_summarize_no_digest_created(self, service, sample_articles):
        """Test when Claude succeeds but doesn't call submit_digest."""
        request = SummarizeRequest(articles=sample_articles, mission="ai-news")

        with patch("services.summarize_service.validate_mission") as mock_validate, \
             patch("services.summarize_service.write_articles_file") as mock_write, \
             patch("services.summarize_service.call_claude_cli") as mock_claude, \
             patch("services.summarize_service.build_prompt") as mock_prompt, \
             patch("services.summarize_service.read_digest_file") as mock_digest:

            mock_validate.return_value = (True, None)
            mock_prompt.return_value = "test prompt"
            mock_claude.return_value = ClaudeResult(
                response="Some response without digest",
                success=True,
                timeline=[],
            )
            mock_digest.return_value = None

            response = await service.summarize(request)

        assert response.success is False
        assert "did not call submit_digest tool" in response.error

    def test_determine_result_status_success(self):
        """Test _determine_result_status with successful digest."""
        result = ClaudeResult(success=True)
        digest = {"digest_id": 123, "content": "test"}

        success, error, digest_id = SummarizeService._determine_result_status(
            result, digest
        )

        assert success is True
        assert error is None
        assert digest_id == 123

    def test_determine_result_status_no_digest_id(self):
        """Test _determine_result_status when digest has no ID."""
        result = ClaudeResult(success=True)
        digest = {"content": "test"}  # Missing digest_id

        success, error, digest_id = SummarizeService._determine_result_status(
            result, digest
        )

        assert success is False
        assert "not saved to database" in error
        assert digest_id is None

    def test_determine_result_status_claude_failed(self):
        """Test _determine_result_status when Claude fails."""
        result = ClaudeResult(success=False, error="Timeout")
        digest = None

        success, error, digest_id = SummarizeService._determine_result_status(
            result, digest
        )

        assert success is False
        assert error == "Timeout"
        assert digest_id is None

    def test_determine_result_status_no_digest(self):
        """Test _determine_result_status when no digest created."""
        result = ClaudeResult(success=True)
        digest = None

        success, error, digest_id = SummarizeService._determine_result_status(
            result, digest
        )

        assert success is False
        assert "did not call submit_digest tool" in error
        assert digest_id is None
