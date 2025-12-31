"""Tests for hook configuration in ConfigMenu."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from mcp_skills.cli.config_menu import ConfigMenu
from mcp_skills.models.config import HookConfig


class TestHookConfiguration:
    """Test hook-related configuration menu functionality."""

    def test_hook_menu_option_exists(self):
        """Test that hook settings menu option exists."""
        menu = ConfigMenu()
        assert "Hook settings (Claude Code integration)" in menu.MAIN_MENU_CHOICES

    def test_hook_action_choices_defined(self):
        """Test that hook action choices are defined."""
        menu = ConfigMenu()
        assert hasattr(menu, "HOOK_ACTION_CHOICES")
        assert len(menu.HOOK_ACTION_CHOICES) == 5
        assert "Enable/disable hooks" in menu.HOOK_ACTION_CHOICES
        assert "Configure threshold" in menu.HOOK_ACTION_CHOICES
        assert "Configure max skills" in menu.HOOK_ACTION_CHOICES
        assert "Test hook" in menu.HOOK_ACTION_CHOICES
        assert "Back to main menu" in menu.HOOK_ACTION_CHOICES

    def test_configure_hooks_method_exists(self):
        """Test that _configure_hooks method exists."""
        menu = ConfigMenu()
        assert hasattr(menu, "_configure_hooks")
        assert callable(menu._configure_hooks)

    def test_toggle_hooks_method_exists(self):
        """Test that _toggle_hooks method exists."""
        menu = ConfigMenu()
        assert hasattr(menu, "_toggle_hooks")
        assert callable(menu._toggle_hooks)

    def test_configure_hook_threshold_method_exists(self):
        """Test that _configure_hook_threshold method exists."""
        menu = ConfigMenu()
        assert hasattr(menu, "_configure_hook_threshold")
        assert callable(menu._configure_hook_threshold)

    def test_configure_hook_max_skills_method_exists(self):
        """Test that _configure_hook_max_skills method exists."""
        menu = ConfigMenu()
        assert hasattr(menu, "_configure_hook_max_skills")
        assert callable(menu._configure_hook_max_skills)

    def test_test_hook_method_exists(self):
        """Test that _test_hook method exists."""
        menu = ConfigMenu()
        assert hasattr(menu, "_test_hook")
        assert callable(menu._test_hook)

    def test_validate_max_skills_valid(self):
        """Test max skills validation with valid inputs."""
        assert ConfigMenu._validate_max_skills("1") is True
        assert ConfigMenu._validate_max_skills("5") is True
        assert ConfigMenu._validate_max_skills("10") is True

    def test_validate_max_skills_invalid(self):
        """Test max skills validation with invalid inputs."""
        # Out of range
        assert ConfigMenu._validate_max_skills("0") == "Max skills must be between 1 and 10"
        assert ConfigMenu._validate_max_skills("11") == "Max skills must be between 1 and 10"
        assert ConfigMenu._validate_max_skills("-1") == "Max skills must be between 1 and 10"

        # Invalid format
        assert ConfigMenu._validate_max_skills("abc") == "Please enter a valid integer"
        assert ConfigMenu._validate_max_skills("5.5") == "Please enter a valid integer"
        assert ConfigMenu._validate_max_skills("") == "Please enter a valid integer"

    @patch("mcp_skills.cli.config_menu.questionary.confirm")
    def test_toggle_hooks_enable(self, mock_confirm):
        """Test enabling hooks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            with patch.object(ConfigMenu, "CONFIG_PATH", config_path):
                menu = ConfigMenu()
                menu.config.hooks.enabled = False

                # Mock user selecting "Yes" to enable
                mock_confirm.return_value.ask.return_value = True

                menu._toggle_hooks()

                # Verify config was updated
                assert menu.config.hooks.enabled is True

                # Verify config was saved to file
                with open(config_path) as f:
                    saved_config = yaml.safe_load(f)
                assert saved_config["hooks"]["enabled"] is True

    @patch("mcp_skills.cli.config_menu.questionary.confirm")
    def test_toggle_hooks_disable(self, mock_confirm):
        """Test disabling hooks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            with patch.object(ConfigMenu, "CONFIG_PATH", config_path):
                menu = ConfigMenu()
                menu.config.hooks.enabled = True

                # Mock user selecting "No" to disable
                mock_confirm.return_value.ask.return_value = False

                menu._toggle_hooks()

                # Verify config was updated
                assert menu.config.hooks.enabled is False

                # Verify config was saved to file
                with open(config_path) as f:
                    saved_config = yaml.safe_load(f)
                assert saved_config["hooks"]["enabled"] is False

    @patch("mcp_skills.cli.config_menu.questionary.text")
    def test_configure_hook_threshold(self, mock_text):
        """Test configuring hook threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            with patch.object(ConfigMenu, "CONFIG_PATH", config_path):
                menu = ConfigMenu()

                # Mock user entering new threshold
                mock_text.return_value.ask.return_value = "0.75"

                menu._configure_hook_threshold()

                # Verify config was updated
                assert menu.config.hooks.threshold == 0.75

                # Verify config was saved to file
                with open(config_path) as f:
                    saved_config = yaml.safe_load(f)
                assert saved_config["hooks"]["threshold"] == 0.75

    @patch("mcp_skills.cli.config_menu.questionary.text")
    def test_configure_hook_max_skills(self, mock_text):
        """Test configuring max skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            with patch.object(ConfigMenu, "CONFIG_PATH", config_path):
                menu = ConfigMenu()

                # Mock user entering new max skills
                mock_text.return_value.ask.return_value = "7"

                menu._configure_hook_max_skills()

                # Verify config was updated
                assert menu.config.hooks.max_skills == 7

                # Verify config was saved to file
                with open(config_path) as f:
                    saved_config = yaml.safe_load(f)
                assert saved_config["hooks"]["max_skills"] == 7

    @patch("subprocess.run")
    @patch("mcp_skills.cli.config_menu.questionary.text")
    def test_test_hook_success(self, mock_text, mock_run):
        """Test hook testing with successful response."""
        import json

        # Mock user input
        mock_text.return_value.ask.return_value = "Write pytest tests"

        # Mock subprocess response
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "systemMessage": "Relevant skill: toolchains-python-testing"
        })
        mock_run.return_value = mock_result

        menu = ConfigMenu()

        # Should not raise any exceptions
        menu._test_hook()

        # Verify subprocess was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.kwargs["input"] == json.dumps({"user_prompt": "Write pytest tests"})
        assert call_args.args[0] == ["mcp-skillset", "enrich-hook"]

    @patch("subprocess.run")
    @patch("mcp_skills.cli.config_menu.questionary.text")
    def test_test_hook_no_matches(self, mock_text, mock_run):
        """Test hook testing with no matching skills."""
        import json

        # Mock user input
        mock_text.return_value.ask.return_value = "Some random prompt"

        # Mock subprocess response (empty result)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({})
        mock_run.return_value = mock_result

        menu = ConfigMenu()

        # Should not raise any exceptions
        menu._test_hook()

    @patch("mcp_skills.cli.config_menu.questionary.text")
    def test_test_hook_cancelled(self, mock_text):
        """Test hook testing when user cancels."""
        # Mock user cancelling
        mock_text.return_value.ask.return_value = None

        menu = ConfigMenu()

        # Should return early without error
        menu._test_hook()

    def test_default_hook_config_loaded(self):
        """Test that default hook config is loaded on initialization."""
        menu = ConfigMenu()

        # Check default values
        assert hasattr(menu.config, "hooks")
        assert menu.config.hooks.enabled is True
        assert menu.config.hooks.threshold == 0.6
        assert menu.config.hooks.max_skills == 5

    @patch("mcp_skills.cli.config_menu.questionary.select")
    def test_configure_hooks_submenu(self, mock_select):
        """Test that configure hooks shows submenu correctly."""
        menu = ConfigMenu()

        # Mock user selecting "Back to main menu"
        mock_select.return_value.ask.return_value = menu.HOOK_ACTION_CHOICES[4]

        # Should return without error
        menu._configure_hooks()

        # Verify select was called with correct choices
        mock_select.assert_called_once()
        call_args = mock_select.call_args
        assert call_args.kwargs["choices"] == menu.HOOK_ACTION_CHOICES

    def test_hook_config_persistence_merge(self):
        """Test that hook config updates merge correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            with patch.object(ConfigMenu, "CONFIG_PATH", config_path):
                menu = ConfigMenu()

                # Save initial hook config
                menu._save_config({
                    "hooks": {
                        "enabled": False,
                        "threshold": 0.8,
                        "max_skills": 3
                    }
                })

                # Update only threshold
                menu._save_config({
                    "hooks": {
                        "threshold": 0.7
                    }
                })

                # Verify merge preserved other values
                with open(config_path) as f:
                    saved_config = yaml.safe_load(f)

                assert saved_config["hooks"]["enabled"] is False
                assert saved_config["hooks"]["threshold"] == 0.7
                assert saved_config["hooks"]["max_skills"] == 3

    def test_hook_config_in_view_configuration(self):
        """Test that hook config appears in view configuration."""
        from io import StringIO
        from rich.console import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            # Capture console output
            output = StringIO()
            test_console = Console(file=output, width=80, force_terminal=True)

            with patch.object(ConfigMenu, "CONFIG_PATH", config_path):
                with patch("mcp_skills.cli.config_menu.console", test_console):
                    with patch("mcp_skills.cli.config_menu.questionary.text") as mock_text:
                        mock_text.return_value.ask.return_value = None

                        menu = ConfigMenu()
                        menu.config.hooks.enabled = False
                        menu.config.hooks.threshold = 0.75
                        menu.config.hooks.max_skills = 7

                        try:
                            menu._view_configuration()
                        except:
                            pass  # Ignore errors from missing services

            # Check that hook settings appear in output
            result = output.getvalue()
            assert "Hook Settings" in result or "🪝" in result
