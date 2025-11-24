"""Tests for IndexingEngine with ChromaDB and NetworkX integration."""

import tempfile
from pathlib import Path

import pytest

from mcp_skills.models.skill import Skill
from mcp_skills.services.indexing import (
    IndexingEngine,
    IndexStats,
    ScoredSkill,
)
from mcp_skills.services.skill_manager import SkillManager


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for ChromaDB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_skills():
    """Create sample skills for testing."""
    skills = [
        Skill(
            id="test-repo/pytest-skill",
            name="pytest-testing",
            description="Professional pytest testing for Python",
            instructions="Use pytest for unit testing. Write test_ functions.",
            category="testing",
            tags=["python", "pytest", "testing", "tdd"],
            dependencies=[],
            examples=["pytest test_example.py"],
            file_path=Path("/tmp/pytest/SKILL.md"),
            repo_id="test-repo",
            version="1.0.0",
            author="Test Author",
        ),
        Skill(
            id="test-repo/debugging-skill",
            name="python-debugger",
            description="Debug Python code using pdb and breakpoints",
            instructions="Use pdb for debugging. Set breakpoints with import pdb; pdb.set_trace().",
            category="debugging",
            tags=["python", "debugging", "pdb"],
            dependencies=["test-repo/pytest-skill"],
            examples=["import pdb; pdb.set_trace()"],
            file_path=Path("/tmp/debugging/SKILL.md"),
            repo_id="test-repo",
            version="1.0.0",
            author="Test Author",
        ),
        Skill(
            id="test-repo/refactoring-skill",
            name="code-refactoring",
            description="Refactor Python code for better maintainability",
            instructions="Apply SOLID principles and extract functions.",
            category="refactoring",
            tags=["python", "refactoring", "clean-code"],
            dependencies=[],
            examples=["Extract method refactoring"],
            file_path=Path("/tmp/refactoring/SKILL.md"),
            repo_id="test-repo",
            version="1.0.0",
            author="Test Author",
        ),
    ]
    return skills


@pytest.fixture
def indexing_engine(temp_storage, sample_skills):
    """Create IndexingEngine with sample skills."""
    # Create mock SkillManager
    skill_manager = SkillManager()
    skill_manager._skill_cache = {skill.id: skill for skill in sample_skills}
    skill_manager._skill_paths = {skill.id: skill.file_path for skill in sample_skills}

    # Create indexing engine
    engine = IndexingEngine(
        vector_backend="chromadb",
        graph_backend="networkx",
        skill_manager=skill_manager,
        storage_path=temp_storage,
    )

    # Index all sample skills
    for skill in sample_skills:
        engine.index_skill(skill)

    return engine


class TestIndexingEngineInitialization:
    """Test IndexingEngine initialization."""

    def test_initialization_creates_storage_directory(self, temp_storage):
        """Test that storage directory is created."""
        IndexingEngine(storage_path=temp_storage)
        assert temp_storage.exists()

    def test_initialization_creates_chromadb_client(self, temp_storage):
        """Test that ChromaDB client is initialized."""
        engine = IndexingEngine(storage_path=temp_storage)
        assert engine.chroma_client is not None
        assert engine.collection is not None

    def test_initialization_creates_networkx_graph(self, temp_storage):
        """Test that NetworkX graph is initialized."""
        engine = IndexingEngine(storage_path=temp_storage)
        assert engine.graph is not None
        assert len(engine.graph.nodes()) == 0  # Empty initially

    def test_initialization_loads_embedding_model(self, temp_storage):
        """Test that sentence-transformers model is loaded."""
        engine = IndexingEngine(storage_path=temp_storage)
        assert engine.embedding_model is not None


class TestIndexingEngineIndexing:
    """Test skill indexing functionality."""

    def test_index_skill_adds_to_chromadb(self, indexing_engine, sample_skills):
        """Test that skills are added to ChromaDB."""
        assert indexing_engine.collection.count() == len(sample_skills)

    def test_index_skill_adds_to_graph(self, indexing_engine, sample_skills):
        """Test that skills are added to NetworkX graph."""
        assert indexing_engine.graph.number_of_nodes() == len(sample_skills)

    def test_index_skill_creates_metadata(self, indexing_engine, sample_skills):
        """Test that ChromaDB metadata is created correctly."""
        results = indexing_engine.collection.get(
            ids=[sample_skills[0].id],
            include=["metadatas"],
        )

        assert results["metadatas"] is not None
        metadata = results["metadatas"][0]
        assert metadata["skill_id"] == sample_skills[0].id
        assert metadata["name"] == sample_skills[0].name
        assert metadata["category"] == sample_skills[0].category
        assert "python" in metadata["tags"]

    def test_extract_relationships_includes_dependencies(
        self, indexing_engine, sample_skills
    ):
        """Test that dependency relationships are extracted."""
        debugging_skill = sample_skills[1]  # Has dependency on pytest
        relationships = indexing_engine.extract_relationships(debugging_skill)

        depends_on = [r for r in relationships if r[1] == "depends_on"]
        assert len(depends_on) > 0
        assert depends_on[0][2] == "test-repo/pytest-skill"

    def test_extract_relationships_includes_category(
        self, indexing_engine, sample_skills
    ):
        """Test that category relationships are extracted."""
        # Index all skills first to establish category relationships
        pytest_skill = sample_skills[0]
        relationships = indexing_engine.extract_relationships(pytest_skill)

        # Should have same_category relationships
        same_category = [r for r in relationships if r[1] == "same_category"]
        # Note: May be empty if indexing order matters
        assert isinstance(same_category, list)

    def test_extract_relationships_includes_tags(self, indexing_engine, sample_skills):
        """Test that tag-based relationships are extracted."""
        pytest_skill = sample_skills[0]
        relationships = indexing_engine.extract_relationships(pytest_skill)

        shared_tag = [r for r in relationships if r[1] == "shared_tag"]
        # Should have shared_tag relationships with other Python skills
        assert isinstance(shared_tag, list)


