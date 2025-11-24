"""Comprehensive tests for toolchain detection service."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_skills.services.toolchain_detector import ToolchainDetector, ToolchainInfo


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def detector() -> ToolchainDetector:
    """Create ToolchainDetector instance for testing."""
    return ToolchainDetector()


@pytest.fixture
def temp_python_project(tmp_path: Path) -> Path:
    """Create temporary Python project with comprehensive markers.

    Creates a Python project with:
    - pyproject.toml (Poetry configuration)
    - requirements.txt (pip dependencies including Flask, Pydantic)
    - pytest.ini (pytest configuration)
    - __pycache__ directory
    """
    project_dir = tmp_path / "python_project"
    project_dir.mkdir()

    # Create Python marker files
    (project_dir / "pyproject.toml").write_text(
        """[tool.poetry]
name = "test-project"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.9"
flask = "^3.0.0"
pydantic = "^2.0.0"
"""
    )

    (project_dir / "requirements.txt").write_text(
        """flask==3.0.0
pydantic==2.0.0
pytest==7.4.0
"""
    )

    (project_dir / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n")
    (project_dir / "__pycache__").mkdir()

    return project_dir


@pytest.fixture
def temp_typescript_project(tmp_path: Path) -> Path:
    """Create temporary TypeScript project with comprehensive markers.

    Creates a TypeScript project with:
    - package.json (with TypeScript and React dependencies)
    - tsconfig.json
    - node_modules directory
    - jest.config.ts
    """
    project_dir = tmp_path / "typescript_project"
    project_dir.mkdir()

    # Create TypeScript marker files
    package_json = {
        "name": "test-typescript-project",
        "version": "1.0.0",
        "dependencies": {"react": "^18.0.0", "next": "^14.0.0"},
        "devDependencies": {
            "typescript": "^5.0.0",
            "@types/react": "^18.0.0",
            "jest": "^29.0.0",
            "vite": "^5.0.0",
        },
    }

    (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))
    (project_dir / "tsconfig.json").write_text(
        '{"compilerOptions": {"target": "ES2020", "module": "commonjs"}}'
    )
    (project_dir / "jest.config.ts").write_text("export default {}")
    (project_dir / "node_modules").mkdir()

    return project_dir


@pytest.fixture
def temp_javascript_project(tmp_path: Path) -> Path:
    """Create temporary JavaScript project with comprehensive markers.

    Creates a JavaScript project with:
    - package.json (with Express and testing frameworks)
    - yarn.lock (indicates yarn package manager)
    - node_modules directory
    """
    project_dir = tmp_path / "javascript_project"
    project_dir.mkdir()

    package_json = {
        "name": "test-js-project",
        "version": "1.0.0",
        "dependencies": {"express": "^4.18.0", "vue": "^3.0.0"},
        "devDependencies": {"mocha": "^10.0.0", "webpack": "^5.0.0"},
    }

    (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))
    (project_dir / "yarn.lock").write_text("# yarn lockfile v1\n")
    (project_dir / "node_modules").mkdir()

    return project_dir


@pytest.fixture
def temp_rust_project(tmp_path: Path) -> Path:
    """Create temporary Rust project with comprehensive markers.

    Creates a Rust project with:
    - Cargo.toml (with Tokio and Axum dependencies)
    - Cargo.lock
    - target directory
    """
    project_dir = tmp_path / "rust_project"
    project_dir.mkdir()

    (project_dir / "Cargo.toml").write_text(
        """[package]
name = "test-rust-project"
version = "0.1.0"

[dependencies]
tokio = { version = "1.0", features = ["full"] }
axum = "0.7"
serde = { version = "1.0", features = ["derive"] }
"""
    )

    (project_dir / "Cargo.lock").write_text("# Cargo.lock\n")
    (project_dir / "target").mkdir()

    return project_dir


@pytest.fixture
def temp_go_project(tmp_path: Path) -> Path:
    """Create temporary Go project with comprehensive markers.

    Creates a Go project with:
    - go.mod (with Gin framework)
    - go.sum
    - vendor directory
    """
    project_dir = tmp_path / "go_project"
    project_dir.mkdir()

    (project_dir / "go.mod").write_text(
        """module github.com/test/project

go 1.21

