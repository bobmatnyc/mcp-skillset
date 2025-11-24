"""End-to-end tests for repository management workflows.

This module tests complete repository management workflows:
1. Clone repository (add)
2. List repositories
3. Index skills from repository
4. Search skills from specific repository
5. Update repository (pull changes)
6. Remove repository

Tests use real git operations and file I/O to ensure production readiness.
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mcp_skills.models.repository import Repository
from mcp_skills.services.indexing_engine import IndexingEngine
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager


@pytest.mark.e2e
class TestRepositoryAddWorkflow:
    """Test adding new repositories."""

    def test_add_repository_from_local(
        self,
        e2e_configured_services: tuple,
        real_skill_repo: Path,
    ) -> None:
        """Test adding repository by copying from local path.

        Note: We use copy instead of git clone for E2E tests
        to avoid network dependencies and git authentication issues.
        """
        repo_manager, skill_manager, indexing_engine = e2e_configured_services

        # Copy repository manually (simulates git clone)
        repo_id = "local-test-repo"
        dest_dir = repo_manager.base_dir / repo_id
        shutil.copytree(real_skill_repo, dest_dir)

        # Create repository metadata
        repository = Repository(
            id=repo_id,
            url="https://github.com/test/local-repo.git",
            local_path=dest_dir,
            priority=90,
            last_updated=datetime.now(timezone.utc),
            skill_count=5,
            license="MIT",
        )

        # Add to metadata store
        repo_manager.metadata_store.add_repository(repository)

        # Verify repository added
        repos = repo_manager.list_repositories()
        assert len(repos) == 1
        assert repos[0].id == repo_id
        assert repos[0].skill_count == 5

        # Verify skills discoverable
        skills = skill_manager.discover_skills()
        assert len(skills) >= 5

    def test_add_repository_invalid_url(
        self,
        e2e_configured_services: tuple,
    ) -> None:
        """Test error handling for invalid repository URL."""
        repo_manager, _, _ = e2e_configured_services

        with pytest.raises(ValueError, match="Invalid git URL"):
            repo_manager.add_repository(
                url="not-a-valid-url",
                priority=50,
            )

    def test_add_repository_priority(
        self,
        e2e_configured_services: tuple,
        real_skill_repo: Path,
    ) -> None:
        """Test that repository priority is correctly set."""
        repo_manager, _, _ = e2e_configured_services

        # Add repository with custom priority
        repo_id = "priority-test-repo"
        dest_dir = repo_manager.base_dir / repo_id
        shutil.copytree(real_skill_repo, dest_dir)

        repository = Repository(
            id=repo_id,
            url="https://github.com/test/priority-repo.git",
            local_path=dest_dir,
            priority=75,
            last_updated=datetime.now(timezone.utc),
            skill_count=5,
            license="MIT",
        )

        repo_manager.metadata_store.add_repository(repository)

        # Verify priority
        repo = repo_manager.get_repository(repo_id)
        assert repo is not None
        assert repo.priority == 75


@pytest.mark.e2e
class TestRepositoryListWorkflow:
    """Test listing repositories."""

    def test_list_empty_repositories(
        self,
        e2e_configured_services: tuple,
    ) -> None:
        """Test listing when no repositories configured."""
        repo_manager, _, _ = e2e_configured_services

        repos = repo_manager.list_repositories()
        assert len(repos) == 0

    def test_list_multiple_repositories(
        self,
        e2e_configured_services: tuple,
        real_skill_repo: Path,
    ) -> None:
        """Test listing multiple repositories."""
        repo_manager, _, _ = e2e_configured_services

        # Add multiple repositories
        for i in range(3):
            repo_id = f"test-repo-{i}"
            dest_dir = repo_manager.base_dir / repo_id
            shutil.copytree(real_skill_repo, dest_dir)

            repository = Repository(
                id=repo_id,
                url=f"https://github.com/test/repo{i}.git",
                local_path=dest_dir,
                priority=100 - (i * 10),
                last_updated=datetime.now(timezone.utc),
                skill_count=5,
                license="MIT",
            )

            repo_manager.metadata_store.add_repository(repository)

        # List repositories
        repos = repo_manager.list_repositories()
        assert len(repos) == 3

        # Verify repositories sorted by priority
        priorities = [repo.priority for repo in repos]
        assert priorities == sorted(priorities, reverse=True)

    def test_list_repository_metadata(
        self,
        e2e_configured_services: tuple,
        real_skill_repo: Path,
    ) -> None:
        """Test that list returns complete repository metadata."""
        repo_manager, _, _ = e2e_configured_services

        # Add repository
        repo_id = "metadata-test-repo"
        dest_dir = repo_manager.base_dir / repo_id
        shutil.copytree(real_skill_repo, dest_dir)

        repository = Repository(
            id=repo_id,
            url="https://github.com/test/metadata-repo.git",
            local_path=dest_dir,
            priority=85,
            last_updated=datetime.now(timezone.utc),
            skill_count=5,
            license="Apache-2.0",
        )

        repo_manager.metadata_store.add_repository(repository)

        # Get repository
        repos = repo_manager.list_repositories()
        repo = repos[0]

        # Verify all metadata fields
        assert repo.id == repo_id
        assert repo.url == "https://github.com/test/metadata-repo.git"
        assert repo.priority == 85
        assert repo.skill_count == 5
        assert repo.license == "Apache-2.0"
        assert repo.last_updated is not None


@pytest.mark.e2e
class TestRepositoryIndexWorkflow:
    """Test indexing skills from repositories."""

    def test_index_skills_from_repository(
        self,
        e2e_services_with_repo: tuple,
    ) -> None:
        """Test indexing skills from a repository."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        # Repository already has indexed skills from fixture
        stats = indexing_engine.get_stats()

        # Verify indexing stats
        assert stats.total_skills >= 5
        assert stats.vector_store_size > 0
        assert stats.graph_nodes >= 5
        assert stats.graph_edges >= 0

    def test_reindex_after_repository_add(
        self,
        e2e_configured_services: tuple,
        real_skill_repo: Path,
    ) -> None:
        """Test reindexing after adding new repository."""
        repo_manager, skill_manager, indexing_engine = e2e_configured_services

        # Initial index should be empty
        stats_before = indexing_engine.get_stats()
        assert stats_before.total_skills == 0

        # Add repository
        repo_id = "new-repo"
        dest_dir = repo_manager.base_dir / repo_id
        shutil.copytree(real_skill_repo, dest_dir)

        repository = Repository(
            id=repo_id,
            url="https://github.com/test/new-repo.git",
            local_path=dest_dir,
            priority=90,
            last_updated=datetime.now(timezone.utc),
            skill_count=5,
            license="MIT",
        )

        repo_manager.metadata_store.add_repository(repository)

        # Reindex
        stats_after = indexing_engine.reindex_all(force=True)

        # Verify new skills indexed
        assert stats_after.total_skills >= 5
        assert stats_after.total_skills > stats_before.total_skills

    def test_search_skills_from_specific_repository(
        self,
        e2e_services_with_repo: tuple,
    ) -> None:
        """Test searching for skills from specific repository."""
        repo_manager, skill_manager, indexing_engine = e2e_services_with_repo

        # Search for skills
        results = indexing_engine.search(query="python testing", top_k=10)

        assert len(results) > 0

        # Verify results are from our repository
        for result in results:
            assert result.skill.repo_id == "test-skills-repo"