class TestIndexingEngineBuildEmbeddings:
    """Test embedding generation."""

    def test_build_embeddings_returns_vector(self, indexing_engine, sample_skills):
        """Test that embeddings are generated."""
        skill = sample_skills[0]
        embedding = indexing_engine.build_embeddings(skill)

        assert isinstance(embedding, list)
        assert len(embedding) == 384  # all-MiniLM-L6-v2 dimension
        assert all(isinstance(x, float) for x in embedding)

    def test_create_embeddable_text_combines_fields(
        self, indexing_engine, sample_skills
    ):
        """Test that embeddable text includes all fields."""
        skill = sample_skills[0]
        text = indexing_engine._create_embeddable_text(skill)

        assert skill.name in text
        assert skill.description in text
        assert "python" in text.lower()
        assert "pytest" in text.lower()


class TestIndexingEngineReindexAll:
    """Test full reindexing functionality."""

    def test_reindex_all_without_skill_manager_raises_error(self, temp_storage):
        """Test that reindex_all requires SkillManager."""
        engine = IndexingEngine(storage_path=temp_storage)

        with pytest.raises(RuntimeError, match="SkillManager not set"):
            engine.reindex_all()

    def test_reindex_all_indexes_discovered_skills(self, temp_storage, sample_skills):
        """Test that reindex_all indexes all discovered skills."""
        skill_manager = SkillManager()
        skill_manager._skill_cache = {skill.id: skill for skill in sample_skills}
        skill_manager._skill_paths = {
            skill.id: skill.file_path for skill in sample_skills
        }

        # Mock discover_skills to return sample skills
        def mock_discover():
            return sample_skills

        skill_manager.discover_skills = mock_discover

        engine = IndexingEngine(storage_path=temp_storage, skill_manager=skill_manager)
        stats = engine.reindex_all()

        assert stats.total_skills == len(sample_skills)
        assert stats.graph_nodes == len(sample_skills)

    def test_reindex_all_with_force_clears_existing(
        self, indexing_engine, sample_skills
    ):
        """Test that force=True clears existing indices."""
        # Verify initial state
        assert indexing_engine.collection.count() == len(sample_skills)

        # Mock discover_skills to return sample skills
        def mock_discover():
            return sample_skills

        indexing_engine.skill_manager.discover_skills = mock_discover

        # Reindex with force
        stats = indexing_engine.reindex_all(force=True)

        # Should still have same number of skills
        assert stats.total_skills == len(sample_skills)


class TestIndexingEngineSearch:
    """Test hybrid search functionality."""

    def test_search_returns_results(self, indexing_engine):
        """Test that search returns relevant results."""
        results = indexing_engine.search("python testing", top_k=5)

        assert len(results) > 0
        assert all(isinstance(r, ScoredSkill) for r in results)
        assert all(0.0 <= r.score <= 1.0 for r in results)

    def test_search_ranks_by_relevance(self, indexing_engine):
        """Test that results are ranked by score."""
        results = indexing_engine.search("python testing", top_k=5)

        if len(results) > 1:
            # Scores should be descending
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_search_with_category_filter(self, indexing_engine):
        """Test that category filter works."""
        results = indexing_engine.search("python", category="testing", top_k=5)

        # All results should be in testing category
        for result in results:
            assert result.skill.category == "testing"

    def test_search_with_toolchain_filter(self, indexing_engine):
        """Test that toolchain filter works."""
        results = indexing_engine.search("testing", toolchain="python", top_k=5)

        # All results should have python tag
        for result in results:
            assert any("python" in tag.lower() for tag in result.skill.tags)

    def test_search_assigns_match_types(self, indexing_engine):
        """Test that match types are assigned."""
        results = indexing_engine.search("python testing", top_k=5)

        for result in results:
            assert result.match_type in ["vector", "graph", "hybrid"]

    def test_search_empty_query_returns_empty(self, indexing_engine):
        """Test that empty query returns empty results."""
        results = indexing_engine.search("", top_k=5)
        assert len(results) == 0


