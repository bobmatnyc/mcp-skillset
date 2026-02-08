"""Git repository management for skills repositories."""

import logging
import re
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

import git
from git import RemoteProgress

from mcp_skills.models.repository import Repository
from mcp_skills.services.metadata_store import MetadataStore


logger = logging.getLogger(__name__)


class RepoConfig(TypedDict):
    """Type definition for repository configuration."""

    url: str
    priority: int
    license: str


class CloneProgress(RemoteProgress):
    """GitPython progress handler for repository cloning and updates.

    Translates GitPython's RemoteProgress callbacks into a simpler callback
    interface suitable for CLI progress bars.

    Args:
        callback: Function called with (current, total, message) during git operations
    """

    def __init__(self, callback: Callable[[int, int, str], None]) -> None:
        """Initialize progress handler with callback function."""
        super().__init__()
        self.callback = callback

    def update(
        self,
        _op_code: int,
        cur_count: int | float,
        max_count: int | float | None = None,
        message: str = "",
    ) -> None:
        """Called by GitPython during clone/pull operations.

        Args:
            op_code: Operation code (not used, but required by GitPython)
            cur_count: Current progress count
            max_count: Total count (None for indeterminate progress)
            message: Progress message from git
        """
        if max_count and self.callback:
            self.callback(int(cur_count), int(max_count), message or "")