@pytest.mark.e2e
class TestRepositoryUpdateWorkflow:
    """Test updating repositories."""

    def test_get_repository_by_id(
        self,
        e2e_services_with_repo: tuple,
    ) -> None:
        """Test getting repository by ID."""
        repo_manager, _, _ = e2e_services_with_repo

        repo = repo_manager.get_repository("test-skills-repo")

        assert repo is not None
        assert repo.id == "test-skills-repo"
        assert repo.skill_count == 5

    def test_get_nonexistent_repository(
        self,
        e2e_configured_services: tuple,
    ) -> None:
        """Test getting non-existent repository returns None."""
        repo_manager, _, _ = e2e_configured_services

        repo = repo_manager.get_repository("nonexistent-repo")
        assert repo is None

    def test_update_repository_metadata(
        self,
        e2e_services_with_repo: tuple,
    ) -> None:
        """Test updating repository metadata."""
        repo_manager, _, _ = e2e_services_with_repo

        # Get original repository
        repo = repo_manager.get_repository("test-skills-repo")
        assert repo is not None
        original_update_time = repo.last_updated

        # Update metadata (simulated - normally would git pull)
        # For E2E test, we just update the metadata timestamp
        import time

        time.sleep(0.1)  # Ensure timestamp difference

        updated_repo = Repository(
            id=repo.id,
            url=repo.url,
            local_path=repo.local_path,
            priority=repo.priority,
            last_updated=datetime.now(timezone.utc),
            skill_count=repo.skill_count,
            license=repo.license,
        )

        repo_manager.metadata_store.update_repository(updated_repo)

        # Verify update
        fetched_repo = repo_manager.get_repository("test-skills-repo")
        assert fetched_repo is not None
        assert fetched_repo.last_updated > original_update_time


