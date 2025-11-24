"""Pytest configuration and fixtures for E2E tests.

This module provides E2E-specific fixtures that use real repositories,
actual file operations, and complete service configurations for testing
production-like scenarios.
"""

import json
from collections.abc import AsyncGenerator, Generator
from datetime import UTC
from pathlib import Path

import git
import pytest
from click.testing import CliRunner

from mcp_skills.mcp.server import configure_services
from mcp_skills.services.indexing import IndexingEngine
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager


@pytest.fixture(scope="function")
def e2e_base_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create E2E base directory with proper structure.

    This fixture creates a temporary base directory that mimics
    the real ~/.mcp-skills structure for E2E testing.

    Args:
        tmp_path: Pytest temporary path fixture

    Yields:
        Path to E2E base directory
    """
    base_dir = tmp_path / "mcp-skills-e2e"
    base_dir.mkdir(parents=True, exist_ok=True)

    # Create expected subdirectories
    (base_dir / "repos").mkdir(exist_ok=True)
    (base_dir / "storage").mkdir(exist_ok=True)
    (base_dir / "chromadb").mkdir(exist_ok=True)

    yield base_dir

    # Cleanup is handled by tmp_path


@pytest.fixture(scope="function")
def e2e_repos_dir(e2e_base_dir: Path) -> Path:
    """Return E2E repos directory."""
    return e2e_base_dir / "repos"


@pytest.fixture(scope="function")
def e2e_storage_dir(e2e_base_dir: Path) -> Path:
    """Return E2E storage directory."""
    return e2e_base_dir / "storage"


@pytest.fixture(scope="function")
def cli_runner() -> CliRunner:
    """Create Click CLI runner for testing CLI commands.

    Returns:
        CliRunner instance for invoking CLI commands
    """
    return CliRunner()


@pytest.fixture(scope="function")
def real_skill_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a realistic skill repository with git history.

    This creates a complete git repository with:
    - Multiple skills across categories
    - README and documentation
    - Git history with commits
    - Realistic SKILL.md files

    Args:
        tmp_path: Pytest temporary path fixture

    Yields:
        Path to the created git repository
    """
    repo_dir = tmp_path / "test-skills-repo"
    repo_dir.mkdir()

    # Initialize git repo
    repo = git.Repo.init(repo_dir)

    # Configure git (required for commits)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create README
    readme = repo_dir / "README.md"
    readme.write_text(
        """# Test Skills Repository

This is a test skills repository for E2E testing.

## Skills Included

- pytest-testing: Python testing with pytest
- flask-web: Flask web development
- python-debugging: Python debugging tools
- typescript-testing: TypeScript testing with Jest
- docker-deployment: Docker deployment skills
"""
    )

    # Create pytest testing skill
    pytest_skill_dir = repo_dir / "testing" / "pytest"
    pytest_skill_dir.mkdir(parents=True)
    (pytest_skill_dir / "SKILL.md").write_text(
        """---
name: pytest-testing
description: Professional Python testing with pytest framework
category: testing
tags:
  - python
  - pytest
  - testing
  - tdd
dependencies: []
version: "2.0.0"
author: Test Team
---

# Pytest Testing Skill

Use pytest to write and run professional Python tests with fixtures, parametrization, and coverage.

## Key Features

- Fixture-based test setup
- Parametrized testing
- Coverage reporting
- Plugin ecosystem

## Usage

Run pytest with coverage:
```bash
pytest --cov=src tests/
```

## Examples

### Basic Test
```python
def test_addition():
    assert 1 + 1 == 2
```

### Fixture Usage
```python
import pytest

@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### Parametrized Test
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 3),
    (3, 4),
])
def test_increment(input, expected):
    assert input + 1 == expected
```
"""
    )

    # Create Flask web skill
    flask_skill_dir = repo_dir / "web" / "flask"
    flask_skill_dir.mkdir(parents=True)
    (flask_skill_dir / "SKILL.md").write_text(
        """---
name: flask-web
description: Build web applications with Flask framework
category: architecture
tags:
  - python
  - flask
  - web
  - rest-api
dependencies: []
version: "1.5.0"
author: Test Team
---

# Flask Web Development Skill

Build production-ready Flask web applications following best practices.

## Key Features

- RESTful API design
- Blueprint architecture
- Database integration
- Security best practices

## Usage

Create Flask app:
```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World!'
```

## Examples

### RESTful API
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    return jsonify({"id": user_id, "name": "Test User"})
```
"""
    )

    # Create Python debugging skill
    debug_skill_dir = repo_dir / "debugging" / "python"
    debug_skill_dir.mkdir(parents=True)
    (debug_skill_dir / "SKILL.md").write_text(
        """---
name: python-debugging
description: Debug Python applications effectively with pdb and logging
category: debugging
tags:
  - python
  - debugging
  - pdb
  - logging
dependencies:
  - test-skills-repo/testing/pytest
version: "1.2.0"
author: Test Team
---

# Python Debugging Skill

Master Python debugging with pdb, logging, and modern tools.

## Key Features

- Interactive debugging with pdb
- Logging best practices
- Performance profiling
- Error tracking

## Usage

Insert breakpoint:
```python
import pdb; pdb.set_trace()
```

Or use Python 3.7+ built-in:
```python
breakpoint()
```

## Examples

### Debug with pdb
```python
def complex_function(data):
    breakpoint()  # Execution stops here
    result = process_data(data)
    return result
```

### Logging
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process():
    logger.debug("Starting process")
    logger.info("Process completed")
```
"""
    )

    # Create TypeScript testing skill
    ts_skill_dir = repo_dir / "testing" / "typescript"
    ts_skill_dir.mkdir(parents=True)
    (ts_skill_dir / "SKILL.md").write_text(
        """---
name: typescript-testing
description: TypeScript testing with Jest and Testing Library
category: testing
tags:
  - typescript
  - jest
  - testing
  - react
dependencies: []
version: "1.0.0"
author: Test Team
---

# TypeScript Testing Skill

Write comprehensive TypeScript tests using Jest and React Testing Library.

## Key Features

- Type-safe testing
- Component testing
- Snapshot testing
- Mock and spy utilities

## Usage

Run Jest:
```bash
npm test
```

## Examples

### Basic TypeScript Test
```typescript
describe('Calculator', () => {
  it('adds two numbers', () => {
    expect(add(1, 2)).toBe(3);
  });
});
```
"""
    )

    # Create Docker deployment skill
    docker_skill_dir = repo_dir / "deployment" / "docker"
    docker_skill_dir.mkdir(parents=True)
    (docker_skill_dir / "SKILL.md").write_text(
        """---
name: docker-deployment
description: Deploy applications using Docker containers
category: deployment
tags:
  - docker
  - deployment
  - containers
  - devops
dependencies: []
version: "2.1.0"
author: Test Team
---

# Docker Deployment Skill

Deploy applications reliably using Docker containers and compose.

## Key Features

- Multi-stage builds
- Docker Compose orchestration
- Health checks
- Volume management

## Usage

Build and run:
```bash
docker build -t myapp .
docker run -p 8000:8000 myapp
```

## Examples

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```
"""
    )

    # Commit all files
    repo.index.add(["*"])
    repo.index.commit("Initial commit with test skills")

    # Create a second commit for realistic history
    (readme).write_text((readme).read_text() + "\n\n## License\n\nMIT\n")
    repo.index.add(["README.md"])
    repo.index.commit("Add license section to README")

    yield repo_dir

    # Cleanup is handled by tmp_path


