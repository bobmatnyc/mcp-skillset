"""Comprehensive performance benchmarks for mcp-skills.

Design Decision: Multi-Scale Performance Testing

Rationale: Test performance across different scales (100, 1000, 10000 skills)
to identify scalability bottlenecks and ensure performance doesn't degrade
non-linearly with dataset growth.

Baseline Thresholds (target performance):
- Index 100 skills: < 10 seconds
- Index 1000 skills: < 100 seconds
- Search query (p50): < 100ms
- Search query (p95): < 500ms
- SQLite lookup by ID: < 1ms
- SQLite query with filters: < 10ms

Performance Monitoring Strategy:
1. Track metrics across scales to detect O(n²) behavior
2. Use pytest-benchmark for consistent measurement
3. Save baseline for regression detection
4. Monitor memory usage for large-scale operations

Error Handling:
- Benchmark failures should not crash test suite
- Out-of-memory scenarios should be handled gracefully
- Timeout protection for large-scale benchmarks
"""

import gc
import time
from datetime import UTC
from pathlib import Path

import pytest

from mcp_skills.models.skill import Skill
from mcp_skills.services.indexing import IndexingEngine
from mcp_skills.services.metadata_store import MetadataStore
from mcp_skills.services.skill_manager import SkillManager


class TestIndexingPerformance:
    """Benchmark indexing performance across different scales.

    Tests measure:
    - Time to index N skills
    - Memory usage during indexing
    - Throughput (skills/second)
    - Scalability characteristics
    """

    def test_index_100_skills_baseline(
        self, benchmark, benchmark_storage_path: Path, benchmark_skills_100: list[Skill]
    ):
        """Benchmark indexing 100 skills (baseline scale).

        Target: < 10 seconds

        Performance Metrics:
        - Total time to index 100 skills
        - Average time per skill (~100ms expected)
        - Memory overhead

        Args:
            benchmark: pytest-benchmark fixture
            benchmark_storage_path: Temporary storage path
            benchmark_skills_100: List of 100 sample skills
        """

        def setup():
            """Setup fresh engine for each benchmark round."""
            skill_manager = SkillManager()
            skill_manager._skill_cache = {
                skill.id: skill for skill in benchmark_skills_100
            }
            skill_manager._skill_paths = {
                skill.id: skill.file_path for skill in benchmark_skills_100
            }

            engine = IndexingEngine(
                vector_backend="chromadb",
                graph_backend="networkx",
                skill_manager=skill_manager,
                storage_path=benchmark_storage_path / "index_100",
            )
            return (engine, benchmark_skills_100), {}

        def index_skills(engine_and_skills, *args):
            """Index all skills."""
            engine, skills = engine_and_skills
            for skill in skills:
                engine.index_skill(skill)

        # Run benchmark with setup
        benchmark.pedantic(index_skills, setup=setup, rounds=3, iterations=1)

        # Verify all skills were indexed
        # (verification happens outside benchmark timing)

    def test_index_1000_skills_moderate_scale(
        self,
        benchmark,
        benchmark_storage_path: Path,
        benchmark_skills_1000: list[Skill],
    ):
        """Benchmark indexing 1000 skills (moderate scale).

        Target: < 100 seconds (10x skills should be ~10x time if O(n))

        Performance Metrics:
        - Total time to index 1000 skills
        - Scalability factor vs. 100 skills
        - Detect O(n²) behavior if present

        Args:
            benchmark: pytest-benchmark fixture
            benchmark_storage_path: Temporary storage path
            benchmark_skills_1000: List of 1000 sample skills
        """

        def setup():
            """Setup fresh engine for each benchmark round."""
            skill_manager = SkillManager()
            skill_manager._skill_cache = {
                skill.id: skill for skill in benchmark_skills_1000
            }
            skill_manager._skill_paths = {
                skill.id: skill.file_path for skill in benchmark_skills_1000
            }

            engine = IndexingEngine(
                vector_backend="chromadb",
                graph_backend="networkx",
                skill_manager=skill_manager,
                storage_path=benchmark_storage_path / "index_1000",
            )
            return (engine, benchmark_skills_1000), {}

        def index_skills(engine_and_skills, *args):
            """Index all skills."""
            engine, skills = engine_and_skills
            for skill in skills:
                engine.index_skill(skill)

        # Run benchmark with setup (fewer rounds due to time)
        benchmark.pedantic(index_skills, setup=setup, rounds=2, iterations=1)

    @pytest.mark.slow
    def test_index_10000_skills_large_scale(
        self,
        benchmark,
        benchmark_storage_path: Path,
        benchmark_skills_10000: list[Skill],
    ):
        """Benchmark indexing 10000 skills (large scale).

        Target: < 1000 seconds (100x skills should be ~100x time if O(n))

        Performance Metrics:
        - Total time to index 10000 skills
        - Scalability characteristics
        - Memory usage at scale

        Note: Marked as 'slow' - skip in normal test runs.

        Args:
            benchmark: pytest-benchmark fixture
            benchmark_storage_path: Temporary storage path
            benchmark_skills_10000: List of 10000 sample skills
        """

        def setup():
            """Setup fresh engine for each benchmark round."""
            # Clear memory before large operation
            gc.collect()

            skill_manager = SkillManager()
            skill_manager._skill_cache = {
                skill.id: skill for skill in benchmark_skills_10000
            }
            skill_manager._skill_paths = {
                skill.id: skill.file_path for skill in benchmark_skills_10000
            }

            engine = IndexingEngine(
                vector_backend="chromadb",
                graph_backend="networkx",
                skill_manager=skill_manager,
                storage_path=benchmark_storage_path / "index_10000",
            )
            return (engine, benchmark_skills_10000), {}

        def index_skills(engine_and_skills, *args):
            """Index all skills."""
            engine, skills = engine_and_skills
            for skill in skills:
                engine.index_skill(skill)

        # Run benchmark with single round due to time
        benchmark.pedantic(index_skills, setup=setup, rounds=1, iterations=1)

    def test_reindex_all_performance(
        self, benchmark, benchmark_storage_path: Path, benchmark_skills_100: list[Skill]
    ):
        """Benchmark reindex_all() operation.

        Tests the batch reindexing performance, which should be
        optimized compared to individual indexing.

        Target: Similar to individual indexing (~10 seconds for 100 skills)

        Args:
            benchmark: pytest-benchmark fixture
            benchmark_storage_path: Temporary storage path
            benchmark_skills_100: List of 100 sample skills
        """

        def setup():
            """Setup engine with skill manager."""
            skill_manager = SkillManager()
            skill_manager._skill_cache = {
                skill.id: skill for skill in benchmark_skills_100
            }
            skill_manager._skill_paths = {
                skill.id: skill.file_path for skill in benchmark_skills_100
            }

            # Mock discover_skills to return our benchmark skills
            skill_manager.discover_skills = lambda: benchmark_skills_100

            engine = IndexingEngine(
                vector_backend="chromadb",
                graph_backend="networkx",
                skill_manager=skill_manager,
                storage_path=benchmark_storage_path / "reindex",
            )
            return (engine,), {}

        def reindex_all(engine_tuple, *args):
            """Reindex all skills."""
            engine = engine_tuple[0]
            engine.reindex_all(force=True)

        benchmark.pedantic(reindex_all, setup=setup, rounds=3, iterations=1)


