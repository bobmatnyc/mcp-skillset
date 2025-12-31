"""Auto-update service for repository maintenance.

This module handles automatic repository updates on MCP server startup,
checking for stale repositories and triggering updates and reindexing
as needed.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from mcp_skills.models.config import AutoUpdateConfig


if TYPE_CHECKING:
    from mcp_skills.services.indexing import IndexingEngine
    from mcp_skills.services.repository_manager import RepositoryManager


logger = logging.getLogger(__name__)


class AutoUpdater:
    """Auto-update service for repository maintenance.

    Checks repositories for staleness on MCP server startup and triggers
    updates and reindexing as needed. Designed to be non-blocking and
    resilient to errors.

    Attributes:
        repo_manager: RepositoryManager instance for repository operations
        indexing_engine: IndexingEngine instance for reindexing after updates
        config: AutoUpdateConfig with enabled flag and max_age_hours
    """

    def __init__(
        self,
        repo_manager: "RepositoryManager",
        indexing_engine: "IndexingEngine",
        config: AutoUpdateConfig,
    ) -> None:
        """Initialize auto-updater service.

        Args:
            repo_manager: Repository manager for update operations
            indexing_engine: Indexing engine for reindexing after updates
            config: Auto-update configuration
        """
        self.repo_manager = repo_manager
        self.indexing_engine = indexing_engine
        self.config = config

    def check_and_update(self) -> None:
        """Check repositories and update stale ones.

        This method is called on MCP server startup. It:
        1. Checks if auto-update is enabled
        2. Lists all repositories
        3. Identifies stale repositories (last_updated > max_age_hours)
        4. Updates each stale repository
        5. Reindexes if skill count changed

        All errors are caught and logged - failures won't crash server startup.

        Design Decision: Non-Blocking Error Handling

        Rationale: Auto-update is a convenience feature that should never
        prevent the MCP server from starting. If updates fail (network issues,
        permission errors, etc.), we log the error and continue.

        Trade-offs:
        - Reliability: Server always starts, even with stale repos
        - User Experience: Silent failures might confuse users
        - Observability: Comprehensive logging mitigates this

        Returns:
            None - logs all results, no exceptions raised
        """
        try:
            # Check if auto-update is enabled
            if not self.config.enabled:
                logger.info("Auto-update disabled, skipping repository checks")
                return

            logger.info(
                f"Starting auto-update check (max_age_hours={self.config.max_age_hours})"
            )

            # Get all repositories
            repositories = self.repo_manager.list_repositories()
            if not repositories:
                logger.info("No repositories configured, skipping auto-update")
                return

            # Calculate staleness threshold
            max_age = timedelta(hours=self.config.max_age_hours)
            now = datetime.now(UTC)
            threshold = now - max_age

            # Track updates
            updated_repos = []
            failed_repos = []
            total_skill_count_before = 0
            total_skill_count_after = 0

            # Check each repository
            for repo in repositories:
                total_skill_count_before += repo.skill_count

                # Check if repository is stale
                if repo.last_updated > threshold:
                    logger.debug(
                        f"Repository {repo.id} is fresh "
                        f"(last_updated: {repo.last_updated.isoformat()})"
                    )
                    total_skill_count_after += repo.skill_count
                    continue

                # Repository is stale - update it
                logger.info(
                    f"Repository {repo.id} is stale "
                    f"(last_updated: {repo.last_updated.isoformat()}, "
                    f"threshold: {threshold.isoformat()})"
                )

                try:
                    updated_repo = self.repo_manager.update_repository(repo.id)
                    updated_repos.append(repo.id)
                    total_skill_count_after += updated_repo.skill_count
                    logger.info(
                        f"Updated repository {repo.id}: "
                        f"{updated_repo.skill_count} skills "
                        f"(was {repo.skill_count})"
                    )
                except Exception as e:
                    # Log error but continue with other repositories
                    logger.error(
                        f"Failed to update repository {repo.id}: {e}",
                        exc_info=True,
                    )
                    failed_repos.append(repo.id)
                    total_skill_count_after += repo.skill_count

            # Log summary
            if updated_repos:
                logger.info(
                    f"Auto-update complete: {len(updated_repos)} repositories updated"
                )
                logger.debug(f"Updated repositories: {', '.join(updated_repos)}")
            else:
                logger.info("Auto-update complete: no stale repositories found")

            if failed_repos:
                logger.warning(
                    f"Auto-update had {len(failed_repos)} failures: "
                    f"{', '.join(failed_repos)}"
                )

            # Reindex if skill count changed
            if total_skill_count_after != total_skill_count_before:
                logger.info(
                    f"Skill count changed "
                    f"({total_skill_count_before} -> {total_skill_count_after}), "
                    f"triggering reindex"
                )
                try:
                    stats = self.indexing_engine.reindex_all(force=True)
                    logger.info(
                        f"Reindexing complete: {stats.total_skills} skills indexed"
                    )
                except Exception as e:
                    # Log error but don't raise - server should still start
                    logger.error(f"Failed to reindex after auto-update: {e}", exc_info=True)
            else:
                logger.debug("Skill count unchanged, skipping reindex")

        except Exception as e:
            # Catch-all for unexpected errors - log but don't raise
            logger.error(f"Auto-update failed unexpectedly: {e}", exc_info=True)
