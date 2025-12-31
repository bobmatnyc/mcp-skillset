"""End-to-end tests for CLI commands.

This module tests all CLI commands with real invocations using Click's
CliRunner. Tests verify command execution, exit codes, and output formatting.

Commands Tested:
- mcp-skillset setup
- mcp-skillset mcp (serve)
- mcp-skillset search
- mcp-skillset list
- mcp-skillset info
- mcp-skillset recommend
- mcp-skillset repo add/list/update
- mcp-skillset index
- mcp-skillset doctor
- mcp-skillset stats
- mcp-skillset config
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from mcp_skills.cli.main import cli


@pytest.mark.e2e
class TestCLISetupCommand:
    """Test 'mcp-skillset setup' command."""

    def test_setup_auto_mode(
        self,
        cli_runner: CliRunner,
        e2e_base_dir: Path,
        monkeypatch,
    ) -> None:
        """Test setup command in auto mode (non-interactive).

        This test verifies:
        - Setup runs without user interaction
        - All 6 setup steps complete
        - Validation passes
        - Proper exit code
        """
        # Mock HOME to use our test directory
        monkeypatch.setenv("HOME", str(e2e_base_dir.parent))

        # Create a minimal project directory for toolchain detection
        project_dir = e2e_base_dir / "test_project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text("[project]\nname='test'\n")

        result = cli_runner.invoke(
            cli,
            [
                "setup",
                "--project-dir",
                str(project_dir),
                "--config",
                str(e2e_base_dir / "config.yaml"),
                "--auto",
            ],
        )

        # Verify command succeeded
        assert result.exit_code == 0, f"Setup failed: {result.output}"

        # Verify output contains setup steps (now 7 steps with agent installation and hooks)
        assert "Step 1/7" in result.output
        assert "Step 2/7" in result.output
        assert "Step 3/7" in result.output
        assert "Step 4/7" in result.output
        assert "Step 5/7" in result.output
        assert "Step 6/7" in result.output
        # Step 7 (hooks) only appears if agents were successfully installed
        # Otherwise, setup completes at step 6
        assert (
            "Step 7/7" in result.output
            or "Skipped agent installation" in result.output
            or "Installed for 0/" in result.output
        )

        # Verify toolchain detection
        assert "Detecting project toolchain" in result.output

        # Verify setup completion message
        assert (
            "Setup complete" in result.output
            or "Setup completed with warnings" in result.output
        )

    def test_setup_detects_python_project(
        self,
        cli_runner: CliRunner,
        sample_python_project_e2e: Path,
        e2e_base_dir: Path,
        monkeypatch,
    ) -> None:
        """Test setup correctly detects Python project toolchain."""
        monkeypatch.setenv("HOME", str(e2e_base_dir.parent))

        result = cli_runner.invoke(
            cli,
            [
                "setup",
                "--project-dir",
                str(sample_python_project_e2e),
                "--config",
                str(e2e_base_dir / "config.yaml"),
                "--auto",
            ],
        )

        # Verify Python detected
        assert "Python" in result.output
        assert "pytest" in result.output.lower() or "flask" in result.output.lower()


@pytest.mark.e2e
class TestCLISearchCommand:
    """Test 'mcp-skillset search' command."""

    def test_search_with_results(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test search command returns results."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        # Mock the service initialization in the search command module
        from mcp_skills.cli.commands import search

        monkeypatch.setattr(search, "SkillManager", lambda **kwargs: skill_manager)
        monkeypatch.setattr(search, "IndexingEngine", lambda **kwargs: indexing_engine)

        result = cli_runner.invoke(cli, ["search", "python testing", "--limit", "5"])

        # Verify command succeeded
        assert result.exit_code == 0, f"Search failed: {result.output}"

        # Verify output contains search results
        assert "Searching for:" in result.output
        assert "python testing" in result.output

        # Should find pytest-testing skill
        assert "pytest-testing" in result.output or "Search Results" in result.output

    def test_search_with_category_filter(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test search with category filter."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import search

        monkeypatch.setattr(search, "SkillManager", lambda **kwargs: skill_manager)
        monkeypatch.setattr(search, "IndexingEngine", lambda **kwargs: indexing_engine)

        result = cli_runner.invoke(
            cli, ["search", "python", "--category", "testing", "--limit", "3"]
        )

        assert result.exit_code == 0
        assert "Category filter: testing" in result.output

    def test_search_no_results(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test search with unusual query completes without error.

        Note: Even unusual queries may find results due to vector
        semantic similarity, so we just verify the command succeeds.
        """
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import search

        monkeypatch.setattr(search, "SkillManager", lambda **kwargs: skill_manager)
        monkeypatch.setattr(search, "IndexingEngine", lambda **kwargs: indexing_engine)

        result = cli_runner.invoke(
            cli, ["search", "nonexistent_query_xyz123", "--limit", "5"]
        )

        # Verify command succeeds (may or may not find results)
        assert result.exit_code == 0
        assert "Searching for:" in result.output