@pytest.fixture(scope="function")
def e2e_configured_services(
    e2e_base_dir: Path,
    e2e_repos_dir: Path,
    e2e_storage_dir: Path,
) -> tuple[RepositoryManager, SkillManager, IndexingEngine]:
    """Create fully configured services for E2E testing.

    This fixture provides production-like service instances configured
    with the E2E base directory.

    Args:
        e2e_base_dir: E2E base directory fixture
        e2e_repos_dir: E2E repos directory fixture
        e2e_storage_dir: E2E storage directory fixture

    Returns:
        Tuple of (repository_manager, skill_manager, indexing_engine)
    """
    repo_manager = RepositoryManager(base_dir=e2e_repos_dir)
    skill_manager = SkillManager(repos_dir=e2e_repos_dir)
    indexing_engine = IndexingEngine(
        skill_manager=skill_manager,
        storage_path=e2e_storage_dir,
    )

    return repo_manager, skill_manager, indexing_engine


@pytest.fixture(scope="function")
def e2e_services_with_repo(
    e2e_configured_services: tuple[RepositoryManager, SkillManager, IndexingEngine],
    real_skill_repo: Path,
) -> tuple[RepositoryManager, SkillManager, IndexingEngine]:
    """Configure services with a real skill repository.

    This fixture sets up services and adds a real skill repository,
    providing a complete E2E testing environment.

    Args:
        e2e_configured_services: Configured services fixture
        real_skill_repo: Real skill repository fixture

    Returns:
        Tuple of configured services with repository added
    """
    repo_manager, skill_manager, indexing_engine = e2e_configured_services

    # Copy real repo to repos directory
    import shutil
    from datetime import datetime

    from mcp_skills.models.repository import Repository

    repo_id = "test-skills-repo"
    dest_dir = repo_manager.base_dir / repo_id
    shutil.copytree(real_skill_repo, dest_dir)

    # Create metadata entry
    repository = Repository(
        id=repo_id,
        url="https://github.com/test/skills.git",
        local_path=dest_dir,
        priority=100,
        last_updated=datetime.now(UTC),
        skill_count=5,
        license="MIT",
    )
    repo_manager.metadata_store.add_repository(repository)

    # Build indices for immediate use
    indexing_engine.reindex_all(force=True)

    return repo_manager, skill_manager, indexing_engine