class RepositoryManager:
    """Manage git-based skills repositories.

    Handles cloning, updating, and tracking multiple skill repositories.
    Supports prioritization for resolving conflicts between repositories.
    """

    # Default repositories to clone on setup
    DEFAULT_REPOS: list[RepoConfig] = [
        {
            "url": "https://github.com/anthropics/skills.git",
            "priority": 100,
            "license": "Apache-2.0",
        },
        {
            "url": "https://github.com/obra/superpowers.git",
            "priority": 90,
            "license": "MIT",
        },
        {
            "url": "https://github.com/ComposioHQ/awesome-claude-skills.git",
            "priority": 85,
            "license": "Apache-2.0",
        },
        {
            "url": "https://github.com/bobmatnyc/claude-mpm-skills.git",
            "priority": 80,
            "license": "MIT",
        },
        # High-priority community collections
        {
            "url": "https://github.com/VoltAgent/awesome-agent-skills.git",
            "priority": 95,
            "license": "MIT",
        },
        {
            "url": "https://github.com/sickn33/antigravity-awesome-skills.git",
            "priority": 94,
            "license": "MIT",
        },
        {
            "url": "https://github.com/alirezarezvani/claude-skills.git",
            "priority": 90,
            "license": "MIT",
        },
        {
            "url": "https://github.com/Jeffallan/claude-skills.git",
            "priority": 88,
            "license": "MIT",
        },
        # Domain-specific expert collections
        {
            "url": "https://github.com/K-Dense-AI/claude-scientific-skills.git",
            "priority": 85,
            "license": "MIT",
        },
        {
            "url": "https://github.com/Orchestra-Research/AI-Research-SKILLs.git",
            "priority": 85,
            "license": "MIT",
        },
        {
            "url": "https://github.com/addyosmani/web-quality-skills.git",
            "priority": 83,
            "license": "MIT",
        },
        {
            "url": "https://github.com/zxkane/aws-skills.git",
            "priority": 82,
            "license": "Apache-2.0",
        },
        {
            "url": "https://github.com/antonbabenko/terraform-skill.git",
            "priority": 82,
            "license": "MIT",
        },
        {
            "url": "https://github.com/secondsky/sap-skills.git",
            "priority": 80,
            "license": "MIT",
        },
    ]

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize repository manager.

        Args:
            base_dir: Base directory for storing repositories.
                     Defaults to ~/.mcp-skillset/repos/

        Migration Note:
        - Automatically migrates from JSON to SQLite on first use
        - JSON file backed up as repos.json.backup after successful migration
        - SQLite database provides O(1) indexed lookups vs O(n) JSON scans
        """
        self.base_dir = base_dir or Path.home() / ".mcp-skillset" / "repos"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.base_dir.parent / "repos.json"

        # Initialize SQLite metadata store
        db_path = self.base_dir.parent / "metadata.db"
        self.metadata_store = MetadataStore(db_path=db_path)

        # Auto-migrate from JSON if needed
        if self.metadata_file.exists() and not self.metadata_store.has_data():
            count = self.metadata_store.migrate_from_json(self.metadata_file)
            if count > 0:
                logger.info(f"Migrated {count} repositories from JSON to SQLite")
                # Backup JSON file after successful migration
                backup_path = self.metadata_file.with_suffix(".json.backup")
                shutil.move(str(self.metadata_file), str(backup_path))
                logger.info(f"JSON metadata backed up to {backup_path}")

    def add_repository(
        self, url: str, priority: int = 0, license: str = "Unknown"
    ) -> Repository:
        """Clone new repository.

        Args:
            url: Git repository URL
            priority: Priority for skill selection (0-100)
            license: Repository license (default: "Unknown")

        Returns:
            Repository metadata object

        Raises:
            ValueError: If URL is invalid or repository already exists

        Design Decision: Git Clone Strategy

        Rationale: Using GitPython's clone_from() for simplicity and Python integration.
        Direct subprocess calls would require manual error handling and platform-specific
        git binary management. GitPython provides consistent cross-platform behavior.

        Trade-offs:
        - Simplicity: GitPython handles git binary detection and error wrapping
        - Performance: Slightly slower than subprocess (~5-10% overhead for small repos)
        - Dependency: Requires GitPython library, but already in project dependencies

        Error Handling:
        - InvalidGitRepositoryError: URL is not a valid git repository
        - GitCommandError: Clone operation failed (network, permissions, etc.)
        - ValueError: Invalid priority range or duplicate repository
        """
        # 1. Validate URL
        if not self._is_valid_git_url(url):
            raise ValueError(f"Invalid git URL: {url}")

        # 2. Validate priority range
        if not 0 <= priority <= 100:
            raise ValueError(f"Priority must be between 0-100, got {priority}")

        # 3. Generate repository ID from URL
        repo_id = self._generate_repo_id(url)

        # 4. Check if already exists
        existing = self.get_repository(repo_id)
        if existing:
            raise ValueError(
                f"Repository already exists: {repo_id} at {existing.local_path}"
            )

        # 5. Clone repository using GitPython
        local_path = self.base_dir / repo_id
        logger.info(f"Cloning repository {url} to {local_path}")

        try:
            git.Repo.clone_from(url, local_path, depth=1)
        except git.exc.GitCommandError as e:
            raise ValueError(f"Failed to clone repository {url}: {e}") from e

        # 6. Scan for skills
        skill_count = self._count_skills(local_path)
        logger.info(f"Found {skill_count} skills in {repo_id}")

        # 7. Create Repository object
        repository = Repository(
            id=repo_id,
            url=url,
            local_path=local_path,
            priority=priority,
            last_updated=datetime.now(UTC),
            skill_count=skill_count,
            license=license,
        )

        # 8. Store metadata in SQLite
        self.metadata_store.add_repository(repository)

        return repository

    def add_repository_with_progress(
        self,
        url: str,
        priority: int = 0,
        license: str = "Unknown",
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> Repository:
        """Clone new repository with progress tracking.

        Args:
            url: Git repository URL
            priority: Priority for skill selection (0-100)
            license: Repository license (default: "Unknown")
            progress_callback: Called with (current, total, message) during clone

        Returns:
            Repository metadata object

        Raises:
            ValueError: If URL is invalid or repository already exists

        Design Decision: Progress Callback Pattern

        Rationale: Using optional callback parameter preserves backward compatibility
        while enabling rich progress displays in CLI. Callback pattern is simpler than
        event-based systems and avoids coupling service layer to UI libraries.

        Trade-offs:
        - Simplicity: Direct callback is easy to understand and test
        - Coupling: Caller controls UI but must handle progress updates
        - Flexibility: Works with any UI framework (Rich, tqdm, etc.)

        Error Handling:
        - InvalidGitRepositoryError: URL is not a valid git repository
        - GitCommandError: Clone operation failed (network, permissions, etc.)
        - ValueError: Invalid priority range or duplicate repository
        """
        # 1. Validate URL
        if not self._is_valid_git_url(url):
            raise ValueError(f"Invalid git URL: {url}")

        # 2. Validate priority range
        if not 0 <= priority <= 100:
            raise ValueError(f"Priority must be between 0-100, got {priority}")

        # 3. Generate repository ID from URL
        repo_id = self._generate_repo_id(url)

        # 4. Check if already exists
        existing = self.get_repository(repo_id)
        if existing:
            raise ValueError(
                f"Repository already exists: {repo_id} at {existing.local_path}"
            )

        # 5. Clone repository with progress tracking
        local_path = self.base_dir / repo_id
        logger.info(f"Cloning repository {url} to {local_path}")

        try:
            if progress_callback:
                progress_handler = CloneProgress(progress_callback)
                git.Repo.clone_from(url, local_path, depth=1, progress=progress_handler)
            else:
                git.Repo.clone_from(url, local_path, depth=1)
        except git.exc.GitCommandError as e:
            raise ValueError(f"Failed to clone repository {url}: {e}") from e

        # 6. Scan for skills
        skill_count = self._count_skills(local_path)
        logger.info(f"Found {skill_count} skills in {repo_id}")

        # 7. Create Repository object
        repository = Repository(
            id=repo_id,
            url=url,
            local_path=local_path,
            priority=priority,
            last_updated=datetime.now(UTC),
            skill_count=skill_count,
            license=license,
        )

        # 8. Store metadata in SQLite
        self.metadata_store.add_repository(repository)

        return repository

    def update_repository(self, repo_id: str) -> Repository:
        """Pull latest changes from repository.

        Args:
            repo_id: Repository identifier

        Returns:
            Updated repository metadata

        Raises:
            ValueError: If repository not found

        Error Handling:
        - ValueError: Repository not found in metadata
        - GitCommandError: Pull operation failed (network, conflicts, etc.)
        - InvalidGitRepositoryError: Local clone is corrupted

        Recovery Strategy:
        - Skill repos are read-only, so we fetch and hard reset to origin
        - This handles local changes and divergent branches automatically
        - If local repository is corrupted, consider re-cloning
        """
        # 1. Find repository by ID
        repository = self.get_repository(repo_id)
        if not repository:
            raise ValueError(f"Repository not found: {repo_id}")

        # 2. Git fetch and reset to origin (skill repos are read-only)
        logger.info(f"Updating repository {repo_id} from {repository.url}")

        try:
            repo = git.Repo(repository.local_path)
            origin = repo.remotes.origin
            # Fetch latest from origin
            origin.fetch()
            # Get the default branch (usually main or master)
            default_branch = repo.active_branch.name
            # Hard reset to origin - discards any local changes
            repo.head.reset(f"origin/{default_branch}", index=True, working_tree=True)
        except git.exc.InvalidGitRepositoryError as e:
            raise ValueError(
                f"Local repository is corrupted: {repository.local_path}. "
                f"Consider removing and re-cloning: {e}"
            ) from e
        except git.exc.GitCommandError as e:
            raise ValueError(f"Failed to update repository {repo_id}: {e}") from e

        # 3. Rescan for new/updated skills
        skill_count = self._count_skills(repository.local_path)
        logger.info(f"Rescanned {repo_id}: {skill_count} skills found")

        # 4. Update metadata
        repository.last_updated = datetime.now(UTC)
        repository.skill_count = skill_count

        # 5. Save updated metadata to SQLite
        self.metadata_store.update_repository(repository)

        return repository

    def update_repository_with_progress(
        self,
        repo_id: str,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> Repository:
        """Pull latest changes from repository with progress tracking.

        Args:
            repo_id: Repository identifier
            progress_callback: Called with (current, total, message) during pull

        Returns:
            Updated repository metadata

        Raises:
            ValueError: If repository not found

        Error Handling:
        - ValueError: Repository not found in metadata
        - GitCommandError: Pull operation failed (network, conflicts, etc.)
        - InvalidGitRepositoryError: Local clone is corrupted

        Recovery Strategy:
        - Skill repos are read-only, so we fetch and hard reset to origin
        - This handles local changes and divergent branches automatically
        - If local repository is corrupted, consider re-cloning
        """
        # 1. Find repository by ID
        repository = self.get_repository(repo_id)
        if not repository:
            raise ValueError(f"Repository not found: {repo_id}")

        # 2. Git fetch and reset to origin (skill repos are read-only)
        logger.info(f"Updating repository {repo_id} from {repository.url}")

        try:
            repo = git.Repo(repository.local_path)
            origin = repo.remotes.origin
            # Fetch latest from origin with optional progress
            if progress_callback:
                progress_handler = CloneProgress(progress_callback)
                origin.fetch(progress=progress_handler)
            else:
                origin.fetch()
            # Get the default branch (usually main or master)
            default_branch = repo.active_branch.name
            # Hard reset to origin - discards any local changes
            repo.head.reset(f"origin/{default_branch}", index=True, working_tree=True)
        except git.exc.InvalidGitRepositoryError as e:
            raise ValueError(
                f"Local repository is corrupted: {repository.local_path}. "
                f"Consider removing and re-cloning: {e}"
            ) from e
        except git.exc.GitCommandError as e:
            raise ValueError(f"Failed to update repository {repo_id}: {e}") from e

        # 3. Rescan for new/updated skills
        skill_count = self._count_skills(repository.local_path)
        logger.info(f"Rescanned {repo_id}: {skill_count} skills found")

        # 4. Update metadata
        repository.last_updated = datetime.now(UTC)
        repository.skill_count = skill_count

        # 5. Save updated metadata to SQLite
        self.metadata_store.update_repository(repository)

        return repository

    def list_repositories(self) -> list[Repository]:
        """List all configured repositories.

        Returns:
            List of Repository objects sorted by priority (highest first)

        Performance Note:
        - Time Complexity: O(n log n) due to ORDER BY in SQL
        - Space Complexity: O(n) for loading all repositories
        - Uses idx_repos_priority index for optimized sorting

        SQLite automatically uses the priority index for efficient sorting
        without requiring full table scan.
        """
        return self.metadata_store.list_repositories()

    def remove_repository(self, repo_id: str) -> None:
        """Remove repository and its skills.

        Args:
            repo_id: Repository identifier to remove

        Raises:
            ValueError: If repository not found

        Error Handling:
        - ValueError: Repository not found in metadata
        - OSError: File deletion failed (permissions, locked files)

        Data Consistency:
        - Metadata is removed atomically with temp file strategy
        - If directory deletion fails after metadata removal, directory is orphaned
        - Future enhancement: Two-phase commit for atomic operation

        Failure Recovery:
        - Orphaned directories can be manually deleted from base_dir
        - Re-running remove will fail (metadata already gone) but directory remains
        - Consider: Mark as deleted in metadata, then cleanup in background
        """
        # 1. Find repository by ID
        repository = self.get_repository(repo_id)
        if not repository:
            raise ValueError(f"Repository not found: {repo_id}")

        logger.info(f"Removing repository {repo_id} from {repository.local_path}")

        # 2. Delete local clone
        try:
            if repository.local_path.exists():
                shutil.rmtree(repository.local_path)
                logger.info(f"Deleted local clone at {repository.local_path}")
        except OSError as e:
            logger.error(f"Failed to delete repository directory: {e}")
            raise ValueError(
                f"Failed to delete repository directory {repository.local_path}: {e}"
            ) from e

        # 3. Remove from metadata storage (SQLite with CASCADE deletes skills)
        # Note: Skill index removal will be handled by SkillManager (Task 4)
        # and ChromaDB integration (Task 5) in later phases
        self.metadata_store.delete_repository(repo_id)

    def get_repository(self, repo_id: str) -> Repository | None:
        """Get repository by ID.

        Args:
            repo_id: Repository identifier

        Returns:
            Repository object or None if not found

        Performance:
        - Time Complexity: O(1) via SQLite primary key index
        - Direct lookup without table scan
        """
        return self.metadata_store.get_repository(repo_id)

    # Private helper methods

    def _is_valid_git_url(self, url: str) -> bool:
        """Validate git repository URL format.

        Args:
            url: URL to validate

        Returns:
            True if URL appears to be a valid git repository URL

        Supported Formats:
        - HTTPS: https://github.com/user/repo.git
        - SSH: git@github.com:user/repo.git
        - Git protocol: git://github.com/user/repo.git

        Note: This is basic format validation, not network reachability check.
        Actual repository validity is tested during clone operation.
        """
        if not url:
            return False

        # HTTPS URLs
        if url.startswith("https://") or url.startswith("http://"):
            try:
                parsed = urlparse(url)
                # Must have scheme, netloc, and path
                return bool(parsed.scheme and parsed.netloc and parsed.path)
            except Exception:
                return False

        # SSH URLs (git@host:path/to/repo.git)
        if url.startswith("git@"):
            # Basic validation: must contain colon separator
            return ":" in url

        # Git protocol URLs
        return bool(url.startswith("git://"))

    def _generate_repo_id(self, url: str) -> str:
        """Generate repository ID from URL.

        Args:
            url: Git repository URL

        Returns:
            Repository ID in format "owner/repo" or "hostname/owner/repo"

        Examples:
            "https://github.com/anthropics/skills.git" -> "anthropics/skills"
            "git@github.com:obra/superpowers.git" -> "obra/superpowers"
            "https://gitlab.com/group/subgroup/project.git" -> "group/subgroup/project"

        Design Decision: ID Format

        Rationale: Use path-based IDs that preserve repository identity across
        different clone URLs (HTTPS vs SSH). This allows identifying duplicates
        when users add same repo with different URL formats.

        Trade-offs:
        - Uniqueness: Path-based IDs work for GitHub/GitLab style URLs
        - Collisions: Rare, but possible for self-hosted repos with same path
        - Readability: IDs are human-readable and match repo names
        """
        # Remove .git suffix if present
        clean_url = url.rstrip("/")
        if clean_url.endswith(".git"):
            clean_url = clean_url[:-4]

        # Handle SSH URLs (git@host:path)
        if url.startswith("git@") and ":" in clean_url:
            # Extract path after colon
            path = clean_url.split(":", 1)[1]
            return path.strip("/")

        # Handle HTTPS/HTTP/Git URLs
        try:
            parsed = urlparse(clean_url)
            # Extract path without leading slash
            path = parsed.path.lstrip("/")
            return path
        except Exception:
            # Fallback: use sanitized URL as ID
            return re.sub(r"[^a-zA-Z0-9_-]", "_", clean_url)

    def _count_skills(self, repo_path: Path) -> int:
        """Count SKILL.md files in repository.

        Args:
            repo_path: Path to repository root

        Returns:
            Number of skill files found

        Performance:
        - Time Complexity: O(n) where n = total files in repo
        - Optimization: Could cache results and only rescan changed files

        Future Enhancement:
        - Use watchdog for incremental updates
        - Store skill metadata during scan for faster access
        """
        skill_files = list(repo_path.rglob("SKILL.md"))
        return len(skill_files)