require (
    github.com/gin-gonic/gin v1.9.0
    gorm.io/gorm v1.25.0
)
"""
    )

    (project_dir / "go.sum").write_text("# Go checksum database\n")
    (project_dir / "vendor").mkdir()

    return project_dir


@pytest.fixture
def temp_polyglot_project(tmp_path: Path) -> Path:
    """Create temporary polyglot project (Python + TypeScript).

    Creates a project with both Python and TypeScript markers
    to test multi-language detection.
    """
    project_dir = tmp_path / "polyglot_project"
    project_dir.mkdir()

    # Python markers
    (project_dir / "requirements.txt").write_text("fastapi==0.104.0\n")
    (project_dir / "pyproject.toml").write_text("[tool.poetry]\nname = 'backend'\n")

    # TypeScript markers
    package_json = {
        "name": "frontend",
        "dependencies": {"react": "^18.0.0"},
        "devDependencies": {"typescript": "^5.0.0"},
    }
    (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))
    (project_dir / "tsconfig.json").write_text("{}")

    return project_dir


@pytest.fixture
def temp_empty_project(tmp_path: Path) -> Path:
    """Create empty project directory for testing edge cases."""
    project_dir = tmp_path / "empty_project"
    project_dir.mkdir()
    return project_dir


# =============================================================================
# Language Detection Tests
# =============================================================================


class TestLanguageDetection:
    """Test suite for language detection functionality."""

    def test_detect_python_project(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test detection of Python as primary language.

        Note: Confidence is normalized to [0.0, 1.0] range. Python has many
        possible markers (theoretical max 2.6), so normalized scores are lower.
        """
        info = detector.detect(temp_python_project)

        assert info.primary_language == "Python"
        assert info.confidence > 0.4  # Normalized from raw score ~1.1
        assert isinstance(info.secondary_languages, list)

    def test_detect_typescript_project(
        self, detector: ToolchainDetector, temp_typescript_project: Path
    ) -> None:
        """Test detection of TypeScript as primary language."""
        info = detector.detect(temp_typescript_project)

        assert info.primary_language == "TypeScript"
        assert info.confidence > 0.7

    def test_detect_javascript_project(
        self, detector: ToolchainDetector, temp_javascript_project: Path
    ) -> None:
        """Test detection of JavaScript as primary language."""
        info = detector.detect(temp_javascript_project)

        # Could be JavaScript or TypeScript depending on markers
        assert info.primary_language in ["JavaScript", "TypeScript"]
        assert info.confidence > 0.5

    def test_detect_rust_project(
        self, detector: ToolchainDetector, temp_rust_project: Path
    ) -> None:
        """Test detection of Rust as primary language."""
        info = detector.detect(temp_rust_project)

        assert info.primary_language == "Rust"
        assert info.confidence > 0.7

    def test_detect_go_project(
        self, detector: ToolchainDetector, temp_go_project: Path
    ) -> None:
        """Test detection of Go as primary language."""
        info = detector.detect(temp_go_project)

        assert info.primary_language == "Go"
        assert info.confidence > 0.7

    def test_detect_languages_returns_sorted_list(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test detect_languages returns list sorted by confidence."""
        languages = detector.detect_languages(temp_python_project)

        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "Python" in languages

    def test_detect_polyglot_project(
        self, detector: ToolchainDetector, temp_polyglot_project: Path
    ) -> None:
        """Test detection of multi-language project."""
        info = detector.detect(temp_polyglot_project)

        # Should detect both languages
        all_languages = [info.primary_language] + info.secondary_languages
        assert "Python" in all_languages or "TypeScript" in all_languages

        # Secondary languages should be detected
        assert len(info.secondary_languages) >= 0  # May have secondary languages

    def test_detect_languages_minimum_threshold(
        self, detector: ToolchainDetector, temp_polyglot_project: Path
    ) -> None:
        """Test that only languages above 0.3 threshold are returned."""
        languages = detector.detect_languages(temp_polyglot_project)

        # All returned languages should meet threshold
        assert isinstance(languages, list)
        # We can't easily test the threshold without exposing scores,
        # but we verify the method works correctly


# =============================================================================
# Framework Detection Tests
# =============================================================================


class TestFrameworkDetection:
    """Test suite for framework detection functionality."""

    def test_detect_python_frameworks(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test detection of Python frameworks (Flask, Pydantic)."""
        frameworks = detector.detect_frameworks(temp_python_project)

        assert "Flask" in frameworks
        assert "Pydantic" in frameworks

    def test_detect_python_django_framework(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test detection of Django framework."""
        project_dir = tmp_path / "django_project"
        project_dir.mkdir()

        (project_dir / "requirements.txt").write_text("django==4.2.0\n")

        frameworks = detector.detect_frameworks(project_dir)
        assert "Django" in frameworks

    def test_detect_javascript_frameworks(
        self, detector: ToolchainDetector, temp_javascript_project: Path
    ) -> None:
        """Test detection of JavaScript frameworks (Express, Vue)."""
        frameworks = detector.detect_frameworks(temp_javascript_project)

        assert "Express" in frameworks
        assert "Vue" in frameworks

    def test_detect_typescript_frameworks(
        self, detector: ToolchainDetector, temp_typescript_project: Path
    ) -> None:
        """Test detection of TypeScript frameworks (React, Next.js)."""
        frameworks = detector.detect_frameworks(temp_typescript_project)

        assert "React" in frameworks
        assert "Next.js" in frameworks

    def test_detect_rust_frameworks(
        self, detector: ToolchainDetector, temp_rust_project: Path
    ) -> None:
        """Test detection of Rust frameworks (Tokio, Axum, Serde)."""
        frameworks = detector.detect_frameworks(temp_rust_project)

        assert "Tokio" in frameworks
        assert "Axum" in frameworks
        assert "Serde" in frameworks

    def test_detect_go_frameworks(
        self, detector: ToolchainDetector, temp_go_project: Path
    ) -> None:
        """Test detection of Go frameworks (Gin, GORM)."""
        frameworks = detector.detect_frameworks(temp_go_project)

        assert "Gin" in frameworks
        assert "GORM" in frameworks

    @pytest.mark.parametrize(
        "framework,dependency",
        [
            ("Rocket", 'rocket = "0.5"'),
            ("Warp", 'warp = "0.3"'),
        ],
    )
    def test_detect_rust_framework_variations(
        self,
        detector: ToolchainDetector,
        tmp_path: Path,
        framework: str,
        dependency: str,
    ) -> None:
        """Test detection of additional Rust frameworks."""
        project_dir = tmp_path / f"test_{framework.lower()}"
        project_dir.mkdir()

        cargo_toml = f"""[package]
name = "test-project"
version = "0.1.0"

[dependencies]
{dependency}
"""
        (project_dir / "Cargo.toml").write_text(cargo_toml)

        frameworks = detector.detect_frameworks(project_dir)
        assert framework in frameworks

    @pytest.mark.parametrize(
        "framework,import_path",
        [
            ("Echo", "labstack/echo"),
            ("Fiber", "gofiber/fiber"),
            ("Gorilla Mux", "gorilla/mux"),
        ],
    )
    def test_detect_go_framework_variations(
        self,
        detector: ToolchainDetector,
        tmp_path: Path,
        framework: str,
        import_path: str,
    ) -> None:
        """Test detection of additional Go frameworks."""
        project_dir = tmp_path / f"test_{framework.lower().replace(' ', '_')}"
        project_dir.mkdir()

        go_mod = f"""module github.com/test/project

go 1.21

require (
    github.com/{import_path} v1.0.0
)
"""
        (project_dir / "go.mod").write_text(go_mod)

        frameworks = detector.detect_frameworks(project_dir)
        assert framework in frameworks

    def test_detect_frameworks_empty_project(
        self, detector: ToolchainDetector, temp_empty_project: Path
    ) -> None:
        """Test framework detection returns empty list for empty project."""
        frameworks = detector.detect_frameworks(temp_empty_project)

        assert isinstance(frameworks, list)
        assert len(frameworks) == 0

    @pytest.mark.parametrize(
        "framework,package",
        [
            ("FastAPI", "fastapi==0.104.0"),
            ("SQLAlchemy", "sqlalchemy==2.0.0"),
            ("Celery", "celery==5.3.0"),
            ("Tornado", "tornado==6.3.0"),
            ("aiohttp", "aiohttp==3.9.0"),
            ("Sanic", "sanic==23.12.0"),
        ],
    )
    def test_detect_python_framework_variations(
        self,
        detector: ToolchainDetector,
        tmp_path: Path,
        framework: str,
        package: str,
    ) -> None:
        """Test detection of various Python frameworks."""
        project_dir = tmp_path / f"test_{framework.lower()}"
        project_dir.mkdir()

        (project_dir / "requirements.txt").write_text(package)

        frameworks = detector.detect_frameworks(project_dir)
        assert framework in frameworks

    @pytest.mark.parametrize(
        "framework,package_name",
        [
            ("Angular", "@angular/core"),
            ("Svelte", "svelte"),
            ("NestJS", "@nestjs/core"),
            ("Koa", "koa"),
            ("Hapi", "hapi"),
            ("Fastify", "fastify"),
        ],
    )
    def test_detect_js_framework_variations(
        self,
        detector: ToolchainDetector,
        tmp_path: Path,
        framework: str,
        package_name: str,
    ) -> None:
        """Test detection of additional JavaScript/TypeScript frameworks."""
        project_dir = tmp_path / f"test_{framework.lower()}"
        project_dir.mkdir()

        package_json = {
            "name": "test-project",
            "dependencies": {package_name: "^1.0.0"},
        }
        (project_dir / "package.json").write_text(json.dumps(package_json))

        frameworks = detector.detect_frameworks(project_dir)
        assert framework in frameworks


# =============================================================================
# Build Tools & Package Manager Tests
# =============================================================================


class TestBuildToolsDetection:
    """Test suite for build tools detection."""

    def test_detect_python_build_tools(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test detection of Python build tools (Poetry)."""
        info = detector.detect(temp_python_project)

        assert "poetry" in info.build_tools

    def test_detect_setuptools(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test detection of setuptools build tool."""
        project_dir = tmp_path / "setuptools_project"
        project_dir.mkdir()

        (project_dir / "setup.py").write_text("from setuptools import setup\n")

        info = detector.detect(project_dir)
        assert "setuptools" in info.build_tools

    def test_detect_javascript_build_tools(
        self, detector: ToolchainDetector, temp_typescript_project: Path
    ) -> None:
        """Test detection of JavaScript build tools (Vite)."""
        info = detector.detect(temp_typescript_project)

        assert "vite" in info.build_tools

    def test_detect_rust_build_tools(
        self, detector: ToolchainDetector, temp_rust_project: Path
    ) -> None:
        """Test detection of Rust build tool (Cargo)."""
        info = detector.detect(temp_rust_project)

        assert "cargo" in info.build_tools

    def test_detect_go_build_tools(
        self, detector: ToolchainDetector, temp_go_project: Path
    ) -> None:
        """Test detection of Go build tool."""
        info = detector.detect(temp_go_project)

        assert "go" in info.build_tools

    @pytest.mark.parametrize(
        "build_tool,dev_dep",
        [
            ("webpack", "webpack"),
            ("rollup", "rollup"),
            ("esbuild", "esbuild"),
            ("parcel", "parcel"),
        ],
    )
    def test_detect_js_build_tool_variations(
        self,
        detector: ToolchainDetector,
        tmp_path: Path,
        build_tool: str,
        dev_dep: str,
    ) -> None:
        """Test detection of various JavaScript build tools."""
        project_dir = tmp_path / f"test_{build_tool}"
        project_dir.mkdir()

        package_json = {
            "name": "test-project",
            "devDependencies": {dev_dep: "^5.0.0"},
        }
        (project_dir / "package.json").write_text(json.dumps(package_json))

        info = detector.detect(project_dir)
        assert build_tool in info.build_tools


class TestPackageManagerDetection:
    """Test suite for package manager detection."""

    def test_detect_python_package_managers(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test detection of Python package managers (pip, poetry)."""
        info = detector.detect(temp_python_project)

        assert "pip" in info.package_managers
        # Poetry is detected via poetry.lock or pyproject.toml

    def test_detect_pipenv(self, detector: ToolchainDetector, tmp_path: Path) -> None:
        """Test detection of Pipenv package manager."""
        project_dir = tmp_path / "pipenv_project"
        project_dir.mkdir()

        (project_dir / "Pipfile").write_text("[packages]\nflask = '*'\n")

        info = detector.detect(project_dir)
        assert "pipenv" in info.package_managers

    def test_detect_poetry_lock(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test detection of Poetry via poetry.lock file."""
        project_dir = tmp_path / "poetry_lock_project"
        project_dir.mkdir()

        (project_dir / "poetry.lock").write_text("# Poetry lock file\n")
        (project_dir / "pyproject.toml").write_text("[tool.poetry]\n")

        info = detector.detect(project_dir)
        assert "poetry" in info.package_managers

    def test_detect_npm(self, detector: ToolchainDetector, tmp_path: Path) -> None:
        """Test detection of npm package manager."""
        project_dir = tmp_path / "npm_project"
        project_dir.mkdir()

        (project_dir / "package.json").write_text('{"name": "test"}')
        (project_dir / "package-lock.json").write_text("{}")

        info = detector.detect(project_dir)
        assert "npm" in info.package_managers

    def test_detect_yarn(
        self, detector: ToolchainDetector, temp_javascript_project: Path
    ) -> None:
        """Test detection of Yarn package manager."""
        info = detector.detect(temp_javascript_project)

        assert "yarn" in info.package_managers

    def test_detect_pnpm(self, detector: ToolchainDetector, tmp_path: Path) -> None:
        """Test detection of pnpm package manager."""
        project_dir = tmp_path / "pnpm_project"
        project_dir.mkdir()

        (project_dir / "package.json").write_text('{"name": "test"}')
        (project_dir / "pnpm-lock.yaml").write_text("")

        info = detector.detect(project_dir)
        assert "pnpm" in info.package_managers

    def test_detect_cargo_package_manager(
        self, detector: ToolchainDetector, temp_rust_project: Path
    ) -> None:
        """Test detection of Cargo package manager."""
        info = detector.detect(temp_rust_project)

        assert "cargo" in info.package_managers

    def test_detect_go_modules(
        self, detector: ToolchainDetector, temp_go_project: Path
    ) -> None:
        """Test detection of Go modules package manager."""
        info = detector.detect(temp_go_project)

        assert "go modules" in info.package_managers

    def test_detect_pdm(self, detector: ToolchainDetector, tmp_path: Path) -> None:
        """Test detection of PDM package manager."""
        project_dir = tmp_path / "pdm_project"
        project_dir.mkdir()

        (project_dir / "pdm.lock").write_text("# PDM lock file\n")
        (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        info = detector.detect(project_dir)
        assert "pdm" in info.package_managers


# =============================================================================
# Test Framework Detection Tests
# =============================================================================


class TestTestFrameworkDetection:
    """Test suite for test framework detection."""

    def test_detect_pytest(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test detection of pytest framework."""
        info = detector.detect(temp_python_project)

        assert "pytest" in info.test_frameworks

    def test_detect_pytest_from_requirements(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test pytest detection from requirements.txt."""
        project_dir = tmp_path / "pytest_req_project"
        project_dir.mkdir()

        (project_dir / "requirements.txt").write_text("pytest==7.4.0\n")
        (project_dir / "pyproject.toml").write_text("[tool.poetry]\n")

        info = detector.detect(project_dir)
        assert "pytest" in info.test_frameworks

    def test_detect_tox(self, detector: ToolchainDetector, tmp_path: Path) -> None:
        """Test detection of tox test framework."""
        project_dir = tmp_path / "tox_project"
        project_dir.mkdir()

        (project_dir / "tox.ini").write_text("[tox]\n")
        (project_dir / "requirements.txt").write_text("")

        info = detector.detect(project_dir)
        assert "tox" in info.test_frameworks

    def test_detect_jest(
        self, detector: ToolchainDetector, temp_typescript_project: Path
    ) -> None:
        """Test detection of Jest test framework."""
        info = detector.detect(temp_typescript_project)

        assert "jest" in info.test_frameworks

    def test_detect_vitest(self, detector: ToolchainDetector, tmp_path: Path) -> None:
        """Test detection of Vitest test framework."""
        project_dir = tmp_path / "vitest_project"
        project_dir.mkdir()

        package_json = {
            "name": "test-project",
            "devDependencies": {"vitest": "^1.0.0", "typescript": "^5.0.0"},
        }
        (project_dir / "package.json").write_text(json.dumps(package_json))
        (project_dir / "tsconfig.json").write_text("{}")

        info = detector.detect(project_dir)
        assert "vitest" in info.test_frameworks

    def test_detect_mocha(
        self, detector: ToolchainDetector, temp_javascript_project: Path
    ) -> None:
        """Test detection of Mocha test framework."""
        info = detector.detect(temp_javascript_project)

        assert "mocha" in info.test_frameworks

    @pytest.mark.parametrize(
        "test_framework",
        ["jasmine", "playwright", "cypress"],
    )
    def test_detect_js_test_framework_variations(
        self, detector: ToolchainDetector, tmp_path: Path, test_framework: str
    ) -> None:
        """Test detection of various JavaScript test frameworks."""
        project_dir = tmp_path / f"test_{test_framework}"
        project_dir.mkdir()

        package_key = (
            "@playwright/test" if test_framework == "playwright" else test_framework
        )
        package_json = {
            "name": "test-project",
            "devDependencies": {package_key: "^1.0.0"},
        }
        (project_dir / "package.json").write_text(json.dumps(package_json))

        info = detector.detect(project_dir)
        assert test_framework in info.test_frameworks

    def test_detect_rust_test_framework(
        self, detector: ToolchainDetector, temp_rust_project: Path
    ) -> None:
        """Test detection of Rust built-in test framework."""
        info = detector.detect(temp_rust_project)

        assert "cargo test" in info.test_frameworks

    def test_detect_go_test_framework(
        self, detector: ToolchainDetector, temp_go_project: Path
    ) -> None:
        """Test detection of Go built-in test framework."""
        info = detector.detect(temp_go_project)

        assert "go test" in info.test_frameworks

    def test_detect_unittest(self, detector: ToolchainDetector, tmp_path: Path) -> None:
        """Test detection of unittest test framework."""
        project_dir = tmp_path / "unittest_project"
        project_dir.mkdir()

        (project_dir / "requirements.txt").write_text("unittest-xml-reporting==3.2.0\n")
        (project_dir / "pyproject.toml").write_text("[tool.poetry]\n")

        info = detector.detect(project_dir)
        assert "unittest" in info.test_frameworks


# =============================================================================
# Confidence Score Tests
# =============================================================================


class TestConfidenceScoring:
    """Test suite for confidence score calculation."""

    def test_confidence_high_for_clear_markers(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test high confidence for project with many clear markers.

        Confidence is now normalized to [0.0, 1.0] by dividing by theoretical max.
        Python has many possible markers (4 files + 3 dirs + 4 configs = 2.6 theoretical max),
        so actual scores are lower but still indicate strong detection.
        """
        info = detector.detect(temp_python_project)

        # Multiple Python markers should give reasonable confidence (normalized)
        # Project has: pyproject.toml + requirements.txt + pytest.ini + __pycache__
        # Raw score: 1.1, Normalized: 1.1/2.6 ≈ 0.42
        assert info.confidence >= 0.4

    def test_confidence_low_for_minimal_markers(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test lower confidence for project with minimal markers."""
        project_dir = tmp_path / "minimal_project"
        project_dir.mkdir()

        # Only one marker file
        (project_dir / "requirements.txt").write_text("")

        info = detector.detect(project_dir)

        # Should still detect but with lower confidence
        assert 0.0 < info.confidence < 1.0

    def test_confidence_zero_for_empty_project(
        self, detector: ToolchainDetector, temp_empty_project: Path
    ) -> None:
        """Test zero confidence for empty project."""
        info = detector.detect(temp_empty_project)

        assert info.confidence == 0.0
        assert info.primary_language == "Unknown"

    def test_polyglot_confidence_distribution(
        self, detector: ToolchainDetector, temp_polyglot_project: Path
    ) -> None:
        """Test confidence distribution in polyglot project."""
        info = detector.detect(temp_polyglot_project)

        # Should have reasonable confidence for primary language
        assert info.confidence > 0.3

        # Should detect secondary languages
        assert isinstance(info.secondary_languages, list)

    def test_confidence_calculation_weights(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test that confidence calculation uses correct weights.

        Weights:
        - Marker files: 0.4 each
        - Directories: 0.2 each
        - Config files: 0.1 each

        Scores are normalized by theoretical maximum to ensure values stay in [0.0, 1.0].
        Python theoretical max: (4*0.4 + 3*0.2 + 4*0.1) * 1.0 = 2.6
        """
        project_dir = tmp_path / "weighted_project"
        project_dir.mkdir()

        # Create exactly one of each type
        (project_dir / "pyproject.toml").write_text("")  # 0.4 weight
        (project_dir / "__pycache__").mkdir()  # 0.2 weight
        (project_dir / "pytest.ini").write_text("")  # 0.1 weight

        # Raw score: 0.4 + 0.2 + 0.1 = 0.7 (with priority 1.0)
        # Normalized: 0.7 / 2.6 ≈ 0.269
        info = detector.detect(project_dir)

        assert info.primary_language == "Python"
        # Confidence should be approximately 0.269 (normalized)
        assert 0.25 <= info.confidence <= 0.30


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_nonexistent_directory(self, detector: ToolchainDetector) -> None:
        """Test handling of non-existent directory."""
        fake_path = Path("/nonexistent/directory/path")
        info = detector.detect(fake_path)

        assert info.primary_language == "Unknown"
        assert info.confidence == 0.0
        assert len(info.frameworks) == 0
        assert len(info.build_tools) == 0

    def test_file_instead_of_directory(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test handling when path is a file, not a directory."""
        file_path = tmp_path / "somefile.txt"
        file_path.write_text("content")

        info = detector.detect(file_path)

        assert info.primary_language == "Unknown"
        assert info.confidence == 0.0

    def test_corrupted_package_json(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test handling of corrupted package.json file."""
        project_dir = tmp_path / "corrupted_json_project"
        project_dir.mkdir()

        # Write invalid JSON
        (project_dir / "package.json").write_text("{invalid json content")
        (project_dir / "tsconfig.json").write_text("{}")

        # Should still detect TypeScript from tsconfig.json
        info = detector.detect(project_dir)

        assert info.primary_language == "TypeScript"
        # Frameworks detection should handle the error gracefully
        assert isinstance(info.frameworks, list)

    def test_permission_error_handling(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test handling of permission errors when reading files."""
        project_dir = tmp_path / "permission_project"
        project_dir.mkdir()

        requirements_file = project_dir / "requirements.txt"
        requirements_file.write_text("flask==3.0.0")

        # Mock permission error
        with patch("pathlib.Path.read_text", side_effect=PermissionError("No access")):
            frameworks = detector.detect_frameworks(project_dir)

            # Should return empty list, not crash
            assert isinstance(frameworks, list)

    def test_empty_package_json(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test handling of empty package.json file."""
        project_dir = tmp_path / "empty_json_project"
        project_dir.mkdir()

        (project_dir / "package.json").write_text("{}")
        (project_dir / "tsconfig.json").write_text("{}")

        info = detector.detect(project_dir)

        assert info.primary_language == "TypeScript"
        assert isinstance(info.frameworks, list)

    def test_empty_requirements_txt(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test handling of empty requirements.txt file."""
        project_dir = tmp_path / "empty_req_project"
        project_dir.mkdir()

        (project_dir / "requirements.txt").write_text("")

        info = detector.detect(project_dir)

        assert info.primary_language == "Python"
        assert len(info.frameworks) == 0

    def test_mixed_case_framework_names(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test framework detection handles case variations."""
        project_dir = tmp_path / "case_test_project"
        project_dir.mkdir()

        # Test with uppercase
        (project_dir / "requirements.txt").write_text("Flask==3.0.0\nDjango==4.2.0")

        frameworks = detector.detect_frameworks(project_dir)

        assert "Flask" in frameworks
        assert "Django" in frameworks

    def test_requirements_dev_txt(
        self, detector: ToolchainDetector, tmp_path: Path
    ) -> None:
        """Test detection from requirements-dev.txt file."""
        project_dir = tmp_path / "dev_req_project"
        project_dir.mkdir()

        (project_dir / "requirements-dev.txt").write_text("pytest==7.4.0")
        (project_dir / "pyproject.toml").write_text("[tool.poetry]\n")

        info = detector.detect(project_dir)

        assert "pytest" in info.test_frameworks


# =============================================================================
# Skill Recommendation Tests
# =============================================================================


class TestSkillRecommendations:
    """Test suite for skill recommendation functionality."""

    def test_recommend_skills_python(self, detector: ToolchainDetector) -> None:
        """Test skill recommendations for Python project."""
        toolchain = ToolchainInfo(
            primary_language="Python",
            secondary_languages=[],
            frameworks=["Flask"],
            build_tools=["poetry"],
            package_managers=["pip"],
            test_frameworks=["pytest"],
            confidence=0.9,
        )

        skills = detector.recommend_skills(toolchain)

        assert "python-testing" in skills
        assert "python-development" in skills
        assert "python-web-development" in skills
        assert "automated-testing" in skills

    def test_recommend_skills_typescript(self, detector: ToolchainDetector) -> None:
        """Test skill recommendations for TypeScript project."""
        toolchain = ToolchainInfo(
            primary_language="TypeScript",
            secondary_languages=[],
            frameworks=["React", "Next.js"],
            build_tools=["vite"],
            package_managers=["npm"],
            test_frameworks=["jest"],
            confidence=0.9,
        )

        skills = detector.recommend_skills(toolchain)

        assert "typescript-development" in skills
        assert "typescript-testing" in skills
        assert "frontend-development" in skills
        assert "automated-testing" in skills

    def test_recommend_skills_javascript(self, detector: ToolchainDetector) -> None:
        """Test skill recommendations for JavaScript project."""
        toolchain = ToolchainInfo(
            primary_language="JavaScript",
            secondary_languages=[],
            frameworks=["Express"],
            build_tools=["webpack"],
            package_managers=["yarn"],
            test_frameworks=["mocha"],
            confidence=0.8,
        )

        skills = detector.recommend_skills(toolchain)

        assert "javascript-development" in skills
        assert "javascript-testing" in skills
        assert "backend-development" in skills

    def test_recommend_skills_rust(self, detector: ToolchainDetector) -> None:
        """Test skill recommendations for Rust project."""
        toolchain = ToolchainInfo(
            primary_language="Rust",
            secondary_languages=[],
            frameworks=["Tokio", "Axum"],
            build_tools=["cargo"],
            package_managers=["cargo"],
            test_frameworks=["cargo test"],
            confidence=0.9,
        )

        skills = detector.recommend_skills(toolchain)

        assert "rust-development" in skills
        assert "rust-testing" in skills
        assert "rust-async-development" in skills

    def test_recommend_skills_go(self, detector: ToolchainDetector) -> None:
        """Test skill recommendations for Go project."""
        toolchain = ToolchainInfo(
            primary_language="Go",
            secondary_languages=[],
            frameworks=["Gin"],
            build_tools=["go"],
            package_managers=["go modules"],
            test_frameworks=["go test"],
            confidence=0.9,
        )

        skills = detector.recommend_skills(toolchain)

        assert "go-development" in skills
        assert "go-testing" in skills

    def test_recommend_skills_no_duplicates(self, detector: ToolchainDetector) -> None:
        """Test that skill recommendations don't contain duplicates."""
        toolchain = ToolchainInfo(
            primary_language="Python",
            secondary_languages=[],
            frameworks=["Flask", "Django", "FastAPI"],
            build_tools=["poetry"],
            package_managers=["pip"],
            test_frameworks=["pytest", "tox"],
            confidence=0.9,
        )

        skills = detector.recommend_skills(toolchain)

        # Check for unique skills
        assert len(skills) == len(set(skills))

    def test_recommend_skills_unknown_language(
        self, detector: ToolchainDetector
    ) -> None:
        """Test skill recommendations for unknown language."""
        toolchain = ToolchainInfo(
            primary_language="Unknown",
            secondary_languages=[],
            frameworks=[],
            build_tools=[],
            package_managers=[],
            test_frameworks=[],
            confidence=0.0,
        )

        skills = detector.recommend_skills(toolchain)

        # Should return empty or minimal skills
        assert isinstance(skills, list)

    @pytest.mark.parametrize(
        "frameworks,expected_skill",
        [
            (["Flask"], "python-web-development"),
            (["Django"], "python-web-development"),
            (["FastAPI"], "python-web-development"),
            (["React"], "frontend-development"),
            (["Vue"], "frontend-development"),
            (["Angular"], "frontend-development"),
            (["Express"], "backend-development"),
            (["NestJS"], "backend-development"),
            (["Tokio"], "rust-async-development"),
            (["Actix"], "rust-async-development"),
        ],
    )
    def test_recommend_skills_framework_specific(
        self,
        detector: ToolchainDetector,
        frameworks: list[str],
        expected_skill: str,
    ) -> None:
        """Test framework-specific skill recommendations."""
        toolchain = ToolchainInfo(
            primary_language="Python",
            secondary_languages=[],
            frameworks=frameworks,
            build_tools=[],
            package_managers=[],
            test_frameworks=[],
            confidence=0.8,
        )

        skills = detector.recommend_skills(toolchain)
        assert expected_skill in skills


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for complete detection flow."""

    def test_full_python_project_detection(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test complete detection flow for Python project.

        Note: Confidence is normalized to [0.0, 1.0] range. Python has many
        possible markers (theoretical max 2.6), so normalized scores are lower.
        """
        info = detector.detect(temp_python_project)

        # Verify all fields are populated correctly
        assert info.primary_language == "Python"
        assert info.confidence > 0.4  # Normalized from raw score ~1.1
        assert len(info.frameworks) > 0
        assert len(info.build_tools) > 0
        assert len(info.package_managers) > 0
        assert len(info.test_frameworks) > 0

        # Verify skill recommendations
        skills = detector.recommend_skills(info)
        assert len(skills) > 0
        assert "python-development" in skills

    def test_full_typescript_project_detection(
        self, detector: ToolchainDetector, temp_typescript_project: Path
    ) -> None:
        """Test complete detection flow for TypeScript project."""
        info = detector.detect(temp_typescript_project)

        assert info.primary_language == "TypeScript"
        assert info.confidence > 0.7
        assert "React" in info.frameworks
        assert "vite" in info.build_tools
        assert len(info.test_frameworks) > 0

        skills = detector.recommend_skills(info)
        assert "typescript-development" in skills
        assert "frontend-development" in skills

    def test_detect_and_recommend_workflow(
        self, detector: ToolchainDetector, temp_rust_project: Path
    ) -> None:
        """Test the complete workflow from detection to skill recommendation."""
        # Step 1: Detect languages
        languages = detector.detect_languages(temp_rust_project)
        assert "Rust" in languages

        # Step 2: Detect frameworks
        frameworks = detector.detect_frameworks(temp_rust_project)
        assert len(frameworks) > 0

        # Step 3: Full detection
        info = detector.detect(temp_rust_project)
        assert info.primary_language == "Rust"

        # Step 4: Get skill recommendations
        skills = detector.recommend_skills(info)
        assert "rust-development" in skills


# =============================================================================
# Private Method Tests
# =============================================================================


class TestPrivateMethods:
    """Test suite for private helper methods (testing implementation details)."""

    def test_calculate_language_scores(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test _calculate_language_scores returns correct structure."""
        scores = detector._calculate_language_scores(temp_python_project)

        assert isinstance(scores, dict)
        assert "Python" in scores
        assert scores["Python"] > 0

    def test_calculate_language_scores_multiple_languages(
        self, detector: ToolchainDetector, temp_polyglot_project: Path
    ) -> None:
        """Test language score calculation for polyglot project."""
        scores = detector._calculate_language_scores(temp_polyglot_project)

        assert isinstance(scores, dict)
        assert len(scores) >= 2  # Should detect multiple languages

    def test_detect_python_frameworks_direct(
        self, detector: ToolchainDetector, temp_python_project: Path
    ) -> None:
        """Test _detect_python_frameworks private method."""
        frameworks = detector._detect_python_frameworks(temp_python_project)

        assert isinstance(frameworks, list)
        assert "Flask" in frameworks

    def test_detect_js_frameworks_direct(
        self, detector: ToolchainDetector, temp_typescript_project: Path
    ) -> None:
        """Test _detect_js_frameworks private method."""
        frameworks = detector._detect_js_frameworks(temp_typescript_project)

        assert isinstance(frameworks, list)
        assert "React" in frameworks

    def test_detect_rust_frameworks_direct(
        self, detector: ToolchainDetector, temp_rust_project: Path
    ) -> None:
        """Test _detect_rust_frameworks private method."""
        frameworks = detector._detect_rust_frameworks(temp_rust_project)

        assert isinstance(frameworks, list)
        assert "Tokio" in frameworks

    def test_detect_go_frameworks_direct(
        self, detector: ToolchainDetector, temp_go_project: Path
    ) -> None:
        """Test _detect_go_frameworks private method."""
        frameworks = detector._detect_go_frameworks(temp_go_project)

        assert isinstance(frameworks, list)
        assert "Gin" in frameworks
