"""Comprehensive tests for SkillManager.

Tests cover:
- SKILL.md parsing and frontmatter extraction
- Skill discovery and caching
- Metadata extraction
- Skill validation
- Basic text search
- Error handling for malformed files
"""

from pathlib import Path

import pytest

from mcp_skills.models.skill import Skill, SkillMetadata
from mcp_skills.services.skill_manager import SkillManager


@pytest.fixture
def temp_repos_dir(tmp_path: Path) -> Path:
    """Create temporary repository directory structure."""
    repos_dir = tmp_path / "repos"
    repos_dir.mkdir()
    return repos_dir


@pytest.fixture
def sample_skill_file(temp_repos_dir: Path) -> Path:
    """Create a valid SKILL.md file for testing."""
    # Create repo structure: repos/test-repo/testing/pytest/SKILL.md
    skill_dir = temp_repos_dir / "test-repo" / "testing" / "pytest"
    skill_dir.mkdir(parents=True)

    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        """---
name: pytest-testing
description: Professional pytest testing for Python projects
category: testing
tags: [python, pytest, tdd, unit-testing]
dependencies: []
version: "1.0.0"
author: Test Author
---

# PyTest Testing Skill

This skill provides comprehensive pytest testing capabilities for Python projects.

## Overview

PyTest is a powerful testing framework that makes it easy to write simple and scalable tests.

## Examples

```python
def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 5 - 3 == 2
```

## Usage

Run pytest with:
```bash
pytest tests/
```
""",
        encoding="utf-8",
    )

    return skill_file


@pytest.fixture
def malformed_skill_file(temp_repos_dir: Path) -> Path:
    """Create a malformed SKILL.md file for error testing."""
    skill_dir = temp_repos_dir / "test-repo" / "bad" / "skill"
    skill_dir.mkdir(parents=True)

    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        """---
name: bad-skill
description: Too short
category: invalid-category
---

# Bad Skill

Not enough content here.
""",
        encoding="utf-8",
    )

    return skill_file


@pytest.fixture
def skill_manager(temp_repos_dir: Path) -> SkillManager:
    """Create SkillManager instance with temporary directory."""
    return SkillManager(repos_dir=temp_repos_dir)


class TestSkillManagerInit:
    """Test SkillManager initialization."""

    def test_default_repos_dir(self) -> None:
        """Test default repos directory is set correctly."""
        manager = SkillManager()
        expected_dir = Path.home() / ".mcp-skills" / "repos"
        assert manager.repos_dir == expected_dir

    def test_custom_repos_dir(self, temp_repos_dir: Path) -> None:
        """Test custom repos directory."""
        manager = SkillManager(repos_dir=temp_repos_dir)
        assert manager.repos_dir == temp_repos_dir

    def test_empty_cache_on_init(self, skill_manager: SkillManager) -> None:
        """Test cache is empty on initialization."""
        assert len(skill_manager._skill_cache) == 0
        assert len(skill_manager._skill_paths) == 0

    def test_valid_categories_defined(self, skill_manager: SkillManager) -> None:
        """Test that valid categories are defined."""
        assert len(skill_manager.VALID_CATEGORIES) > 0
        assert "testing" in skill_manager.VALID_CATEGORIES
        assert "debugging" in skill_manager.VALID_CATEGORIES


class TestFrontmatterParsing:
    """Test YAML frontmatter parsing."""

    def test_split_frontmatter_valid(self, skill_manager: SkillManager) -> None:
        """Test splitting valid frontmatter."""
        content = """---
name: test
description: Test description
---

# Instructions
Content here"""

        frontmatter, instructions = skill_manager._split_frontmatter(content)

        assert "name: test" in frontmatter
        assert "description: Test description" in frontmatter
        assert "# Instructions" in instructions
        assert "Content here" in instructions

    def test_split_frontmatter_no_frontmatter(
        self, skill_manager: SkillManager
    ) -> None:
        """Test content without frontmatter."""
        content = "# Just some content\n\nNo frontmatter here"

        frontmatter, instructions = skill_manager._split_frontmatter(content)

        assert frontmatter == ""
        assert instructions == content

    def test_split_frontmatter_whitespace(self, skill_manager: SkillManager) -> None:
        """Test frontmatter with extra whitespace."""
        content = """---

name: test
description: desc

---

# Content"""

        frontmatter, instructions = skill_manager._split_frontmatter(content)

        assert "name: test" in frontmatter
        assert "# Content" in instructions


