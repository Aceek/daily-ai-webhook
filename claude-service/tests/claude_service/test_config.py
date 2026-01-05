"""Tests for config module."""

from unittest.mock import patch, MagicMock

from config import (
    discover_missions,
    validate_mission,
    validate_weekly_mission,
    build_allowed_tools,
    get_mcp_tool_names,
    Settings,
    BASE_TOOLS,
    MCP_SERVER_NAME,
)


class TestDiscoverMissions:
    """Tests for discover_missions function."""

    def test_discover_missions_empty_path(self, tmp_path):
        """Test with empty missions directory."""
        missions = discover_missions(str(tmp_path))
        assert missions == []

    def test_discover_missions_with_missions(self, tmp_path):
        """Test with valid missions directory."""
        # Create mission directories
        (tmp_path / "ai-news").mkdir()
        (tmp_path / "ai-news" / "mission.md").touch()
        (tmp_path / "tech-news").mkdir()
        (tmp_path / "tech-news" / "mission.md").touch()

        missions = discover_missions(str(tmp_path))
        assert "ai-news" in missions
        assert "tech-news" in missions
        assert len(missions) == 2

    def test_discover_missions_ignores_underscore_dirs(self, tmp_path):
        """Test that directories starting with _ are ignored."""
        (tmp_path / "_templates").mkdir()
        (tmp_path / "_templates" / "mission.md").touch()
        (tmp_path / "ai-news").mkdir()
        (tmp_path / "ai-news" / "mission.md").touch()

        missions = discover_missions(str(tmp_path))
        assert "_templates" not in missions
        assert "ai-news" in missions

    def test_discover_missions_ignores_dirs_without_mission_md(self, tmp_path):
        """Test that directories without mission.md are ignored."""
        (tmp_path / "incomplete").mkdir()
        (tmp_path / "ai-news").mkdir()
        (tmp_path / "ai-news" / "mission.md").touch()

        missions = discover_missions(str(tmp_path))
        assert "incomplete" not in missions
        assert "ai-news" in missions

    def test_discover_missions_returns_sorted(self, tmp_path):
        """Test that missions are returned in sorted order."""
        (tmp_path / "zebra").mkdir()
        (tmp_path / "zebra" / "mission.md").touch()
        (tmp_path / "alpha").mkdir()
        (tmp_path / "alpha" / "mission.md").touch()
        (tmp_path / "beta").mkdir()
        (tmp_path / "beta" / "mission.md").touch()

        missions = discover_missions(str(tmp_path))
        assert missions == ["alpha", "beta", "zebra"]

    def test_discover_missions_nonexistent_path(self):
        """Test with non-existent path."""
        missions = discover_missions("/nonexistent/path")
        assert missions == []


class TestValidateMission:
    """Tests for validate_mission function."""

    def test_validate_mission_not_found(self, tmp_path):
        """Test validation fails for non-existent mission."""
        with patch("config.get_valid_missions", return_value=["ai-news"]):
            valid, error = validate_mission("nonexistent", str(tmp_path))
            assert valid is False
            assert "Unknown mission" in error
            assert "nonexistent" in error

    def test_validate_mission_missing_files(self, tmp_path):
        """Test validation fails when required files are missing."""
        mission_dir = tmp_path / "ai-news"
        mission_dir.mkdir()
        (mission_dir / "mission.md").touch()
        # Missing other required files

        with patch("config.get_valid_missions", return_value=["ai-news"]):
            valid, error = validate_mission("ai-news", str(tmp_path))
            assert valid is False
            assert "Missing mission file" in error

    def test_validate_mission_success(self, tmp_path):
        """Test validation succeeds for valid mission."""
        mission_dir = tmp_path / "ai-news"
        mission_dir.mkdir()
        (mission_dir / "mission.md").touch()
        (mission_dir / "selection-rules.md").touch()
        (mission_dir / "editorial-guide.md").touch()
        (mission_dir / "output-schema.md").touch()

        with patch("config.get_valid_missions", return_value=["ai-news"]):
            valid, error = validate_mission("ai-news", str(tmp_path))
            assert valid is True
            assert error is None