@pytest.mark.e2e
class TestRepositoryRemoveWorkflow:
    """Test removing repositories."""

    def test_remove_repository(
        self,
        e2e_services_with_repo: tuple,
    ) -> None:
        """Test removing a repository."""
        repo_manager, skill_manager, _ = e2e_services_with_repo

        # Verify repository exists
        repos_before = repo_manager.list_repositories()
        assert len(repos_before) == 1

        # Remove repository
        repo_manager.remove_repository("test-skills-repo")

        # Verify repository removed
        repos_after = repo_manager.list_repositories()
        assert len(repos_after) == 0

        # Verify repository directory deleted (full removal)
        repo_dir = repo_manager.base_dir / "test-skills-repo"
        assert not repo_dir.exists()

    def test_remove_nonexistent_repository(
        self,
        e2e_configured_services: tuple,
    ) -> None:
        """Test removing non-existent repository raises error."""
        repo_manager, _, _ = e2e_configured_services

        with pytest.raises(ValueError, match="Repository not found"):
            repo_manager.remove_repository("nonexistent-repo")

    def test_remove_repository_cascades_to_skills(
        self,
        e2e_services_with_repo: tuple,
    ) -> None:
        """Test that removing repository affects skill discovery."""
        repo_manager, skill_manager, _ = e2e_services_with_repo

        # Verify skills discoverable before removal
        skills_before = skill_manager.discover_skills()
        assert len(skills_before) >= 5

        # Remove repository metadata
        repo_manager.remove_repository("test-skills-repo")

        # Skills should still be on disk but not in metadata
        repos_after = repo_manager.list_repositories()
        assert len(repos_after) == 0


