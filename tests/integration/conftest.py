"""Pytest configuration and fixtures for integration tests."""

import json
from collections.abc import Generator
from pathlib import Path

import git
import pytest

from mcp_skills.services.indexing import IndexingEngine
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager
from mcp_skills.services.toolchain_detector import ToolchainDetector


@pytest.fixture
def temp_repos_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create temporary directory for test repositories.

    Args:
        tmp_path: Pytest temporary path fixture

    Yields:
        Path to temporary repos directory
    """
    repos_dir = tmp_path / "repos"
    repos_dir.mkdir()
    yield repos_dir


@pytest.fixture
def temp_storage_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create temporary directory for ChromaDB storage.

    Args:
        tmp_path: Pytest temporary path fixture

    Yields:
        Path to temporary storage directory
    """
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    yield storage_dir


@pytest.fixture
def sample_skill_content() -> dict[str, str]:
    """Return sample SKILL.md content for different skill types.

    Returns:
        Dictionary mapping skill type to SKILL.md content
    """
    return {
        "pytest": """---
name: pytest-testing
description: Run tests with pytest framework
category: testing
tags:
  - python
  - pytest
  - testing
dependencies: []
version: "1.0.0"
author: Test Author
---

# Pytest Testing Skill

Use pytest to run Python tests with proper fixtures and assertions.

## Usage

Run pytest with:
```bash
pytest tests/
```

## Examples

```python
def test_example():
    assert 1 + 1 == 2
```
""",
        "flask": """---
name: flask-development
description: Build web applications with Flask
category: architecture
tags:
  - python
  - flask
  - web
dependencies: []
version: "1.0.0"
author: Test Author
---

# Flask Development Skill

Build Flask web applications following best practices.

## Usage

Create Flask app:
```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'
```

## Examples

Run development server:
```bash
flask run --debug
```
""",
        "debugging": """---
name: python-debugging
description: Debug Python applications effectively
category: debugging
tags:
  - python
  - debugging
  - pdb
dependencies:
  - sample-repo/testing/pytest
version: "1.0.0"
author: Test Author
---

# Python Debugging Skill

Use pdb and debugging tools to troubleshoot Python code.

## Usage

Insert breakpoint:
```python
import pdb; pdb.set_trace()
```

## Examples

Debug with breakpoint():
```python
def buggy_function():
    breakpoint()  # Python 3.7+
    return result
```
""",
    }


@pytest.fixture
def sample_skill_repo(
    tmp_path: Path, sample_skill_content: dict[str, str]
) -> Generator[Path, None, None]:
    """Create a sample skill repository with multiple skills.

    This creates a git repository with realistic skill structure:
    - sample-repo/testing/pytest/SKILL.md
    - sample-repo/web/flask/SKILL.md
    - sample-repo/debugging/python/SKILL.md

    Args:
        tmp_path: Pytest temporary path fixture
        sample_skill_content: Sample SKILL.md content fixture

    Yields:
        Path to the created git repository
    """
    # Create repo directory
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()

    # Initialize git repo
    repo = git.Repo.init(repo_dir)

    # Create skill files
    skills = {
        "testing/pytest": sample_skill_content["pytest"],
        "web/flask": sample_skill_content["flask"],
        "debugging/python": sample_skill_content["debugging"],
    }

    for skill_path, content in skills.items():
        skill_dir = repo_dir / skill_path
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content)

    # Create README
    readme = repo_dir / "README.md"
    readme.write_text(
        "# Test Skills Repository\n\nTest skills for integration testing."
    )

    # Commit files
    repo.index.add(["*"])
    repo.index.commit("Initial commit with test skills")

    yield repo_dir

    # Cleanup is handled by tmp_path


@pytest.fixture
def populated_repos_dir(
    temp_repos_dir: Path, sample_skill_content: dict[str, str]
) -> Generator[Path, None, None]:
    """Create a temporary repos directory with pre-populated skills.

    This fixture creates skills directly in the repos directory structure
    without needing git operations, making it faster for testing.

    Args:
        temp_repos_dir: Temporary repos directory fixture
        sample_skill_content: Sample SKILL.md content fixture

    Yields:
        Path to populated repos directory
    """
    # Create sample-repo structure directly in repos_dir
    repo_dir = temp_repos_dir / "sample-repo"
    repo_dir.mkdir()

    # Create skill files
    skills = {
        "testing/pytest": sample_skill_content["pytest"],
        "web/flask": sample_skill_content["flask"],
        "debugging/python": sample_skill_content["debugging"],
    }

    for skill_path, content in skills.items():
        skill_dir = repo_dir / skill_path
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content)

    yield temp_repos_dir


@pytest.fixture
def configured_repository_manager(
    temp_repos_dir: Path,
) -> Generator[RepositoryManager, None, None]:
    """Create and configure a RepositoryManager for testing.

    Args:
        temp_repos_dir: Temporary repos directory fixture

    Yields:
        Configured RepositoryManager instance
    """
    # Create base directory for metadata
    manager = RepositoryManager(base_dir=temp_repos_dir)

    yield manager

    # Cleanup is handled by temp_repos_dir


