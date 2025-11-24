"""Pytest configuration and fixtures for performance benchmarks.

Design Decision: Benchmark-Specific Fixtures

Rationale: Separate fixtures for benchmarks to avoid contaminating unit tests
with performance-specific setup. Benchmarks need larger datasets and realistic
workloads that would slow down unit tests.

Trade-offs:
- Isolation: Benchmark fixtures separate from unit test fixtures
- Performance: Can optimize fixtures for benchmark-specific needs
- Maintenance: Additional conftest.py to maintain

Performance Requirements:
- Generate realistic skill datasets efficiently
- Reuse generated data across benchmark runs
- Clean up temporary storage after benchmarks
"""

import tempfile
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from mcp_skills.models.repository import Repository
from mcp_skills.models.skill import Skill
from mcp_skills.services.indexing import IndexingEngine
from mcp_skills.services.metadata_store import MetadataStore
from mcp_skills.services.skill_manager import SkillManager


@pytest.fixture
def benchmark_storage_path() -> Generator[Path, None, None]:
    """Create temporary storage directory for benchmark tests.

    Yields:
        Path to temporary storage directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir)
        yield storage_path


def create_sample_skill(index: int, category: str = "testing") -> Skill:
    """Create a sample skill for benchmarking.

    Args:
        index: Skill index for unique identification
        category: Skill category

    Returns:
        Sample Skill object
    """
    categories = ["testing", "debugging", "refactoring", "documentation", "performance"]
    tags_options = [
        ["python", "pytest", "tdd"],
        ["javascript", "jest", "testing"],
        ["debugging", "pdb", "breakpoints"],
        ["refactoring", "solid", "clean-code"],
        ["docs", "markdown", "sphinx"],
    ]

    selected_category = categories[index % len(categories)]
    selected_tags = tags_options[index % len(tags_options)]

    return Skill(
        id=f"benchmark-repo/skill-{index:05d}",
        name=f"benchmark-skill-{index:05d}",
        description=f"This is benchmark skill number {index} for performance testing. "
        f"It demonstrates {selected_category} capabilities and serves as realistic test data.",
        instructions=(
            f"# Skill {index}\n\n"
            f"This skill provides {selected_category} functionality.\n\n"
            f"## Usage\n\n"
            f"Use this skill when you need to perform {selected_category} tasks.\n\n"
            f"## Examples\n\n"
            f"Example {index}: Demonstrates the primary use case.\n"
            f"Example {index + 1}: Shows an advanced scenario.\n\n"
            f"## Best Practices\n\n"
            f"- Follow the {selected_category} guidelines\n"
            f"- Consider edge cases\n"
            f"- Write comprehensive tests\n"
        ),
        category=selected_category,
        tags=selected_tags + [f"skill-{index}"],
        dependencies=(
            [f"benchmark-repo/skill-{(index - 1):05d}" for i in range(min(2, index))]
            if index > 0
            else []
        ),
        examples=[
            f"Example {index}: Primary use case",
            f"Example {index + 1}: Advanced scenario",
        ],
        file_path=Path(f"/tmp/benchmark/skill-{index:05d}/SKILL.md"),
        repo_id="benchmark-repo",
        version="1.0.0",
        author="Benchmark Author",
    )


@pytest.fixture
def benchmark_skills_100() -> list[Skill]:
    """Generate 100 sample skills for benchmarking.

    Returns:
        List of 100 Skill objects
    """
    return [create_sample_skill(i) for i in range(100)]


@pytest.fixture
def benchmark_skills_1000() -> list[Skill]:
    """Generate 1000 sample skills for benchmarking.

    Returns:
        List of 1000 Skill objects
    """
    return [create_sample_skill(i) for i in range(1000)]


@pytest.fixture
def benchmark_skills_10000() -> list[Skill]:
    """Generate 10000 sample skills for benchmarking.

    Performance Note:
    - Generation time: ~1-2 seconds
    - Memory usage: ~50MB for skill objects

    Returns:
        List of 10000 Skill objects
    """
    return [create_sample_skill(i) for i in range(10000)]


@pytest.fixture
def indexed_engine_100(
    benchmark_storage_path: Path, benchmark_skills_100: list[Skill]
) -> IndexingEngine:
    """Pre-indexed engine with 100 skills for search benchmarks.

    Args:
        benchmark_storage_path: Temporary storage path
        benchmark_skills_100: List of 100 skills

    Returns:
        IndexingEngine with 100 indexed skills
    """
    # Create skill manager with cached skills
    skill_manager = SkillManager()
    skill_manager._skill_cache = {skill.id: skill for skill in benchmark_skills_100}
    skill_manager._skill_paths = {
        skill.id: skill.file_path for skill in benchmark_skills_100
    }

    # Create and index engine
    engine = IndexingEngine(
        vector_backend="chromadb",
        graph_backend="networkx",
        skill_manager=skill_manager,
        storage_path=benchmark_storage_path / "chromadb_100",
    )

    # Index all skills
    for skill in benchmark_skills_100:
        engine.index_skill(skill)

    return engine


@pytest.fixture
def indexed_engine_1000(
    benchmark_storage_path: Path, benchmark_skills_1000: list[Skill]
) -> IndexingEngine:
    """Pre-indexed engine with 1000 skills for search benchmarks.

    Args:
        benchmark_storage_path: Temporary storage path
        benchmark_skills_1000: List of 1000 skills

    Returns:
        IndexingEngine with 1000 indexed skills
    """
    # Create skill manager with cached skills
    skill_manager = SkillManager()
    skill_manager._skill_cache = {skill.id: skill for skill in benchmark_skills_1000}
    skill_manager._skill_paths = {
        skill.id: skill.file_path for skill in benchmark_skills_1000
    }

    # Create and index engine
    engine = IndexingEngine(
        vector_backend="chromadb",
        graph_backend="networkx",
        skill_manager=skill_manager,
        storage_path=benchmark_storage_path / "chromadb_1000",
    )

    # Index all skills
    for skill in benchmark_skills_1000:
        engine.index_skill(skill)

    return engine


@pytest.fixture
def metadata_store_100(benchmark_storage_path: Path) -> MetadataStore:
    """Metadata store with 100 repositories for database benchmarks.

    Args:
        benchmark_storage_path: Temporary storage path

    Returns:
        MetadataStore with 100 indexed repositories
    """
    store = MetadataStore(db_path=benchmark_storage_path / "metadata_100.db")

    # Insert 100 repositories
    for i in range(100):
        repo = Repository(
            id=f"benchmark/repo-{i:05d}",
            url=f"https://github.com/benchmark/repo-{i:05d}.git",
            local_path=benchmark_storage_path / "repos" / f"repo-{i:05d}",
            priority=50 + (i % 50),
            last_updated=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            skill_count=10 + (i % 20),
            license="MIT",
        )
        store.add_repository(repo)

    return store


@pytest.fixture
def metadata_store_1000(benchmark_storage_path: Path) -> MetadataStore:
    """Metadata store with 1000 repositories for database benchmarks.

    Args:
        benchmark_storage_path: Temporary storage path

    Returns:
        MetadataStore with 1000 indexed repositories
    """
    store = MetadataStore(db_path=benchmark_storage_path / "metadata_1000.db")

    # Batch insert for better performance
    for i in range(1000):
        repo = Repository(
            id=f"benchmark/repo-{i:05d}",
            url=f"https://github.com/benchmark/repo-{i:05d}.git",
            local_path=benchmark_storage_path / "repos" / f"repo-{i:05d}",
            priority=50 + (i % 50),
            last_updated=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            skill_count=10 + (i % 20),
            license="MIT",
        )
        store.add_repository(repo)

    return store