@pytest.fixture(scope="function")
async def mcp_server_configured(
    e2e_base_dir: Path,
    e2e_storage_dir: Path,
) -> AsyncGenerator[None, None]:
    """Configure MCP server for E2E testing.

    This fixture configures the global MCP server services
    for testing MCP tools via direct function calls.

    Args:
        e2e_base_dir: E2E base directory fixture
        e2e_storage_dir: E2E storage directory fixture

    Yields:
        None (services are configured globally)
    """
    # Configure MCP server services
    configure_services(
        base_dir=e2e_base_dir,
        storage_path=e2e_storage_dir,
    )

    yield

    # Services are global and will be cleaned up with temp directories


@pytest.fixture(scope="function")
def sample_python_project_e2e(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a comprehensive Python project for E2E testing.

    This creates a more realistic Python project with:
    - pyproject.toml with dependencies
    - Multiple source files
    - Test directory with actual tests
    - Configuration files (pytest.ini, .gitignore)
    - README

    Args:
        tmp_path: Pytest temporary path fixture

    Yields:
        Path to sample Python project
    """
    project_dir = tmp_path / "sample_python_project"
    project_dir.mkdir()

    # Create pyproject.toml
    (project_dir / "pyproject.toml").write_text(
        """[project]
name = "sample-app"
version = "1.0.0"
description = "Sample Python application for testing"
dependencies = [
    "flask>=3.0.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing"

[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
"""
    )

    # Create src directory with modules
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")

    (src_dir / "app.py").write_text(
        """\"\"\"Main Flask application.\"\"\"

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"message": "Hello World"})


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True)
"""
    )

    (src_dir / "utils.py").write_text(
        """\"\"\"Utility functions.\"\"\"