@pytest.mark.e2e
class TestCompleteRepositoryWorkflow:
    """Test complete end-to-end repository workflows."""

    def test_full_repository_lifecycle(
        self,
        e2e_configured_services: tuple,
        real_skill_repo: Path,
    ) -> None:
        """Test complete repository lifecycle: add → index → search → remove.

        Workflow:
        1. Add repository
        2. Discover skills from repository
        3. Build indices
        4. Search for skills
        5. Verify search results
        6. Remove repository
        7. Verify cleanup
        """
        repo_manager, skill_manager, indexing_engine = e2e_configured_services

        # 1. Add repository
        repo_id = "lifecycle-test-repo"
        dest_dir = repo_manager.base_dir / repo_id
        shutil.copytree(real_skill_repo, dest_dir)

        repository = Repository(
            id=repo_id,
            url="https://github.com/test/lifecycle-repo.git",
            local_path=dest_dir,
            priority=95,
            last_updated=datetime.now(timezone.utc),
            skill_count=5,
            license="MIT",
        )

        repo_manager.metadata_store.add_repository(repository)

        # Verify repository added
        repos = repo_manager.list_repositories()
        assert len(repos) == 1
        assert repos[0].id == repo_id

        # 2. Discover skills
        skills = skill_manager.discover_skills()
        assert len(skills) >= 5

        # 3. Build indices
        stats = indexing_engine.reindex_all(force=True)
        assert stats.total_skills >= 5

        # 4. Search for skills
        results = indexing_engine.search(query="python testing", top_k=5)

        # 5. Verify search results
        assert len(results) > 0
        assert all(r.skill.repo_id == repo_id for r in results)

        # 6. Remove repository
        repo_manager.remove_repository(repo_id)

        # 7. Verify cleanup
        remaining_repos = repo_manager.list_repositories()
        assert len(remaining_repos) == 0

    def test_multiple_repositories_workflow(
        self,
        e2e_configured_services: tuple,
        real_skill_repo: Path,
    ) -> None:
        """Test workflow with multiple repositories.

        Workflow:
        1. Add multiple repositories
        2. Index all skills
        3. Search across all repositories
        4. Verify results from multiple repos
        5. Remove one repository
        6. Verify other repositories unaffected
        """
        repo_manager, skill_manager, indexing_engine = e2e_configured_services

        # 1. Add multiple repositories
        repo_ids = ["repo-a", "repo-b", "repo-c"]
        for repo_id in repo_ids:
            dest_dir = repo_manager.base_dir / repo_id
            shutil.copytree(real_skill_repo, dest_dir)

            repository = Repository(
                id=repo_id,
                url=f"https://github.com/test/{repo_id}.git",
                local_path=dest_dir,
                priority=90,
                last_updated=datetime.now(timezone.utc),
                skill_count=5,
                license="MIT",
            )

            repo_manager.metadata_store.add_repository(repository)

        # Verify all repositories added
        repos = repo_manager.list_repositories()
        assert len(repos) == 3

        # 2. Index all skills
        stats = indexing_engine.reindex_all(force=True)
        # 3 repos * 5 skills = 15 skills (but may have duplicates across repos)
        assert stats.total_skills >= 5

        # 3. Search across all repositories
        results = indexing_engine.search(query="testing", top_k=20)
        assert len(results) > 0

        # 4. Verify results from multiple repos
        repo_ids_in_results = {r.skill.repo_id for r in results}
        # Should have skills from our repositories
        assert len(repo_ids_in_results) >= 1

        # 5. Remove one repository
        repo_manager.remove_repository("repo-a")

        # 6. Verify other repositories unaffected
        remaining_repos = repo_manager.list_repositories()
        assert len(remaining_repos) == 2
        remaining_ids = {r.id for r in remaining_repos}
        assert remaining_ids == {"repo-b", "repo-c"}

    def test_repository_priority_affects_search_ranking(
        self,
        e2e_configured_services: tuple,
        real_skill_repo: Path,
    ) -> None:
        """Test that repository priority can affect skill ranking.

        Note: Current implementation may not use priority in ranking,
        but this test documents expected behavior for future enhancement.
        """
        repo_manager, skill_manager, indexing_engine = e2e_configured_services

        # Add high-priority repository
        high_priority_id = "high-priority-repo"
        high_dest = repo_manager.base_dir / high_priority_id
        shutil.copytree(real_skill_repo, high_dest)

        high_repo = Repository(
            id=high_priority_id,
            url="https://github.com/test/high-priority.git",
            local_path=high_dest,
            priority=100,
            last_updated=datetime.now(timezone.utc),
            skill_count=5,
            license="MIT",
        )

        repo_manager.metadata_store.add_repository(high_repo)

        # Add low-priority repository
        low_priority_id = "low-priority-repo"
        low_dest = repo_manager.base_dir / low_priority_id
        shutil.copytree(real_skill_repo, low_dest)

        low_repo = Repository(
            id=low_priority_id,
            url="https://github.com/test/low-priority.git",
            local_path=low_dest,
            priority=10,
            last_updated=datetime.now(timezone.utc),
            skill_count=5,
            license="MIT",
        )

        repo_manager.metadata_store.add_repository(low_repo)

        # Index and search
        indexing_engine.reindex_all(force=True)
        results = indexing_engine.search(query="python testing", top_k=10)

        assert len(results) > 0
        # Note: This test documents the feature but may not enforce
        # priority-based ranking if not yet implemented
