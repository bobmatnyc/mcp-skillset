"""Toolchain detection service for identifying project technology stack."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


@dataclass
class ToolchainInfo:
    """Detected toolchain information.

    Attributes:
        primary_language: Main programming language detected
        secondary_languages: Additional languages found in project
        frameworks: Detected frameworks (Flask, React, etc.)
        build_tools: Build system tools (npm, cargo, pip, etc.)
        package_managers: Package managers in use
        test_frameworks: Testing frameworks detected
        confidence: Confidence score (0.0-1.0) for detection accuracy
    """

    primary_language: str
    secondary_languages: list[str]
    frameworks: list[str]
    build_tools: list[str]
    package_managers: list[str]
    test_frameworks: list[str]
    confidence: float


class ToolchainDetector:
    """Automatically identify project technology stack.

    Scans project directory for toolchain markers (files, directories, configs)
    and determines the primary language, frameworks, and tools in use.
    """

    # Detection patterns for common toolchains
    TOOLCHAIN_PATTERNS = {
        "Python": {
            "files": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"],
            "dirs": ["venv", ".venv", "__pycache__"],
            "configs": ["pytest.ini", "tox.ini", ".flake8", "mypy.ini"],
            "priority": 1.0,
        },
        "TypeScript": {
            "files": ["tsconfig.json", "package.json"],
            "dirs": ["node_modules", "dist"],
            "configs": [".eslintrc", ".prettierrc", "jest.config.ts"],
            "priority": 1.0,
        },
        "JavaScript": {
            "files": ["package.json", "yarn.lock"],
            "dirs": ["node_modules", "dist"],
            "configs": [".eslintrc", ".prettierrc", "jest.config.js"],
            "priority": 0.9,
        },
        "Rust": {
            "files": ["Cargo.toml", "Cargo.lock"],
            "dirs": ["target"],
            "configs": [],
            "priority": 0.9,
        },
        "Go": {
            "files": ["go.mod", "go.sum"],
            "dirs": ["vendor"],
            "configs": [],
            "priority": 0.9,
        },
    }

    def detect(self, project_dir: Path) -> ToolchainInfo:
        """Analyze project directory and return toolchain information.

        Args:
            project_dir: Path to project root directory

        Returns:
            ToolchainInfo with detected languages, frameworks, and tools

        Example:
            detector = ToolchainDetector()
            info = detector.detect(Path("/path/to/project"))
            print(f"Primary language: {info.primary_language}")
        """
        if not project_dir.exists() or not project_dir.is_dir():
            logger.warning(f"Project directory does not exist: {project_dir}")
            return ToolchainInfo(
                primary_language="Unknown",
                secondary_languages=[],
                frameworks=[],
                build_tools=[],
                package_managers=[],
                test_frameworks=[],
                confidence=0.0,
            )

        # Calculate confidence scores for each language
        language_scores = self._calculate_language_scores(project_dir)

        # Determine primary and secondary languages
        if not language_scores:
            primary_language = "Unknown"
            secondary_languages = []
            confidence = 0.0
        else:
            # Sort by confidence score (descending)
            sorted_languages = sorted(
                language_scores.items(), key=lambda x: x[1], reverse=True
            )

            # Primary language is the one with highest confidence
            primary_language = sorted_languages[0][0]
            confidence = sorted_languages[0][1]

            # Secondary languages are those above minimum threshold (0.3)
            secondary_languages = [
                lang for lang, score in sorted_languages[1:] if score >= 0.3
            ]

        # Detect frameworks
        frameworks = self.detect_frameworks(project_dir)

        # Detect build tools and package managers
        build_tools = self._detect_build_tools(project_dir, language_scores)
        package_managers = self._detect_package_managers(project_dir, language_scores)

        # Detect test frameworks
        test_frameworks = self._detect_test_frameworks(project_dir, language_scores)

        return ToolchainInfo(
            primary_language=primary_language,
            secondary_languages=secondary_languages,
            frameworks=frameworks,
            build_tools=build_tools,
            package_managers=package_managers,
            test_frameworks=test_frameworks,
            confidence=confidence,
        )

    def detect_languages(self, project_dir: Path) -> list[str]:
        """Identify programming languages used in project.

        Args:
            project_dir: Path to project root

        Returns:
            List of detected language names sorted by confidence
        """
        language_scores = self._calculate_language_scores(project_dir)

        # Filter languages with minimum confidence threshold (0.3)
        # and sort by confidence score (descending)
        detected_languages = [
            lang
            for lang, score in sorted(
                language_scores.items(), key=lambda x: x[1], reverse=True
            )
            if score >= 0.3
        ]

        return detected_languages

    def detect_frameworks(self, project_dir: Path) -> list[str]:
        """Identify frameworks used in project.

        Parses package files (package.json, requirements.txt, etc.)
        to detect frameworks like Flask, React, Next.js.

        Args:
            project_dir: Path to project root

        Returns:
            List of detected framework names
        """
        frameworks = []

        # Python frameworks
        frameworks.extend(self._detect_python_frameworks(project_dir))

        # JavaScript/TypeScript frameworks
        frameworks.extend(self._detect_js_frameworks(project_dir))

        # Rust frameworks
        frameworks.extend(self._detect_rust_frameworks(project_dir))

        # Go frameworks
        frameworks.extend(self._detect_go_frameworks(project_dir))

        return frameworks

    def recommend_skills(self, toolchain: ToolchainInfo) -> list[str]:
        """Suggest skills based on detected toolchain.

        Args:
            toolchain: Detected toolchain information

        Returns:
            List of recommended skill IDs (generic categories for now)
        """
        skills = []

        # Language-based skills
        if toolchain.primary_language == "Python":
            skills.append("python-testing")
            skills.append("python-development")
        elif toolchain.primary_language == "TypeScript":
            skills.append("typescript-development")
            skills.append("typescript-testing")
        elif toolchain.primary_language == "JavaScript":
            skills.append("javascript-development")
            skills.append("javascript-testing")
        elif toolchain.primary_language == "Rust":
            skills.append("rust-development")
            skills.append("rust-testing")
        elif toolchain.primary_language == "Go":
            skills.append("go-development")
            skills.append("go-testing")

        # Framework-based skills
        for framework in toolchain.frameworks:
            framework_lower = framework.lower()
            if framework_lower in ["flask", "django", "fastapi"]:
                skills.append("python-web-development")
            elif framework_lower in ["react", "next.js", "vue", "angular"]:
                skills.append("frontend-development")
            elif framework_lower in ["express", "nestjs"]:
                skills.append("backend-development")
            elif framework_lower in ["tokio", "actix", "rocket", "axum"]:
                skills.append("rust-async-development")

        # Test framework-based skills
        if toolchain.test_frameworks:
            skills.append("automated-testing")

        return list(set(skills))  # Remove duplicates

    # Private helper methods

    def _calculate_language_scores(self, project_dir: Path) -> dict[str, float]:
        """Calculate confidence scores for each language based on pattern matching.

        Weights:
        - Marker files: 0.4 each
        - Directories: 0.2 each
        - Config files: 0.1 each

        Scores are normalized to [0.0, 1.0] range by dividing by the theoretical
        maximum score for each language (sum of all possible pattern weights).

        Args:
            project_dir: Path to project root

        Returns:
            Dictionary mapping language name to normalized confidence score (0.0-1.0)
        """
        scores: dict[str, float] = {}

        for language, patterns in self.TOOLCHAIN_PATTERNS.items():
            score = 0.0

            # Check for marker files (0.4 weight each)
            for file_name in patterns["files"]:
                if (project_dir / file_name).exists():
                    score += 0.4

            # Check for directories (0.2 weight each)
            for dir_name in patterns["dirs"]:
                if (project_dir / dir_name).exists():
                    score += 0.2

            # Check for config files (0.1 weight each)
            for config_name in patterns["configs"]:
                if (project_dir / config_name).exists():
                    score += 0.1

            # Apply language priority multiplier
            score *= patterns["priority"]

            if score > 0:
                # Normalize by theoretical maximum to ensure score <= 1.0
                # Theoretical max = (num_files * 0.4 + num_dirs * 0.2 + num_configs * 0.1) * priority
                theoretical_max = (
                    len(patterns["files"]) * 0.4
                    + len(patterns["dirs"]) * 0.2
                    + len(patterns["configs"]) * 0.1
                ) * patterns["priority"]

                # Normalize score to [0.0, 1.0] range
                normalized_score = (
                    min(score / theoretical_max, 1.0) if theoretical_max > 0 else 0.0
                )
                scores[language] = normalized_score

        return scores

    def _detect_build_tools(
        self, project_dir: Path, language_scores: dict[str, float]
    ) -> list[str]:
        """Detect build tools based on detected languages and marker files.

        Args:
            project_dir: Path to project root
            language_scores: Calculated language confidence scores

        Returns:
            List of detected build tool names
        """
        build_tools = []

        # Python build tools
        if "Python" in language_scores:
            if (project_dir / "setup.py").exists():
                build_tools.append("setuptools")
            if (project_dir / "pyproject.toml").exists():
                build_tools.append("poetry")

        # JavaScript/TypeScript build tools
        if "JavaScript" in language_scores or "TypeScript" in language_scores:
            package_json = project_dir / "package.json"
            if package_json.exists():
                try:
                    with open(package_json) as f:
                        data = json.load(f)
                        dev_deps = data.get("devDependencies", {})

                        if "webpack" in dev_deps:
                            build_tools.append("webpack")
                        if "vite" in dev_deps:
                            build_tools.append("vite")
                        if "rollup" in dev_deps:
                            build_tools.append("rollup")
                        if "esbuild" in dev_deps:
                            build_tools.append("esbuild")
                        if "parcel" in dev_deps:
                            build_tools.append("parcel")
                except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
                    logger.debug(f"Failed to parse package.json: {e}")

        # Rust build tools
        if "Rust" in language_scores and (project_dir / "Cargo.toml").exists():
            build_tools.append("cargo")

        # Go build tools
        if "Go" in language_scores and (project_dir / "go.mod").exists():
            build_tools.append("go")

        return build_tools

    def _detect_package_managers(
        self, project_dir: Path, language_scores: dict[str, float]
    ) -> list[str]:
        """Detect package managers based on lock files and marker files.

        Args:
            project_dir: Path to project root
            language_scores: Calculated language confidence scores

        Returns:
            List of detected package manager names
        """
        package_managers = []

        # Python package managers
        if "Python" in language_scores:
            if (project_dir / "requirements.txt").exists():
                package_managers.append("pip")
            if (project_dir / "Pipfile").exists():
                package_managers.append("pipenv")
            if (project_dir / "poetry.lock").exists():
                package_managers.append("poetry")
            if (project_dir / "pdm.lock").exists():
                package_managers.append("pdm")

        # JavaScript/TypeScript package managers
        if "JavaScript" in language_scores or "TypeScript" in language_scores:
            if (project_dir / "package-lock.json").exists():
                package_managers.append("npm")
            if (project_dir / "yarn.lock").exists():
                package_managers.append("yarn")
            if (project_dir / "pnpm-lock.yaml").exists():
                package_managers.append("pnpm")

        # Rust package manager
        if "Rust" in language_scores and (project_dir / "Cargo.lock").exists():
            package_managers.append("cargo")

        # Go package manager
        if "Go" in language_scores and (project_dir / "go.sum").exists():
            package_managers.append("go modules")

        return package_managers

    def _detect_test_frameworks(
        self, project_dir: Path, language_scores: dict[str, float]
    ) -> list[str]:
        """Detect test frameworks based on config files and dependencies.

        Args:
            project_dir: Path to project root
            language_scores: Calculated language confidence scores

        Returns:
            List of detected test framework names
        """
        test_frameworks = []

        # Python test frameworks
        if "Python" in language_scores:
            if (project_dir / "pytest.ini").exists() or (
                project_dir / "pyproject.toml"
            ).exists():
                # Check if pytest is in requirements
                test_frameworks.append("pytest")
            if (project_dir / "tox.ini").exists():
                test_frameworks.append("tox")

            # Check requirements files for test frameworks
            for req_file in ["requirements.txt", "requirements-dev.txt"]:
                req_path = project_dir / req_file
                if req_path.exists():
                    try:
                        content = req_path.read_text()
                        if (
                            "pytest" in content.lower()
                            and "pytest" not in test_frameworks
                        ):
                            test_frameworks.append("pytest")
                        if "unittest" in content.lower():
                            test_frameworks.append("unittest")
                    except (FileNotFoundError, PermissionError) as e:
                        logger.debug(f"Failed to read {req_file}: {e}")

        # JavaScript/TypeScript test frameworks
        if "JavaScript" in language_scores or "TypeScript" in language_scores:
            package_json = project_dir / "package.json"
            if package_json.exists():
                try:
                    with open(package_json) as f:
                        data = json.load(f)
                        dev_deps = data.get("devDependencies", {})
                        deps = data.get("dependencies", {})

                        all_deps = {**deps, **dev_deps}

                        if "jest" in all_deps:
                            test_frameworks.append("jest")
                        if "vitest" in all_deps:
                            test_frameworks.append("vitest")
                        if "mocha" in all_deps:
                            test_frameworks.append("mocha")
                        if "jasmine" in all_deps:
                            test_frameworks.append("jasmine")
                        if "@playwright/test" in all_deps:
                            test_frameworks.append("playwright")
                        if "cypress" in all_deps:
                            test_frameworks.append("cypress")
                except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
                    logger.debug(f"Failed to parse package.json: {e}")

        # Rust test frameworks (built-in, but check for additional ones)
        if "Rust" in language_scores:
            test_frameworks.append("cargo test")  # Built-in

        # Go test frameworks (built-in, but check for additional ones)
        if "Go" in language_scores:
            test_frameworks.append("go test")  # Built-in

        return test_frameworks

    def _detect_python_frameworks(self, project_dir: Path) -> list[str]:
        """Detect Python frameworks from requirements files and pyproject.toml.

        Args:
            project_dir: Path to project root

        Returns:
            List of detected Python framework names
        """
        frameworks = []
        framework_patterns = {
            "Flask": ["flask"],
            "Django": ["django"],
            "FastAPI": ["fastapi"],
            "Pydantic": ["pydantic"],
            "SQLAlchemy": ["sqlalchemy"],
            "Celery": ["celery"],
            "Tornado": ["tornado"],
            "Pyramid": ["pyramid"],
            "aiohttp": ["aiohttp"],
            "Sanic": ["sanic"],
        }

        # Check requirements.txt and variants
        for req_file in [
            "requirements.txt",
            "requirements-dev.txt",
            "requirements-prod.txt",
        ]:
            req_path = project_dir / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text().lower()
                    for framework, patterns in framework_patterns.items():
                        if (
                            any(pattern in content for pattern in patterns)
                            and framework not in frameworks
                        ):
                            frameworks.append(framework)
                except (FileNotFoundError, PermissionError) as e:
                    logger.debug(f"Failed to read {req_file}: {e}")

        # Check pyproject.toml
        pyproject = project_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text().lower()
                for framework, patterns in framework_patterns.items():
                    if (
                        any(pattern in content for pattern in patterns)
                        and framework not in frameworks
                    ):
                        frameworks.append(framework)
            except (FileNotFoundError, PermissionError) as e:
                logger.debug(f"Failed to read pyproject.toml: {e}")

        return frameworks

    def _detect_js_frameworks(self, project_dir: Path) -> list[str]:
        """Detect JavaScript/TypeScript frameworks from package.json.

        Args:
            project_dir: Path to project root

        Returns:
            List of detected JS/TS framework names
        """
        frameworks = []
        package_json = project_dir / "package.json"

        if not package_json.exists():
            return frameworks

        try:
            with open(package_json) as f:
                data = json.load(f)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})

                all_deps = {**deps, **dev_deps}

                # Frontend frameworks
                if "react" in all_deps:
                    frameworks.append("React")
                if "next" in all_deps:
                    frameworks.append("Next.js")
                if "vue" in all_deps:
                    frameworks.append("Vue")
                if "@angular/core" in all_deps:
                    frameworks.append("Angular")
                if "svelte" in all_deps:
                    frameworks.append("Svelte")

                # Backend frameworks
                if "express" in all_deps:
                    frameworks.append("Express")
                if "@nestjs/core" in all_deps:
                    frameworks.append("NestJS")
                if "koa" in all_deps:
                    frameworks.append("Koa")
                if "hapi" in all_deps:
                    frameworks.append("Hapi")
                if "fastify" in all_deps:
                    frameworks.append("Fastify")

        except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
            logger.debug(f"Failed to parse package.json: {e}")

        return frameworks

    def _detect_rust_frameworks(self, project_dir: Path) -> list[str]:
        """Detect Rust frameworks from Cargo.toml.

        Args:
            project_dir: Path to project root

        Returns:
            List of detected Rust framework names
        """
        frameworks = []
        cargo_toml = project_dir / "Cargo.toml"

        if not cargo_toml.exists():
            return frameworks

        try:
            content = cargo_toml.read_text().lower()

            # Async runtimes
            if "tokio" in content:
                frameworks.append("Tokio")

            # Web frameworks
            if "actix-web" in content:
                frameworks.append("Actix")
            if "rocket" in content:
                frameworks.append("Rocket")
            if "axum" in content:
                frameworks.append("Axum")
            if "warp" in content:
                frameworks.append("Warp")

            # Other frameworks
            if "serde" in content:
                frameworks.append("Serde")

        except (FileNotFoundError, PermissionError) as e:
            logger.debug(f"Failed to read Cargo.toml: {e}")

        return frameworks

    def _detect_go_frameworks(self, project_dir: Path) -> list[str]:
        """Detect Go frameworks from go.mod.

        Args:
            project_dir: Path to project root

        Returns:
            List of detected Go framework names
        """
        frameworks = []
        go_mod = project_dir / "go.mod"

        if not go_mod.exists():
            return frameworks

        try:
            content = go_mod.read_text().lower()

            # Web frameworks
            if "gin-gonic/gin" in content:
                frameworks.append("Gin")
            if "labstack/echo" in content:
                frameworks.append("Echo")
            if "gofiber/fiber" in content:
                frameworks.append("Fiber")
            if "gorilla/mux" in content:
                frameworks.append("Gorilla Mux")

            # ORMs
            if "gorm.io/gorm" in content:
                frameworks.append("GORM")

        except (FileNotFoundError, PermissionError) as e:
            logger.debug(f"Failed to read go.mod: {e}")

        return frameworks
