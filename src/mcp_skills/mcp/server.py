"""FastMCP-based MCP server implementation for mcp-skillset.

This module implements the MCP server using the official FastMCP SDK,
providing skill discovery, search, and recommendation via the Model
Context Protocol.

The server manages global service instances (skill_manager, indexing_engine,
etc.) that are configured at startup and used by all tool implementations.
"""

import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..models.config import MCPSkillsConfig
from ..services.auto_updater import AutoUpdater
from ..services.indexing import IndexingEngine
from ..services.repository_manager import RepositoryManager
from ..services.skill_manager import SkillManager
from ..services.toolchain_detector import ToolchainDetector


# Initialize FastMCP server
mcp = FastMCP("mcp-skillset")

# Global service instances
_skill_manager: SkillManager | None = None
_indexing_engine: IndexingEngine | None = None
_toolchain_detector: ToolchainDetector | None = None
_repo_manager: RepositoryManager | None = None

# Configure logging
logger = logging.getLogger(__name__)


def configure_services(
    base_dir: Path | None = None,
    storage_path: Path | None = None,
) -> None:
    """Configure global service instances.

    This must be called before starting the server to initialize all
    services that will handle skill operations.

    Args:
        base_dir: Base directory for mcp-skillset data (default: ~/.mcp-skillset)
        storage_path: Path for storage (ChromaDB, knowledge graph)
                     (default: {base_dir}/storage)

    Raises:
        RuntimeError: If service configuration fails

    """
    global _skill_manager, _indexing_engine, _toolchain_detector, _repo_manager

    try:
        # Set default paths
        base_dir = base_dir or Path.home() / ".mcp-skillset"
        storage_path = storage_path or base_dir / "storage"

        # Ensure directories exist
        base_dir.mkdir(parents=True, exist_ok=True)
        storage_path.mkdir(parents=True, exist_ok=True)

        # Load configuration
        config = MCPSkillsConfig()

        # Initialize services
        _repo_manager = RepositoryManager(base_dir / "repos")
        _skill_manager = SkillManager(_repo_manager.base_dir)
        _indexing_engine = IndexingEngine(
            storage_path=storage_path,
            skill_manager=_skill_manager,
            config=config,
        )
        _toolchain_detector = ToolchainDetector()

        logger.info(f"Configured mcp-skillset services at {base_dir}")

        # Auto-update repositories if enabled
        if config.auto_update.enabled:
            logger.info("Auto-update enabled, checking repositories...")
            auto_updater = AutoUpdater(
                repo_manager=_repo_manager,
                indexing_engine=_indexing_engine,
                config=config.auto_update,
            )
            # Run auto-update synchronously during startup
            # This ensures indices are fresh before server accepts requests
            auto_updater.check_and_update()
            logger.info("Auto-update check complete")
        else:
            logger.info("Auto-update disabled, skipping repository checks")

    except Exception as e:
        logger.error(f"Failed to configure services: {e}")
        raise RuntimeError(f"Service configuration failed: {e}") from e


def get_skill_manager() -> SkillManager:
    """Get the configured SkillManager instance.

    Returns:
        The global skill_manager instance

    Raises:
        RuntimeError: If services have not been configured

    """
    if _skill_manager is None:
        raise RuntimeError(
            "Services not configured. Call configure_services() before starting server."
        )
    return _skill_manager


def get_indexing_engine() -> IndexingEngine:
    """Get the configured IndexingEngine instance.

    Returns:
        The global indexing_engine instance

    Raises:
        RuntimeError: If services have not been configured

    """
    if _indexing_engine is None:
        raise RuntimeError(
            "Services not configured. Call configure_services() before starting server."
        )
    return _indexing_engine


def get_toolchain_detector() -> ToolchainDetector:
    """Get the configured ToolchainDetector instance.

    Returns:
        The global toolchain_detector instance

    Raises:
        RuntimeError: If services have not been configured

    """
    if _toolchain_detector is None:
        raise RuntimeError(
            "Services not configured. Call configure_services() before starting server."
        )
    return _toolchain_detector


def get_repo_manager() -> RepositoryManager:
    """Get the configured RepositoryManager instance.

    Returns:
        The global repo_manager instance

    Raises:
        RuntimeError: If services have not been configured

    """
    if _repo_manager is None:
        raise RuntimeError(
            "Services not configured. Call configure_services() before starting server."
        )
    return _repo_manager


# Import all tool modules to register them with FastMCP
# These imports must come after mcp is initialized but before main()
from . import tools  # noqa: E402, F401


def main() -> None:
    """Run the FastMCP server.

    This function starts the server using stdio transport for
    JSON-RPC communication with Claude Desktop/Code.

    Services must be configured via configure_services() before
    calling this function.

    """
    # Run the server with stdio transport
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