class TestValidateWeeklyMission:
    """Tests for validate_weekly_mission function."""

    def test_validate_weekly_mission_not_found(self, tmp_path):
        """Test weekly validation fails for non-existent mission."""
        with patch("config.get_valid_missions", return_value=["ai-news"]):
            valid, error = validate_weekly_mission("nonexistent", str(tmp_path))
            assert valid is False
            assert "Unknown mission" in error

    def test_validate_weekly_mission_missing_weekly_dir(self, tmp_path):
        """Test validation fails when weekly directory is missing."""
        mission_dir = tmp_path / "ai-news"
        mission_dir.mkdir()

        with patch("config.get_valid_missions", return_value=["ai-news"]):
            valid, error = validate_weekly_mission("ai-news", str(tmp_path))
            assert valid is False
            assert "Missing weekly mission file" in error

    def test_validate_weekly_mission_success(self, tmp_path):
        """Test validation succeeds for valid weekly mission."""
        weekly_dir = tmp_path / "ai-news" / "weekly"
        weekly_dir.mkdir(parents=True)
        (weekly_dir / "mission.md").touch()
        (weekly_dir / "analysis-rules.md").touch()
        (weekly_dir / "output-schema.md").touch()

        with patch("config.get_valid_missions", return_value=["ai-news"]):
            valid, error = validate_weekly_mission("ai-news", str(tmp_path))
            assert valid is True
            assert error is None


class TestBuildAllowedTools:
    """Tests for build_allowed_tools function."""

    def test_build_allowed_tools_includes_base_tools(self):
        """Test that base tools are always included."""
        with patch("config.get_mcp_tool_names", return_value=[]):
            tools_str = build_allowed_tools()
            tools = tools_str.split(",")

            for base_tool in BASE_TOOLS:
                assert base_tool in tools

    def test_build_allowed_tools_includes_mcp_tools(self):
        """Test that MCP tools are included."""
        mock_mcp_tools = [
            f"mcp__{MCP_SERVER_NAME}__submit_digest",
            f"mcp__{MCP_SERVER_NAME}__check_urls",
        ]

        with patch("config.get_mcp_tool_names", return_value=mock_mcp_tools):
            tools_str = build_allowed_tools()
            tools = tools_str.split(",")

            for mcp_tool in mock_mcp_tools:
                assert mcp_tool in tools

    def test_build_allowed_tools_format(self):
        """Test that tools are comma-separated."""
        with patch("config.get_mcp_tool_names", return_value=["mcp__test__tool"]):
            tools_str = build_allowed_tools()

            assert "," in tools_str
            assert tools_str.count(",") >= len(BASE_TOOLS)


class TestGetMcpToolNames:
    """Tests for get_mcp_tool_names function."""

    def test_get_mcp_tool_names_import_error(self):
        """Test graceful handling when MCP server can't be imported."""
        # Mock the import to raise ImportError
        with patch.dict("sys.modules", {"mcp_tools.server": None}):
            with patch("config.get_mcp_tool_names") as mock_get:
                mock_get.return_value = []
                tools = mock_get()
                assert tools == []

    def test_get_mcp_tool_names_success(self):
        """Test successful retrieval of MCP tool names."""
        # Mock the MCP server structure
        mock_mcp = MagicMock()
        mock_tool_manager = MagicMock()
        mock_tool_manager._tools = {
            "submit_digest": MagicMock(),
            "check_urls": MagicMock(),
        }
        mock_mcp._tool_manager = mock_tool_manager

        with patch("mcp_tools.server.mcp", mock_mcp):
            tools = get_mcp_tool_names()

            expected_tools = [
                f"mcp__{MCP_SERVER_NAME}__submit_digest",
                f"mcp__{MCP_SERVER_NAME}__check_urls",
            ]
            assert set(tools) == set(expected_tools)


class TestSettings:
    """Tests for Settings class."""

    def test_settings_defaults(self):
        """Test that Settings has correct default values."""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()

            assert settings.claude_model == "sonnet"
            assert settings.claude_timeout == 600
            assert settings.retry_count == 1
            assert settings.logs_path == "/app/logs"
            assert settings.missions_path == "/app/.claude/missions"
            assert settings.data_path == "/app/data"
            assert settings.digests_path == "/app/logs/digests"
            assert settings.log_level == "info"

    def test_settings_environment_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(
            "os.environ",
            {
                "CLAUDE_claude_model": "opus",
                "CLAUDE_claude_timeout": "1200",
                "CLAUDE_log_level": "debug",
            },
        ):
            settings = Settings()

            assert settings.claude_model == "opus"
            assert settings.claude_timeout == 1200
            assert settings.log_level == "debug"

    def test_settings_database_url(self):
        """Test database_url uses DATABASE_URL without prefix."""
        with patch.dict(
            "os.environ",
            {"DATABASE_URL": "postgresql://user:pass@localhost/db"},
        ):
            settings = Settings()
            assert settings.database_url == "postgresql://user:pass@localhost/db"

    def test_settings_allowed_tools_property(self):
        """Test that allowed_tools property calls build_allowed_tools."""
        with patch("config.build_allowed_tools", return_value="Read,Write,WebSearch"):
            settings = Settings()
            assert settings.allowed_tools == "Read,Write,WebSearch"