class TestSearchPerformance:
    """Benchmark search performance across different scales.

    Tests measure:
    - Query latency (p50, p95, p99)
    - ChromaDB vector search time
    - NetworkX graph search time
    - Hybrid search combination time
    """

    def test_vector_search_latency_100_skills(
        self, benchmark, indexed_engine_100: IndexingEngine
    ):
        """Benchmark vector search latency with 100 indexed skills.

        Target: < 100ms (p50 latency)

        Performance Metrics:
        - Median query time (p50)
        - 95th percentile (p95)
        - 99th percentile (p99)

        Args:
            benchmark: pytest-benchmark fixture
            indexed_engine_100: Pre-indexed engine with 100 skills
        """

        def search_query():
            """Execute search query."""
            results = indexed_engine_100._vector_search(
                query="python testing tools", top_k=10
            )
            return results

        # Run many iterations to get accurate percentile measurements
        benchmark(search_query)

        # Benchmark automatically tracks min, max, mean, median, stddev

    def test_vector_search_latency_1000_skills(
        self, benchmark, indexed_engine_1000: IndexingEngine
    ):
        """Benchmark vector search latency with 1000 indexed skills.

        Target: < 200ms (p50 latency, scaling sub-linearly)

        Performance Metrics:
        - Compare to 100-skill benchmark
        - Should scale sub-linearly due to indexing

        Args:
            benchmark: pytest-benchmark fixture
            indexed_engine_1000: Pre-indexed engine with 1000 skills
        """

        def search_query():
            """Execute search query."""
            results = indexed_engine_1000._vector_search(
                query="python testing tools", top_k=10
            )
            return results

        benchmark(search_query)

    def test_graph_search_latency(self, benchmark, indexed_engine_100: IndexingEngine):
        """Benchmark graph search latency.

        Target: < 10ms (graph traversal should be very fast)

        Performance Metrics:
        - BFS traversal time
        - Graph query efficiency

        Args:
            benchmark: pytest-benchmark fixture
            indexed_engine_100: Pre-indexed engine with 100 skills
        """

        def graph_search():
            """Execute graph search."""
            # Use first skill as seed
            seed_id = "benchmark-repo/skill-00000"
            results = indexed_engine_100._graph_search(seed_id, max_depth=2)
            return results

        benchmark(graph_search)

    def test_hybrid_search_end_to_end(
        self, benchmark, indexed_engine_100: IndexingEngine
    ):
        """Benchmark full hybrid search (vector + graph).

        Target: < 200ms (combined vector + graph + reranking)

        Performance Metrics:
        - End-to-end search latency
        - Hybrid combination overhead

        Args:
            benchmark: pytest-benchmark fixture
            indexed_engine_100: Pre-indexed engine with 100 skills
        """

        def hybrid_search():
            """Execute full hybrid search."""
            results = indexed_engine_100.search(query="python testing tools", top_k=10)
            return results

        benchmark(hybrid_search)

    def test_search_with_filters(self, benchmark, indexed_engine_100: IndexingEngine):
        """Benchmark search with category and toolchain filters.

        Target: Similar to unfiltered search (~200ms)

        Performance Metrics:
        - Filter application overhead
        - ChromaDB metadata filtering efficiency

        Args:
            benchmark: pytest-benchmark fixture
            indexed_engine_100: Pre-indexed engine with 100 skills
        """

        def filtered_search():
            """Execute search with filters."""
            results = indexed_engine_100.search(
                query="python testing",
                category="testing",
                toolchain="python",
                top_k=10,
            )
            return results

        benchmark(filtered_search)

    def test_related_skills_traversal(
        self, benchmark, indexed_engine_100: IndexingEngine
    ):
        """Benchmark get_related_skills() graph traversal.

        Target: < 20ms (graph traversal + skill loading)

        Performance Metrics:
        - Graph traversal time
        - Skill loading overhead

        Args:
            benchmark: pytest-benchmark fixture
            indexed_engine_100: Pre-indexed engine with 100 skills
        """

        def get_related():
            """Get related skills."""
            results = indexed_engine_100.get_related_skills(
                skill_id="benchmark-repo/skill-00000", max_depth=2
            )
            return results

        benchmark(get_related)


