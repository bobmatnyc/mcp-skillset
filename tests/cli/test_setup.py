"""Tests for setup command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

from click.testing import CliRunner

from mcp_skills.cli.main import cli


if TYPE_CHECKING:
    from mcp_skills.models.toolchain import ToolchainInfo


class TestSetupCommand:
    """Test suite for setup command."""

    def test_setup_help(self, cli_runner: CliRunner) -> None:
        """Test setup command help."""
        result = cli_runner.invoke(cli, ["setup", "--help"])

        assert result.exit_code == 0
        assert "Auto-configure mcp-skillset for your project" in result.output
        assert "--project-dir" in result.output
        assert "--config" in result.output
        assert "--auto" in result.output

    @patch("mcp_skills.cli.main.ToolchainDetector")
    @patch("mcp_skills.cli.main.RepositoryManager")
    @patch("mcp_skills.cli.main.SkillManager")
    @patch("mcp_skills.cli.main.IndexingEngine")
    @patch("mcp_skills.cli.main.AgentDetector")
    @patch("mcp_skills.cli.main.AgentInstaller")
    def test_setup_auto_mode(
        self,
        mock_installer_cls: Mock,
        mock_detector_cls: Mock,
        mock_engine_cls: Mock,
        mock_skill_manager_cls: Mock,
        mock_repo_cls: Mock,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info: ToolchainInfo,
        tmp_path: Path,
    ) -> None:
        """Test setup command in auto mode."""
        # Setup mocks
        mock_toolchain = Mock()
        mock_toolchain.detect.return_value = mock_toolchain_info
        mock_toolchain_cls.return_value = mock_toolchain

        mock_repo_manager = Mock()
        mock_repo_manager.DEFAULT_REPOS = []
        mock_repo_manager.add_repository.return_value = None
        mock_repo_manager.list_repositories.return_value = []  # Return list, not Mock
        mock_repo_cls.return_value = mock_repo_manager

        # Setup SkillManager mock to return empty list
        mock_skill_manager = Mock()
        mock_skill_manager.discover_skills.return_value = []
        mock_skill_manager_cls.return_value = mock_skill_manager

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = Mock(
            total_skills=5,
            vector_store_size=50000,
            graph_nodes=10,
            graph_edges=15,
        )
        mock_engine_cls.return_value = mock_engine

        mock_detector = Mock()
        mock_detector.detect_all.return_value = []  # No agents detected
        mock_detector_cls.return_value = mock_detector

        mock_installer = Mock()
        mock_installer_cls.return_value = mock_installer

        # Run command
        config_path = tmp_path / "config.yaml"
        result = cli_runner.invoke(
            cli,
            [
                "setup",
                "--project-dir",
                str(tmp_path),
                "--config",
                str(config_path),
                "--auto",
            ],
        )

        # Verify
        assert result.exit_code == 0
        assert "Starting mcp-skillset setup" in result.output
        assert "Detecting project toolchain" in result.output
        assert "Python" in result.output

    @patch("mcp_skills.cli.main.ToolchainDetector")
    def test_setup_toolchain_detection_failure(
        self,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """Test setup command when toolchain detection fails."""
        # Setup mock to raise exception
        mock_toolchain = Mock()
        mock_toolchain.detect.side_effect = Exception("Detection failed")
        mock_toolchain_cls.return_value = mock_toolchain

        # Run command
        result = cli_runner.invoke(
            cli,
            ["setup", "--project-dir", str(tmp_path), "--auto"],
        )

        # Verify error handling
        assert result.exit_code != 0
        assert "Setup failed" in result.output or "Detection failed" in result.output

    @patch("mcp_skills.cli.main.ToolchainDetector")
    @patch("mcp_skills.cli.main.RepositoryManager")
    @patch("mcp_skills.cli.main.SkillManager")
    @patch("mcp_skills.cli.main.IndexingEngine")
    @patch("mcp_skills.cli.main.AgentDetector")
    def test_setup_with_custom_config_path(
        self,
        mock_detector_cls: Mock,
        mock_engine_cls: Mock,
        mock_skill_manager_cls: Mock,
        mock_repo_cls: Mock,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info: ToolchainInfo,
        tmp_path: Path,
    ) -> None:
        """Test setup command with custom config path."""
        # Setup mocks
        mock_toolchain = Mock()
        mock_toolchain.detect.return_value = mock_toolchain_info
        mock_toolchain_cls.return_value = mock_toolchain

        mock_repo_manager = Mock()
        mock_repo_manager.DEFAULT_REPOS = []
        mock_repo_manager.list_repositories.return_value = []
        mock_repo_cls.return_value = mock_repo_manager

        mock_skill_manager = Mock()
        mock_skill_manager.discover_skills.return_value = []
        mock_skill_manager_cls.return_value = mock_skill_manager

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = Mock(
            total_skills=0,
            vector_store_size=0,
            graph_nodes=0,
            graph_edges=0,
        )
        mock_engine_cls.return_value = mock_engine

        mock_detector = Mock()
        mock_detector.detect_all.return_value = []
        mock_detector_cls.return_value = mock_detector

        # Run command with custom config path
        custom_config = tmp_path / "custom" / "config.yaml"
        result = cli_runner.invoke(
            cli,
            [
                "setup",
                "--project-dir",
                str(tmp_path),
                "--config",
                str(custom_config),
                "--auto",
            ],
        )

        # Verify custom path is used
        assert str(custom_config) in result.output or result.exit_code == 0

    @patch("mcp_skills.cli.main.ToolchainDetector")
    @patch("mcp_skills.cli.main.RepositoryManager")
    @patch("mcp_skills.cli.main.SkillManager")
    @patch("mcp_skills.cli.main.IndexingEngine")
    @patch("mcp_skills.cli.main.AgentDetector")
    def test_setup_with_repository_cloning(
        self,
        mock_detector_cls: Mock,
        mock_engine_cls: Mock,
        mock_skill_manager_cls: Mock,
        mock_repo_cls: Mock,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info: ToolchainInfo,
        tmp_path: Path,
    ) -> None:
        """Test setup command includes repository cloning."""
        # Setup mocks
        mock_toolchain = Mock()
        mock_toolchain.detect.return_value = mock_toolchain_info
        mock_toolchain_cls.return_value = mock_toolchain

        mock_repo_manager = Mock()
        mock_repo_manager.DEFAULT_REPOS = [
            {
                "url": "https://github.com/example/skills.git",
                "priority": 1,
                "license": "MIT",
            }
        ]
        mock_repo_manager.add_repository.return_value = None
        mock_repo_manager.list_repositories.return_value = []
        mock_repo_cls.return_value = mock_repo_manager

        mock_skill_manager = Mock()
        mock_skill_manager.discover_skills.return_value = []
        mock_skill_manager_cls.return_value = mock_skill_manager

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = Mock(
            total_skills=0,
            vector_store_size=0,
            graph_nodes=0,
            graph_edges=0,
        )
        mock_engine_cls.return_value = mock_engine

        mock_detector = Mock()
        mock_detector.detect_all.return_value = []
        mock_detector_cls.return_value = mock_detector

        # Run command
        result = cli_runner.invoke(
            cli,
            ["setup", "--project-dir", str(tmp_path), "--auto"],
        )

        # Verify repository setup step is included
        assert result.exit_code == 0
        assert "Setting up skill repositories" in result.output

    def test_setup_invalid_project_dir(self, cli_runner: CliRunner) -> None:
        """Test setup command with invalid project directory."""
        result = cli_runner.invoke(
            cli,
            ["setup", "--project-dir", "/nonexistent/path", "--auto"],
        )

        # Should fail with path error
        assert result.exit_code != 0

    @patch("mcp_skills.cli.main.ToolchainDetector")
    @patch("mcp_skills.cli.main.RepositoryManager")
    @patch("mcp_skills.cli.main.SkillManager")
    @patch("mcp_skills.cli.main.IndexingEngine")
    @patch("mcp_skills.cli.main.AgentDetector")
    def test_setup_indexing_step(
        self,
        mock_detector_cls: Mock,
        mock_engine_cls: Mock,
        mock_skill_manager_cls: Mock,
        mock_repo_cls: Mock,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info: ToolchainInfo,
        tmp_path: Path,
    ) -> None:
        """Test setup command includes indexing step."""
        # Setup mocks
        mock_toolchain = Mock()
        mock_toolchain.detect.return_value = mock_toolchain_info
        mock_toolchain_cls.return_value = mock_toolchain

        mock_repo_manager = Mock()
        mock_repo_manager.DEFAULT_REPOS = []
        mock_repo_manager.list_repositories.return_value = []
        mock_repo_cls.return_value = mock_repo_manager

        mock_skill_manager = Mock()
        mock_skill_manager.discover_skills.return_value = []
        mock_skill_manager_cls.return_value = mock_skill_manager

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = Mock(
            total_skills=10,
            vector_store_size=100000,
            graph_nodes=20,
            graph_edges=30,
        )
        mock_engine_cls.return_value = mock_engine

        mock_detector = Mock()
        mock_detector.detect_all.return_value = []
        mock_detector_cls.return_value = mock_detector

        # Run command
        result = cli_runner.invoke(
            cli,
            ["setup", "--project-dir", str(tmp_path), "--auto"],
        )

        # Verify indexing step
        assert result.exit_code == 0
        assert "Indexing skills" in result.output or "indexed" in result.output.lower()

    @patch("mcp_skills.cli.main.ToolchainDetector")
    @patch("mcp_skills.cli.main.RepositoryManager")
    @patch("mcp_skills.cli.main.SkillManager")
    @patch("mcp_skills.cli.main.IndexingEngine")
    @patch("mcp_skills.cli.main.AgentDetector")
    @patch("mcp_skills.cli.main.AgentInstaller")
    def test_setup_skip_agents(
        self,
        mock_installer_cls: Mock,
        mock_detector_cls: Mock,
        mock_engine_cls: Mock,
        mock_skill_manager_cls: Mock,
        mock_repo_cls: Mock,
        mock_toolchain_cls: Mock,
        cli_runner: CliRunner,
        mock_toolchain_info: ToolchainInfo,
        tmp_path: Path,
    ) -> None:
        """Test setup command with --skip-agents flag."""
        # Setup mocks
        mock_toolchain = Mock()
        mock_toolchain.detect.return_value = mock_toolchain_info
        mock_toolchain_cls.return_value = mock_toolchain

        mock_repo_manager = Mock()
        mock_repo_manager.DEFAULT_REPOS = []
        mock_repo_manager.list_repositories.return_value = []
        mock_repo_cls.return_value = mock_repo_manager

        mock_skill_manager = Mock()
        mock_skill_manager.discover_skills.return_value = []
        mock_skill_manager_cls.return_value = mock_skill_manager

        mock_engine = Mock()
        mock_engine.reindex_all.return_value = Mock(
            total_skills=5,
            vector_store_size=50000,
            graph_nodes=10,
            graph_edges=15,
        )
        mock_engine_cls.return_value = mock_engine

        # Agent detector should NOT be called when --skip-agents is used
        mock_detector = Mock()
        mock_detector_cls.return_value = mock_detector

        mock_installer = Mock()
        mock_installer_cls.return_value = mock_installer

        # Run command with --skip-agents
        result = cli_runner.invoke(
            cli,
            [
                "setup",
                "--project-dir",
                str(tmp_path),
                "--auto",
                "--skip-agents",
            ],
        )

        # Verify success
        assert result.exit_code == 0

        # Verify agent installation was skipped
        assert "Skipped agent installation" in result.output

        # Verify AgentDetector.detect_all() was NOT called
        mock_detector.detect_all.assert_not_called()

        # Verify AgentInstaller was NOT instantiated
        mock_installer_cls.assert_not_called()