@pytest.fixture
def configured_skill_manager(
    temp_repos_dir: Path,
) -> Generator[SkillManager, None, None]:
    """Create and configure a SkillManager for testing.

    Args:
        temp_repos_dir: Temporary repos directory fixture

    Yields:
        Configured SkillManager instance
    """
    manager = SkillManager(repos_dir=temp_repos_dir)
    yield manager


@pytest.fixture
def configured_indexing_engine(
    configured_skill_manager: SkillManager,
    temp_storage_dir: Path,
) -> Generator[IndexingEngine, None, None]:
    """Create and configure an IndexingEngine for testing.

    Args:
        configured_skill_manager: Configured SkillManager fixture
        temp_storage_dir: Temporary storage directory fixture

    Yields:
        Configured IndexingEngine instance
    """
    engine = IndexingEngine(
        skill_manager=configured_skill_manager,
        storage_path=temp_storage_dir,
    )
    yield engine


@pytest.fixture
def configured_services(
    configured_repository_manager: RepositoryManager,
    configured_skill_manager: SkillManager,
    configured_indexing_engine: IndexingEngine,
) -> tuple[RepositoryManager, SkillManager, IndexingEngine]:
    """Provide fully configured service instances.

    Args:
        configured_repository_manager: Repository manager fixture
        configured_skill_manager: Skill manager fixture
        configured_indexing_engine: Indexing engine fixture

    Returns:
        Tuple of (repository_manager, skill_manager, indexing_engine)
    """
    return (
        configured_repository_manager,
        configured_skill_manager,
        configured_indexing_engine,
    )


@pytest.fixture
def populated_services(
    populated_repos_dir: Path,
    temp_storage_dir: Path,
) -> tuple[RepositoryManager, SkillManager, IndexingEngine]:
    """Provide fully configured services with pre-populated skills.

    This fixture is optimized for tests that need skills but don't need
    to test repository operations.

    Args:
        populated_repos_dir: Repos directory with pre-populated skills
        temp_storage_dir: Temporary storage directory

    Returns:
        Tuple of (repository_manager, skill_manager, indexing_engine)
    """
    repo_manager = RepositoryManager(base_dir=populated_repos_dir)
    skill_manager = SkillManager(repos_dir=populated_repos_dir)
    indexing_engine = IndexingEngine(
        skill_manager=skill_manager,
        storage_path=temp_storage_dir,
    )
    return repo_manager, skill_manager, indexing_engine


@pytest.fixture
def sample_python_project(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a sample Python project for toolchain detection.

    Args:
        tmp_path: Pytest temporary path fixture

    Yields:
        Path to sample Python project
    """
    project_dir = tmp_path / "python_project"
    project_dir.mkdir()

    # Create Python project markers
    (project_dir / "pyproject.toml").write_text(
        """[project]
name = "test-project"
version = "1.0.0"
dependencies = ["flask>=3.0.0", "pytest>=7.0"]
"""
    )

    (project_dir / "requirements.txt").write_text("flask>=3.0.0\npytest>=7.0\n")

    (project_dir / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n")

    # Create source files
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text(
        """from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World!'
"""
    )

    # Create test directory
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text(
        """def test_example():
    assert 1 + 1 == 2
"""
    )

    yield project_dir


@pytest.fixture
def sample_typescript_project(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a sample TypeScript project for toolchain detection.

    Args:
        tmp_path: Pytest temporary path fixture

    Yields:
        Path to sample TypeScript project
    """
    project_dir = tmp_path / "typescript_project"
    project_dir.mkdir()

    # Create TypeScript project markers
    (project_dir / "package.json").write_text(
        json.dumps(
            {
                "name": "test-project",
                "version": "1.0.0",
                "devDependencies": {
                    "typescript": "^5.0.0",
                    "jest": "^29.0.0",
                    "@types/node": "^20.0.0",
                },
            }
        )
    )

    (project_dir / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "commonjs",
                    "strict": True,
                }
            }
        )
    )

    # Create source files
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "index.ts").write_text(
        """export function greet(name: string): string {
    return `Hello, ${name}!`;
}
"""
    )

    yield project_dir


@pytest.fixture
def old_json_metadata(tmp_path: Path) -> Generator[Path, None, None]:
    """Create old-style JSON metadata file for migration testing.

    Args:
        tmp_path: Pytest temporary path fixture

    Yields:
        Path to JSON metadata file
    """
    json_file = tmp_path / "repos.json"

    metadata = {
        "repositories": [
            {
                "id": "test/repo1",
                "url": "https://github.com/test/repo1.git",
                "local_path": str(tmp_path / "repos" / "test" / "repo1"),
                "priority": 100,
                "last_updated": "2024-01-01T00:00:00Z",
                "skill_count": 5,
                "license": "MIT",
            },
            {
                "id": "test/repo2",
                "url": "https://github.com/test/repo2.git",
                "local_path": str(tmp_path / "repos" / "test" / "repo2"),
                "priority": 90,
                "last_updated": "2024-01-01T00:00:00Z",
                "skill_count": 3,
                "license": "Apache-2.0",
            },
        ]
    }

    json_file.write_text(json.dumps(metadata, indent=2))
    yield json_file


@pytest.fixture
def configured_toolchain_detector() -> ToolchainDetector:
    """Create a configured ToolchainDetector instance.

    Returns:
        ToolchainDetector instance
    """
    return ToolchainDetector()
