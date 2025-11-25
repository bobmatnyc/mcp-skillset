"""AI Agent Installer Module.

Safely installs MCP SkillKit configuration into AI agent config files with
automatic backup and rollback capabilities.

Design Decision: Atomic config updates with backup/restore

Rationale: Configuration files are critical - corruption can break the agent.
We implement a backup-before-modify pattern with automatic rollback on failure.

Trade-offs:
- Safety vs Speed: Double file I/O (backup + write) vs direct modification
- Disk space: Keep timestamped backups vs single backup
- Complexity: Atomic updates with rollback vs simple file overwrites

Alternatives Considered:
1. In-place modification: Rejected - no recovery from write failures
2. Temp file + atomic rename: Rejected - cross-platform issues with Windows
3. Git-style versioning: Rejected - adds complexity, backup files sufficient

Error Handling Strategy:
- Config parsing errors: Refuse to modify, show error
- Write failures: Rollback to backup automatically
- Backup failures: Abort operation, don't risk data loss
- JSON validation: Parse before and after modification

Backup Policy:
- Format: {original_name}.backup.{timestamp}
- Retention: Unlimited (user can manually clean old backups)
- Location: Same directory as original config
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .agent_detector import DetectedAgent


class ConfigError(Exception):
    """Base exception for configuration errors."""

    pass


class BackupError(ConfigError):
    """Backup operation failed."""

    pass


class ValidationError(ConfigError):
    """Configuration validation failed."""

    pass


class InstallResult:
    """Result of an installation operation.

    Attributes:
        success: Whether installation succeeded
        agent_name: Name of the agent
        agent_id: Agent identifier
        config_path: Path to the config file
        backup_path: Path to backup file (if created)
        error: Error message (if failed)
        changes_made: Description of changes made
    """

    def __init__(
        self,
        success: bool,
        agent_name: str,
        agent_id: str,
        config_path: Path,
        backup_path: Path | None = None,
        error: str | None = None,
        changes_made: str | None = None,
    ):
        self.success = success
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.config_path = config_path
        self.backup_path = backup_path
        self.error = error
        self.changes_made = changes_made


class AgentInstaller:
    """Installs MCP SkillKit into AI agent configurations.

    Performance:
    - Time Complexity: O(1) for single agent install
    - Space Complexity: O(n) where n is config file size (2x during backup)
    - Typical config size: 1-10 KB, backup overhead negligible

    Usage:
        installer = AgentInstaller()
        result = installer.install(detected_agent, force=False)
        if result.success:
            print(f"Installed for {result.agent_name}")
            print(f"Backup at: {result.backup_path}")
        else:
            print(f"Failed: {result.error}")
    """

    MCP_SERVER_CONFIG = {
        "command": "mcp-skillkit",
        "args": ["mcp"],
        "env": {},
    }

    GITIGNORE_ENTRIES = [
        "",
        "# MCP SkillKit datasets (added by mcp-skillkit installer)",
        "# User-specific data files that should never be committed",
        ".mcp-skillkit/",
        "**/.mcp-skillkit/",
    ]

    def __init__(self) -> None:
        """Initialize the agent installer."""
        pass

    def install(
        self,
        agent: DetectedAgent,
        force: bool = False,
        dry_run: bool = False,
    ) -> InstallResult:
        """Install MCP SkillKit for a detected agent.

        Args:
            agent: DetectedAgent to install for
            force: Overwrite existing mcp-skillkit configuration
            dry_run: Show what would be done without making changes

        Returns:
            InstallResult with success status and details

        Error Conditions:
            - Config file missing: Creates new config with MCP configuration
            - Invalid JSON: Returns error, refuses to modify
            - Permission denied: Returns error with clear message
            - Backup failure: Returns error, doesn't proceed

        Example:
            result = installer.install(agent, force=True)
            if result.success:
                print(f"Backup: {result.backup_path}")
                print(f"Changes: {result.changes_made}")
        """
        try:
            # Check if config directory exists
            config_dir = agent.config_path.parent
            if not config_dir.exists():
                return InstallResult(
                    success=False,
                    agent_name=agent.name,
                    agent_id=agent.id,
                    config_path=agent.config_path,
                    error=f"Configuration directory not found: {config_dir}\n"
                    f"Please install {agent.name} first.",
                )

            # Load existing config or create new
            if agent.exists:
                config, error = self._load_config(agent.config_path)
                if error:
                    return InstallResult(
                        success=False,
                        agent_name=agent.name,
                        agent_id=agent.id,
                        config_path=agent.config_path,
                        error=f"Failed to parse config file: {error}\n"
                        f"The config file may be corrupted. Please check: {agent.config_path}",
                    )
            else:
                config = {}

            # Check if already installed
            if not force:
                mcp_servers = config.get("mcpServers", {})
                if "mcp-skillkit" in mcp_servers:
                    return InstallResult(
                        success=False,
                        agent_name=agent.name,
                        agent_id=agent.id,
                        config_path=agent.config_path,
                        error="mcp-skillkit is already installed. Use --force to overwrite.",
                    )

            # Dry run: show what would happen
            if dry_run:
                changes = self._describe_changes(config)
                return InstallResult(
                    success=True,
                    agent_name=agent.name,
                    agent_id=agent.id,
                    config_path=agent.config_path,
                    changes_made=f"[DRY RUN] Would make these changes:\n{changes}",
                )

            # Backup existing config
            backup_path = None
            if agent.exists:
                backup_path, error = self._create_backup(agent.config_path)
                if error:
                    return InstallResult(
                        success=False,
                        agent_name=agent.name,
                        agent_id=agent.id,
                        config_path=agent.config_path,
                        error=f"Failed to create backup: {error}\n"
                        f"Aborting installation to prevent data loss.",
                    )

            # Modify configuration
            modified_config = self._add_mcp_config(config)

            # Validate modified config
            if not self._validate_config(modified_config):
                # Rollback is not needed as we haven't written yet
                return InstallResult(
                    success=False,
                    agent_name=agent.name,
                    agent_id=agent.id,
                    config_path=agent.config_path,
                    backup_path=backup_path,
                    error="Modified configuration failed validation. Aborting.",
                )

            # Write new configuration
            error = self._write_config(agent.config_path, modified_config)
            if error:
                # Attempt rollback
                if backup_path:
                    self._restore_backup(backup_path, agent.config_path)
                return InstallResult(
                    success=False,
                    agent_name=agent.name,
                    agent_id=agent.id,
                    config_path=agent.config_path,
                    backup_path=backup_path,
                    error=f"Failed to write config: {error}\n"
                    f"Configuration has been restored from backup.",
                )

            # Update .gitignore if found (best effort, don't fail installation)
            self._update_gitignore_if_exists(agent.config_path.parent)

            # Success
            changes = self._describe_changes(config)
            return InstallResult(
                success=True,
                agent_name=agent.name,
                agent_id=agent.id,
                config_path=agent.config_path,
                backup_path=backup_path,
                changes_made=changes,
            )

        except Exception as e:
            return InstallResult(
                success=False,
                agent_name=agent.name,
                agent_id=agent.id,
                config_path=agent.config_path,
                error=f"Unexpected error: {e}",
            )

    def _load_config(self, config_path: Path) -> tuple[dict[str, Any], str | None]:
        """Load and parse JSON configuration file.

        Args:
            config_path: Path to config file

        Returns:
            Tuple of (config_dict, error_message)
            On success: (config, None)
            On failure: ({}, error_message)
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            return config, None
        except json.JSONDecodeError as e:
            return {}, f"Invalid JSON: {e}"
        except PermissionError:
            return {}, f"Permission denied reading: {config_path}"
        except Exception as e:
            return {}, str(e)

    def _create_backup(self, config_path: Path) -> tuple[Path | None, str | None]:
        """Create timestamped backup of config file.

        Args:
            config_path: Path to config file

        Returns:
            Tuple of (backup_path, error_message)
            On success: (backup_path, None)
            On failure: (None, error_message)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = config_path.parent / f"{config_path.name}.backup.{timestamp}"

            shutil.copy2(config_path, backup_path)
            return backup_path, None
        except PermissionError:
            return None, f"Permission denied creating backup at: {config_path.parent}"
        except Exception as e:
            return None, str(e)

    def _add_mcp_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Add MCP SkillKit configuration to config dict.

        Args:
            config: Existing configuration dictionary

        Returns:
            Modified configuration with MCP SkillKit added
        """
        modified = config.copy()

        # Ensure mcpServers key exists
        if "mcpServers" not in modified:
            modified["mcpServers"] = {}

        # Add mcp-skillkit configuration
        modified["mcpServers"]["mcp-skillkit"] = self.MCP_SERVER_CONFIG.copy()

        return modified

    def _validate_config(self, config: dict[str, Any]) -> bool:
        """Validate configuration structure.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Must be a dictionary
            if not isinstance(config, dict):
                return False

            # Must have mcpServers
            if "mcpServers" not in config:
                return False

            # mcpServers must be a dict
            if not isinstance(config["mcpServers"], dict):
                return False

            # mcp-skillkit must be present
            if "mcp-skillkit" not in config["mcpServers"]:
                return False

            # Validate mcp-skillkit structure
            mcp_config = config["mcpServers"]["mcp-skillkit"]
            if not isinstance(mcp_config, dict):
                return False

            # Must have command and args
            if "command" not in mcp_config or "args" not in mcp_config:
                return False

            # Ensure it's valid JSON (round-trip test)
            json.dumps(config)

            return True
        except Exception:
            return False

    def _write_config(self, config_path: Path, config: dict[str, Any]) -> str | None:
        """Write configuration to file with pretty formatting.

        Args:
            config_path: Path to write config to
            config: Configuration dictionary

        Returns:
            Error message on failure, None on success
        """
        try:
            # Ensure parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write with pretty formatting
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.write("\n")  # Trailing newline

            return None
        except PermissionError:
            return f"Permission denied writing to: {config_path}"
        except Exception as e:
            return str(e)

    def _restore_backup(self, backup_path: Path, config_path: Path) -> None:
        """Restore configuration from backup.

        Args:
            backup_path: Path to backup file
            config_path: Path to restore to

        Note:
            Errors during restore are logged but not raised,
            as this is a best-effort recovery attempt.
        """
        try:
            shutil.copy2(backup_path, config_path)
        except Exception as e:
            # Log error but don't raise - rollback is best-effort
            print(f"Warning: Failed to restore backup: {e}")

    def _describe_changes(self, original_config: dict[str, Any]) -> str:
        """Describe what changes will be made to the configuration.

        Args:
            original_config: Original configuration dict

        Returns:
            Human-readable description of changes
        """
        if not original_config:
            return "Create new config file with MCP SkillKit configuration"

        has_mcp = "mcpServers" in original_config
        has_skillkit = has_mcp and "mcp-skillkit" in original_config.get(
            "mcpServers", {}
        )

        if has_skillkit:
            return "Update existing mcp-skillkit configuration"
        elif has_mcp:
            return "Add mcp-skillkit to existing mcpServers configuration"
        else:
            return "Add mcpServers section with mcp-skillkit configuration"

    def _update_gitignore_if_exists(self, search_dir: Path) -> None:
        """Update .gitignore to exclude .mcp-skillkit/ if file exists.

        Searches for .gitignore in the given directory and parent directories
        up to the user's home directory. Adds MCP SkillKit entries if not present.

        Args:
            search_dir: Directory to start searching from

        Note:
            This is best-effort only - failures are silently ignored to not
            disrupt the main installation process.
        """
        try:
            # Search for .gitignore up to home directory
            current_dir = search_dir.resolve()
            home_dir = Path.home()

            while current_dir >= home_dir:
                gitignore_path = current_dir / ".gitignore"
                if gitignore_path.exists():
                    self._add_to_gitignore(gitignore_path)
                    return

                # Move up one directory
                if current_dir.parent == current_dir:
                    # Reached root without finding .gitignore
                    break
                current_dir = current_dir.parent

        except Exception:
            # Silently ignore errors - .gitignore update is nice-to-have
            pass

    def _add_to_gitignore(self, gitignore_path: Path) -> None:
        """Add MCP SkillKit entries to .gitignore if not already present.

        Args:
            gitignore_path: Path to .gitignore file
        """
        try:
            # Read existing content
            content = gitignore_path.read_text(encoding="utf-8")

            # Check if already has our entries
            if ".mcp-skillkit/" in content:
                return  # Already present

            # Add our entries
            entries_text = "\n".join(self.GITIGNORE_ENTRIES)

            # Ensure file ends with newline before appending
            if content and not content.endswith("\n"):
                content += "\n"

            # Append our entries
            updated_content = content + entries_text + "\n"

            # Write back
            gitignore_path.write_text(updated_content, encoding="utf-8")

        except Exception:
            # Silently ignore errors
            pass
