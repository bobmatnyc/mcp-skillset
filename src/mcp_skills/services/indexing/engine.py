"""Main indexing engine orchestrating vector and graph stores.

Design Decision: Composition Over Inheritance

Rationale: IndexingEngine composes VectorStore, GraphStore, and HybridSearcher
rather than inheriting functionality. This follows SOLID principles and allows
independent testing and evolution of each component.

Architecture:
- IndexingEngine: Orchestration layer (this file)
- VectorStore: ChromaDB semantic search
- GraphStore: NetworkX relationship queries
- HybridSearcher: Result combination logic

Trade-offs:
- Maintainability: Clear separation of concerns vs. single monolithic class
- Testability: Each component independently testable
- Complexity: More files to navigate vs. everything in one place

Extension Points:
- Swap vector store backend (Qdrant, FAISS)
- Swap graph backend (Neo4j)
- Adjust hybrid weighting via HybridSearcher configuration
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mcp_skills.models.config import MCPSkillsConfig
from mcp_skills.models.skill import Skill
from mcp_skills.services.indexing.graph_store import GraphStore
from mcp_skills.services.indexing.hybrid_search import HybridSearcher, ScoredSkill
from mcp_skills.services.indexing.vector_store import VectorStore


if TYPE_CHECKING:
    from mcp_skills.services.skill_manager import SkillManager


logger = logging.getLogger(__name__)


@dataclass
class IndexStats:
    """Index statistics.

    Attributes:
        total_skills: Total number of indexed skills
        vector_store_size: Size of vector store in bytes
        graph_nodes: Number of nodes in knowledge graph
        graph_edges: Number of edges in knowledge graph
        last_indexed: Timestamp of last indexing operation
    """

    total_skills: int
    vector_store_size: int
    graph_nodes: int
    graph_edges: int
    last_indexed: str


class IndexingEngine:
    """Build and maintain vector + KG indices for skill discovery.

    Combines vector embeddings for semantic search with knowledge graph
    for relationship-based discovery.

    Architecture:
        - Vector Store: ChromaDB for semantic similarity
        - Knowledge Graph: NetworkX for skill relationships
        - Embeddings: sentence-transformers/all-MiniLM-L6-v2
        - Hybrid Search: 70% vector + 30% graph weighting

    Performance Requirements:
    - Batch indexing: Index all skills at once when possible
    - Cache embeddings: Don't regenerate if skill unchanged
    - Graph queries: Use NetworkX shortest_path, neighbors for efficiency
    - ChromaDB queries: Use where filters for metadata filtering

    Error Handling:
    - ChromaDB connection failures → Log error, raise RuntimeError
    - Missing skills during indexing → Log warning, skip
    - Invalid embeddings → Log error, skip skill
    - Graph cycles in dependencies → Allow (use DiGraph, no cycle checking)

    Example:
        >>> from pathlib import Path
        >>> engine = IndexingEngine(
        ...     skill_manager=manager,
        ...     storage_path=Path.home() / ".mcp-skillset"
        ... )
        >>> stats = engine.reindex_all(force=True)
        >>> results = engine.search("python testing", top_k=5)
        >>> results[0].skill.name
        'pytest-testing'
    """

    # Hybrid search weights (delegated to HybridSearcher)
    VECTOR_WEIGHT = 0.7
    GRAPH_WEIGHT = 0.3

    def __init__(
        self,
        vector_backend: str = "chromadb",
        graph_backend: str = "networkx",
        skill_manager: Optional["SkillManager"] = None,
        storage_path: Path | None = None,
        config: MCPSkillsConfig | None = None,
    ) -> None:
        """Initialize indexing engine with optional configuration.

        Args:
            vector_backend: Vector store backend (chromadb, qdrant, faiss)
            graph_backend: Knowledge graph backend (networkx, neo4j)
            skill_manager: SkillManager instance for skill loading
            storage_path: Path to store ChromaDB data (defaults to ~/.mcp-skillset/chromadb/)
            config: Optional MCPSkillsConfig for hybrid search weights and other settings

        Raises:
            RuntimeError: If ChromaDB or component initialization fails
        """
        self.vector_backend = vector_backend
        self.graph_backend = graph_backend
        self.skill_manager = skill_manager
        self.storage_path = storage_path or (Path.home() / ".mcp-skillset" / "chromadb")
        self.config = config

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Determine graph persistence path
        # For test isolation: custom storage paths store graph inside their directory
        # For production: use standard ~/.mcp-skillset/indices/ location
        if config and config.knowledge_graph.persist_path:
            self._graph_path = config.knowledge_graph.persist_path
        else:
            default_storage = Path.home() / ".mcp-skillset" / "chromadb"
            if self.storage_path == default_storage:
                # Production: use standard location for backward compatibility
                self._graph_path = (
                    Path.home() / ".mcp-skillset" / "indices" / "knowledge_graph.pkl"
                )
            else:
                # Custom/test: store graph inside storage_path for isolation
                self._graph_path = self.storage_path / "knowledge_graph.pkl"

        # Initialize components
        try:
            self.vector_store = VectorStore(persist_directory=self.storage_path)
            self.graph_store = GraphStore()

            # Try to load existing graph from disk
            if self._graph_path.exists():
                loaded = self.graph_store.load(self._graph_path)
                if loaded:
                    stats = self.graph_store.get_stats()
                    logger.info(
                        f"Loaded persisted knowledge graph: "
                        f"{stats['nodes']} nodes, {stats['edges']} edges"
                    )

            # Initialize HybridSearcher with weights from config if available
            if config:
                self.hybrid_searcher = HybridSearcher(
                    vector_store=self.vector_store,
                    graph_store=self.graph_store,
                    skill_manager=skill_manager,
                    vector_weight=config.hybrid_search.vector_weight,
                    graph_weight=config.hybrid_search.graph_weight,
                )
                logger.info(
                    f"IndexingEngine initialized with hybrid search weights: "
                    f"vector={config.hybrid_search.vector_weight:.2f}, "
                    f"graph={config.hybrid_search.graph_weight:.2f}"
                )
            else:
                # No config - use defaults
                self.hybrid_searcher = HybridSearcher(
                    vector_store=self.vector_store,
                    graph_store=self.graph_store,
                    skill_manager=skill_manager,
                )
                logger.info(
                    "IndexingEngine initialized with default hybrid search weights"
                )

        except Exception as e:
            logger.error(f"Failed to initialize IndexingEngine: {e}")
            raise RuntimeError(f"IndexingEngine initialization failed: {e}") from e

        # Track last indexing time
        self._last_indexed: datetime | None = None

    def index_skill(self, skill: Skill) -> None:
        """Add skill to vector + KG stores.

        Indexing Flow:
        1. Index in vector store (embeddings + metadata)
        2. Add node to graph store
        3. Add edges for dependencies, category, tags

        Args:
            skill: Skill object to index

        Raises:
            RuntimeError: If indexing fails critically (but typically logs and continues)
        """
        try:
            # 1. Index in vector store
            self.vector_store.index_skill(skill)

            # 2. Add node to knowledge graph
            self.graph_store.add_skill(skill)

            # 3. Add relationships (edges)
            self.graph_store.add_relationships(skill)

            logger.debug(f"Indexed skill: {skill.id}")

        except Exception as e:
            logger.error(f"Failed to index skill {skill.id}: {e}")
            # Don't raise - allow indexing to continue for other skills

    def build_embeddings(self, skill: Skill) -> list[float]:
        """Generate embeddings from skill content.

        Delegates to VectorStore for embedding generation.

        Args:
            skill: Skill to generate embeddings for

        Returns:
            Embedding vector as list of floats

        Performance:
        - Time Complexity: O(n) where n = text length
        - ~15ms per skill on CPU, ~3ms on GPU
        - Embeddings cached by ChromaDB (no regeneration needed)

        Error Handling:
        - Empty text: Returns empty list
        - Encoding errors: Logs error and returns empty list
        """
        return self.vector_store.build_embeddings(skill)

    def extract_relationships(self, skill: Skill) -> list[tuple[str, str, str]]:
        """Identify skill dependencies and relationships.

        Delegates to GraphStore for relationship extraction.

        Args:
            skill: Skill to extract relationships from

        Returns:
            List of (source_id, relation_type, target_id) tuples
        """
        return self.graph_store.extract_relationships(skill)

    def reindex_all(self, force: bool = False) -> IndexStats:
        """Rebuild indices from scratch.

        Reindexing Process:
        1. Clear existing indices (if force=True)
        2. Discover all skills via SkillManager
        3. Generate embeddings for all skills
        4. Build knowledge graph relationships
        5. Return statistics

        Args:
            force: Force rebuild even if indices exist

        Returns:
            Index statistics after rebuild

        Performance:
        - Time Complexity: O(n * m) where n = skills, m = avg text length
        - Expected: ~2-5 seconds for 100 skills on CPU
        - Batch processing for efficiency

        Error Handling:
        - SkillManager not set → Raise RuntimeError
        - Skill loading failures → Log warning and skip
        - Embedding failures → Log error and skip
        """
        if not self.skill_manager:
            raise RuntimeError(
                "SkillManager not set. Pass skill_manager to __init__() "
                "or set self.skill_manager before calling reindex_all()"
            )

        logger.info(f"Starting reindex (force={force})...")

        # 1. Clear existing indices if forced
        if force:
            logger.info("Clearing existing indices...")
            self.vector_store.clear()
            self.graph_store.clear()

        # 2. Discover all skills
        skills = self.skill_manager.discover_skills()
        logger.info(f"Discovered {len(skills)} skills for indexing")

        # 3. Index each skill (embeddings + graph)
        indexed_count = 0
        failed_count = 0

        for skill in skills:
            try:
                self.index_skill(skill)
                indexed_count += 1
            except Exception as e:
                logger.error(f"Failed to index skill {skill.id}: {e}")
                failed_count += 1

        # Update last indexed timestamp
        self._last_indexed = datetime.now()

        # 4. Save graph to disk for persistence
        if self.graph_store.save(self._graph_path):
            logger.info(f"Knowledge graph saved to {self._graph_path}")
        else:
            logger.warning("Failed to save knowledge graph to disk")

        logger.info(
            f"Reindexing complete: {indexed_count} indexed, {failed_count} failed"
        )

        # 5. Return statistics
        return self.get_stats()

    def search(
        self,
        query: str,
        toolchain: str | None = None,
        category: str | None = None,
        top_k: int = 10,
    ) -> list[ScoredSkill]:
        """Search skills using vector similarity + KG.

        Delegates to HybridSearcher for the actual search logic.

        Args:
            query: Search query (natural language)
            toolchain: Optional toolchain filter (Python, TypeScript, etc.)
            category: Optional category filter (testing, debugging, etc.)
            top_k: Maximum number of results

        Returns:
            List of ScoredSkill objects sorted by relevance

        Performance:
        - Vector search: O(n log k) with ChromaDB indexing
        - Graph search: O(n + e) for BFS traversal
        - Total: ~50-100ms for 1000 skills

        Example:
            >>> engine = IndexingEngine(skill_manager=manager)
            >>> results = engine.search("python testing", category="testing")
            >>> results[0].skill.name
            'pytest-testing'
            >>> results[0].score
            0.92
            >>> results[0].match_type
            'hybrid'
        """
        return self.hybrid_searcher.search(
            query=query,
            toolchain=toolchain,
            category=category,
            top_k=top_k,
        )

    def get_related_skills(self, skill_id: str, max_depth: int = 2) -> list[Skill]:
        """Find related skills via knowledge graph.

        Traverses graph to find skills connected via dependencies,
        categories, or tags.

        Args:
            skill_id: Starting skill ID
            max_depth: Maximum traversal depth

        Returns:
            List of related Skill objects

        Performance:
        - Time Complexity: O(n + e) for BFS traversal
        - Expected: <10ms for 1000 skills

        Example:
            >>> engine = IndexingEngine(skill_manager=manager)
            >>> related = engine.get_related_skills("anthropics/pytest", max_depth=2)
            >>> related[0].name
            'pytest-fixtures'
        """
        if not self.skill_manager:
            logger.warning("SkillManager not set, cannot load related skills")
            return []

        return self.graph_store.get_related_skills(
            skill_id=skill_id,
            skill_manager=self.skill_manager,
            max_depth=max_depth,
        )

    def get_stats(self) -> IndexStats:
        """Get current index statistics.

        Returns:
            IndexStats object with current metrics

        Statistics Include:
        - total_skills: Number of skills in ChromaDB
        - vector_store_size: Estimated size in bytes
        - graph_nodes: Number of nodes in NetworkX graph
        - graph_edges: Number of edges in graph
        - last_indexed: ISO timestamp of last indexing

        Example:
            >>> stats = engine.get_stats()
            >>> stats.total_skills
            42
            >>> stats.graph_nodes
            42
            >>> stats.graph_edges
            156
        """
        try:
            # Get vector store stats
            total_skills = self.vector_store.count()

            # Estimate vector store size
            # Rough estimate: 384 dims * 4 bytes/float + metadata ~= 2KB per skill
            vector_store_size = total_skills * 2048

            # Get graph stats
            graph_stats = self.graph_store.get_stats()
            graph_nodes = graph_stats["nodes"]
            graph_edges = graph_stats["edges"]

            # Last indexed timestamp
            last_indexed = (
                self._last_indexed.isoformat() if self._last_indexed else "never"
            )

            return IndexStats(
                total_skills=total_skills,
                vector_store_size=vector_store_size,
                graph_nodes=graph_nodes,
                graph_edges=graph_edges,
                last_indexed=last_indexed,
            )

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return IndexStats(
                total_skills=0,
                vector_store_size=0,
                graph_nodes=0,
                graph_edges=0,
                last_indexed="error",
            )

    # Expose collection property for backward compatibility
    @property
    def collection(self) -> Any:
        """Access ChromaDB collection (backward compatibility).

        Returns:
            ChromaDB collection object
        """
        return self.vector_store.collection

    # Expose graph property for backward compatibility
    @property
    def graph(self) -> Any:
        """Access NetworkX graph (backward compatibility).

        Returns:
            NetworkX DiGraph object
        """
        return self.graph_store.graph

    # Expose embedding_model property for backward compatibility
    @property
    def embedding_model(self) -> Any:
        """Access sentence-transformers model (backward compatibility).

        Returns:
            SentenceTransformer model object
        """
        return self.vector_store.embedding_model

    # Expose chroma_client property for backward compatibility
    @property
    def chroma_client(self) -> Any:
        """Access ChromaDB client (backward compatibility).

        Returns:
            ChromaDB client object
        """
        return self.vector_store.chroma_client

    # Expose private methods for backward compatibility with tests
    def _create_embeddable_text(self, skill: Skill) -> str:
        """Create embeddable text (backward compatibility for tests)."""
        return self.vector_store._create_embeddable_text(skill)

    def _vector_search(
        self,
        query: str,
        toolchain: str | None = None,
        category: str | None = None,
        top_k: int = 20,
    ) -> list[dict]:
        """Perform vector search (backward compatibility for tests)."""
        return self.hybrid_searcher._vector_search(
            query=query,
            toolchain=toolchain,
            category=category,
            top_k=top_k,
        )

    def _graph_search(self, seed_skill_id: str, max_depth: int = 2) -> list[dict]:
        """Perform graph search (backward compatibility for tests)."""
        return self.hybrid_searcher._graph_search(seed_skill_id, max_depth)

    def _combine_results(
        self, vector_results: list[dict], graph_results: list[dict]
    ) -> list[ScoredSkill]:
        """Combine results (backward compatibility for tests)."""
        return self.hybrid_searcher._combine_results(vector_results, graph_results)
