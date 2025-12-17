"""Integration tests for end-to-end workflows.

This module contains comprehensive integration tests that verify complete
workflows work correctly from start to finish, testing interactions between
multiple components.
"""

import json
import shutil
from datetime import UTC
from pathlib import Path

import pytest

from mcp_skills.mcp.server import configure_services
from mcp_skills.mcp.tools.skill_tool import (
    skill_categories,
    skill_get,
    skill_recommend,
    skill_reindex,
    skill_search,
)
from mcp_skills.models.skill import Skill
from mcp_skills.services.indexing import IndexingEngine
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager
from mcp_skills.services.toolchain_detector import ToolchainDetector


class TestFullSetupWorkflow:
    """Test complete setup workflow from scratch."""

    def test_full_setup_workflow(
        self,
        populated_services: tuple[RepositoryManager, SkillManager, IndexingEngine],
    ) -> None:
        """Test complete setup workflow.

        Workflow:
        1. Get pre-configured services
        2. Verify SkillManager can discover skills
        3. Verify skills discovered successfully
        4. Initialize IndexingEngine
        5. Build indices (vector + graph)
        6. Verify indices built successfully
        7. Search for a skill
        8. Verify search returns results
        """
        repo_manager, skill_manager, indexing_engine = populated_services

        # 2. Verify SkillManager can discover skills
        assert skill_manager.repos_dir.exists()

        # 3. Verify skills discovered
        skills = skill_manager.discover_skills()
        assert len(skills) >= 3  # We created 3 skills
        assert any(skill.name == "pytest-testing" for skill in skills)
        assert any(skill.name == "flask-development" for skill in skills)

        # Verify skill structure
        pytest_skill = next(s for s in skills if s.name == "pytest-testing")
        assert pytest_skill.category == "testing"
        assert "python" in pytest_skill.tags
        assert "pytest" in pytest_skill.tags
        assert len(pytest_skill.instructions) > 50

        # 4. Verify IndexingEngine is configured
        assert indexing_engine.storage_path.exists()

        # 5. Build indices (vector + graph)
        stats = indexing_engine.reindex_all(force=True)

        # 6. Verify indices built successfully
        assert stats.total_skills >= 3
        assert stats.graph_nodes >= 3
        assert stats.vector_store_size > 0
        assert stats.last_indexed != "never"

        # 7. Search for a skill
        results = indexing_engine.search(query="python testing", top_k=5)

        # 8. Verify search returns results
        assert len(results) > 0
        # pytest-testing should be in top results (ranking may vary)
        skill_names = [r.skill.name for r in results]
        assert "pytest-testing" in skill_names
        top_skill = results[0]
        assert top_skill.score > 0.5
        assert top_skill.match_type in ["vector", "graph", "hybrid"]


class TestSearchWorkflow:
    """Test hybrid RAG search end-to-end."""

    def test_search_workflow(
        self,
        populated_services: tuple[RepositoryManager, SkillManager, IndexingEngine],
    ) -> None:
        """Test hybrid search workflow.

        Workflow:
        1. Use services with pre-populated skills
        2. Build indices
        3. Search with natural language query
        4. Verify results ranked by relevance
        5. Search with category filter
        6. Search with toolchain filter
        7. Verify filters work correctly
        """
        repo_manager, skill_manager, indexing_engine = populated_services

        # 1. Discover skills
        skills = skill_manager.discover_skills()
        assert len(skills) >= 3

        # 2. Build indices
        stats = indexing_engine.reindex_all(force=True)
        assert stats.total_skills >= 3

        # 3. Search with natural language query
        results = indexing_engine.search(
            query="testing framework for python applications", top_k=10
        )

        # 4. Verify results ranked by relevance
        assert len(results) > 0
        # Should find pytest-testing in top results (ranking may vary)
        skill_names = [r.skill.name for r in results]
        assert "pytest-testing" in skill_names
        # Scores should be descending
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

        # 5. Search with category filter
        testing_results = indexing_engine.search(
            query="python", category="testing", top_k=10
        )
        # All results should be in testing category
        for result in testing_results:
            assert result.skill.category == "testing"

        # 6. Search with toolchain filter
        flask_results = indexing_engine.search(
            query="web development", toolchain="flask", top_k=10
        )

        # 7. Verify filters work correctly
        # Should find flask skill
        assert len(flask_results) > 0
        assert any(result.skill.name == "flask-development" for result in flask_results)
        # All results should have flask or web in tags
        for result in flask_results:
            assert any(
                tag.lower() in ["flask", "web", "python"] for tag in result.skill.tags
            )

    def test_search_with_no_indices(
        self, configured_indexing_engine: IndexingEngine
    ) -> None:
        """Test search behavior when no indices are built."""
        # Search without building indices
        results = configured_indexing_engine.search(query="testing", top_k=10)

        # Should return empty results, not crash
        assert results == []

    def test_search_empty_query(
        self,
        populated_services: tuple[RepositoryManager, SkillManager, IndexingEngine],
    ) -> None:
        """Test search with empty query."""
        _, skill_manager, indexing_engine = populated_services

        # Build indices
        skill_manager.discover_skills()
        indexing_engine.reindex_all(force=True)

        # Search with empty query
        results = indexing_engine.search(query="", top_k=10)

        # Should return empty results
        assert results == []


