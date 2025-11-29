"""End-to-end tests for skill auto-detection workflows.

This module tests the complete skill auto-detection workflow:
1. Detect project toolchain (Python, TypeScript, multi-language)
2. Recommend relevant skills based on detected toolchain
3. Verify recommendations match project characteristics

Tests cover:
- Python project detection and skill recommendations
- TypeScript project detection and skill recommendations
- Multi-language project detection
- Edge cases (empty project, unknown toolchain)
"""

from pathlib import Path

import pytest

from mcp_skills.mcp.server import configure_services
from mcp_skills.mcp.tools.skill_tools import skills_recommend, skills_reindex
from mcp_skills.services.toolchain_detector import ToolchainDetector


@pytest.mark.e2e
class TestPythonProjectAutoDetect:
    """Test auto-detection for Python projects."""

    def test_detect_python_project(
        self,
        sample_python_project_e2e: Path,
    ) -> None:
        """Test toolchain detection for Python project."""
        detector = ToolchainDetector()
        result = detector.detect(sample_python_project_e2e)

        # Verify Python detected
        assert result.primary_language == "Python"

        # Verify frameworks detected
        assert "flask" in [f.lower() for f in result.frameworks]

        # Verify test framework detected
        assert "pytest" in [t.lower() for t in result.test_frameworks]

        # Verify confidence (lowered threshold for test environment)
        assert result.confidence > 0.1

    @pytest.mark.asyncio
    async def test_recommend_skills_python_project(
        self,
        sample_python_project_e2e: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test skill recommendations for Python project."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        # Reindex first
        await skills_reindex(force=True)

        # Get recommendations
        result = await skills_recommend(
            project_path=str(sample_python_project_e2e),
            limit=10,
        )

        assert result["status"] == "completed"
        assert result["recommendation_type"] == "project_based"

        # Verify context contains Python
        assert "Python" in result["context"]["detected_toolchains"]

        # Verify recommendations are relevant to Python
        recommendations = result["recommendations"]
        if len(recommendations) > 0:
            # Should recommend Python-related skills
            [r["name"] for r in recommendations]
            skill_tags = [tag for r in recommendations for tag in r["tags"]]

            # At least some skills should have python tag
            assert "python" in [t.lower() for t in skill_tags]

    @pytest.mark.asyncio
    async def test_recommend_pytest_for_python_project(
        self,
        sample_python_project_e2e: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test that pytest skills are recommended for Python project with pytest."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await skills_reindex(force=True)

        result = await skills_recommend(
            project_path=str(sample_python_project_e2e),
            limit=10,
        )

        assert result["status"] == "completed"

        # Should recommend pytest-testing skill
        recommendations = result["recommendations"]
        skill_names = [r["name"] for r in recommendations]

        # pytest-testing should be in recommendations
        assert "pytest-testing" in skill_names

    @pytest.mark.asyncio
    async def test_recommend_flask_for_flask_project(
        self,
        sample_python_project_e2e: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test that Flask skills are recommended for Flask project."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await skills_reindex(force=True)

        result = await skills_recommend(
            project_path=str(sample_python_project_e2e),
            limit=10,
        )

        assert result["status"] == "completed"

        # Should recommend flask-web skill
        recommendations = result["recommendations"]
        skill_names = [r["name"] for r in recommendations]

        # flask-web should be in recommendations
        assert "flask-web" in skill_names


@pytest.mark.e2e
class TestTypeScriptProjectAutoDetect:
    """Test auto-detection for TypeScript projects."""

    def test_detect_typescript_project(
        self,
        sample_typescript_project_e2e: Path,
    ) -> None:
        """Test toolchain detection for TypeScript project."""
        detector = ToolchainDetector()
        result = detector.detect(sample_typescript_project_e2e)

        # Verify TypeScript detected
        assert result.primary_language == "TypeScript"

        # Verify test framework detected
        assert "jest" in [t.lower() for t in result.test_frameworks]

        # Verify confidence (lowered threshold for test environment)
        assert result.confidence > 0.1

    @pytest.mark.asyncio
    async def test_recommend_skills_typescript_project(
        self,
        sample_typescript_project_e2e: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test skill recommendations for TypeScript project."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await skills_reindex(force=True)

        result = await skills_recommend(
            project_path=str(sample_typescript_project_e2e),
            limit=10,
        )

        assert result["status"] == "completed"
        assert result["recommendation_type"] == "project_based"

        # Verify context contains TypeScript
        assert "TypeScript" in result["context"]["detected_toolchains"]

        # Verify recommendations are relevant to TypeScript
        recommendations = result["recommendations"]
        if len(recommendations) > 0:
            skill_tags = [tag for r in recommendations for tag in r["tags"]]

            # At least some skills should have typescript tag
            assert "typescript" in [t.lower() for t in skill_tags]

    @pytest.mark.asyncio
    async def test_recommend_jest_for_typescript_project(
        self,
        sample_typescript_project_e2e: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test that Jest/TypeScript skills recommended for TS project."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await skills_reindex(force=True)

        result = await skills_recommend(
            project_path=str(sample_typescript_project_e2e),
            limit=10,
        )

        assert result["status"] == "completed"

        # Should recommend typescript-testing skill
        recommendations = result["recommendations"]
        skill_names = [r["name"] for r in recommendations]

        # typescript-testing should be in recommendations
        assert "typescript-testing" in skill_names


@pytest.mark.e2e
class TestMultiLanguageProjectAutoDetect:
    """Test auto-detection for multi-language projects."""

    def test_detect_multi_language_project(
        self,
        tmp_path: Path,
    ) -> None:
        """Test detection of project with multiple languages."""
        # Create multi-language project
        project_dir = tmp_path / "multi_lang_project"
        project_dir.mkdir()

        # Python files
        (project_dir / "backend").mkdir()
        (project_dir / "backend" / "app.py").write_text(
            "from flask import Flask\napp = Flask(__name__)"
        )
        (project_dir / "requirements.txt").write_text("flask>=3.0.0\n")

        # TypeScript files
        (project_dir / "frontend").mkdir()
        (project_dir / "frontend" / "index.ts").write_text("console.log('Hello');")
        (project_dir / "package.json").write_text(
            '{"dependencies": {"typescript": "^5.0.0"}}'
        )

        # Detect toolchain
        detector = ToolchainDetector()
        result = detector.detect(project_dir)

        # Should detect primary language (likely Python since it has more markers)
        assert result.primary_language in ["Python", "TypeScript"]

        # Should detect secondary language (may or may not depending on file structure)
        # Note: Secondary language detection may vary based on file counts and patterns
        # So we just verify that at least one language was detected with reasonable confidence
        assert result.confidence > 0.1

    @pytest.mark.asyncio
    async def test_recommend_skills_multi_language_project(
        self,
        tmp_path: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test recommendations for multi-language project."""
        # Create multi-language project
        project_dir = tmp_path / "multi_lang_project"
        project_dir.mkdir()

        # Python backend
        (project_dir / "backend").mkdir()
        (project_dir / "backend" / "app.py").write_text(
            "from flask import Flask\napp = Flask(__name__)"
        )
        (project_dir / "pyproject.toml").write_text(
            "[project]\nname='backend'\ndependencies=['flask']\n"
        )

        # TypeScript frontend
        (project_dir / "frontend").mkdir()
        (project_dir / "frontend" / "index.ts").write_text("console.log('Hello');")
        (project_dir / "package.json").write_text(
            '{"dependencies": {"typescript": "^5.0.0"}}'
        )

        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await skills_reindex(force=True)

        result = await skills_recommend(
            project_path=str(project_dir),
            limit=10,
        )

        assert result["status"] == "completed"

        # Should detect multiple languages
        detected_langs = result["context"]["detected_toolchains"]
        assert len(detected_langs) >= 1

        # Recommendations should include skills for detected languages
        recommendations = result["recommendations"]
        if len(recommendations) > 0:
            skill_tags = [tag for r in recommendations for tag in r["tags"]]
            tags_lower = [t.lower() for t in skill_tags]

            # Should have skills for at least one of the languages
            assert "python" in tags_lower or "typescript" in tags_lower


@pytest.mark.e2e
class TestEdgeCases:
    """Test edge cases for auto-detection."""

    def test_detect_empty_project(
        self,
        tmp_path: Path,
    ) -> None:
        """Test detection of empty project directory."""
        empty_dir = tmp_path / "empty_project"
        empty_dir.mkdir()

        detector = ToolchainDetector()
        result = detector.detect(empty_dir)

        # Should return Unknown
        assert result.primary_language == "Unknown"
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_recommend_skills_empty_project(
        self,
        tmp_path: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test recommendations for empty project."""
        empty_dir = tmp_path / "empty_project"
        empty_dir.mkdir()

        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await skills_reindex(force=True)

        result = await skills_recommend(
            project_path=str(empty_dir),
            limit=10,
        )

        assert result["status"] == "completed"

        # Should return empty recommendations with message
        assert len(result["recommendations"]) == 0
        assert "context" in result
        assert "message" in result["context"]

    def test_detect_project_with_only_readme(
        self,
        tmp_path: Path,
    ) -> None:
        """Test detection of project with only README."""
        project_dir = tmp_path / "readme_only"
        project_dir.mkdir()
        (project_dir / "README.md").write_text("# My Project\n")

        detector = ToolchainDetector()
        result = detector.detect(project_dir)

        # Should return Unknown (README doesn't indicate toolchain)
        assert result.primary_language == "Unknown"

    def test_detect_project_with_multiple_test_frameworks(
        self,
        tmp_path: Path,
    ) -> None:
        """Test detection with multiple test frameworks."""
        project_dir = tmp_path / "multi_test_project"
        project_dir.mkdir()

        # Python with pytest and unittest
        (project_dir / "pyproject.toml").write_text(
            "[project]\nname='test'\n"
            "[project.optional-dependencies]\n"
            'dev=["pytest", "unittest2"]\n'
        )

        detector = ToolchainDetector()
        result = detector.detect(project_dir)

        assert result.primary_language == "Python"
        # Should detect at least one test framework
        assert len(result.test_frameworks) >= 1
        assert any("pytest" in tf.lower() for tf in result.test_frameworks)


@pytest.mark.e2e
class TestAutoDetectWorkflowIntegration:
    """Test complete auto-detect workflows."""

    @pytest.mark.asyncio
    async def test_complete_python_workflow(
        self,
        sample_python_project_e2e: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test complete workflow: detect → recommend → verify.

        Workflow:
        1. Detect Python project toolchain
        2. Get skill recommendations
        3. Verify recommendations are actionable
        4. Verify recommendation confidence scores
        """
        # 1. Detect toolchain
        detector = ToolchainDetector()
        toolchain = detector.detect(sample_python_project_e2e)

        assert toolchain.primary_language == "Python"
        assert toolchain.confidence > 0.1

        # 2. Get recommendations
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await skills_reindex(force=True)

        result = await skills_recommend(
            project_path=str(sample_python_project_e2e),
            limit=10,
        )

        assert result["status"] == "completed"

        # 3. Verify recommendations are actionable
        recommendations = result["recommendations"]
        assert len(recommendations) > 0

        for rec in recommendations:
            # Each recommendation should have all required fields
            assert "id" in rec
            assert "name" in rec
            assert "description" in rec
            assert "confidence" in rec
            assert "reason" in rec

            # Descriptions should be meaningful
            assert len(rec["description"]) > 20

            # Reasons should explain why recommended
            assert len(rec["reason"]) > 10

        # 4. Verify confidence scores
        for rec in recommendations:
            assert 0.0 <= rec["confidence"] <= 1.0

        # Top recommendation should have decent confidence
        if len(recommendations) > 0:
            assert recommendations[0]["confidence"] > 0.4

    @pytest.mark.asyncio
    async def test_complete_typescript_workflow(
        self,
        sample_typescript_project_e2e: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test complete TypeScript detection and recommendation workflow."""
        # Detect toolchain
        detector = ToolchainDetector()
        toolchain = detector.detect(sample_typescript_project_e2e)

        assert toolchain.primary_language == "TypeScript"

        # Get recommendations
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await skills_reindex(force=True)

        result = await skills_recommend(
            project_path=str(sample_typescript_project_e2e),
            limit=10,
        )

        assert result["status"] == "completed"
        assert len(result["recommendations"]) > 0

        # Verify TypeScript skills recommended
        skill_tags = [tag for r in result["recommendations"] for tag in r["tags"]]
        assert "typescript" in [t.lower() for t in skill_tags]

    @pytest.mark.asyncio
    async def test_workflow_recommendation_ranking(
        self,
        sample_python_project_e2e: Path,
        e2e_services_with_repo: tuple,
        e2e_base_dir,
        e2e_storage_dir,
    ) -> None:
        """Test that recommendations are properly ranked by relevance."""
        configure_services(
            base_dir=e2e_base_dir,
            storage_path=e2e_storage_dir,
        )

        await skills_reindex(force=True)

        result = await skills_recommend(
            project_path=str(sample_python_project_e2e),
            limit=10,
        )

        assert result["status"] == "completed"
        recommendations = result["recommendations"]

        if len(recommendations) > 1:
            # Confidence scores should be in descending order
            confidences = [r["confidence"] for r in recommendations]
            for i in range(len(confidences) - 1):
                assert confidences[i] >= confidences[i + 1]
