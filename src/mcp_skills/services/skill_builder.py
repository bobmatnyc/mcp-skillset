"""Service for building progressive skills from templates or parameters.

This module provides the SkillBuilder service for generating progressive skills
that follow the Claude Code skills format with YAML frontmatter and markdown body.

Design Decision: Template-Based Generation with Jinja2

Rationale: Use Jinja2 for template rendering to enable flexible, maintainable
skill generation with variable substitution and logic. Templates provide
consistent structure while allowing customization.

Trade-offs:
- Flexibility: Jinja2 templates vs. hardcoded string formatting
- Maintainability: Template files vs. code-embedded templates
- Learning curve: Template syntax vs. pure Python

Performance:
- Template loading: O(1) with Jinja2 caching
- Rendering: O(n) where n = template size (~5KB typical)
- Validation: O(m) where m = YAML frontmatter size (~100 tokens)
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


logger = logging.getLogger(__name__)


@dataclass
class SkillBuildResult:
    """Result of skill building operation.

    Attributes:
        status: "success" or "error"
        skill_path: Path to generated SKILL.md (if successful)
        skill_id: Generated skill identifier
        message: Success or error message
        warnings: List of validation warnings (non-blocking)
    """

    status: str
    skill_path: Path | None
    skill_id: str
    message: str
    warnings: list[str] | None = None


@dataclass
class ValidationResult:
    """Result of skill validation.

    Attributes:
        valid: Whether skill passes all critical validation
        errors: Critical errors that prevent deployment
        warnings: Non-critical issues for improvement
    """

    valid: bool
    errors: list[str]
    warnings: list[str]


class SkillBuilder:
    """Service for building progressive skills from templates or parameters.

    This service generates progressive skills following the Claude Code format:
    - YAML frontmatter with metadata (~100 tokens)
    - Markdown body with instructions (<5000 tokens)
    - Progressive disclosure architecture

    Supports:
    - Template-based generation (Jinja2)
    - Custom parameter overrides
    - Validation and security scanning
    - Deployment to ~/.claude/skills/

    Example:
        >>> builder = SkillBuilder()
        >>> result = builder.build_skill(
        ...     name="fastapi-testing",
        ...     description="Test FastAPI endpoints with pytest",
        ...     domain="web development",
        ...     tags=["fastapi", "pytest", "testing"]
        ... )
        >>> print(result.skill_path)
        /Users/user/.claude/skills/fastapi-testing/SKILL.md
    """

    # Size limits for progressive disclosure
    MAX_FRONTMATTER_SIZE = 100  # tokens (approximate as ~4 chars per token)
    MAX_FRONTMATTER_CHARS = 400  # ~100 tokens
    MAX_BODY_SIZE = 5000  # tokens
    MAX_BODY_CHARS = 20000  # ~5000 tokens

    # Security patterns to detect in skill content
    SECURITY_PATTERNS = [
        (
            r"(password|secret|api_key)\s*[:=]\s*['\"][^'\"]+['\"]",
            "Hardcoded credentials",
        ),
        (r"exec\s*\(", "Code execution patterns"),
        (r"eval\s*\(", "Dynamic code evaluation"),
        (r"__import__\s*\(", "Dynamic imports"),
    ]

    def __init__(self, config_path: Path | None = None):
        """Initialize SkillBuilder with Jinja2 template engine.

        Args:
            config_path: Optional path to configuration file
                        Defaults to package templates directory
        """
        # Determine templates directory
        if config_path:
            self.templates_dir = config_path.parent / "templates" / "skills"
        else:
            # Use package templates directory
            package_root = Path(__file__).parent.parent
            self.templates_dir = package_root / "templates" / "skills"

        # Create templates directory if it doesn't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        # autoescape=False is intentional: templates render Markdown, not HTML.  # nosec B701
        self.jinja_env = Environment(  # nosec B701
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.debug(f"SkillBuilder initialized with templates: {self.templates_dir}")

    def build_skill(
        self,
        name: str,
        description: str,
        domain: str,
        tags: list[str] | None = None,
        template: str | None = None,
        deploy: bool = True,
        spec_compliant: bool = False,
        **kwargs: Any,
    ) -> dict:
        """Build a skill from parameters or template.

        Generates a progressive skill with YAML frontmatter and markdown body.
        Validates structure, checks security patterns, and optionally deploys
        to ~/.claude/skills/.

        Args:
            name: Skill identifier (kebab-case recommended)
            description: Activation trigger and usage context
            domain: Technology domain (e.g., "web development", "testing")
            tags: Optional list of tags for discovery
            template: Optional template name (without .j2 extension)
            deploy: Whether to deploy to ~/.claude/skills/ (default: True)
            spec_compliant: Generate agentskills.io spec-compliant output (default: False)
                          When True, uses nested metadata format and validates spec limits
            **kwargs: Additional template variables
                - version: Skill version (default: "1.0.0")
                - category: Skill category
                - toolchain: List of required tools
                - frameworks: List of frameworks
                - related_skills: List of related skill names
                - author: Skill author (default: "mcp-skillset")
                - license: License identifier (default: "MIT")
                - compatibility: Compatibility requirements (agentskills.io spec)
                - allowed_tools: Space-delimited list of allowed tools (agentskills.io spec)

        Returns:
            dict with:
                - status: "success" or "error"
                - skill_path: Path to generated SKILL.md
                - skill_id: Generated skill identifier
                - message: Success/error message
                - warnings: List of validation warnings (if any)

        Error Handling:
        - Invalid template: Returns error status with message
        - Validation failure: Returns error status with validation errors
        - Security issues: Returns error status with security violations
        - Deployment failure: Returns error status with file system error

        Example:
            >>> result = builder.build_skill(
            ...     name="postgres-optimization",
            ...     description="Optimize PostgreSQL queries using EXPLAIN",
            ...     domain="database",
            ...     tags=["postgresql", "optimization", "performance"],
            ...     template="api-development"
            ... )
            >>> result["status"]
            'success'
        """
        try:
            # Normalize skill name to kebab-case
            skill_id = self._normalize_skill_id(name)

            # Build context for template rendering
            context = self._build_template_context(
                name=name,
                skill_id=skill_id,
                description=description,
                domain=domain,
                tags=tags or [],
                spec_compliant=spec_compliant,
                **kwargs,
            )

            # Generate skill content from template
            skill_content = self._generate_from_template(template, context)

            # Validate skill content
            validation = self.validate_skill(skill_content)
            if not validation.valid:
                return {
                    "status": "error",
                    "skill_path": None,
                    "skill_id": skill_id,
                    "message": f"Skill validation failed: {'; '.join(validation.errors)}",
                    "errors": validation.errors,
                    "warnings": validation.warnings,
                }

            # Deploy skill if requested
            skill_path = None
            if deploy:
                skill_path = self.deploy_skill(skill_content, skill_id)

            return {
                "status": "success",
                "skill_path": str(skill_path) if skill_path else None,
                "skill_id": skill_id,
                "message": f"Skill '{skill_id}' created successfully",
                "warnings": validation.warnings if validation.warnings else None,
            }

        except Exception as e:
            logger.error(f"Failed to build skill '{name}': {e}")
            return {
                "status": "error",
                "skill_path": None,
                "skill_id": name,
                "message": f"Failed to build skill: {str(e)}",
            }

    def validate_skill(self, skill_content: str) -> ValidationResult:
        """Validate skill YAML frontmatter and body.

        Performs comprehensive validation including:
        - YAML syntax validation
        - Required field presence
        - Progressive disclosure size limits
        - Security pattern scanning
        - Content quality checks

        Args:
            skill_content: Complete SKILL.md content

        Returns:
            ValidationResult with:
                - valid: bool
                - errors: list[str] of critical errors
                - warnings: list[str] of non-critical issues

        Validation Rules:
        - ERRORS (critical, prevent deployment):
            - Invalid YAML syntax
            - Missing required fields (name, description)
            - Description too short (<20 chars)
            - Security patterns detected
            - Body exceeds size limits (>20K chars)

        - WARNINGS (non-critical, logged):
            - Frontmatter exceeds size limit (>400 chars)
            - Body has no examples
            - Missing optional fields (tags, version)

        Example:
            >>> content = "---\\nname: test\\n---\\n# Test"
            >>> result = builder.validate_skill(content)
            >>> result.valid
            False
            >>> result.errors
            ['Description too short (0 chars, minimum 20)']
        """
        errors: list[str] = []
        warnings: list[str] = []

        try:
            # Split frontmatter and body
            frontmatter_yaml, body = self._split_skill_content(skill_content)

            if not frontmatter_yaml:
                errors.append("Missing YAML frontmatter")
                return ValidationResult(valid=False, errors=errors, warnings=warnings)

            # Parse YAML frontmatter
            try:
                frontmatter = yaml.safe_load(frontmatter_yaml)
                if not isinstance(frontmatter, dict):
                    errors.append("Frontmatter must be a YAML dictionary")
                    return ValidationResult(
                        valid=False, errors=errors, warnings=warnings
                    )
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax: {e}")
                return ValidationResult(valid=False, errors=errors, warnings=warnings)

            # Validate required fields
            if not frontmatter.get("name"):
                errors.append("Missing required field: name")

            description = frontmatter.get("description", "")
            if not description or len(description.strip()) < 20:
                errors.append(
                    f"Description too short ({len(description)} chars, minimum 20)"
                )

            # Validate progressive disclosure size limits
            frontmatter_size = len(frontmatter_yaml)
            if frontmatter_size > self.MAX_FRONTMATTER_CHARS:
                warnings.append(
                    f"Frontmatter exceeds recommended size "
                    f"({frontmatter_size} chars > {self.MAX_FRONTMATTER_CHARS} chars). "
                    "Consider moving content to body."
                )

            body_size = len(body)
            if body_size > self.MAX_BODY_CHARS:
                errors.append(
                    f"Body exceeds maximum size "
                    f"({body_size} chars > {self.MAX_BODY_CHARS} chars). "
                    "Use bundled resources for large content."
                )

            # Security validation
            security_errors = self._scan_security_patterns(skill_content)
            errors.extend(security_errors)

            # Content quality checks (warnings only)
            if not frontmatter.get("tags"):
                warnings.append("No tags specified. Tags improve discoverability.")

            if not frontmatter.get("version"):
                warnings.append(
                    "No version specified. Consider adding semantic version."
                )

            # Check for examples in body
            if "```" not in body and "example" not in body.lower():
                warnings.append(
                    "No code examples or usage examples found in body. "
                    "Consider adding practical examples."
                )

        except Exception as e:
            errors.append(f"Validation error: {e}")
            logger.error(f"Validation failed: {e}")

        return ValidationResult(
            valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def deploy_skill(self, skill_content: str, skill_name: str) -> Path:
        """Deploy skill to ~/.claude/skills/skill-name/SKILL.md

        Creates directory structure and writes SKILL.md file to Claude Code
        skills directory.

        Args:
            skill_content: Complete SKILL.md content
            skill_name: Skill identifier (used for directory name)

        Returns:
            Path to deployed SKILL.md file

        Error Handling:
        - Directory creation failure: Raises OSError
        - File write failure: Raises OSError
        - Permission issues: Raises PermissionError

        Example:
            >>> path = builder.deploy_skill(content, "my-skill")
            >>> path
            PosixPath('/Users/user/.claude/skills/my-skill/SKILL.md')
        """
        # Determine deployment path
        claude_skills_dir = Path.home() / ".claude" / "skills"
        skill_dir = claude_skills_dir / skill_name
        skill_file = skill_dir / "SKILL.md"

        # Create directory structure
        skill_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created skill directory: {skill_dir}")

        # Write SKILL.md file
        skill_file.write_text(skill_content, encoding="utf-8")
        logger.info(f"Deployed skill to: {skill_file}")

        return skill_file

    def list_templates(self) -> list[str]:
        """List available skill templates.

        Returns:
            List of template names (without .j2 extension)

        Example:
            >>> builder.list_templates()
            ['base', 'web-development', 'api-development', 'testing']
        """
        if not self.templates_dir.exists():
            return []

        templates = []
        for template_file in self.templates_dir.glob("*.md.j2"):
            # Remove .md.j2 extension
            template_name = template_file.name.replace(".md.j2", "")
            templates.append(template_name)

        return sorted(templates)

    # Private helper methods

    def _normalize_skill_id(self, skill_id: str) -> str:
        """Normalize skill ID to lowercase kebab-case.

        Args:
            skill_id: Raw skill ID

        Returns:
            Normalized skill ID (lowercase, hyphens)

        Examples:
            "FastAPI Testing" -> "fastapi-testing"
            "My Cool Skill!" -> "my-cool-skill"
        """
        # Convert to lowercase
        normalized = skill_id.lower()

        # Replace spaces and special chars with hyphens
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized)

        # Remove leading/trailing hyphens
        normalized = normalized.strip("-")

        # Remove consecutive hyphens
        normalized = re.sub(r"-+", "-", normalized)

        return normalized

    def _build_template_context(
        self,
        name: str,
        skill_id: str,
        description: str,
        domain: str,
        tags: list[str],
        spec_compliant: bool = False,
        **kwargs: Any,
    ) -> dict:
        """Build context dictionary for template rendering.

        Args:
            name: Skill display name
            skill_id: Normalized skill identifier
            description: Skill description and activation context
            domain: Technology domain
            tags: List of tags
            spec_compliant: Generate agentskills.io spec-compliant format
            **kwargs: Additional template variables

        Returns:
            Dictionary with all template variables
        """
        # Build base context
        context = {
            "name": name,
            "skill_id": skill_id,
            "description": description,
            "domain": domain,
            "tags": tags,
            "version": kwargs.get("version", "1.0.0"),
            "category": kwargs.get("category", domain.title()),
            "toolchain": kwargs.get("toolchain", []),
            "frameworks": kwargs.get("frameworks", []),
            "related_skills": kwargs.get("related_skills", []),
            "author": kwargs.get("author", "mcp-skillset"),
            "license": kwargs.get("license", "MIT"),
            "created": kwargs.get("created", datetime.now().strftime("%Y-%m-%d")),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "spec_compliant": spec_compliant,
            # agentskills.io spec fields
            "compatibility": kwargs.get("compatibility"),
            "allowed_tools": kwargs.get("allowed_tools"),
        }

        # Add any additional kwargs as template variables
        for key, value in kwargs.items():
            if key not in context:
                context[key] = value

        return context

    def _generate_from_template(self, template_name: str | None, context: dict) -> str:
        """Generate skill content from Jinja2 template.

        Args:
            template_name: Template name (without .j2 extension) or None for base
            context: Template rendering context

        Returns:
            Rendered SKILL.md content

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        # Use base template if no template specified
        if not template_name:
            template_name = "base"

        # Load and render template
        try:
            template = self.jinja_env.get_template(f"{template_name}.md.j2")
            return str(template.render(**context))
        except TemplateNotFound:
            # If custom template not found, fall back to base
            logger.warning(f"Template '{template_name}' not found, using base template")
            template = self.jinja_env.get_template("base.md.j2")
            return str(template.render(**context))

    def _split_skill_content(self, content: str) -> tuple[str, str]:
        """Split SKILL.md into frontmatter and body.

        Args:
            content: Complete SKILL.md content

        Returns:
            Tuple of (frontmatter_yaml, body_markdown)
        """
        # Match YAML frontmatter between --- markers
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            return match.group(1), match.group(2)

        # No frontmatter found
        return "", content

    def _scan_security_patterns(self, content: str) -> list[str]:
        """Scan skill content for security patterns.

        Args:
            content: Skill content to scan

        Returns:
            List of security error messages
        """
        errors = []

        for pattern, description in self.SECURITY_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append(f"Security violation: {description} detected")

        return errors