class TestSkillIDNormalization:
    """Test skill ID normalization."""

    def test_normalize_lowercase(self, skill_manager: SkillManager) -> None:
        """Test ID is converted to lowercase."""
        assert skill_manager._normalize_skill_id("UPPER/Case") == "upper/case"

    def test_normalize_special_chars(self, skill_manager: SkillManager) -> None:
        """Test special characters are replaced with hyphens."""
        assert skill_manager._normalize_skill_id("test skill!") == "test-skill"
        assert skill_manager._normalize_skill_id("a@b#c$d") == "a-b-c-d"

    def test_normalize_preserve_slashes(self, skill_manager: SkillManager) -> None:
        """Test slashes are preserved for path structure."""
        assert skill_manager._normalize_skill_id("repo/path/skill") == "repo/path/skill"

    def test_normalize_consecutive_hyphens(self, skill_manager: SkillManager) -> None:
        """Test consecutive hyphens are collapsed."""
        assert skill_manager._normalize_skill_id("test---skill") == "test-skill"

    def test_normalize_trim_hyphens(self, skill_manager: SkillManager) -> None:
        """Test leading/trailing hyphens are removed."""
        assert skill_manager._normalize_skill_id("-test-") == "test"


class TestExampleExtraction:
    """Test example extraction from instructions."""

    def test_extract_examples_section(self, skill_manager: SkillManager) -> None:
        """Test extracting Examples section."""
        instructions = """# Skill

## Examples

Example 1 content
Example 2 content

## Other Section"""

        examples = skill_manager._extract_examples(instructions)

        assert len(examples) > 0
        assert "Example 1 content" in examples[0]

    def test_extract_code_blocks(self, skill_manager: SkillManager) -> None:
        """Test extracting code blocks as examples."""
        instructions = """# Skill

```python
def test():
    pass
```

```bash
pytest
```"""

        examples = skill_manager._extract_examples(instructions)

        assert len(examples) == 2
        assert "def test():" in examples[0]
        assert "pytest" in examples[1]

    def test_extract_no_examples(self, skill_manager: SkillManager) -> None:
        """Test when no examples are present."""
        instructions = "# Skill\n\nJust instructions, no examples."

        examples = skill_manager._extract_examples(instructions)

        assert len(examples) == 0


