"""End-to-end tests for MCP tools via direct function calls.

This module tests all 5 MCP tools by calling them directly as async functions.
While true JSON-RPC testing would require a running server and JSON-RPC client,
this approach verifies the tool implementations work correctly end-to-end.

MCP Tools Tested:
- search_skills: Hybrid RAG search (vector + knowledge graph)
- get_skill: Retrieve complete skill details
- recommend_skills: Project-based and skill-based recommendations
- list_categories: List all skill categories
- reindex_skills: Rebuild search indices

For true JSON-RPC testing, see integration test_mcp_server_workflow.
"""

import pytest

from mcp_skills.mcp.server import configure_services
from mcp_skills.mcp.tools.skill_tools import (
    get_skill,
    list_categories,
    recommend_skills,
    reindex_skills,
    search_skills,
)


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPSearchSkills:
    """Test search_skills MCP tool."""

    async def test_search_skills_basic(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test basic skill search via MCP tool."""
        # Configure MCP server services
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        # Reindex first
        reindex_result = await reindex_skills(force=True)
        assert reindex_result["status"] == "completed"
        assert reindex_result["indexed_count"] >= 5

        # Search for Python testing
        result = await search_skills(query="python testing", limit=10)

        # Verify response structure
        assert result["status"] == "completed"
        assert "skills" in result
        assert "count" in result
        assert "search_method" in result
        assert result["search_method"] == "hybrid_rag_70_30"

        # Verify skills structure
        if result["count"] > 0:
            skill = result["skills"][0]
            assert "id" in skill
            assert "name" in skill
            assert "description" in skill
            assert "score" in skill
            assert "category" in skill
            assert "tags" in skill
            assert "match_type" in skill

            # Should find pytest-testing with high score
            skill_names = [s["name"] for s in result["skills"]]
            assert "pytest-testing" in skill_names

            # Verify score is reasonable
            assert 0.0 <= result["skills"][0]["score"] <= 1.0

    async def test_search_skills_with_toolchain_filter(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test search with toolchain filter."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        result = await search_skills(
            query="testing",
            toolchain="python",
            limit=5,
        )

        assert result["status"] == "completed"
        assert "filters_applied" in result
        assert result["filters_applied"]["toolchain"] == "python"

    async def test_search_skills_with_category_filter(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test search with category filter."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        result = await search_skills(
            query="python",
            category="testing",
            limit=5,
        )

        assert result["status"] == "completed"
        assert result["filters_applied"]["category"] == "testing"

        # All results should be in testing category
        for skill in result["skills"]:
            assert skill["category"] == "testing"

    async def test_search_skills_with_tags_filter(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test search with tags filter."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        result = await search_skills(
            query="python",
            tags=["python", "testing"],
            limit=10,
        )

        assert result["status"] == "completed"

        # All results should have both required tags
        for skill in result["skills"]:
            skill_tags = set(skill["tags"])
            assert "python" in skill_tags
            assert "testing" in skill_tags

    async def test_search_skills_empty_query(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test search with empty query."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        result = await search_skills(query="", limit=10)

        assert result["status"] == "completed"
        assert result["count"] == 0
        assert len(result["skills"]) == 0

    async def test_search_skills_limit_cap(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test search respects limit cap of 50."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        result = await search_skills(query="test", limit=100)

        assert result["status"] == "completed"
        # Should be capped at 50
        assert result["count"] <= 50


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPGetSkill:
    """Test get_skill MCP tool."""

    async def test_get_skill_existing(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test getting an existing skill."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        # Search to get a valid skill ID
        search_result = await search_skills(query="pytest", limit=1)
        assert search_result["count"] > 0

        skill_id = search_result["skills"][0]["id"]

        # Get the skill
        result = await get_skill(skill_id=skill_id)

        # Verify response structure
        assert result["status"] == "completed"
        assert "skill" in result
        assert "source" in result

        # Verify skill has all required fields
        skill = result["skill"]
        assert skill["id"] == skill_id
        assert "name" in skill
        assert "description" in skill
        assert "instructions" in skill
        assert "category" in skill
        assert "tags" in skill
        assert "dependencies" in skill
        assert "version" in skill
        assert "author" in skill
        assert "file_path" in skill
        assert "repo_id" in skill

        # Verify instructions are complete
        assert len(skill["instructions"]) > 100
        assert "pytest" in skill["instructions"].lower()

    async def test_get_skill_nonexistent(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test getting a non-existent skill."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        result = await get_skill(skill_id="nonexistent/skill/id")

        assert result["status"] == "error"
        assert "error" in result
        assert "not found" in result["error"].lower()

    async def test_get_skill_cache_source(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test skill retrieval from cache."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        search_result = await search_skills(query="pytest", limit=1)
        skill_id = search_result["skills"][0]["id"]

        # First call should load from disk
        result1 = await get_skill(skill_id=skill_id)
        assert result1["status"] == "completed"

        # Second call may be from cache
        result2 = await get_skill(skill_id=skill_id)
        assert result2["status"] == "completed"
        assert result2["skill"]["id"] == skill_id


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPRecommendSkills:
    """Test recommend_skills MCP tool."""

    async def test_recommend_skills_project_based(
        self,
        e2e_services_with_repo: tuple,
        sample_python_project_e2e,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test project-based skill recommendations."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        result = await recommend_skills(
            project_path=str(sample_python_project_e2e),
            limit=5,
        )

        # Verify response structure
        assert result["status"] == "completed"
        assert "recommendations" in result
        assert "recommendation_type" in result
        assert result["recommendation_type"] == "project_based"
        assert "context" in result

        # Verify context contains toolchain info
        context = result["context"]
        assert "detected_toolchains" in context
        assert "Python" in context["detected_toolchains"]

        # Verify recommendations structure
        if len(result["recommendations"]) > 0:
            rec = result["recommendations"][0]
            assert "id" in rec
            assert "name" in rec
            assert "description" in rec
            assert "confidence" in rec
            assert "reason" in rec
            assert "category" in rec
            assert "tags" in rec

            # Confidence should be reasonable
            assert 0.0 <= rec["confidence"] <= 1.0

    async def test_recommend_skills_skill_based(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test skill-based recommendations."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        # Get a skill ID first
        search_result = await search_skills(query="pytest", limit=1)
        assert search_result["count"] > 0
        skill_id = search_result["skills"][0]["id"]

        result = await recommend_skills(
            current_skill=skill_id,
            limit=5,
        )

        assert result["status"] == "completed"
        assert result["recommendation_type"] == "skill_based"
        assert "context" in result
        assert result["context"]["base_skill"] == skill_id

    async def test_recommend_skills_no_params(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test recommendations with no parameters returns error."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        result = await recommend_skills(limit=5)

        assert result["status"] == "error"
        assert "error" in result
        assert "must be provided" in result["error"]

    async def test_recommend_skills_invalid_project_path(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test recommendations with invalid project path."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        result = await recommend_skills(
            project_path="/nonexistent/path",
            limit=5,
        )

        assert result["status"] == "error"
        assert "does not exist" in result["error"]

    async def test_recommend_skills_limit_cap(
        self,
        e2e_services_with_repo: tuple,
        sample_python_project_e2e,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test recommendations respects limit cap of 20."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await reindex_skills(force=True)

        result = await recommend_skills(
            project_path=str(sample_python_project_e2e),
            limit=100,
        )

        assert result["status"] == "completed"
        # Should be capped at 20
        assert len(result["recommendations"]) <= 20


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPListCategories:
    """Test list_categories MCP tool."""

    async def test_list_categories_basic(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test listing all categories."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        result = await list_categories()

        # Verify response structure
        assert result["status"] == "completed"
        assert "categories" in result
        assert "total_categories" in result

        # We should have multiple categories from our test repo
        assert result["total_categories"] >= 3

        # Verify category structure
        categories = result["categories"]
        for category in categories:
            assert "name" in category
            assert "count" in category
            assert category["count"] > 0

        # Verify expected categories exist
        category_names = [c["name"] for c in categories]
        assert "testing" in category_names
        assert "architecture" in category_names
        assert "debugging" in category_names

    async def test_list_categories_counts(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test category counts are accurate."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        result = await list_categories()

        assert result["status"] == "completed"

        # Find testing category
        testing_cat = next(
            (c for c in result["categories"] if c["name"] == "testing"),
            None,
        )

        # Should have at least 2 testing skills (pytest-testing, typescript-testing)
        assert testing_cat is not None
        assert testing_cat["count"] >= 2


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPReindexSkills:
    """Test reindex_skills MCP tool."""

    async def test_reindex_skills_basic(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test basic reindexing."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        result = await reindex_skills(force=False)

        # Verify response structure
        assert result["status"] == "completed"
        assert "indexed_count" in result
        assert "vector_store_size" in result
        assert "graph_nodes" in result
        assert "graph_edges" in result
        assert "last_indexed" in result
        assert "duration_seconds" in result
        assert "forced" in result

        # Verify we indexed our test skills
        assert result["indexed_count"] >= 5
        assert result["graph_nodes"] >= 5
        assert result["vector_store_size"] > 0

        # Verify duration is reasonable
        assert result["duration_seconds"] < 30.0

    async def test_reindex_skills_force(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test force reindexing."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        result = await reindex_skills(force=True)

        assert result["status"] == "completed"
        assert result["forced"] is True
        assert result["indexed_count"] >= 5

    async def test_reindex_skills_incremental(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test incremental reindexing."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        # First reindex
        result1 = await reindex_skills(force=True)
        assert result1["status"] == "completed"

        # Second reindex (incremental)
        result2 = await reindex_skills(force=False)
        assert result2["status"] == "completed"
        assert result2["forced"] is False

        # Should have same skill count
        assert result2["indexed_count"] == result1["indexed_count"]


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPToolsIntegration:
    """Test MCP tools working together in realistic workflows."""

    async def test_complete_search_workflow(
        self,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test complete search workflow using multiple tools.

        Workflow:
        1. Reindex skills
        2. List categories to see what's available
        3. Search for skills in a category
        4. Get detailed info for a skill
        """
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        # 1. Reindex
        reindex_result = await reindex_skills(force=True)
        assert reindex_result["status"] == "completed"
        assert reindex_result["indexed_count"] >= 5

        # 2. List categories
        categories_result = await list_categories()
        assert categories_result["status"] == "completed"
        assert "testing" in [c["name"] for c in categories_result["categories"]]

        # 3. Search in testing category
        search_result = await search_skills(
            query="python",
            category="testing",
            limit=5,
        )
        assert search_result["status"] == "completed"
        assert search_result["count"] > 0

        # 4. Get detailed skill info
        skill_id = search_result["skills"][0]["id"]
        get_result = await get_skill(skill_id=skill_id)
        assert get_result["status"] == "completed"
        assert len(get_result["skill"]["instructions"]) > 100

    async def test_recommendation_workflow(
        self,
        e2e_services_with_repo: tuple,
        sample_python_project_e2e,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test recommendation workflow.

        Workflow:
        1. Reindex skills
        2. Get project-based recommendations
        3. Get details for recommended skill
        4. Get related skills (skill-based recommendations)
        """
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        # 1. Reindex
        await reindex_skills(force=True)

        # 2. Project-based recommendations
        rec_result = await recommend_skills(
            project_path=str(sample_python_project_e2e),
            limit=5,
        )
        assert rec_result["status"] == "completed"
        assert len(rec_result["recommendations"]) > 0

        # 3. Get details for recommended skill
        rec_skill_id = rec_result["recommendations"][0]["id"]
        skill_result = await get_skill(skill_id=rec_skill_id)
        assert skill_result["status"] == "completed"

        # 4. Skill-based recommendations
        related_result = await recommend_skills(
            current_skill=rec_skill_id,
            limit=3,
        )
        assert related_result["status"] == "completed"
        assert related_result["recommendation_type"] == "skill_based"
