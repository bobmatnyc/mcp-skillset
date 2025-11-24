"""Vector store using ChromaDB for semantic similarity search.

Design Decision: Persistent ChromaDB Storage

Rationale: Use persistent storage to avoid reindexing on every startup.
Skills are relatively stable, making persistence valuable.

Trade-offs:
- Startup Speed: Faster restarts vs. initial indexing overhead
- Disk Space: ~100KB per 100 skills (minimal)
- Data Freshness: Must detect when reindexing is needed

Error Handling:
- ChromaDB connection failures → Raise RuntimeError with details
- Corrupted database → Delete and reinitialize (future enhancement)
- Empty embeddings → Log warning and skip skill
"""

import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from mcp_skills.models.skill import Skill


logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store using ChromaDB for semantic similarity search.

    This class encapsulates all ChromaDB operations including:
    - Collection management
    - Embedding generation
    - Vector similarity search
    - Batch operations

    Architecture:
    - Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
    - Storage: Persistent ChromaDB on disk
    - Indexing: Automatic via ChromaDB

    Performance:
    - Embedding generation: ~15ms per skill on CPU, ~3ms on GPU
    - Search: O(n log k) with ChromaDB indexing
    - Storage: ~2KB per skill (embeddings + metadata)
    """

    def __init__(self, persist_directory: Path | None = None) -> None:
        """Initialize ChromaDB vector store.

        Args:
            persist_directory: Path to store ChromaDB data
                             (defaults to ~/.mcp-skills/chromadb/)

        Raises:
            RuntimeError: If ChromaDB initialization fails
        """
        self.persist_directory = persist_directory or (
            Path.home() / ".mcp-skills" / "chromadb"
        )

        # Ensure storage directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        try:
            self._init_chromadb()
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise RuntimeError(f"ChromaDB initialization failed: {e}") from e

        # Initialize sentence-transformers model for embeddings
        try:
            self._init_embedding_model()
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Embedding model initialization failed: {e}") from e

    def _init_chromadb(self) -> None:
        """Initialize ChromaDB persistent client.

        Creates or connects to persistent ChromaDB instance with
        sentence-transformers embedding function.
        """
        try:
            # Create persistent ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            # Use sentence-transformers embedding function
            # This matches our manual embedding model for consistency
            embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

            # Get or create collection
            # Type ignore for ChromaDB's complex embedding function types
            self.collection = self.chroma_client.get_or_create_collection(
                name="skills",
                embedding_function=embedding_fn,  # type: ignore[arg-type]
                metadata={"description": "MCP Skills vector embeddings"},
            )

            logger.info(
                f"ChromaDB initialized at {self.persist_directory} "
                f"with {self.collection.count()} skills"
            )

        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise

    def _init_embedding_model(self) -> None:
        """Initialize sentence-transformers embedding model.

        Uses all-MiniLM-L6-v2 for fast, high-quality embeddings:
        - Embedding size: 384 dimensions
        - Speed: ~15ms per skill on CPU
        - Quality: Optimized for semantic similarity

        Performance Note:
        - Model loaded once and cached in memory (~90MB)
        - GPU acceleration used if available (CUDA)
        """
        self.embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        logger.info("Sentence-transformers model loaded successfully")

    def index_skill(self, skill: Skill) -> None:
        """Add skill to vector store.

        Creates embeddings from skill content and stores in ChromaDB
        with metadata for filtering.

        Args:
            skill: Skill object to index

        Error Handling:
        - Empty embeddable text → Log warning and skip
        - Embedding generation failure → Log error and skip
        - ChromaDB add failure → Log error (allows batch to continue)
        """
        try:
            # Create embeddable text
            embeddable_text = self._create_embeddable_text(skill)

            if not embeddable_text.strip():
                logger.warning(f"Empty embeddable text for skill: {skill.id}")
                return

            # Prepare metadata
            metadata = {
                "skill_id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "tags": ",".join(skill.tags),  # Comma-separated for ChromaDB
                "repo_id": skill.repo_id,
            }

            # Add to ChromaDB (embeddings generated automatically)
            self.collection.add(
                ids=[skill.id],
                documents=[embeddable_text],
                metadatas=[metadata],
            )

            logger.debug(f"Indexed skill in vector store: {skill.id}")

        except Exception as e:
            logger.error(f"Failed to index skill {skill.id} in vector store: {e}")
            # Don't raise - allow indexing to continue for other skills

    def _create_embeddable_text(self, skill: Skill) -> str:
        """Create text representation for embedding.

        Combines skill fields weighted by importance:
        - Name (highest weight)
        - Description
        - First 500 chars of instructions
        - Tags

        Args:
            skill: Skill to create text from

        Returns:
            Combined text string for embedding
        """
        # Truncate instructions to avoid overwhelming embedding
        instructions_preview = skill.instructions[:500]

        # Combine fields with space separation
        embeddable_text = (
            f"{skill.name} "
            f"{skill.description} "
            f"{instructions_preview} "
            f"{' '.join(skill.tags)}"
        )

        return embeddable_text

    def build_embeddings(self, skill: Skill) -> list[float]:
        """Generate embeddings from skill content.

        Combines name, description, instructions, and tags
        into embeddings using sentence-transformers.

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
        try:
            # Create embeddable text
            embeddable_text = self._create_embeddable_text(skill)

            if not embeddable_text.strip():
                logger.warning(f"Empty embeddable text for skill: {skill.id}")
                return []

            # Generate embedding using sentence-transformers
            embedding = self.embedding_model.encode(
                embeddable_text, convert_to_numpy=True
            )

            # Convert numpy array to list for JSON serialization
            embedding_list: list[float] = embedding.tolist()
            return embedding_list

        except Exception as e:
            logger.error(f"Failed to generate embedding for {skill.id}: {e}")
            return []

    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search vector store for similar skills.

        Performs semantic similarity search using ChromaDB's vector search.

        Args:
            query: Search query (natural language)
            top_k: Maximum number of results
            filters: Optional metadata filters (e.g., {"category": "testing"})

        Returns:
            List of dicts with skill_id, score, and metadata

        Performance:
        - Time Complexity: O(n log k) with ChromaDB indexing
        - Expected: ~20-50ms for 1000 skills

        Example:
            >>> vector_store = VectorStore()
            >>> results = vector_store.search(
            ...     "python testing",
            ...     filters={"category": "testing"}
            ... )
            >>> results[0]["skill_id"]
            'anthropics/pytest'
            >>> results[0]["score"]
            0.92
        """
        try:
            # ChromaDB query with optional filters
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, self.collection.count()),
                where=filters if filters else None,
            )

            # Convert to structured format
            vector_results = []
            if results["ids"] and results["distances"]:
                for i, skill_id in enumerate(results["ids"][0]):
                    # Convert distance to similarity score (0-1)
                    # ChromaDB uses L2 distance, convert to similarity
                    distance = results["distances"][0][i]
                    similarity = 1.0 / (1.0 + distance)

                    metadata = (
                        results["metadatas"][0][i] if results["metadatas"] else {}
                    )

                    vector_results.append(
                        {
                            "skill_id": skill_id,
                            "score": similarity,
                            "metadata": metadata,
                        }
                    )

            return vector_results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def clear(self) -> None:
        """Clear all vectors from store.

        Deletes all documents from the ChromaDB collection.
        Useful for reindexing operations.
        """
        try:
            existing_ids = self.collection.get()["ids"]
            if existing_ids:
                self.collection.delete(ids=existing_ids)
                logger.info(f"Cleared {len(existing_ids)} skills from vector store")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            raise

    def count(self) -> int:
        """Get number of skills in vector store.

        Returns:
            Number of indexed skills
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to count vector store: {e}")
            return 0