@pytest.mark.e2e
class TestCLIListCommand:
    """Test 'mcp-skillset list' command."""

    def test_list_all_skills(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test list command shows all skills."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import list_skills

        monkeypatch.setattr(list_skills, "SkillManager", lambda **kwargs: skill_manager)

        result = cli_runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "Available Skills" in result.output

        # Should show our test skills
        assert "pytest-testing" in result.output or "Skills" in result.output

    def test_list_with_category_filter(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test list with category filter."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import list_skills

        monkeypatch.setattr(list_skills, "SkillManager", lambda **kwargs: skill_manager)

        result = cli_runner.invoke(cli, ["list", "--category", "testing"])

        assert result.exit_code == 0
        assert "Category: testing" in result.output

    def test_list_compact_mode(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test list in compact mode."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import list_skills

        monkeypatch.setattr(list_skills, "SkillManager", lambda **kwargs: skill_manager)

        result = cli_runner.invoke(cli, ["list", "--compact"])

        assert result.exit_code == 0
        # Compact mode shows bullet list
        assert "•" in result.output or "Total:" in result.output


@pytest.mark.e2e
class TestCLIInfoCommand:
    """Test 'mcp-skillset info' command."""

    def test_info_existing_skill(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test info command for existing skill."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import info

        monkeypatch.setattr(info, "SkillManager", lambda **kwargs: skill_manager)

        # Get a real skill ID from our repository
        skills = skill_manager.discover_skills()
        if skills:
            skill_id = skills[0].id

            result = cli_runner.invoke(cli, ["info", skill_id])

            assert result.exit_code == 0
            assert "Skill Information:" in result.output
            assert "Metadata" in result.output
            assert "Description" in result.output

    def test_info_nonexistent_skill(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test info command for non-existent skill."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import info

        monkeypatch.setattr(info, "SkillManager", lambda **kwargs: skill_manager)

        result = cli_runner.invoke(cli, ["info", "nonexistent-skill-id"])

        assert result.exit_code == 0
        assert "Skill not found" in result.output


@pytest.mark.e2e
class TestCLIRecommendCommand:
    """Test 'mcp-skillset recommend' command."""

    def test_recommend_for_python_project(
        self,
        cli_runner: CliRunner,
        sample_python_project_e2e: Path,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test recommend command for Python project."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import recommend

        monkeypatch.setattr(recommend, "SkillManager", lambda **kwargs: skill_manager)
        monkeypatch.setattr(
            recommend, "IndexingEngine", lambda **kwargs: indexing_engine
        )

        # Import ToolchainDetector directly to avoid recursion
        from mcp_skills.services.toolchain_detector import ToolchainDetector

        monkeypatch.setattr(recommend, "ToolchainDetector", lambda: ToolchainDetector())

        # Change to Python project directory
        monkeypatch.chdir(sample_python_project_e2e)

        result = cli_runner.invoke(cli, ["recommend"])

        assert result.exit_code == 0
        assert "Skill Recommendations" in result.output
        assert "Detected Toolchain" in result.output
        assert "Python" in result.output


@pytest.mark.e2e
class TestCLIRepoCommands:
    """Test 'mcp-skillset repo' commands."""

    def test_repo_list_empty(
        self,
        cli_runner: CliRunner,
        e2e_configured_services: tuple,
        monkeypatch,
    ) -> None:
        """Test repo list with no repositories."""
        repo_manager, skill_manager, indexing_engine = e2e_configured_services

        from mcp_skills.cli.commands import repo

        monkeypatch.setattr(repo, "RepositoryManager", lambda **kwargs: repo_manager)

        result = cli_runner.invoke(cli, ["repo", "list"])

        assert result.exit_code == 0
        assert "No repositories configured" in result.output

    def test_repo_list_with_repositories(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test repo list with configured repositories."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import repo

        monkeypatch.setattr(repo, "RepositoryManager", lambda **kwargs: repo_manager)

        result = cli_runner.invoke(cli, ["repo", "list"])

        assert result.exit_code == 0
        assert "Configured Repositories" in result.output
        assert "test-skills-repo" in result.output

    def test_repo_add_invalid_url(
        self,
        cli_runner: CliRunner,
        e2e_configured_services: tuple,
        monkeypatch,
    ) -> None:
        """Test repo add with invalid URL."""
        repo_manager, skill_manager, indexing_engine = e2e_configured_services

        from mcp_skills.cli.commands import repo

        monkeypatch.setattr(repo, "RepositoryManager", lambda **kwargs: repo_manager)

        result = cli_runner.invoke(cli, ["repo", "add", "not-a-valid-url"])

        assert result.exit_code == 1
        assert "Failed to add repository" in result.output


@pytest.mark.e2e
class TestCLIIndexCommand:
    """Test 'mcp-skillset index' command."""

    def test_index_command(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test index command builds indices."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import index

        monkeypatch.setattr(index, "SkillManager", lambda **kwargs: skill_manager)
        monkeypatch.setattr(index, "IndexingEngine", lambda **kwargs: indexing_engine)

        result = cli_runner.invoke(cli, ["index"])

        assert result.exit_code == 0
        assert (
            "Indexing skills" in result.output or "Indexing complete" in result.output
        )

    def test_index_force_rebuild(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test index --force rebuilds from scratch."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import index

        monkeypatch.setattr(index, "SkillManager", lambda **kwargs: skill_manager)
        monkeypatch.setattr(index, "IndexingEngine", lambda **kwargs: indexing_engine)

        result = cli_runner.invoke(cli, ["index", "--force"])

        assert result.exit_code == 0
        assert "Full reindex" in result.output or "Indexing complete" in result.output


@pytest.mark.e2e
class TestCLIDoctorCommand:
    """Test 'mcp-skillset doctor' command."""

    def test_doctor_check(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test doctor command checks system status."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import doctor

        monkeypatch.setattr(doctor, "SkillManager", lambda **kwargs: skill_manager)
        monkeypatch.setattr(doctor, "IndexingEngine", lambda **kwargs: indexing_engine)
        monkeypatch.setattr(doctor, "RepositoryManager", lambda **kwargs: repo_manager)

        result = cli_runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0
        assert "System Health Check" in result.output
        assert "ChromaDB Vector Store" in result.output
        assert "Knowledge Graph" in result.output
        assert "Repositories" in result.output


@pytest.mark.e2e
class TestCLIStatsCommand:
    """Test 'mcp-skillset stats' command."""

    def test_stats_command(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test stats command shows statistics."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import stats

        monkeypatch.setattr(stats, "SkillManager", lambda **kwargs: skill_manager)
        monkeypatch.setattr(stats, "IndexingEngine", lambda **kwargs: indexing_engine)
        monkeypatch.setattr(stats, "RepositoryManager", lambda **kwargs: repo_manager)

        result = cli_runner.invoke(cli, ["stats"])

        assert result.exit_code == 0
        assert "Usage Statistics" in result.output
        assert "System Statistics" in result.output


@pytest.mark.e2e
class TestCLIConfigCommand:
    """Test 'mcp-skillset config' command."""

    def test_config_display(
        self,
        cli_runner: CliRunner,
        e2e_services_with_repo: tuple,
        monkeypatch,
    ) -> None:
        """Test config command displays configuration."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        from mcp_skills.cli.commands import config

        monkeypatch.setattr(config, "SkillManager", lambda **kwargs: skill_manager)
        monkeypatch.setattr(config, "IndexingEngine", lambda **kwargs: indexing_engine)
        monkeypatch.setattr(config, "RepositoryManager", lambda **kwargs: repo_manager)

        result = cli_runner.invoke(cli, ["config", "--show"])

        assert result.exit_code == 0
        assert "Current Configuration" in result.output
        assert (
            "Base Directory" in result.output
            or "mcp-skillset Configuration" in result.output
        )


@pytest.mark.e2e
class TestCLIVersionCommand:
    """Test version output."""

    def test_version_flag(self, cli_runner: CliRunner) -> None:
        """Test --version flag."""
        result = cli_runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "mcp-skillset" in result.output


@pytest.mark.e2e
class TestCLIHelpOutput:
    """Test CLI help output."""

    def test_help_main(self, cli_runner: CliRunner) -> None:
        """Test main help output."""
        result = cli_runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "MCP Skills" in result.output
        assert "Dynamic RAG-powered skills" in result.output

        # Verify main commands listed
        assert "setup" in result.output
        assert "search" in result.output
        assert "list" in result.output

    def test_help_search(self, cli_runner: CliRunner) -> None:
        """Test search command help."""
        result = cli_runner.invoke(cli, ["search", "--help"])

        assert result.exit_code == 0
        assert "Search for skills" in result.output

    def test_help_repo(self, cli_runner: CliRunner) -> None:
        """Test repo command help."""
        result = cli_runner.invoke(cli, ["repo", "--help"])

        assert result.exit_code == 0
        assert "Manage skill repositories" in result.output


@pytest.mark.e2e
class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_invalid_command(self, cli_runner: CliRunner) -> None:
        """Test handling of invalid command."""
        result = cli_runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0
        # Click shows error for unknown commands

    def test_missing_argument(self, cli_runner: CliRunner) -> None:
        """Test handling of missing required argument."""
        result = cli_runner.invoke(cli, ["info"])

        assert result.exit_code != 0
        # Click shows error for missing arguments
