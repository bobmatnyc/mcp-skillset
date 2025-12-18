"""AI Agent Installer - Thin Adapter for py-mcp-installer-service.

This module provides a backward-compatible interface to the py-mcp-installer-service
library. It delegates all installation logic to py-mcp-installer while maintaining
the original API surface for existing code.

Design Decision: Adapter pattern with delegation
- Original 656-line implementation replaced with ~95-line adapter
- All installation logic delegated to py-mcp-installer-service
- Backward compatibility maintained for existing callers
- Platform mapping handled via simple dictionary

Reduced from 656 lines to ~95 lines (85% reduction).
"""

from __future__ import annotations

from pathlib import Path

from .agent_detector import DetectedAgent
from .py_mcp_installer_wrapper import (
    InstallationResult as PyInstallResult,
)
from .py_mcp_installer_wrapper import (
    MCPInstaller,
    Platform,
    PyMCPInstallerError,
)


# Backward compatibility exceptions
class ConfigError(Exception):
    """Base exception for configuration errors."""

    pass


class BackupError(ConfigError):
    """Backup operation failed."""

    pass


class ValidationError(ConfigError):
    """Configuration validation failed."""

    pass


# Platform ID mapping: agent_detector ID -> py-mcp-installer Platform
PLATFORM_MAP = {
    "claude-desktop": Platform.CLAUDE_DESKTOP,
    "claude-code": Platform.CLAUDE_CODE,
    "auggie": Platform.AUGGIE,
    "cursor": Platform.CURSOR,
    "codex": Platform.CODEX,
    "windsurf": Platform.WINDSURF,
    "gemini-cli": Platform.GEMINI_CLI,
}


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
    """Installs MCP SkillSet into AI agent configurations.

    This is a thin adapter that delegates to py-mcp-installer-service
    while maintaining backward compatibility with the original interface.
    """

    def __init__(self) -> None:
        """Initialize the agent installer."""
        pass

    def install(
        self,
        agent: DetectedAgent,
        force: bool = False,
        dry_run: bool = False,
    ) -> InstallResult:
        """Install MCP SkillSet for a detected agent.

        Args:
            agent: DetectedAgent to install for
            force: Overwrite existing mcp-skillset configuration
            dry_run: Show what would be done without making changes

        Returns:
            InstallResult with success status and details
        """
        # Map agent ID to Platform enum
        platform = PLATFORM_MAP.get(agent.id)
        if not platform:
            return InstallResult(
                success=False,
                agent_name=agent.name,
                agent_id=agent.id,
                config_path=agent.config_path,
                error=f"Unsupported agent: {agent.id}",
            )

        # Create installer for the platform (dry_run is set at constructor level)
        try:
            installer = MCPInstaller(platform=platform, dry_run=dry_run)
        except PyMCPInstallerError as e:
            return InstallResult(
                success=False,
                agent_name=agent.name,
                agent_id=agent.id,
                config_path=agent.config_path,
                error=f"Failed to create installer: {e}",
            )

        # Install the server (force parameter handles updates automatically)
        try:
            result: PyInstallResult = installer.install_server(
                name="mcp-skillset",
                command="mcp-skillset",
                args=["mcp"],
                description="Dynamic RAG-powered skills for code assistants",
                force=force,
            )

            # Map to legacy InstallResult format
            # Note: py-mcp-installer doesn't expose backup_path in result,
            # so we set it to None for backward compatibility
            return InstallResult(
                success=result.success,
                agent_name=agent.name,
                agent_id=agent.id,
                config_path=result.config_path or agent.config_path,
                backup_path=None,  # py-mcp-installer handles backups internally
                error=result.message if not result.success else None,
                changes_made=result.message if result.success else None,
            )

        except PyMCPInstallerError as e:
            return InstallResult(
                success=False,
                agent_name=agent.name,
                agent_id=agent.id,
                config_path=agent.config_path,
                error=str(e),
            )