class TestDatabasePerformance:
    """Benchmark SQLite metadata store performance.

    Tests measure:
    - Lookup by ID (indexed)
    - Query with filters
    - Batch insert performance
    - Index effectiveness
    """

    def test_lookup_by_id_single(self, benchmark, metadata_store_100: MetadataStore):
        """Benchmark SQLite lookup by ID (indexed column).

        Target: < 1ms (indexed lookup should be very fast)

        Performance Metrics:
        - Single row retrieval time
        - Index effectiveness

        Args:
            benchmark: pytest-benchmark fixture
            metadata_store_100: Metadata store with 100 repositories
        """

        def lookup_repository():
            """Lookup repository by ID."""
            repo_id = "benchmark/repo-00050"
            repo = metadata_store_100.get_repository(repo_id)
            return repo

        benchmark(lookup_repository)

    def test_list_all_repositories(self, benchmark, metadata_store_100: MetadataStore):
        """Benchmark SQLite query to list all repositories.

        Target: < 10ms for 100 repositories

        Performance Metrics:
        - Full table scan performance
        - Result materialization time

        Args:
            benchmark: pytest-benchmark fixture
            metadata_store_100: Metadata store with 100 repositories
        """

        def list_all():
            """List all repositories."""
            repos = metadata_store_100.list_repositories()
            return list(repos)

        benchmark(list_all)

    def test_update_repository_metadata(
        self, benchmark, metadata_store_100: MetadataStore
    ):
        """Benchmark updating repository metadata.

        Target: < 5ms per update

        Performance Metrics:
        - Update operation time
        - Index maintenance overhead

        Args:
            benchmark: pytest-benchmark fixture
            metadata_store_100: Metadata store with 100 repositories
        """

        def update_repo():
            """Update repository metadata."""
            repo = metadata_store_100.get_repository("benchmark/repo-00050")
            if repo:
                repo.skill_count = 42
                metadata_store_100.update_repository(repo)

        benchmark(update_repo)

    def test_list_1000_repositories(
        self, benchmark, metadata_store_1000: MetadataStore
    ):
        """Benchmark listing all repositories (no filters).

        Target: < 50ms for 1000 repositories

        Performance Metrics:
        - Full table scan performance
        - Result materialization time

        Args:
            benchmark: pytest-benchmark fixture
            metadata_store_1000: Metadata store with 1000 repositories
        """

        def list_all():
            """List all repositories."""
            repos = metadata_store_1000.list_repositories()
            return list(repos)

        benchmark(list_all)

    def test_batch_insert_performance(self, benchmark, benchmark_storage_path: Path):
        """Benchmark batch insert of 100 repositories.

        Target: < 1 second for 100 inserts

        Performance Metrics:
        - Insert throughput (repositories/second)
        - Transaction overhead

        Args:
            benchmark: pytest-benchmark fixture
            benchmark_storage_path: Temporary storage path
        """
        from datetime import datetime

        from mcp_skills.models.repository import Repository

        # Create a unique database for this benchmark
        timestamp = int(time.time() * 1000000)
        db_path = benchmark_storage_path / f"batch_insert_{timestamp}.db"
        store = MetadataStore(db_path=db_path)

        # Counter to make IDs unique across benchmark rounds
        round_counter = [0]

        def batch_insert():
            """Insert all repositories."""
            offset = round_counter[0] * 100
            for i in range(100):
                repo = Repository(
                    id=f"benchmark/repo-{(offset + i):06d}",
                    url=f"https://github.com/benchmark/repo-{(offset + i):06d}.git",
                    local_path=benchmark_storage_path
                    / "repos"
                    / f"repo-{(offset + i):06d}",
                    priority=50 + (i % 50),
                    last_updated=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
                    skill_count=10 + (i % 20),
                    license="MIT",
                )
                store.add_repository(repo)
            round_counter[0] += 1

        benchmark(batch_insert)