def process_data(data: dict) -> dict:
    \"\"\"Process input data.\"\"\"
    return {**data, "processed": True}


def validate_input(value: str) -> bool:
    \"\"\"Validate input string.\"\"\"
    return len(value) > 0 and value.strip() == value
"""
    )

    # Create tests directory
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")

    (tests_dir / "test_app.py").write_text(
        """\"\"\"Tests for Flask application.\"\"\"

import pytest
from src.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json["message"] == "Hello World"


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"
"""
    )

    (tests_dir / "test_utils.py").write_text(
        """\"\"\"Tests for utility functions.\"\"\"

from src.utils import process_data, validate_input


def test_process_data():
    result = process_data({"key": "value"})
    assert result["key"] == "value"
    assert result["processed"] is True


def test_validate_input_valid():
    assert validate_input("hello") is True


def test_validate_input_empty():
    assert validate_input("") is False


def test_validate_input_whitespace():
    assert validate_input("  hello  ") is False
"""
    )

    # Create pytest.ini
    (project_dir / "pytest.ini").write_text(
        """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
"""
    )

    # Create README
    (project_dir / "README.md").write_text(
        """# Sample Python Application

A sample Flask application for testing mcp-skills.

## Installation

```bash
pip install -e ".[dev]"
```

## Testing

```bash
pytest
```

## Running

```bash
python src/app.py
```
"""
    )

    # Create .gitignore
    (project_dir / ".gitignore").write_text(
        """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
"""
    )

    yield project_dir


@pytest.fixture(scope="function")
def sample_typescript_project_e2e(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a comprehensive TypeScript project for E2E testing.

    Args:
        tmp_path: Pytest temporary path fixture

    Yields:
        Path to sample TypeScript project
    """
    project_dir = tmp_path / "sample_typescript_project"
    project_dir.mkdir()

    # Create package.json
    (project_dir / "package.json").write_text(
        json.dumps(
            {
                "name": "sample-typescript-app",
                "version": "1.0.0",
                "description": "Sample TypeScript application",
                "scripts": {
                    "build": "tsc",
                    "test": "jest",
                    "lint": "eslint src/**/*.ts",
                },
                "devDependencies": {
                    "typescript": "^5.2.0",
                    "jest": "^29.7.0",
                    "@types/jest": "^29.5.0",
                    "@types/node": "^20.8.0",
                    "ts-jest": "^29.1.0",
                    "eslint": "^8.51.0",
                },
            },
            indent=2,
        )
    )

    # Create tsconfig.json
    (project_dir / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "commonjs",
                    "lib": ["ES2020"],
                    "outDir": "./dist",
                    "rootDir": "./src",
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True,
                },
                "include": ["src/**/*"],
                "exclude": ["node_modules", "dist", "**/*.test.ts"],
            },
            indent=2,
        )
    )

    # Create jest.config.js
    (project_dir / "jest.config.js").write_text(
        """module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  collectCoverageFrom: ['src/**/*.ts', '!src/**/*.test.ts'],
};
"""
    )

    # Create src directory
    src_dir = project_dir / "src"
    src_dir.mkdir()

    (src_dir / "index.ts").write_text(
        """export function greet(name: string): string {
  return `Hello, ${name}!`;
}

export function add(a: number, b: number): number {
  return a + b;
}
"""
    )

    (src_dir / "index.test.ts").write_text(
        """import { greet, add } from './index';

describe('greet', () => {
  it('should greet with name', () => {
    expect(greet('World')).toBe('Hello, World!');
  });
});

describe('add', () => {
  it('should add two numbers', () => {
    expect(add(1, 2)).toBe(3);
  });
});
"""
    )

    # Create README
    (project_dir / "README.md").write_text(
        """# Sample TypeScript Application

A sample TypeScript application for testing mcp-skills.

## Installation

```bash
npm install
```

## Build

```bash
npm run build
```

## Test

```bash
npm test
```
"""
    )

    yield project_dir
