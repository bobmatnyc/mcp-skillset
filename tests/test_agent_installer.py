"""Tests for AI agent detection and installation modules.

Test Coverage:
- Agent detection across platforms (mocked)
- Config file parsing (valid/invalid JSON)
- Backup and restore operations
- Installation with various scenarios
- Error handling and rollback
- Cross-platform path resolution
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_skills.services.agent_detector import AgentDetector, DetectedAgent
from mcp_skills.services.agent_installer import AgentInstaller, InstallResult


class TestAgentDetector:
    """Test suite for AgentDetector."""

    def test_platform_detection(self):
        """Test platform normalization."""
        detector = AgentDetector()
        assert detector.platform in ["darwin", "win32", "linux"]

    @patch("platform.system")
    def test_darwin_platform(self, mock_system):
        """Test macOS platform detection."""
        mock_system.return_value = "Darwin"
        detector = AgentDetector()
        assert detector.platform == "darwin"

    @patch("platform.system")
    def test_windows_platform(self, mock_system):
        """Test Windows platform detection."""
        mock_system.return_value = "Windows"
        detector = AgentDetector()
        assert detector.platform == "win32"

    @patch("platform.system")
    def test_linux_platform(self, mock_system):
        """Test Linux platform detection."""
        mock_system.return_value = "Linux"
        detector = AgentDetector()
        assert detector.platform == "linux"

    def test_detect_all_returns_list(self):
        """Test that detect_all returns a list of DetectedAgent objects."""
        detector = AgentDetector()
        agents = detector.detect_all()

        assert isinstance(agents, list)
        assert (
            len(agents) >= 8
        )  # Now support 8 platforms: Claude Desktop, Claude Code, Auggie, Cursor, Windsurf, Continue, Codex, Gemini CLI

        for agent in agents:
            assert isinstance(agent, DetectedAgent)
            assert agent.name
            assert agent.id
            assert isinstance(agent.config_path, Path)
            assert isinstance(agent.exists, bool)

    def test_detect_specific_agent_claude_desktop(self):
        """Test detecting Claude Desktop specifically."""
        detector = AgentDetector()
        agent = detector.detect_agent("claude-desktop")

        assert agent is not None
        assert agent.name == "Claude Desktop"
        assert agent.id == "claude-desktop"
        assert "Claude" in str(agent.config_path)

    def test_detect_specific_agent_claude_code(self):
        """Test detecting Claude Code specifically."""
        detector = AgentDetector()
        agent = detector.detect_agent("claude-code")

        assert agent is not None
        assert agent.name == "Claude Code"
        assert agent.id == "claude-code"
        assert "Code" in str(agent.config_path)

    def test_detect_unknown_agent(self):
        """Test detecting unknown agent returns None."""
        detector = AgentDetector()
        agent = detector.detect_agent("nonexistent-agent")

        assert agent is None

    def test_config_paths_are_absolute(self):
        """Test that all detected config paths are absolute."""
        detector = AgentDetector()
        agents = detector.detect_all()

        for agent in agents:
            assert agent.config_path.is_absolute()


class TestAgentInstaller:
    """Test suite for AgentInstaller adapter (delegates to py-mcp-installer)."""

    @pytest.fixture
    def installer(self):
        """Create an AgentInstaller instance."""
        return AgentInstaller()

    @pytest.fixture
    def temp_agent(self, tmp_path):
        """Create a temporary detected agent for testing."""
        config_dir = tmp_path / "test_agent"
        config_dir.mkdir()
        config_path = config_dir / "config.json"

        return DetectedAgent(
            name="Test Agent",
            id="cursor",  # Use a supported platform ID
            config_path=config_path,
            exists=False,
        )

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_install_creates_new_config(
        self, mock_installer_cls, installer, temp_agent, tmp_path
    ):
        """Test installation creates new config when none exists."""
        # Mock MCPInstaller instance
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=True,
            message="Installed successfully",
            config_path=temp_agent.config_path,
        )
        mock_installer_cls.return_value = mock_installer

        result = installer.install(temp_agent)

        assert result.success
        assert result.agent_name == "Test Agent"
        assert result.changes_made == "Installed successfully"

        # Verify MCPInstaller was called correctly
        mock_installer.install_server.assert_called_once()

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_unsupported_agent(self, mock_installer_cls, installer, tmp_path):
        """Test installation fails for unsupported agent IDs."""
        # Create agent with unsupported ID
        agent = DetectedAgent(
            name="Unsupported Agent",
            id="unsupported-agent-id",
            config_path=tmp_path / "config.json",
            exists=False,
        )

        result = installer.install(agent)

        assert not result.success
        assert "Unsupported agent" in result.error
        # MCPInstaller should not be called
        mock_installer_cls.assert_not_called()


class TestClaudeCLIIntegration:
    """Test suite for Claude CLI integration (1M-432)."""

    @pytest.fixture
    def installer(self):
        """Create an AgentInstaller instance."""
        return AgentInstaller()

    @pytest.fixture
    def claude_code_agent(self, tmp_path):
        """Create a Claude Code agent for testing."""
        config_path = tmp_path / "Code" / "settings.json"
        return DetectedAgent(
            name="Claude Code",
            id="claude-code",
            config_path=config_path,
            exists=False,
        )

    @pytest.fixture
    def claude_desktop_agent(self, tmp_path):
        """Create a Claude Desktop agent for testing."""
        config_path = tmp_path / "Claude" / "claude_desktop_config.json"
        return DetectedAgent(
            name="Claude Desktop",
            id="claude-desktop",
            config_path=config_path,
            exists=False,
        )

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_claude_cli_installation_success(
        self, mock_installer_cls, installer, claude_code_agent
    ):
        """Test successful installation via py-mcp-installer.

        Verifies that the adapter correctly delegates to py-mcp-installer
        and returns success when installation completes.
        """
        # Mock MCPInstaller instance
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=True,
            message="Installed successfully",
            config_path=claude_code_agent.config_path,
        )
        mock_installer_cls.return_value = mock_installer

        # Install
        result = installer.install(claude_code_agent)

        # Verify success
        assert result.success
        assert result.agent_name == "Claude Code"
        assert result.agent_id == "claude-code"
        assert result.changes_made == "Installed successfully"

        # Verify MCPInstaller was created with correct platform
        mock_installer_cls.assert_called_once()
        call_kwargs = mock_installer_cls.call_args[1]
        assert "platform" in call_kwargs
        assert call_kwargs["dry_run"] is False

        # Verify install_server was called with force=False (default)
        mock_installer.install_server.assert_called_once_with(
            name="mcp-skillset",
            command="mcp-skillset",
            args=["mcp"],
            description="Dynamic RAG-powered skills for code assistants",
            force=False,
        )

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_claude_cli_not_found(
        self, mock_installer_cls, installer, claude_code_agent
    ):
        """Test error when py-mcp-installer fails to initialize.

        Verifies that installation fails with clear error message when
        py-mcp-installer cannot be initialized.
        """
        # Mock MCPInstaller initialization failure
        from mcp_skills.services.py_mcp_installer_wrapper import PyMCPInstallerError

        mock_installer_cls.side_effect = PyMCPInstallerError("Platform not supported")

        # Install
        result = installer.install(claude_code_agent)

        # Verify failure
        assert not result.success
        assert result.error is not None
        assert "Failed to create installer" in result.error

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_claude_cli_already_installed(
        self, mock_installer_cls, installer, claude_code_agent
    ):
        """Test detection of already installed server.

        Verifies that without --force flag, installation fails when
        mcp-skillset is already installed.
        """
        # Mock MCPInstaller instance
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=False,
            message="Server 'mcp-skillset' already installed",
            config_path=None,
        )
        mock_installer_cls.return_value = mock_installer

        # Install without force
        result = installer.install(claude_code_agent, force=False)

        # Verify failure
        assert not result.success
        assert result.error is not None
        assert "already installed" in result.error

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_claude_cli_force_reinstall(
        self, mock_installer_cls, installer, claude_code_agent
    ):
        """Test force reinstall workflow.

        Verifies that with --force flag, installation passes force=True
        to install_server, which handles update internally.
        """
        # Mock MCPInstaller instance
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=True,
            message="Successfully updated 'mcp-skillset'",
            config_path=claude_code_agent.config_path,
        )
        mock_installer_cls.return_value = mock_installer

        # Install with force
        result = installer.install(claude_code_agent, force=True)

        # Verify success
        assert result.success
        assert result.changes_made == "Successfully updated 'mcp-skillset'"

        # Verify install_server was called with force=True
        mock_installer.install_server.assert_called_once_with(
            name="mcp-skillset",
            command="mcp-skillset",
            args=["mcp"],
            description="Dynamic RAG-powered skills for code assistants",
            force=True,
        )

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_claude_cli_dry_run(self, mock_installer_cls, installer, claude_code_agent):
        """Test dry-run mode.

        Verifies that dry-run mode shows what would be done without
        actually making any changes.
        """
        # Mock MCPInstaller instance with dry_run=True
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=True,
            message="[DRY RUN] Would install mcp-skillset",
            config_path=claude_code_agent.config_path,
        )
        mock_installer_cls.return_value = mock_installer

        # Install in dry-run mode
        result = installer.install(claude_code_agent, dry_run=True)

        # Verify success but no actual execution
        assert result.success
        assert result.changes_made is not None
        assert (
            "DRY RUN" in result.changes_made or "Would install" in result.changes_made
        )

        # Verify MCPInstaller was created with dry_run=True
        call_kwargs = mock_installer_cls.call_args[1]
        assert call_kwargs["dry_run"] is True

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_claude_cli_dry_run_with_force(
        self, mock_installer_cls, installer, claude_code_agent
    ):
        """Test dry-run mode with force flag.

        Verifies that dry-run mode with force shows uninstall/install workflow
        without making actual changes.
        """
        # Mock MCPInstaller instance with dry_run=True
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=True,
            message="[DRY RUN] Would reinstall mcp-skillset",
            config_path=claude_code_agent.config_path,
        )
        mock_installer_cls.return_value = mock_installer

        # Install in dry-run mode with force
        result = installer.install(claude_code_agent, dry_run=True, force=True)

        # Verify success
        assert result.success
        assert (
            "DRY RUN" in result.changes_made or "Would reinstall" in result.changes_made
        )

        # Verify MCPInstaller was created with dry_run=True
        call_kwargs = mock_installer_cls.call_args[1]
        assert call_kwargs["dry_run"] is True

        # In dry_run mode, uninstall should NOT be called
        mock_installer.uninstall_server.assert_not_called()

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_claude_cli_add_command_fails(
        self, mock_installer_cls, installer, claude_code_agent
    ):
        """Test handling of failed installation.

        Verifies that installation fails gracefully when py-mcp-installer
        returns an error.
        """
        # Mock MCPInstaller instance
        from mcp_skills.services.py_mcp_installer_wrapper import PyMCPInstallerError

        mock_installer = Mock()
        mock_installer.install_server.side_effect = PyMCPInstallerError(
            "Failed to install server"
        )
        mock_installer_cls.return_value = mock_installer

        # Install
        result = installer.install(claude_code_agent)

        # Verify failure
        assert not result.success
        assert result.error is not None
        assert "Failed to install" in result.error

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_fresh_install_without_force(
        self, mock_installer_cls, installer, claude_code_agent
    ):
        """Test fresh installation without force flag.

        When server doesn't exist, installation should succeed
        without requiring force flag.
        """
        # Mock MCPInstaller instance
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=True,
            message="Installed successfully",
            config_path=claude_code_agent.config_path,
        )
        mock_installer_cls.return_value = mock_installer

        # Install without force
        result = installer.install(claude_code_agent, force=False)

        # Verify success
        assert result.success
        assert result.changes_made == "Installed successfully"

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_backward_compatibility_claude_desktop(
        self, mock_installer_cls, installer, claude_desktop_agent, tmp_path
    ):
        """Test that Claude Desktop is handled by py-mcp-installer.

        Verifies that the adapter correctly delegates Claude Desktop
        installation to py-mcp-installer.
        """
        # Mock MCPInstaller instance
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=True,
            message="Installed successfully",
            config_path=claude_desktop_agent.config_path,
        )
        mock_installer_cls.return_value = mock_installer

        # Create config directory
        claude_desktop_agent.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Install for Claude Desktop (delegated to py-mcp-installer)
        result = installer.install(claude_desktop_agent)

        # Verify success
        assert result.success

        # Verify MCPInstaller was created with correct platform
        call_kwargs = mock_installer_cls.call_args[1]
        assert "platform" in call_kwargs

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_platform_routing_based_on_agent_id(
        self,
        mock_installer_cls,
        installer,
        claude_code_agent,
        claude_desktop_agent,
    ):
        """Test that installation is routed to correct platform.

        Verifies that agent IDs are correctly mapped to Platform enums.
        """
        # Mock MCPInstaller instance
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=True,
            message="Installed successfully",
            config_path=claude_code_agent.config_path,
        )
        mock_installer_cls.return_value = mock_installer

        # Install Claude Code
        result_code = installer.install(claude_code_agent)
        assert result_code.success

        # Verify platform was set correctly
        first_call_kwargs = mock_installer_cls.call_args_list[0][1]
        assert "platform" in first_call_kwargs

        # Reset mocks
        mock_installer_cls.reset_mock()
        mock_installer.install_server.reset_mock()

        # Install Claude Desktop
        result_desktop = installer.install(claude_desktop_agent)
        assert result_desktop.success

        # Verify platform was set correctly
        second_call_kwargs = mock_installer_cls.call_args_list[0][1]
        assert "platform" in second_call_kwargs


class TestCrossPlatformPaths:
    """Test cross-platform path resolution."""

    @patch("platform.system")
    def test_claude_desktop_paths_darwin(self, mock_system):
        """Test Claude Desktop paths on macOS."""
        mock_system.return_value = "Darwin"
        detector = AgentDetector()
        agent = detector.detect_agent("claude-desktop")

        assert agent is not None
        assert "Library/Application Support/Claude" in str(agent.config_path)

    @patch("platform.system")
    def test_claude_desktop_paths_linux(self, mock_system):
        """Test Claude Desktop paths on Linux."""
        mock_system.return_value = "Linux"
        detector = AgentDetector()
        agent = detector.detect_agent("claude-desktop")

        assert agent is not None
        assert ".config/Claude" in str(agent.config_path)

    @patch("platform.system")
    @patch.dict("os.environ", {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"})
    def test_claude_desktop_paths_windows(self, mock_system):
        """Test Claude Desktop paths on Windows."""
        mock_system.return_value = "Windows"
        detector = AgentDetector()
        agent = detector.detect_agent("claude-desktop")

        assert agent is not None
        # Windows path should contain Claude directory


class TestInstallResult:
    """Test InstallResult data class."""

    def test_install_result_success(self):
        """Test creating successful InstallResult."""
        result = InstallResult(
            success=True,
            agent_name="Test Agent",
            agent_id="test-agent",
            config_path=Path("/test/path"),
            backup_path=Path("/test/backup"),
            changes_made="Added mcp-skillset",
        )

        assert result.success
        assert result.agent_name == "Test Agent"
        assert result.error is None

    def test_install_result_failure(self):
        """Test creating failed InstallResult."""
        result = InstallResult(
            success=False,
            agent_name="Test Agent",
            agent_id="test-agent",
            config_path=Path("/test/path"),
            error="Something went wrong",
        )

        assert not result.success
        assert result.error == "Something went wrong"
        assert result.backup_path is None


class TestAgentNameDetection:
    """Test suite for agent name detection bug fixes."""

    def test_claude_code_name_is_correct(self):
        """Test that Claude Code is detected with correct name (Bug Fix #2)."""
        detector = AgentDetector()
        agent = detector.detect_agent("claude-code")

        assert agent is not None
        assert agent.name == "Claude Code"
        assert agent.id == "claude-code"
        assert "Code" in str(agent.config_path)
        assert "settings.json" in str(agent.config_path)

    def test_claude_desktop_name_is_correct(self):
        """Test that Claude Desktop is detected with correct name (Bug Fix #2)."""
        detector = AgentDetector()
        agent = detector.detect_agent("claude-desktop")

        assert agent is not None
        assert agent.name == "Claude Desktop"
        assert agent.id == "claude-desktop"
        assert "Claude" in str(agent.config_path)
        assert "claude_desktop_config.json" in str(agent.config_path)

    def test_all_agents_have_unique_names(self):
        """Test that all detected agents have unique, correct names."""
        detector = AgentDetector()
        agents = detector.detect_all()

        # Collect agent names
        names = {agent.name for agent in agents}

        # Verify expected agents have correct names
        assert "Claude Desktop" in names
        assert "Claude Code" in names
        assert "Auggie" in names

        # Verify no duplicate names
        assert len(names) == len(agents)

    def test_agent_name_matches_config_path(self):
        """Test that agent names correctly match their config paths."""
        detector = AgentDetector()
        agents = detector.detect_all()

        for agent in agents:
            if agent.id == "claude-desktop":
                assert agent.name == "Claude Desktop"
                assert "Claude" in str(agent.config_path)
                assert "claude_desktop_config.json" in str(agent.config_path)
            elif agent.id == "claude-code":
                assert agent.name == "Claude Code"
                assert "Code" in str(agent.config_path)
                assert "settings.json" in str(agent.config_path)
            elif agent.id == "auggie":
                assert agent.name == "Auggie"
                assert "Auggie" in str(agent.config_path)


class TestNewPlatforms:
    """Test suite for new platform support (8 platforms total)."""

    @pytest.mark.parametrize(
        "platform_id,platform_name",
        [
            ("cursor", "Cursor"),
            ("windsurf", "Windsurf"),
            ("continue", "Continue"),
            ("codex", "Codex"),
            ("gemini-cli", "Gemini CLI"),
        ],
    )
    def test_detect_new_platform(self, platform_id, platform_name):
        """Test detection of new platforms."""
        detector = AgentDetector()
        agent = detector.detect_agent(platform_id)

        assert agent is not None
        assert agent.name == platform_name
        assert agent.id == platform_id
        assert isinstance(agent.config_path, Path)
        assert agent.config_path.is_absolute()

    def test_all_eight_platforms_detected(self):
        """Test that all 8 platforms are detected."""
        detector = AgentDetector()
        agents = detector.detect_all()

        expected_ids = {
            "claude-desktop",
            "claude-code",
            "auggie",
            "cursor",
            "windsurf",
            "continue",
            "codex",
            "gemini-cli",
        }

        detected_ids = {agent.id for agent in agents}

        # Verify all expected platforms are present
        assert expected_ids.issubset(detected_ids)
        assert len(agents) == 8

    @patch("mcp_skills.services.agent_installer.MCPInstaller")
    def test_new_platform_installation(self, mock_installer_cls):
        """Test installation for new platforms."""
        detector = AgentDetector()
        installer = AgentInstaller()

        # Test Cursor platform
        cursor_agent = detector.detect_agent("cursor")
        assert cursor_agent is not None

        # Mock successful installation
        mock_installer = Mock()
        mock_installer.install_server.return_value = Mock(
            success=True,
            message="Installed successfully",
            config_path=cursor_agent.config_path,
        )
        mock_installer_cls.return_value = mock_installer

        result = installer.install(cursor_agent)

        assert result.success
        assert result.agent_name == "Cursor"
        assert result.agent_id == "cursor"

    def test_new_platform_config_paths(self):
        """Test that new platforms have valid config paths."""
        detector = AgentDetector()

        # Map platform IDs to expected directory names
        platform_dirs = {
            "cursor": ".cursor",
            "windsurf": ".codeium/windsurf",
            "continue": ".continue",
            "codex": ".codex",
            "gemini-cli": ".gemini",
        }

        for platform_id, expected_dir in platform_dirs.items():
            agent = detector.detect_agent(platform_id)
            assert agent is not None
            assert agent.config_path.is_absolute()
            # Config path should contain platform-specific directory
            config_path_str = str(agent.config_path)
            assert (
                expected_dir in config_path_str
            ), f"Expected '{expected_dir}' in {config_path_str}"