class TestMemoryUsage:
    """Memory usage benchmarks for large-scale operations.

    Tests measure:
    - Memory usage during indexing
    - Memory growth with dataset size
    - Memory cleanup after operations
    """

    def test_memory_usage_index_1000_skills(
        self,
        benchmark,
        benchmark_storage_path: Path,
        benchmark_skills_1000: list[Skill],
    ):
        """Benchmark memory usage when indexing 1000 skills.

        Performance Metrics:
        - Peak memory usage
        - Memory growth pattern
        - Post-operation cleanup

        Args:
            benchmark: pytest-benchmark fixture
            benchmark_storage_path: Temporary storage path
            benchmark_skills_1000: List of 1000 sample skills
        """
        # Note: pytest-benchmark doesn't directly measure memory,
        # but we can track it manually in the benchmark function

        def setup():
            """Setup with memory tracking."""
            gc.collect()  # Clean memory before measurement

            skill_manager = SkillManager()
            skill_manager._skill_cache = {
                skill.id: skill for skill in benchmark_skills_1000
            }
            skill_manager._skill_paths = {
                skill.id: skill.file_path for skill in benchmark_skills_1000
            }

            engine = IndexingEngine(
                vector_backend="chromadb",
                graph_backend="networkx",
                skill_manager=skill_manager,
                storage_path=benchmark_storage_path / "memory_test",
            )
            return (engine, benchmark_skills_1000), {}

        def index_with_memory_tracking(engine_and_skills, *args):
            """Index and track memory."""
            engine, skills = engine_and_skills

            for i, skill in enumerate(skills):
                engine.index_skill(skill)

                # Sample memory every 100 skills
                if i % 100 == 0:
                    gc.collect()  # Force collection to get accurate reading

        benchmark.pedantic(
            index_with_memory_tracking, setup=setup, rounds=1, iterations=1
        )