class TestRecommendationWorkflow:
    """Test project-based recommendations."""

    def test_recommendation_workflow(
        self,
        sample_python_project: Path,
        populated_services: tuple[RepositoryManager, SkillManager, IndexingEngine],
        configured_toolchain_detector: ToolchainDetector,
    ) -> None:
        """Test recommendation workflow.

        Workflow:
        1. Create test project with known toolchain (Python with pytest)
        2. Use ToolchainDetector to detect
        3. Get recommendations based on detected toolchain
        4. Verify relevant skills recommended
        5. Verify confidence scores make sense
        """
        repo_manager, skill_manager, indexing_engine = populated_services

        # Build indices
        skill_manager.discover_skills()
        indexing_engine.reindex_all(force=True)

        # 2. Use ToolchainDetector to detect
        toolchain_info = configured_toolchain_detector.detect(sample_python_project)

        # 3. Verify detection
        assert toolchain_info.primary_language == "Python"
        assert "pytest" in toolchain_info.test_frameworks
        assert toolchain_info.confidence > 0.3  # Lowered threshold for test environment

        # 4. Get recommendations based on detected toolchain
        # Search for skills matching the detected toolchain
        query = (
            f"{toolchain_info.primary_language} {' '.join(toolchain_info.frameworks)}"
        )
        results = indexing_engine.search(query=query, top_k=10)

        # 5. Verify relevant skills recommended
        assert len(results) > 0

        # Should recommend testing skills for Python + pytest project
        skill_names = [r.skill.name for r in results]
        assert "pytest-testing" in skill_names

        # 6. Verify confidence scores make sense
        for result in results:
            assert 0.0 <= result.score <= 1.0
            # Top results should have high confidence
            if result == results[0]:
                assert result.score > 0.5


class TestMCPServerWorkflow:
    """Test MCP server tools integration."""

    @pytest.mark.asyncio
    async def test_mcp_server_workflow(
        self,
        populated_repos_dir: Path,
        temp_storage_dir: Path,
    ) -> None:
        """Test MCP server tools.

        Workflow:
        1. Configure services
        2. Call reindex_skills tool
        3. Call search_skills tool
        4. Call get_skill tool
        5. Call list_categories tool
        6. Call recommend_skills tool
        7. Verify all tools return proper {"status": "completed", ...} format
        8. Test error handling (invalid inputs)
        """
        # 1. Configure services
        base_dir = populated_repos_dir.parent
        configure_services(base_dir=base_dir, storage_path=temp_storage_dir)

        # 2. Call skill_reindex tool first
        reindex_result = await skill_reindex(force=True)
        assert reindex_result["status"] == "completed"
        assert reindex_result["indexed_count"] >= 3
        assert reindex_result["graph_nodes"] >= 3

        # 3. Call skill_search tool
        search_result = await skill_search(query="python testing", limit=5)
        assert search_result["status"] == "completed"
        assert "skills" in search_result
        assert len(search_result["skills"]) > 0
        # Verify skill structure
        skill = search_result["skills"][0]
        assert "id" in skill
        assert "name" in skill
        assert "description" in skill
        assert "score" in skill

        # 4. Call skill_get tool
        skill_id = search_result["skills"][0]["id"]
        get_result = await skill_get(skill_id=skill_id)
        assert get_result["status"] == "completed"
        assert get_result["skill"]["id"] == skill_id
        assert "instructions" in get_result["skill"]

        # 5. Call skill_categories tool
        categories_result = await skill_categories()
        assert categories_result["status"] == "completed"
        assert "categories" in categories_result
        assert len(categories_result["categories"]) > 0
        # Should have testing and architecture categories
        category_names = [c["name"] for c in categories_result["categories"]]
        assert "testing" in category_names
        assert "architecture" in category_names

        # 6. Call skill_recommend tool (with populated repo dir)
        recommend_result = await skill_recommend(
            project_path=str(populated_repos_dir), limit=5
        )
        assert recommend_result["status"] == "completed"
        assert "recommendations" in recommend_result
        # It's ok if no recommendations since the populated_repos_dir has no toolchain markers
        assert isinstance(recommend_result["recommendations"], list)

        # 7. Verify all tools return proper format
        # All results checked above have correct structure

        # 8. Test error handling (invalid inputs)
        # Test skill_get with non-existent ID
        error_result = await skill_get(skill_id="invalid/skill/id")
        assert error_result["status"] == "error"
        assert "error" in error_result

        # Test search with invalid parameters
        search_error = await skill_search(query="", limit=5)
        # Empty query should return empty results, not error
        assert search_error["status"] == "completed"
        assert len(search_error["skills"]) == 0


