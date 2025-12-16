"""AI Agent Detection Module.

Detects installed AI agents (Claude Desktop, Claude Code, Auggie, Cursor,
Windsurf, Continue, Codex, Gemini CLI) by checking for their configuration
files in platform-specific directories.

Design Decision: Cross-platform path detection with environment variable support

Rationale: Different platforms store application data in different locations.
This module abstracts platform-specific logic to provide consistent detection
across macOS, Windows, and Linux.

Trade-offs:
- Simplicity: Hard-coded paths vs. registry/config scanning
- Coverage: Known agents vs. plugin architecture for extensibility
- Performance: File system checks are fast enough for this use case

Alternatives Considered:
1. Registry scanning (Windows): Rejected - adds complexity, not all agents register
2. Process scanning: Rejected - agent may not be running during install
3. Plugin architecture: Deferred - YAGNI until more agents need support

Future Extensibility: AgentConfig dataclass allows easy addition of new agents
by simply adding entries to AGENT_CONFIGS list.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentConfig:
    """Configuration for an AI agent detection.

    Attributes:
        name: Human-readable agent name (e.g., "Claude Desktop")
        id: Machine-readable identifier (e.g., "claude-desktop")
        config_paths: Platform-specific paths to config directory
        config_file: Name of the config file to modify
        config_key_path: JSON path to MCP servers configuration
    """

    name: str
    id: str
    config_paths: dict[str, Path]
    config_file: str
    config_key_path: str = "mcpServers"


@dataclass
class DetectedAgent:
    """Information about a detected AI agent.

    Attributes:
        name: Human-readable agent name
        id: Machine-readable identifier
        config_path: Absolute path to the configuration file
        exists: Whether the config file currently exists
    """

    name: str
    id: str
    config_path: Path
    exists: bool


# Agent configuration registry
AGENT_CONFIGS = [
    AgentConfig(
        name="Claude Desktop",
        id="claude-desktop",
        config_paths={
            "darwin": Path.home() / "Library" / "Application Support" / "Claude",
            "win32": (
                Path(os.environ.get("APPDATA", "")) / "Claude"
                if platform.system() == "Windows"
                else Path()
            ),
            "linux": Path.home() / ".config" / "Claude",
        },
        config_file="claude_desktop_config.json",
    ),
    AgentConfig(
        name="Claude Code",
        id="claude-code",
        config_paths={
            "darwin": Path.home() / "Library" / "Application Support" / "Code" / "User",
            "win32": (
                Path(os.environ.get("APPDATA", "")) / "Code" / "User"
                if platform.system() == "Windows"
                else Path()
            ),
            "linux": Path.home() / ".config" / "Code" / "User",
        },
        config_file="settings.json",
    ),
    AgentConfig(
        name="Auggie",
        id="auggie",
        config_paths={
            "darwin": Path.home() / "Library" / "Application Support" / "Auggie",
            "win32": (
                Path(os.environ.get("APPDATA", "")) / "Auggie"
                if platform.system() == "Windows"
                else Path()
            ),
            "linux": Path.home() / ".config" / "Auggie",
        },
        config_file="config.json",
    ),
    AgentConfig(
        name="Cursor",
        id="cursor",
        config_paths={
            "darwin": Path.home() / ".cursor",
            "win32": (
                Path.home() / ".cursor"
                if platform.system() == "Windows"
                else Path()
            ),
            "linux": Path.home() / ".cursor",
        },
        config_file="mcp.json",
    ),
    AgentConfig(
        name="Windsurf",
        id="windsurf",
        config_paths={
            "darwin": Path.home() / ".codeium" / "windsurf",
            "win32": (
                Path.home() / ".codeium" / "windsurf"
                if platform.system() == "Windows"
                else Path()
            ),
            "linux": Path.home() / ".codeium" / "windsurf",
        },
        config_file="mcp_config.json",
    ),
    AgentConfig(
        name="Continue",
        id="continue",
        config_paths={
            "darwin": Path.home() / ".continue",
            "win32": (
                Path.home() / ".continue"
                if platform.system() == "Windows"
                else Path()
            ),
            "linux": Path.home() / ".continue",
        },
        config_file="config.json",
    ),
    AgentConfig(
        name="Codex",
        id="codex",
        config_paths={
            "darwin": Path.home() / ".codex",
            "win32": (
                Path.home() / ".codex"
                if platform.system() == "Windows"
                else Path()
            ),
            "linux": Path.home() / ".codex",
        },
        config_file="config.toml",
    ),
    AgentConfig(
        name="Gemini CLI",
        id="gemini-cli",
        config_paths={
            "darwin": Path.home() / ".gemini",
            "win32": (
                Path.home() / ".gemini"
                if platform.system() == "Windows"
                else Path()
            ),
            "linux": Path.home() / ".gemini",
        },
        config_file="settings.json",
    ),
]


class AgentDetector:
    """Detects installed AI agents on the current system.

    Performance:
    - Time Complexity: O(n) where n is number of configured agents
    - Space Complexity: O(n) for storing detection results
    - File system checks are I/O bound, typically <10ms per agent

    Usage:
        detector = AgentDetector()
        agents = detector.detect_all()
        for agent in agents:
            if agent.exists:
                print(f"Found {agent.name} at {agent.config_path}")
    """

    def __init__(self) -> None:
        """Initialize agent detector with current platform."""
        self.platform = self._get_platform()

    def _get_platform(self) -> str:
        """Get normalized platform identifier.

        Returns:
            Platform identifier: 'darwin', 'win32', or 'linux'

        Error Handling:
            Unknown platforms default to 'linux' (most compatible)
        """
        system = platform.system().lower()
        if system == "darwin":
            return "darwin"
        elif system == "windows":
            return "win32"
        else:
            return "linux"

    def detect_agent(self, agent_id: str) -> DetectedAgent | None:
        """Detect a specific AI agent by ID.

        Args:
            agent_id: Agent identifier (e.g., 'claude-desktop')

        Returns:
            DetectedAgent if found, None if agent_id is unknown

        Example:
            agent = detector.detect_agent("claude-desktop")
            if agent and agent.exists:
                print(f"Config at: {agent.config_path}")
        """
        config = self._get_agent_config(agent_id)
        if not config:
            return None

        config_dir = config.config_paths.get(self.platform)
        if not config_dir:
            return None

        config_path = config_dir / config.config_file
        exists = config_path.exists()

        return DetectedAgent(
            name=config.name,
            id=config.id,
            config_path=config_path,
            exists=exists,
        )

    def detect_all(self) -> list[DetectedAgent]:
        """Detect all configured AI agents.

        Returns:
            List of DetectedAgent objects for all known agents on this platform

        Example:
            agents = detector.detect_all()
            installed = [a for a in agents if a.exists]
            print(f"Found {len(installed)} installed agents")
        """
        detected = []
        for config in AGENT_CONFIGS:
            config_dir = config.config_paths.get(self.platform)
            if not config_dir:
                continue

            config_path = config_dir / config.config_file
            exists = config_path.exists()

            detected.append(
                DetectedAgent(
                    name=config.name,
                    id=config.id,
                    config_path=config_path,
                    exists=exists,
                )
            )

        return detected

    def _get_agent_config(self, agent_id: str) -> AgentConfig | None:
        """Get configuration for a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentConfig if found, None otherwise
        """
        for config in AGENT_CONFIGS:
            if config.id == agent_id:
                return config
        return None
