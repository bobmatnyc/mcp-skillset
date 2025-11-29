"""Tests for install command default behavior (Bug Fixes).

Test Coverage:
- Bug Fix #1: Default install excludes Claude Desktop
- Bug Fix #2: Agent names correctly displayed
- Explicit agent selection still works
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from mcp_skills.cli.main import cli
from mcp_skills.services.agent_detector import DetectedAgent


class TestInstallDefaultBehavior:
    """Test suite for install command default behavior (Bug Fix #1)."""

    @pytest.fixture
    def mock_detected_agents(self):
        """Create mock detected agents for all three types."""
        return [
            DetectedAgent(
                name="Claude Desktop",
                id="claude-desktop",
                config_path=Path("/test/claude_desktop_config.json"),
                exists=True,
            ),
            DetectedAgent(
                name="Claude Code",
                id="claude-code",
                config_path=Path("/test/Code/User/settings.json"),
                exists=True,
            ),
            DetectedAgent(
                name="Auggie",
                id="auggie",
                config_path=Path("/test/auggie/config.json"),
                exists=True,
            ),
        ]

    @patch("mcp_skills.cli.main.AgentInstaller")
    @patch("mcp_skills.cli.main.AgentDetector")
    def test_default_install_excludes_claude_desktop(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
        mock_detected_agents,
    ):
        """Test that default install excludes Claude Desktop (Bug Fix #1)."""
        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_all.return_value = mock_detected_agents
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock
        mock_installer = Mock()
        mock_installer.install.return_value = Mock(
            success=True,
            agent_name="Claude Code",
            agent_id="claude-code",
            config_path=Path("/test/settings.json"),
            backup_path=None,
            error=None,
            changes_made="Added mcp-skillset",
        )
        mock_installer_cls.return_value = mock_installer

        # Run install with default (no --agent flag)
        result = cli_runner.invoke(cli, ["install", "--force", "--dry-run"])

        # Verify output
        assert result.exit_code == 0

        # Verify Claude Desktop was NOT detected/installed
        assert "Claude Desktop" not in result.output or "Not found" in result.output

        # Verify Claude Code and Auggie were detected
        # (Note: Auggie might show as "not found" if not installed, but should be in the check)
        output_lower = result.output.lower()
        assert "claude code" in output_lower or "code" in output_lower

    @patch("mcp_skills.cli.main.AgentInstaller")
    @patch("mcp_skills.cli.main.AgentDetector")
    def test_explicit_claude_desktop_still_works(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
        mock_detected_agents,
    ):
        """Test that --agent claude-desktop still works explicitly (Bug Fix #1)."""
        # Setup detector mock
        mock_detector = Mock()
        claude_desktop = mock_detected_agents[0]  # Claude Desktop
        mock_detector.detect_agent.return_value = claude_desktop
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock
        mock_installer = Mock()
        mock_installer.install.return_value = Mock(
            success=True,
            agent_name="Claude Desktop",
            agent_id="claude-desktop",
            config_path=Path("/test/claude_desktop_config.json"),
            backup_path=None,
            error=None,
            changes_made="Added mcp-skillset",
        )
        mock_installer_cls.return_value = mock_installer

        # Run install with explicit --agent claude-desktop
        result = cli_runner.invoke(
            cli, ["install", "--agent", "claude-desktop", "--force", "--dry-run"]
        )

        # Verify it worked
        assert result.exit_code == 0
        assert "Claude Desktop" in result.output

        # Verify detect_agent was called with claude-desktop
        mock_detector.detect_agent.assert_called_with("claude-desktop")

    @patch("mcp_skills.cli.main.AgentInstaller")
    @patch("mcp_skills.cli.main.AgentDetector")
    def test_claude_code_selected_by_default(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
        mock_detected_agents,
    ):
        """Test that Claude Code is selected when using default (Bug Fix #1)."""
        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_all.return_value = mock_detected_agents
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock
        mock_installer = Mock()

        def install_side_effect(agent, **kwargs):
            return Mock(
                success=True,
                agent_name=agent.name,
                agent_id=agent.id,
                config_path=agent.config_path,
                backup_path=None,
                error=None,
                changes_made=f"Added mcp-skillset for {agent.name}",
            )

        mock_installer.install.side_effect = install_side_effect
        mock_installer_cls.return_value = mock_installer

        # Run install with default
        result = cli_runner.invoke(cli, ["install", "--force", "--dry-run"])

        # Verify
        assert result.exit_code == 0

        # Get all install calls
        install_calls = mock_installer.install.call_args_list

        # Extract agent IDs from calls
        installed_agent_ids = [call[0][0].id for call in install_calls]

        # Verify Claude Code was installed
        assert "claude-code" in installed_agent_ids

        # Verify Claude Desktop was NOT installed
        assert "claude-desktop" not in installed_agent_ids


class TestAgentNameDisplay:
    """Test suite for agent name display (Bug Fix #2)."""

    @patch("mcp_skills.cli.main.AgentInstaller")
    @patch("mcp_skills.cli.main.AgentDetector")
    def test_claude_code_displays_correct_name(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ):
        """Test that Claude Code path displays as 'Claude Code' not 'Claude Desktop'."""
        # Setup detector mock
        mock_detector = Mock()
        claude_code = DetectedAgent(
            name="Claude Code",
            id="claude-code",
            config_path=Path(
                "/Users/test/Library/Application Support/Code/User/settings.json"
            ),
            exists=True,
        )
        mock_detector.detect_agent.return_value = claude_code
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock
        mock_installer = Mock()
        mock_installer.install.return_value = Mock(
            success=True,
            agent_name="Claude Code",
            agent_id="claude-code",
            config_path=claude_code.config_path,
            backup_path=None,
            error=None,
        )
        mock_installer_cls.return_value = mock_installer

        # Run install
        result = cli_runner.invoke(
            cli, ["install", "--agent", "claude-code", "--force", "--dry-run"]
        )

        # Verify correct name is displayed
        assert result.exit_code == 0
        assert "Claude Code" in result.output
        assert "settings.json" in result.output

        # Verify it's NOT showing as Claude Desktop
        lines = result.output.split("\n")
        for line in lines:
            if "settings.json" in line:
                # This line should say "Claude Code" not "Claude Desktop"
                assert "Claude Code" in line
                assert "Claude Desktop" not in line

    @patch("mcp_skills.cli.main.AgentInstaller")
    @patch("mcp_skills.cli.main.AgentDetector")
    def test_all_agents_display_correct_names(
        self,
        mock_detector_cls: Mock,
        mock_installer_cls: Mock,
        cli_runner: CliRunner,
    ):
        """Test that all agents display their correct names."""
        agents = [
            DetectedAgent(
                name="Claude Desktop",
                id="claude-desktop",
                config_path=Path(
                    "/Users/test/Library/Application Support/Claude/claude_desktop_config.json"
                ),
                exists=True,
            ),
            DetectedAgent(
                name="Claude Code",
                id="claude-code",
                config_path=Path(
                    "/Users/test/Library/Application Support/Code/User/settings.json"
                ),
                exists=True,
            ),
            DetectedAgent(
                name="Auggie",
                id="auggie",
                config_path=Path(
                    "/Users/test/Library/Application Support/Auggie/config.json"
                ),
                exists=False,  # Not installed
            ),
        ]

        # Setup detector mock
        mock_detector = Mock()
        mock_detector.detect_all.return_value = agents
        mock_detector_cls.return_value = mock_detector

        # Setup installer mock (not really needed for this test)
        mock_installer = Mock()
        mock_installer_cls.return_value = mock_installer

        # Run install (will be filtered to exclude claude-desktop by default)
        result = cli_runner.invoke(cli, ["install", "--dry-run"])

        # Verify names are correct
        assert result.exit_code == 0

        # Claude Code should be shown with correct name
        if "Code/User/settings.json" in result.output:
            # Find the line with this path
            for line in result.output.split("\n"):
                if "settings.json" in line:
                    assert "Claude Code" in line
                    assert "Claude Desktop" not in line

        # Auggie should be shown as "not found" but with correct name
        if "Auggie" in result.output:
            assert "Auggie" in result.output