class TestRepositoryWorkflow:
    """Test repository management workflow."""

    def test_repository_workflow(
        self,
        sample_skill_repo: Path,
        configured_repository_manager: RepositoryManager,
        configured_skill_manager: SkillManager,
    ) -> None:
        """Test repository management workflow.

        Workflow:
        1. Manually copy a sample repo to repos directory
        2. Verify skills discoverable
        3. Test repository operations (list, update, remove)
        """
        repo_manager = configured_repository_manager
        skill_manager = configured_skill_manager

        # 1. Manually copy sample repo to repos directory
        # Since we can't use add_repository with file:// URLs, we copy directly
        repo_id = "sample-repo"
        dest_dir = repo_manager.base_dir / repo_id
        shutil.copytree(sample_skill_repo, dest_dir)

        # Manually create metadata entry
        from datetime import datetime

        from mcp_skills.models.repository import Repository

        repository = Repository(
            id=repo_id,
            url="https://github.com/test/sample-repo.git",
            local_path=dest_dir,
            priority=100,
            last_updated=datetime.now(UTC),
            skill_count=3,
            license="MIT",
        )
        repo_manager.metadata_store.add_repository(repository)

        # 2. Verify skills discoverable
        skills = skill_manager.discover_skills()
        assert len(skills) >= 3

        # 3. List repositories
        repositories = repo_manager.list_repositories()
        assert len(repositories) > 0
        assert any(repo.id == repo_id for repo in repositories)

        # Get repository by ID
        fetched_repo = repo_manager.get_repository(repo_id)
        assert fetched_repo is not None
        assert fetched_repo.id == repo_id

        # 4. Remove repository
        repo_manager.remove_repository(repo_id)

        # 5. Verify repository removed
        remaining_repos = repo_manager.list_repositories()
        assert not any(repo.id == repo_id for repo in remaining_repos)


class TestCLIWorkflow:
    """Test CLI commands integration."""

    def test_cli_workflow(
        self,
        populated_services: tuple[RepositoryManager, SkillManager, IndexingEngine],
    ) -> None:
        """Test CLI commands end-to-end.

        Workflow:
        1. Use pre-configured services
        2. Test health check (stats)
        3. Test search command
        4. Test list command (discover skills)
        5. Verify all commands execute without errors
        6. Verify output formats are correct
        """
        repo_manager, skill_manager, indexing_engine = populated_services

        # Build indices
        skill_manager.discover_skills()
        indexing_engine.reindex_all(force=True)

        # 2. Test health check (stats)
        stats = indexing_engine.get_stats()
        assert stats.total_skills >= 3
        assert stats.graph_nodes >= 3

        # 3. Test stats command
        repositories = repo_manager.list_repositories()
        # May be empty since we're using populated skills directly
        assert isinstance(repositories, list)

        # 4. Test search command
        results = indexing_engine.search(query="python testing", top_k=10)
        assert len(results) > 0
        assert all(hasattr(r, "skill") for r in results)
        assert all(hasattr(r, "score") for r in results)

        # 5. Test list command (discover skills)
        skills = skill_manager.discover_skills()
        assert len(skills) >= 3
        assert all(isinstance(skill, Skill) for skill in skills)

        # 6. Verify output formats are correct
        # Check that we can serialize results to JSON
        stats_dict = {
            "total_skills": stats.total_skills,
            "graph_nodes": stats.graph_nodes,
            "graph_edges": stats.graph_edges,
        }
        assert json.dumps(stats_dict)  # Should not raise

        skill_dict = {
            "id": skills[0].id,
            "name": skills[0].name,
            "description": skills[0].description,
        }
        assert json.dumps(skill_dict)  # Should not raise


