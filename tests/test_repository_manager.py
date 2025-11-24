"""Tests for repository management service."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import git
import pytest

from mcp_skills.services.repository_manager import Repository, RepositoryManager


class TestRepository:
    """Test suite for Repository dataclass."""

    def test_repository_to_dict(self, tmp_path: Path) -> None:
        """Test converting Repository to dictionary."""
        repo = Repository(
            id="test/repo",
            url="https://github.com/test/repo.git",
            local_path=tmp_path / "test/repo",
            priority=50,
            last_updated=datetime(2024, 1, 1, 12, 0, 0),
            skill_count=5,
            license="MIT",
        )

        data = repo.to_dict()

        assert data["id"] == "test/repo"
        assert data["url"] == "https://github.com/test/repo.git"
        assert data["local_path"] == str(tmp_path / "test/repo")
        assert data["priority"] == 50
        assert data["last_updated"] == "2024-01-01T12:00:00"
        assert data["skill_count"] == 5
        assert data["license"] == "MIT"

    def test_repository_from_dict(self, tmp_path: Path) -> None:
        """Test creating Repository from dictionary."""
        data = {
            "id": "test/repo",
            "url": "https://github.com/test/repo.git",
            "local_path": str(tmp_path / "test/repo"),
            "priority": 50,
            "last_updated": "2024-01-01T12:00:00",
            "skill_count": 5,
            "license": "MIT",
        }

        repo = Repository.from_dict(data)

        assert repo.id == "test/repo"
        assert repo.url == "https://github.com/test/repo.git"
        assert repo.local_path == tmp_path / "test/repo"
        assert repo.priority == 50
        assert repo.last_updated == datetime(2024, 1, 1, 12, 0, 0)
        assert repo.skill_count == 5
        assert repo.license == "MIT"


class TestRepositoryManager:
    """Test suite for RepositoryManager."""

    def test_manager_initialization(self, tmp_path: Path) -> None:
        """Test repository manager can be initialized."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")
        assert manager is not None
        assert manager.base_dir.exists()
        # metadata_file is in parent of base_dir
        assert manager.metadata_file == tmp_path / "repos.json"

    def test_default_repos_defined(self) -> None:
        """Test default repositories are defined."""
        assert hasattr(RepositoryManager, "DEFAULT_REPOS")
        assert isinstance(RepositoryManager.DEFAULT_REPOS, list)
        assert len(RepositoryManager.DEFAULT_REPOS) > 0

    def test_list_repositories_returns_list(self, tmp_path: Path) -> None:
        """Test list_repositories returns empty list initially."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")
        repos = manager.list_repositories()

        assert isinstance(repos, list)
        assert len(repos) == 0

    def test_get_repository_returns_optional(self, tmp_path: Path) -> None:
        """Test get_repository returns None for non-existent repo."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")
        repo = manager.get_repository("non-existent")

        assert repo is None

    def test_add_repository_validates_url(self, tmp_path: Path) -> None:
        """Test add_repository validates git URL format."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        with pytest.raises(ValueError, match="Invalid git URL"):
            manager.add_repository(url="not-a-valid-url", priority=50)

        with pytest.raises(ValueError, match="Invalid git URL"):
            manager.add_repository(url="", priority=50)

    def test_add_repository_validates_priority(self, tmp_path: Path) -> None:
        """Test add_repository validates priority range."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        with pytest.raises(ValueError, match="Priority must be between 0-100"):
            manager.add_repository(url="https://github.com/test/repo.git", priority=-1)

        with pytest.raises(ValueError, match="Priority must be between 0-100"):
            manager.add_repository(url="https://github.com/test/repo.git", priority=101)

    @patch("git.Repo.clone_from")
    def test_add_repository_clones_successfully(
        self, mock_clone: MagicMock, tmp_path: Path
    ) -> None:
        """Test add_repository clones repository."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Create fake skill files
        repo_path = tmp_path / "repos" / "test/repo"
        repo_path.mkdir(parents=True)
        (repo_path / "SKILL.md").write_text("# Test Skill")

        repo = manager.add_repository(
            url="https://github.com/test/repo.git", priority=50, license="MIT"
        )

        # Verify clone was called
        mock_clone.assert_called_once()
        assert mock_clone.call_args[0][0] == "https://github.com/test/repo.git"

        # Verify repository metadata
        assert repo.id == "test/repo"
        assert repo.url == "https://github.com/test/repo.git"
        assert repo.priority == 50
        assert repo.license == "MIT"
        assert repo.skill_count == 1

    @patch("git.Repo.clone_from")
    def test_add_repository_detects_duplicates(
        self, mock_clone: MagicMock, tmp_path: Path
    ) -> None:
        """Test add_repository prevents duplicate repositories."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Create fake repo directory
        repo_path = tmp_path / "repos" / "test/repo"
        repo_path.mkdir(parents=True)

        # Add first repository
        manager.add_repository(
            url="https://github.com/test/repo.git", priority=50, license="MIT"
        )

        # Try to add duplicate
        with pytest.raises(ValueError, match="Repository already exists"):
            manager.add_repository(
                url="https://github.com/test/repo.git", priority=60, license="MIT"
            )

    @patch("git.Repo.clone_from")
    def test_add_repository_handles_clone_failure(
        self, mock_clone: MagicMock, tmp_path: Path
    ) -> None:
        """Test add_repository handles git clone failures."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Simulate clone failure
        mock_clone.side_effect = git.exc.GitCommandError(
            "clone", "fatal: repository not found"
        )

        with pytest.raises(ValueError, match="Failed to clone repository"):
            manager.add_repository(
                url="https://github.com/test/nonexistent.git", priority=50
            )

    @patch("git.Repo.clone_from")
    def test_list_repositories_sorted_by_priority(
        self, mock_clone: MagicMock, tmp_path: Path
    ) -> None:
        """Test list_repositories returns repos sorted by priority."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Create multiple repos with different priorities
        for name, priority in [("repo1", 30), ("repo2", 90), ("repo3", 50)]:
            repo_path = tmp_path / "repos" / f"test/{name}"
            repo_path.mkdir(parents=True)
            manager.add_repository(
                url=f"https://github.com/test/{name}.git",
                priority=priority,
                license="MIT",
            )

        repos = manager.list_repositories()

        # Verify sorted by priority descending
        assert len(repos) == 3
        assert repos[0].priority == 90
        assert repos[1].priority == 50
        assert repos[2].priority == 30

    @patch("git.Repo.clone_from")
    def test_get_repository_finds_existing(
        self, mock_clone: MagicMock, tmp_path: Path
    ) -> None:
        """Test get_repository finds existing repository."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Add repository
        repo_path = tmp_path / "repos" / "test/repo"
        repo_path.mkdir(parents=True)
        added = manager.add_repository(
            url="https://github.com/test/repo.git", priority=50, license="MIT"
        )

        # Retrieve repository
        found = manager.get_repository("test/repo")

        assert found is not None
        assert found.id == added.id
        assert found.url == added.url

    @patch("git.Repo")
    @patch("git.Repo.clone_from")
    def test_update_repository_pulls_changes(
        self, mock_clone: MagicMock, mock_repo_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test update_repository pulls latest changes."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Add repository
        repo_path = tmp_path / "repos" / "test/repo"
        repo_path.mkdir(parents=True)
        (repo_path / "SKILL.md").write_text("# Skill 1")
        manager.add_repository(
            url="https://github.com/test/repo.git", priority=50, license="MIT"
        )

        # Mock git operations for update
        mock_repo_instance = MagicMock()
        mock_origin = MagicMock()
        mock_repo_instance.remotes.origin = mock_origin
        mock_repo_class.return_value = mock_repo_instance

        # Add new skill file to simulate changes
        (repo_path / "subdir").mkdir()
        (repo_path / "subdir" / "SKILL.md").write_text("# Skill 2")

        # Update repository
        updated = manager.update_repository("test/repo")

        # Verify pull was called
        mock_origin.pull.assert_called_once()

        # Verify skill count updated
        assert updated.skill_count == 2

    def test_update_repository_not_found(self, tmp_path: Path) -> None:
        """Test update_repository raises error for non-existent repo."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        with pytest.raises(ValueError, match="Repository not found"):
            manager.update_repository("non-existent")

    @patch("git.Repo")
    @patch("git.Repo.clone_from")
    def test_update_repository_handles_pull_failure(
        self, mock_clone: MagicMock, mock_repo_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test update_repository handles git pull failures."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Add repository
        repo_path = tmp_path / "repos" / "test/repo"
        repo_path.mkdir(parents=True)
        manager.add_repository(
            url="https://github.com/test/repo.git", priority=50, license="MIT"
        )

        # Mock git pull failure
        mock_repo_instance = MagicMock()
        mock_origin = MagicMock()
        mock_origin.pull.side_effect = git.exc.GitCommandError(
            "pull", "fatal: unable to access repository"
        )
        mock_repo_instance.remotes.origin = mock_origin
        mock_repo_class.return_value = mock_repo_instance

        with pytest.raises(ValueError, match="Failed to update repository"):
            manager.update_repository("test/repo")

    @patch("git.Repo.clone_from")
    def test_remove_repository_deletes_successfully(
        self, mock_clone: MagicMock, tmp_path: Path
    ) -> None:
        """Test remove_repository deletes repo and metadata."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Add repository
        repo_path = tmp_path / "repos" / "test/repo"
        repo_path.mkdir(parents=True)
        manager.add_repository(
            url="https://github.com/test/repo.git", priority=50, license="MIT"
        )

        # Verify it exists
        assert manager.get_repository("test/repo") is not None
        assert repo_path.exists()

        # Remove repository
        manager.remove_repository("test/repo")

        # Verify it's gone
        assert manager.get_repository("test/repo") is None
        assert not repo_path.exists()

    def test_remove_repository_not_found(self, tmp_path: Path) -> None:
        """Test remove_repository raises error for non-existent repo."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        with pytest.raises(ValueError, match="Repository not found"):
            manager.remove_repository("non-existent")

    def test_metadata_persistence_across_instances(self, tmp_path: Path) -> None:
        """Test repository metadata persists across manager instances."""
        with patch("git.Repo.clone_from"):
            # Create first manager and add repository
            manager1 = RepositoryManager(base_dir=tmp_path / "repos")
            repo_path = tmp_path / "repos" / "test/repo"
            repo_path.mkdir(parents=True)
            manager1.add_repository(
                url="https://github.com/test/repo.git", priority=50, license="MIT"
            )

            # Create second manager instance
            manager2 = RepositoryManager(base_dir=tmp_path / "repos")
            repos = manager2.list_repositories()

            # Verify repository was persisted
            assert len(repos) == 1
            assert repos[0].id == "test/repo"

    def test_generate_repo_id_https(self, tmp_path: Path) -> None:
        """Test repository ID generation from HTTPS URLs."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        assert (
            manager._generate_repo_id("https://github.com/anthropics/skills.git")
            == "anthropics/skills"
        )
        assert manager._generate_repo_id("https://github.com/test/repo") == "test/repo"

    def test_generate_repo_id_ssh(self, tmp_path: Path) -> None:
        """Test repository ID generation from SSH URLs."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        assert (
            manager._generate_repo_id("git@github.com:anthropics/skills.git")
            == "anthropics/skills"
        )

    def test_count_skills(self, tmp_path: Path) -> None:
        """Test skill counting in repository."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Create test repository with skills
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        (repo_path / "SKILL.md").write_text("# Root Skill")
        (repo_path / "subdir1").mkdir()
        (repo_path / "subdir1" / "SKILL.md").write_text("# Subdir1 Skill")
        (repo_path / "subdir2").mkdir()
        (repo_path / "subdir2" / "SKILL.md").write_text("# Subdir2 Skill")

        count = manager._count_skills(repo_path)
        assert count == 3

    def test_is_valid_git_url(self, tmp_path: Path) -> None:
        """Test git URL validation."""
        manager = RepositoryManager(base_dir=tmp_path / "repos")

        # Valid URLs
        assert manager._is_valid_git_url("https://github.com/test/repo.git")
        assert manager._is_valid_git_url("http://github.com/test/repo")
        assert manager._is_valid_git_url("git@github.com:test/repo.git")
        assert manager._is_valid_git_url("git://github.com/test/repo.git")

        # Invalid URLs
        assert not manager._is_valid_git_url("")
        assert not manager._is_valid_git_url("not-a-url")
        assert not manager._is_valid_git_url("ftp://example.com/repo")