class TestSkillDiscovery:
    """Test skill discovery functionality."""

    def test_discover_single_skill(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test discovering a single skill."""
        skills = skill_manager.discover_skills()

        assert len(skills) == 1
        assert skills[0].name == "pytest-testing"
        assert skills[0].repo_id == "test-repo"

    def test_discover_populates_cache(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test discovery populates skill path cache."""
        skill_manager.discover_skills()

        assert len(skill_manager._skill_paths) == 1

    def test_discover_nonexistent_dir(self, tmp_path: Path) -> None:
        """Test discovery with non-existent directory."""
        manager = SkillManager(repos_dir=tmp_path / "nonexistent")
        skills = manager.discover_skills()

        assert len(skills) == 0

    def test_discover_case_insensitive(
        self, skill_manager: SkillManager, temp_repos_dir: Path
    ) -> None:
        """Test SKILL.md is case-insensitive."""
        # Create skill with uppercase filename
        skill_dir = temp_repos_dir / "test-repo" / "case-test"
        skill_dir.mkdir(parents=True)

        skill_file = skill_dir / "skill.md"  # Lowercase
        skill_file.write_text(
            """---
name: case-test
description: Test case-insensitive discovery
category: testing
---

# Case Test Skill

Testing case-insensitive file discovery.
""",
            encoding="utf-8",
        )

        skills = skill_manager.discover_skills()

        # Should find both SKILL.md and skill.md
        assert any(s.name == "case-test" for s in skills)


class TestSkillLoading:
    """Test skill loading with caching."""

    def test_load_skill_from_discovery(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test loading skill after discovery."""
        skill_manager.discover_skills()

        skill = skill_manager.load_skill("test-repo/testing/pytest")

        assert skill is not None
        assert skill.name == "pytest-testing"

    def test_load_skill_caching(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test skill is cached after loading."""
        skill_manager.discover_skills()

        skill1 = skill_manager.load_skill("test-repo/testing/pytest")
        skill2 = skill_manager.load_skill("test-repo/testing/pytest")

        assert skill1 is skill2  # Same object (cached)

    def test_load_skill_not_found(self, skill_manager: SkillManager) -> None:
        """Test loading non-existent skill."""
        skill = skill_manager.load_skill("nonexistent/skill")

        assert skill is None

    def test_load_skill_before_discovery(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test loading skill without prior discovery."""
        # Should still work by searching filesystem
        skill = skill_manager.load_skill("test-repo/testing/pytest")

        assert skill is not None
        assert skill.name == "pytest-testing"


class TestMetadataExtraction:
    """Test skill metadata extraction."""

    def test_get_metadata_from_cache(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test getting metadata from cached skill."""
        skill_manager.discover_skills()
        skill_manager.load_skill("test-repo/testing/pytest")  # Load to cache

        metadata = skill_manager.get_skill_metadata("test-repo/testing/pytest")

        assert metadata is not None
        assert metadata.name == "pytest-testing"
        assert metadata.category == "testing"

    def test_get_metadata_without_cache(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test getting metadata without cached skill."""
        skill_manager.discover_skills()

        metadata = skill_manager.get_skill_metadata("test-repo/testing/pytest")

        assert metadata is not None
        assert metadata.name == "pytest-testing"

    def test_get_metadata_not_found(self, skill_manager: SkillManager) -> None:
        """Test getting metadata for non-existent skill."""
        metadata = skill_manager.get_skill_metadata("nonexistent/skill")

        assert metadata is None


class TestSkillValidation:
    """Test skill validation."""

    def test_validate_valid_skill(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test validating a valid skill."""
        skill_manager.discover_skills()
        skill = skill_manager.load_skill("test-repo/testing/pytest")

        assert skill is not None
        result = skill_manager.validate_skill(skill)

        assert len(result["errors"]) == 0
        # May have warnings (e.g., dependency resolution)

    def test_validate_missing_name(self, skill_manager: SkillManager) -> None:
        """Test validation fails for missing name."""
        skill = Skill(
            id="test/skill",
            name="",
            description="Valid description",
            instructions="Long enough instructions " * 10,
            category="testing",
            tags=["test"],
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
        )

        result = skill_manager.validate_skill(skill)

        assert len(result["errors"]) > 0
        assert any("name" in error.lower() for error in result["errors"])

    def test_validate_short_description(self, skill_manager: SkillManager) -> None:
        """Test validation fails for short description."""
        skill = Skill(
            id="test/skill",
            name="test-skill",
            description="Short",  # Too short
            instructions="Long enough instructions " * 10,
            category="testing",
            tags=["test"],
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
        )

        result = skill_manager.validate_skill(skill)

        assert len(result["errors"]) > 0
        assert any("description" in error.lower() for error in result["errors"])

    def test_validate_short_instructions(self, skill_manager: SkillManager) -> None:
        """Test validation fails for short instructions."""
        skill = Skill(
            id="test/skill",
            name="test-skill",
            description="Valid description here",
            instructions="Too short",  # Too short
            category="testing",
            tags=["test"],
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
        )

        result = skill_manager.validate_skill(skill)

        assert len(result["errors"]) > 0
        assert any("instructions" in error.lower() for error in result["errors"])

    def test_validate_invalid_category(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test warning for invalid category."""
        skill_manager.discover_skills()
        skill = skill_manager.load_skill("test-repo/testing/pytest")

        assert skill is not None
        # Modify category to invalid one
        skill.category = "invalid-category"

        result = skill_manager.validate_skill(skill)

        assert len(result["warnings"]) > 0
        assert any("category" in warning.lower() for warning in result["warnings"])

    def test_validate_missing_tags(self, skill_manager: SkillManager) -> None:
        """Test warning for missing tags."""
        skill = Skill(
            id="test/skill",
            name="test-skill",
            description="Valid description here",
            instructions="Long enough instructions " * 10,
            category="testing",
            tags=[],  # No tags
            dependencies=[],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
        )

        result = skill_manager.validate_skill(skill)

        assert len(result["warnings"]) > 0
        assert any("tags" in warning.lower() for warning in result["warnings"])


class TestSkillSearch:
    """Test skill search functionality."""

    def test_search_by_name(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test searching by skill name."""
        skill_manager.discover_skills()

        results = skill_manager.search_skills("pytest")

        assert len(results) == 1
        assert results[0].name == "pytest-testing"

    def test_search_by_tag(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test searching by tag."""
        skill_manager.discover_skills()

        results = skill_manager.search_skills("tdd")

        assert len(results) == 1
        assert results[0].name == "pytest-testing"

    def test_search_by_description(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test searching by description."""
        skill_manager.discover_skills()

        results = skill_manager.search_skills("professional")

        assert len(results) == 1
        assert results[0].name == "pytest-testing"

    def test_search_case_insensitive(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test search is case-insensitive."""
        skill_manager.discover_skills()

        results = skill_manager.search_skills("PYTEST")

        assert len(results) == 1

    def test_search_with_category_filter(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test searching with category filter."""
        skill_manager.discover_skills()

        results = skill_manager.search_skills("pytest", category="testing")

        assert len(results) == 1

    def test_search_category_mismatch(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test search returns empty when category doesn't match."""
        skill_manager.discover_skills()

        results = skill_manager.search_skills("pytest", category="debugging")

        assert len(results) == 0

    def test_search_no_results(self, skill_manager: SkillManager) -> None:
        """Test search with no matches."""
        results = skill_manager.search_skills("nonexistent-term")

        assert len(results) == 0

    def test_search_limit(
        self, skill_manager: SkillManager, temp_repos_dir: Path
    ) -> None:
        """Test search respects limit parameter."""
        # Create multiple skills
        for i in range(5):
            skill_dir = temp_repos_dir / "test-repo" / f"skill-{i}"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"""---
name: test-skill-{i}
description: Test skill number {i}
category: testing
tags: [test]
---

# Test Skill {i}

Instructions for skill {i}.
""",
                encoding="utf-8",
            )

        skill_manager.discover_skills()

        results = skill_manager.search_skills("test", limit=3)

        assert len(results) <= 3


class TestCacheManagement:
    """Test cache clearing and management."""

    def test_clear_cache(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test clearing cache."""
        skill_manager.discover_skills()
        skill_manager.load_skill("test-repo/testing/pytest")

        assert len(skill_manager._skill_cache) > 0
        assert len(skill_manager._skill_paths) > 0

        skill_manager.clear_cache()

        assert len(skill_manager._skill_cache) == 0
        assert len(skill_manager._skill_paths) == 0


class TestErrorHandling:
    """Test error handling for malformed files."""

    def test_parse_malformed_yaml(
        self, skill_manager: SkillManager, temp_repos_dir: Path
    ) -> None:
        """Test handling malformed YAML."""
        skill_dir = temp_repos_dir / "test-repo" / "bad-yaml"
        skill_dir.mkdir(parents=True)

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            """---
name: test
description: [unclosed array
---

# Content""",
            encoding="utf-8",
        )

        skills = skill_manager.discover_skills()

        # Should skip malformed file
        assert len(skills) == 0

    def test_parse_missing_frontmatter(
        self, skill_manager: SkillManager, temp_repos_dir: Path
    ) -> None:
        """Test handling file without frontmatter."""
        skill_dir = temp_repos_dir / "test-repo" / "no-frontmatter"
        skill_dir.mkdir(parents=True)

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "# Just content\n\nNo frontmatter here.", encoding="utf-8"
        )

        skills = skill_manager.discover_skills()

        # Should skip file without frontmatter
        assert len(skills) == 0

    def test_parse_missing_required_fields(
        self, skill_manager: SkillManager, malformed_skill_file: Path
    ) -> None:
        """Test handling file with missing required fields."""
        # malformed_skill_file has short description and instructions
        skills = skill_manager.discover_skills()

        # Should skip due to validation errors
        assert len(skills) == 0

    def test_parse_generic_exception(
        self, skill_manager: SkillManager, temp_repos_dir: Path
    ) -> None:
        """Test handling generic exceptions during parsing."""
        skill_dir = temp_repos_dir / "test-repo" / "exception-test"
        skill_dir.mkdir(parents=True)

        # Create a file that will cause an exception when parsing
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("---\n!!invalid!!\n---\n# Test", encoding="utf-8")

        skills = skill_manager.discover_skills()

        # Should gracefully handle the exception and continue
        assert len(skills) == 0

    def test_load_skill_invalid_path(self, skill_manager: SkillManager) -> None:
        """Test loading skill with invalid path format."""
        # Single part ID (no slash)
        skill = skill_manager.load_skill("invalid-id-format")

        assert skill is None

    def test_validate_unresolved_dependencies(
        self, skill_manager: SkillManager, sample_skill_file: Path
    ) -> None:
        """Test validation warning for unresolved dependencies."""
        skill = Skill(
            id="test/skill",
            name="test-skill",
            description="Valid description here",
            instructions="Long enough instructions " * 10,
            category="testing",
            tags=["test"],
            dependencies=["nonexistent/dependency"],
            examples=[],
            file_path=Path("/tmp/test.md"),
            repo_id="test",
        )

        result = skill_manager.validate_skill(skill)

        assert len(result["warnings"]) > 0
        assert any("dependency" in warning.lower() for warning in result["warnings"])


class TestDataclassSerialization:
    """Test Skill and SkillMetadata serialization."""

    def test_skill_to_dict(self, sample_skill_file: Path) -> None:
        """Test Skill.to_dict() method."""
        skill = Skill(
            id="test/skill",
            name="test-skill",
            description="Test description",
            instructions="Test instructions",
            category="testing",
            tags=["test"],
            dependencies=[],
            examples=["example 1"],
            file_path=Path("/tmp/test.md"),
            repo_id="test-repo",
            version="1.0.0",
            author="Test Author",
        )

        data = skill.to_dict()

        assert data["id"] == "test/skill"
        assert data["name"] == "test-skill"
        assert data["file_path"] == "/tmp/test.md"  # Path converted to string
        assert data["version"] == "1.0.0"
        assert data["author"] == "Test Author"

    def test_skill_from_dict(self) -> None:
        """Test Skill.from_dict() method."""
        data = {
            "id": "test/skill",
            "name": "test-skill",
            "description": "Test description",
            "instructions": "Test instructions",
            "category": "testing",
            "tags": ["test"],
            "dependencies": [],
            "examples": ["example 1"],
            "file_path": "/tmp/test.md",
            "repo_id": "test-repo",
            "version": "1.0.0",
            "author": "Test Author",
        }

        skill = Skill.from_dict(data)

        assert skill.id == "test/skill"
        assert skill.name == "test-skill"
        assert isinstance(skill.file_path, Path)
        assert skill.version == "1.0.0"
        assert skill.author == "Test Author"

    def test_skill_metadata_to_dict(self) -> None:
        """Test SkillMetadata.to_dict() method."""
        metadata = SkillMetadata(
            name="test-skill",
            description="Test description",
            category="testing",
            tags=["test"],
            dependencies=[],
            version="1.0.0",
            author="Test Author",
        )

        data = metadata.to_dict()

        assert data["name"] == "test-skill"
        assert data["version"] == "1.0.0"
        assert data["author"] == "Test Author"

    def test_skill_metadata_from_dict(self) -> None:
        """Test SkillMetadata.from_dict() method."""
        data = {
            "name": "test-skill",
            "description": "Test description",
            "category": "testing",
            "tags": ["test"],
            "dependencies": [],
            "version": "1.0.0",
            "author": "Test Author",
        }

        metadata = SkillMetadata.from_dict(data)

        assert metadata.name == "test-skill"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