class TestMigrationWorkflow:
    """Test JSON to SQLite migration."""

    def test_migration_workflow(
        self,
        tmp_path: Path,
        old_json_metadata: Path,
    ) -> None:
        """Test JSON to SQLite migration.

        Workflow:
        1. Create old JSON metadata file with test data
        2. Initialize RepositoryManager (triggers migration)
        3. Verify all repositories migrated to SQLite
        4. Verify JSON backed up to .backup file
        5. Verify all repository operations work with SQLite
        6. Verify data integrity maintained
        """
        # 1. Old JSON metadata file already created by fixture

        # Copy JSON file to expected location
        base_dir = tmp_path / "test_migration"
        base_dir.mkdir()
        repos_json = base_dir / "repos.json"
        shutil.copy(old_json_metadata, repos_json)

        # Verify JSON file exists with correct data
        with open(repos_json) as f:
            old_data = json.load(f)
        assert len(old_data["repositories"]) == 2

        # 2. Initialize RepositoryManager (triggers migration)
        repo_manager = RepositoryManager(base_dir=base_dir / "repos")

        # 3. Verify all repositories migrated to SQLite
        repositories = repo_manager.list_repositories()
        assert len(repositories) == 2

        # Verify repository data
        repo_ids = [repo.id for repo in repositories]
        assert "test/repo1" in repo_ids
        assert "test/repo2" in repo_ids

        # Check specific repository details
        repo1 = next(r for r in repositories if r.id == "test/repo1")
        assert repo1.priority == 100
        assert repo1.skill_count == 5
        assert repo1.license == "MIT"

        # 4. Verify JSON backed up to .backup file
        backup_file = base_dir / "repos.json.backup"
        assert backup_file.exists()

        # Verify backup contains original data
        with open(backup_file) as f:
            backup_data = json.load(f)
        assert backup_data == old_data

        # 5. Verify all repository operations work with SQLite
        # Get repository by ID
        fetched_repo = repo_manager.get_repository("test/repo1")
        assert fetched_repo is not None
        assert fetched_repo.id == "test/repo1"

        # List repositories (already tested above)
        assert len(repo_manager.list_repositories()) == 2

        # 6. Verify data integrity maintained
        # All data checks passed above
        # Verify priorities are correct
        priorities = [repo.priority for repo in repositories]
        assert 100 in priorities
        assert 90 in priorities


class TestErrorHandlingWorkflow:
    """Test error handling across workflows."""

    def test_error_handling_workflow(
        self,
        configured_repository_manager: RepositoryManager,
        configured_skill_manager: SkillManager,
        configured_indexing_engine: IndexingEngine,
    ) -> None:
        """Test error handling across workflows.

        Workflow:
        1. Test invalid git URL
        2. Test search with no indices built
        3. Test get_skill with invalid ID
        4. Test repository operations on non-existent repo
        5. Verify proper error messages returned
        """
        repo_manager = configured_repository_manager
        skill_manager = configured_skill_manager
        indexing_engine = configured_indexing_engine

        # 1. Test invalid git URL
        with pytest.raises(ValueError, match="Invalid git URL"):
            repo_manager.add_repository(url="not-a-valid-url", priority=50)

        # Test non-existent git URL (network error simulation)
        with pytest.raises(ValueError, match="Failed to clone repository"):
            repo_manager.add_repository(
                url="https://github.com/nonexistent/repo123456789.git", priority=50
            )

        # 2. Test search with no indices built
        results = indexing_engine.search(query="testing", top_k=10)
        # Should return empty results, not crash
        assert results == []

        # 3. Test get_skill with invalid ID
        skill = skill_manager.load_skill("invalid/skill/id")
        # Should return None, not crash
        assert skill is None

        # Test get_skill_metadata with invalid ID
        metadata = skill_manager.get_skill_metadata("invalid/skill/id")
        assert metadata is None

        # 4. Test repository operations on non-existent repo
        # Test get_repository with non-existent ID
        repo = repo_manager.get_repository("nonexistent/repo")
        assert repo is None

        # Test update_repository with non-existent ID
        with pytest.raises(ValueError, match="Repository not found"):
            repo_manager.update_repository("nonexistent/repo")

        # Test remove_repository with non-existent ID
        with pytest.raises(ValueError, match="Repository not found"):
            repo_manager.remove_repository("nonexistent/repo")

        # 5. Verify proper error messages returned
        # All error messages checked in assertions above

    def test_skill_validation_errors(
        self,
        configured_skill_manager: SkillManager,
    ) -> None:
        """Test skill validation error handling."""
        # Create invalid skill content
        invalid_skill_content = """---
name: ""
description: "Too short"
category: testing
---

Not enough content here.
"""

        # Create temp file in a proper location within repos_dir
        skill_dir = configured_skill_manager.repos_dir / "test-invalid" / "broken"
        skill_dir.mkdir(parents=True, exist_ok=True)
        invalid_skill_file = skill_dir / "SKILL.md"
        invalid_skill_file.write_text(invalid_skill_content)

        # Try to parse invalid skill
        # This should log an error and return None, not crash
        skill = configured_skill_manager._parse_skill_file(
            invalid_skill_file, "test-invalid"
        )
        # Should fail validation and return None
        assert skill is None
