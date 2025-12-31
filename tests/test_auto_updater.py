"""Tests for auto-update service."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_skills.models.config import AutoUpdateConfig
from mcp_skills.models.repository import Repository
from mcp_skills.services.auto_updater import AutoUpdater
from mcp_skills.services.indexing.engine import IndexStats


class TestAutoUpdater:
    """Test suite for AutoUpdater service."""

    @pytest.fixture
    def mock_repo_manager(self) -> MagicMock:
        """Create mock RepositoryManager."""
        manager = MagicMock()
        manager.list_repositories = MagicMock(return_value=[])
        manager.update_repository = MagicMock()
        return manager

    @pytest.fixture
    def mock_indexing_engine(self) -> MagicMock:
        """Create mock IndexingEngine."""
        engine = MagicMock()
        engine.reindex_all = MagicMock(
            return_value=IndexStats(
                total_skills=10,
                vector_store_size=20480,
                graph_nodes=10,
                graph_edges=30,
                last_indexed="2024-01-01T12:00:00",
            )
        )
        return engine

    @pytest.fixture
    def default_config(self) -> AutoUpdateConfig:
        """Create default AutoUpdateConfig."""
        return AutoUpdateConfig(enabled=True, max_age_hours=24)

    @pytest.fixture
    def auto_updater(
        self,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
        default_config: AutoUpdateConfig,
    ) -> AutoUpdater:
        """Create AutoUpdater instance with mocks."""
        return AutoUpdater(
            repo_manager=mock_repo_manager,
            indexing_engine=mock_indexing_engine,
            config=default_config,
        )

    def test_initialization(
        self,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
        default_config: AutoUpdateConfig,
    ) -> None:
        """Test AutoUpdater can be initialized."""
        updater = AutoUpdater(
            repo_manager=mock_repo_manager,
            indexing_engine=mock_indexing_engine,
            config=default_config,
        )
        assert updater is not None
        assert updater.repo_manager == mock_repo_manager
        assert updater.indexing_engine == mock_indexing_engine
        assert updater.config == default_config

    def test_check_and_update_disabled(
        self,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
    ) -> None:
        """Test auto-update does nothing when disabled."""
        config = AutoUpdateConfig(enabled=False, max_age_hours=24)
        updater = AutoUpdater(
            repo_manager=mock_repo_manager,
            indexing_engine=mock_indexing_engine,
            config=config,
        )

        updater.check_and_update()

        # Should not call any methods
        mock_repo_manager.list_repositories.assert_not_called()
        mock_repo_manager.update_repository.assert_not_called()
        mock_indexing_engine.reindex_all.assert_not_called()

    def test_check_and_update_no_repositories(
        self,
        auto_updater: AutoUpdater,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
    ) -> None:
        """Test auto-update handles no repositories gracefully."""
        mock_repo_manager.list_repositories.return_value = []

        auto_updater.check_and_update()

        # Should list repositories but not update or reindex
        mock_repo_manager.list_repositories.assert_called_once()
        mock_repo_manager.update_repository.assert_not_called()
        mock_indexing_engine.reindex_all.assert_not_called()

    def test_check_and_update_fresh_repositories(
        self,
        auto_updater: AutoUpdater,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test auto-update skips fresh repositories."""
        # Create fresh repository (updated 1 hour ago)
        fresh_repo = Repository(
            id="test/fresh",
            url="https://github.com/test/fresh.git",
            local_path=tmp_path / "fresh",
            priority=50,
            last_updated=datetime.now(UTC) - timedelta(hours=1),
            skill_count=5,
            license="MIT",
        )
        mock_repo_manager.list_repositories.return_value = [fresh_repo]

        auto_updater.check_and_update()

        # Should list repositories but not update
        mock_repo_manager.list_repositories.assert_called_once()
        mock_repo_manager.update_repository.assert_not_called()
        mock_indexing_engine.reindex_all.assert_not_called()

    def test_check_and_update_stale_repository(
        self,
        auto_updater: AutoUpdater,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test auto-update updates stale repository."""
        # Create stale repository (updated 48 hours ago, threshold is 24 hours)
        stale_repo = Repository(
            id="test/stale",
            url="https://github.com/test/stale.git",
            local_path=tmp_path / "stale",
            priority=50,
            last_updated=datetime.now(UTC) - timedelta(hours=48),
            skill_count=5,
            license="MIT",
        )

        # Updated repository with same skill count (no reindex needed)
        updated_repo = Repository(
            id="test/stale",
            url="https://github.com/test/stale.git",
            local_path=tmp_path / "stale",
            priority=50,
            last_updated=datetime.now(UTC),
            skill_count=5,  # Same count
            license="MIT",
        )

        mock_repo_manager.list_repositories.return_value = [stale_repo]
        mock_repo_manager.update_repository.return_value = updated_repo

        auto_updater.check_and_update()

        # Should update repository but not reindex (skill count unchanged)
        mock_repo_manager.list_repositories.assert_called_once()
        mock_repo_manager.update_repository.assert_called_once_with("test/stale")
        mock_indexing_engine.reindex_all.assert_not_called()

    def test_check_and_update_triggers_reindex(
        self,
        auto_updater: AutoUpdater,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test auto-update triggers reindex when skill count changes."""
        # Create stale repository with 5 skills
        stale_repo = Repository(
            id="test/stale",
            url="https://github.com/test/stale.git",
            local_path=tmp_path / "stale",
            priority=50,
            last_updated=datetime.now(UTC) - timedelta(hours=48),
            skill_count=5,
            license="MIT",
        )

        # Updated repository with 10 skills (reindex needed)
        updated_repo = Repository(
            id="test/stale",
            url="https://github.com/test/stale.git",
            local_path=tmp_path / "stale",
            priority=50,
            last_updated=datetime.now(UTC),
            skill_count=10,  # Changed!
            license="MIT",
        )

        mock_repo_manager.list_repositories.return_value = [stale_repo]
        mock_repo_manager.update_repository.return_value = updated_repo

        auto_updater.check_and_update()

        # Should update repository AND reindex (skill count changed)
        mock_repo_manager.list_repositories.assert_called_once()
        mock_repo_manager.update_repository.assert_called_once_with("test/stale")
        mock_indexing_engine.reindex_all.assert_called_once_with(force=True)

    def test_check_and_update_multiple_repositories(
        self,
        auto_updater: AutoUpdater,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test auto-update handles multiple repositories correctly."""
        now = datetime.now(UTC)

        # Mix of fresh and stale repositories
        fresh_repo = Repository(
            id="test/fresh",
            url="https://github.com/test/fresh.git",
            local_path=tmp_path / "fresh",
            priority=50,
            last_updated=now - timedelta(hours=1),
            skill_count=5,
            license="MIT",
        )

        stale_repo1 = Repository(
            id="test/stale1",
            url="https://github.com/test/stale1.git",
            local_path=tmp_path / "stale1",
            priority=60,
            last_updated=now - timedelta(hours=48),
            skill_count=3,
            license="MIT",
        )

        stale_repo2 = Repository(
            id="test/stale2",
            url="https://github.com/test/stale2.git",
            local_path=tmp_path / "stale2",
            priority=70,
            last_updated=now - timedelta(hours=72),
            skill_count=7,
            license="Apache-2.0",
        )

        # Updated repositories
        updated_repo1 = Repository(
            id="test/stale1",
            url="https://github.com/test/stale1.git",
            local_path=tmp_path / "stale1",
            priority=60,
            last_updated=now,
            skill_count=4,  # Changed
            license="MIT",
        )

        updated_repo2 = Repository(
            id="test/stale2",
            url="https://github.com/test/stale2.git",
            local_path=tmp_path / "stale2",
            priority=70,
            last_updated=now,
            skill_count=7,  # Same
            license="Apache-2.0",
        )

        mock_repo_manager.list_repositories.return_value = [
            fresh_repo,
            stale_repo1,
            stale_repo2,
        ]

        # Mock update calls to return updated repos
        def update_side_effect(repo_id: str) -> Repository:
            if repo_id == "test/stale1":
                return updated_repo1
            elif repo_id == "test/stale2":
                return updated_repo2
            raise ValueError(f"Unexpected repo_id: {repo_id}")

        mock_repo_manager.update_repository.side_effect = update_side_effect

        auto_updater.check_and_update()

        # Should update only stale repositories
        assert mock_repo_manager.update_repository.call_count == 2
        mock_repo_manager.update_repository.assert_any_call("test/stale1")
        mock_repo_manager.update_repository.assert_any_call("test/stale2")

        # Should reindex because skill count changed (3+7=10 before, 4+7=11 after)
        mock_indexing_engine.reindex_all.assert_called_once_with(force=True)

    def test_check_and_update_handles_update_failure(
        self,
        auto_updater: AutoUpdater,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test auto-update continues after update failure."""
        stale_repo1 = Repository(
            id="test/stale1",
            url="https://github.com/test/stale1.git",
            local_path=tmp_path / "stale1",
            priority=50,
            last_updated=datetime.now(UTC) - timedelta(hours=48),
            skill_count=5,
            license="MIT",
        )

        stale_repo2 = Repository(
            id="test/stale2",
            url="https://github.com/test/stale2.git",
            local_path=tmp_path / "stale2",
            priority=60,
            last_updated=datetime.now(UTC) - timedelta(hours=48),
            skill_count=3,
            license="MIT",
        )

        updated_repo2 = Repository(
            id="test/stale2",
            url="https://github.com/test/stale2.git",
            local_path=tmp_path / "stale2",
            priority=60,
            last_updated=datetime.now(UTC),
            skill_count=3,
            license="MIT",
        )

        mock_repo_manager.list_repositories.return_value = [stale_repo1, stale_repo2]

        # First update fails, second succeeds
        def update_side_effect(repo_id: str) -> Repository:
            if repo_id == "test/stale1":
                raise ValueError("Network error")
            elif repo_id == "test/stale2":
                return updated_repo2
            raise ValueError(f"Unexpected repo_id: {repo_id}")

        mock_repo_manager.update_repository.side_effect = update_side_effect

        # Should not raise exception
        auto_updater.check_and_update()

        # Should attempt both updates
        assert mock_repo_manager.update_repository.call_count == 2

        # Should not reindex (no skill count change)
        mock_indexing_engine.reindex_all.assert_not_called()

    def test_check_and_update_handles_reindex_failure(
        self,
        auto_updater: AutoUpdater,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test auto-update handles reindex failure gracefully."""
        stale_repo = Repository(
            id="test/stale",
            url="https://github.com/test/stale.git",
            local_path=tmp_path / "stale",
            priority=50,
            last_updated=datetime.now(UTC) - timedelta(hours=48),
            skill_count=5,
            license="MIT",
        )

        updated_repo = Repository(
            id="test/stale",
            url="https://github.com/test/stale.git",
            local_path=tmp_path / "stale",
            priority=50,
            last_updated=datetime.now(UTC),
            skill_count=10,  # Changed - triggers reindex
            license="MIT",
        )

        mock_repo_manager.list_repositories.return_value = [stale_repo]
        mock_repo_manager.update_repository.return_value = updated_repo

        # Make reindex fail
        mock_indexing_engine.reindex_all.side_effect = RuntimeError("ChromaDB error")

        # Should not raise exception
        auto_updater.check_and_update()

        # Should still have attempted update and reindex
        mock_repo_manager.update_repository.assert_called_once_with("test/stale")
        mock_indexing_engine.reindex_all.assert_called_once_with(force=True)

    def test_check_and_update_custom_max_age(
        self,
        mock_repo_manager: MagicMock,
        mock_indexing_engine: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test auto-update respects custom max_age_hours."""
        # Config with 48 hour threshold
        config = AutoUpdateConfig(enabled=True, max_age_hours=48)
        updater = AutoUpdater(
            repo_manager=mock_repo_manager,
            indexing_engine=mock_indexing_engine,
            config=config,
        )

        # Repository updated 36 hours ago (fresh with 48h threshold)
        repo = Repository(
            id="test/repo",
            url="https://github.com/test/repo.git",
            local_path=tmp_path / "repo",
            priority=50,
            last_updated=datetime.now(UTC) - timedelta(hours=36),
            skill_count=5,
            license="MIT",
        )

        mock_repo_manager.list_repositories.return_value = [repo]

        updater.check_and_update()

        # Should not update (within 48 hour threshold)
        mock_repo_manager.update_repository.assert_not_called()