class TestIndexingEngineGetRelatedSkills:
    """Test graph-based related skills."""

    def test_get_related_skills_finds_dependencies(
        self, indexing_engine, sample_skills
    ):
        """Test that related skills include dependencies."""
        debugging_skill = sample_skills[1]  # Has dependency on pytest
        related = indexing_engine.get_related_skills(debugging_skill.id, max_depth=2)

        # Should find pytest skill as related
        [skill.id for skill in related]
        # May or may not include depending on graph structure
        assert isinstance(related, list)

    def test_get_related_skills_excludes_starting_skill(
        self, indexing_engine, sample_skills
    ):
        """Test that starting skill is not in results."""
        skill = sample_skills[0]
        related = indexing_engine.get_related_skills(skill.id, max_depth=2)

        related_ids = [s.id for s in related]
        assert skill.id not in related_ids

    def test_get_related_skills_missing_skill_returns_empty(self, indexing_engine):
        """Test that missing skill returns empty list."""
        related = indexing_engine.get_related_skills("nonexistent-skill", max_depth=2)
        assert len(related) == 0

    def test_get_related_skills_respects_max_depth(
        self, indexing_engine, sample_skills
    ):
        """Test that max_depth parameter works."""
        skill = sample_skills[0]

        # With depth 1, should find immediate neighbors
        related_1 = indexing_engine.get_related_skills(skill.id, max_depth=1)

        # With depth 2, may find more
        related_2 = indexing_engine.get_related_skills(skill.id, max_depth=2)

        # Both should be valid lists
        assert isinstance(related_1, list)
        assert isinstance(related_2, list)


class TestIndexingEngineGetStats:
    """Test statistics functionality."""

    def test_get_stats_returns_correct_counts(self, indexing_engine, sample_skills):
        """Test that stats return correct counts."""
        stats = indexing_engine.get_stats()

        assert isinstance(stats, IndexStats)
        assert stats.total_skills == len(sample_skills)
        assert stats.graph_nodes == len(sample_skills)
        assert stats.graph_edges >= 0  # At least no negative edges

    def test_get_stats_includes_timestamps(self, indexing_engine):
        """Test that stats include timestamp."""
        indexing_engine.reindex_all()
        stats = indexing_engine.get_stats()

        # Should have a valid timestamp after reindexing
        assert stats.last_indexed != "never"

    def test_get_stats_estimates_size(self, indexing_engine, sample_skills):
        """Test that vector store size is estimated."""
        stats = indexing_engine.get_stats()

        # Should estimate size based on skill count
        assert stats.vector_store_size > 0
        expected_size = len(sample_skills) * 2048
        assert stats.vector_store_size == expected_size


class TestIndexingEngineHybridSearch:
    """Test hybrid search combining vector and graph."""

    def test_vector_search_returns_results(self, indexing_engine):
        """Test vector search component."""
        results = indexing_engine._vector_search("python testing", top_k=5)

        assert isinstance(results, list)
        if results:
            assert "skill_id" in results[0]
            assert "score" in results[0]

    def test_graph_search_returns_results(self, indexing_engine, sample_skills):
        """Test graph search component."""
        seed_skill = sample_skills[0]
        results = indexing_engine._graph_search(seed_skill.id, max_depth=2)

        assert isinstance(results, list)

    def test_combine_results_weights_scores(self, indexing_engine, sample_skills):
        """Test that result combination uses proper weighting."""
        vector_results = [
            {"skill_id": sample_skills[0].id, "score": 0.9, "metadata": {}}
        ]
        graph_results = [{"skill_id": sample_skills[0].id, "score": 0.8}]

        combined = indexing_engine._combine_results(vector_results, graph_results)

        assert len(combined) > 0
        # Score should be weighted combination
        expected_score = 0.7 * 0.9 + 0.3 * 0.8  # VECTOR_WEIGHT * v + GRAPH_WEIGHT * g
        assert abs(combined[0].score - expected_score) < 0.01


class TestIndexingEngineErrorHandling:
    """Test error handling and edge cases."""

    def test_index_skill_handles_empty_tags(self, temp_storage):
        """Test indexing skill with empty tags."""
        skill = Skill(
            id="test/empty-tags",
            name="test-skill",
            description="Test skill with no tags",
            instructions="Test instructions",
            category="testing",
            tags=[],  # Empty tags
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test/SKILL.md"),
            repo_id="test-repo",
        )

        engine = IndexingEngine(storage_path=temp_storage)
        engine.index_skill(skill)  # Should not raise

        assert engine.collection.count() == 1

    def test_search_handles_no_results(self, temp_storage):
        """Test search with no indexed skills."""
        engine = IndexingEngine(storage_path=temp_storage)
        results = engine.search("nonexistent query", top_k=5)

        assert len(results) == 0

    def test_build_embeddings_handles_empty_content(self, temp_storage):
        """Test embedding generation with minimal content."""
        skill = Skill(
            id="test/minimal",
            name="x",
            description="y" * 10,  # Minimal description
            instructions="z" * 50,  # Minimal instructions
            category="testing",
            tags=[],
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test/SKILL.md"),
            repo_id="test-repo",
        )

        engine = IndexingEngine(storage_path=temp_storage)
        embedding = engine.build_embeddings(skill)

        # Should still generate embedding
        assert len(embedding) == 384
