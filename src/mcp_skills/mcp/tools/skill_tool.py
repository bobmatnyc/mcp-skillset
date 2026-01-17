"""Unified skill tool for CRUD operations with git workflow.

This module provides a single entry point for all skill CRUD operations
with git-based authorization for write operations.
"""

from __future__ import annotations

import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ..server import (
    get_indexing_engine,
    get_skill_manager,
    mcp,
)


logger = logging.getLogger(__name__)

# Authorized users who can push directly to main
AUTHORIZED_USERS = [
    "bobmatnyc@users.noreply.github.com",
    "bobmatnyc@gmail.com",
]

# Target skills repository
SKILLS_REPO = "bobmatnyc/claude-mpm-skills"


def get_git_user() -> str:
    """Get current git user email."""
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def is_authorized_pusher() -> bool:
    """Check if current user can push directly to main."""
    return get_git_user() in AUTHORIZED_USERS


def get_skills_repo_path() -> Path:
    """Get the local path to the skills repository."""
    # Check common locations
    paths = [
        Path.home() / ".mcp-skillset" / "repos" / "claude-mpm-skills",
        Path.home() / ".mcp-skillset" / "repos" / "bobmatnyc" / "claude-mpm-skills",
    ]
    for path in paths:
        if path.exists() and (path / ".git").exists():
            return path
    # Default to first path
    return paths[0]


@mcp.tool()
async def skill(
    action: str,
    skill_id: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Read skill details, view skill instructions and examples, or rebuild search indices for skill discovery.

    This tool provides read access to skill metadata, instructions, examples, and dependencies. Use action="read" to view complete skill details including instructions and code examples. Use action="reindex" to rebuild vector search indices and knowledge graph for updated skill discovery.

    Available Actions:
    - read: Get complete skill details, view instructions, examples, and metadata
    - reindex: Rebuild search indices (vector store + knowledge graph) for skill discovery

    Note: Write operations (create/update/delete) are available via CLI only.
    Use `mcp-skillset build-skill` for creating skills, or edit skill files directly for updates.

    Args:
        action: Operation to perform - valid values: read, reindex
        skill_id: Skill ID for read action (required when action="read")
        force: Force reindex even if indices are up-to-date (optional, default: False)

    Returns:
        Dict with status and result data:
        - For read: Returns skill metadata, instructions, examples, tags, category, toolchain, dependencies
        - For reindex: Returns indexing statistics (indexed_count, vector_store_size, graph_nodes, graph_edges)

    Common Use Cases:
        # Get skill details and instructions
        skill(action="read", skill_id="pytest-skill")

        # View skill examples and code snippets
        skill(action="read", skill_id="fastapi-testing")

        # Rebuild search index after skill updates
        skill(action="reindex", force=True)

        # Incremental reindex (only if needed)
        skill(action="reindex")

    Examples:
        >>> # Read skill details
        >>> skill(action="read", skill_id="pytest-skill")
        {
            "status": "completed",
            "skill": {
                "id": "pytest-skill",
                "name": "pytest",
                "description": "Testing patterns with pytest",
                "category": "testing",
                "tags": ["python", "testing", "tdd"],
                "instructions": "...",
                "examples": [...]
            }
        }

        >>> # Reindex all skills
        >>> skill(action="reindex", force=True)
        {
            "status": "completed",
            "action": "reindex",
            "indexed_count": 42,
            "vector_store_size": 1024,
            "graph_nodes": 50,
            "graph_edges": 120
        }

    """
    try:
        if action == "read":
            if not skill_id:
                return {"status": "error", "message": "skill_id required for read"}
            return await _read_skill(skill_id)

        elif action == "reindex":
            return await _reindex_skills(force)

        elif action in ("create", "update", "delete"):
            return {
                "status": "error",
                "message": f"Action '{action}' is not available via MCP. "
                "Use CLI instead: `mcp-skillset build-skill` for create, "
                "or edit skill files directly for update/delete.",
            }

        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}. Valid: read|reindex",
            }

    except Exception as e:
        logger.exception(f"Error in skill tool: {e}")
        return {"status": "error", "message": str(e)}


async def _read_skill(skill_id: str) -> dict[str, Any]:
    """Read complete skill details."""
    skill_manager = get_skill_manager()

    skill = skill_manager.load_skill(skill_id)
    if not skill:
        return {"status": "error", "message": f"Skill not found: {skill_id}"}

    return {
        "status": "completed",
        "skill": {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "tags": skill.tags or [],
            "version": skill.version,
            "author": skill.author,
            "instructions": skill.instructions,
            "file_path": str(skill.file_path) if skill.file_path else None,
            "repo_id": skill.repo_id,
            "dependencies": skill.dependencies or [],
            "examples": skill.examples or [],
        },
    }


async def _create_skill(
    name: str,
    description: str,
    domain: str,
    tags: list[str] | None,
    template: str,
    deploy: bool,
    commit_message: str | None,
) -> dict[str, Any]:
    """Create a new skill with git workflow."""
    from ...services.skill_builder import SkillBuilder

    # Generate skill ID
    skill_id = _normalize_skill_id(name)

    # Build skill content
    builder = SkillBuilder()
    skill_content = builder.build_skill(
        name=name,
        description=description,
        domain=domain,
        tags=tags or [],
        template=template,
        deploy=False,  # Don't deploy yet, we'll handle git workflow first
    )

    if skill_content["status"] != "success":
        return skill_content

    # Get the generated content
    # Note: SkillBuilder.build_skill returns a dict, not the content directly
    # We need to generate the content using the builder's internal methods
    builder_context = {
        "name": name,
        "skill_id": skill_id,
        "description": description,
        "domain": domain,
        "tags": tags or [],
        "version": "1.0.0",
        "category": domain.title(),
        "toolchain": [],
        "frameworks": [],
        "related_skills": [],
        "author": "mcp-skillset",
        "license": "MIT",
        "created": datetime.now().strftime("%Y-%m-%d"),
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
    }
    content = builder._generate_from_template(template, builder_context)

    if not deploy:
        return {
            "status": "completed",
            "action": "preview",
            "skill_id": skill_id,
            "content": content,
            "message": "Skill generated but not deployed. Set deploy=True to save.",
        }

    # Determine git workflow
    repo_path = get_skills_repo_path()

    # Create skill directory structure: skills/domain/skill-id/SKILL.md
    domain_slug = _normalize_skill_id(domain)
    skill_path = repo_path / "skills" / domain_slug / skill_id / "SKILL.md"

    # Create skill file
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(content)

    # Git operations
    git_result = await _git_commit_and_push(
        repo_path=repo_path,
        files=[str(skill_path.relative_to(repo_path))],
        commit_message=commit_message or f"feat: add {name} skill",
        action="create",
        skill_id=skill_id,
    )

    # Reindex
    reindex_result = await _trigger_reindex()

    return {
        "status": "completed",
        "action": "create",
        "skill_id": skill_id,
        "skill_path": str(skill_path),
        **git_result,
        "reindexed": reindex_result.get("success", False),
    }


async def _update_skill(
    skill_id: str,
    description: str | None,
    tags: list[str] | None,
    content: str | None,
    commit_message: str | None,
) -> dict[str, Any]:
    """Update an existing skill with git workflow."""
    skill_manager = get_skill_manager()

    # Load existing skill
    skill = skill_manager.load_skill(skill_id)
    if not skill:
        return {"status": "error", "message": f"Skill not found: {skill_id}"}

    if not skill.file_path:
        return {
            "status": "error",
            "message": f"Skill file path not found: {skill_id}",
        }

    skill_path = Path(skill.file_path)
    repo_path = get_skills_repo_path()

    if content:
        # Full content replacement
        skill_path.write_text(content)
    else:
        # Partial update - modify frontmatter
        current_content = skill_path.read_text()
        updated_content = _update_frontmatter(current_content, description, tags)
        skill_path.write_text(updated_content)

    # Git operations
    git_result = await _git_commit_and_push(
        repo_path=repo_path,
        files=[str(skill_path.relative_to(repo_path))],
        commit_message=commit_message or f"docs: update {skill_id} skill",
        action="update",
        skill_id=skill_id,
    )

    # Reindex
    reindex_result = await _trigger_reindex()

    return {
        "status": "completed",
        "action": "update",
        "skill_id": skill_id,
        "skill_path": str(skill_path),
        **git_result,
        "reindexed": reindex_result.get("success", False),
    }


async def _delete_skill(
    skill_id: str,
    commit_message: str | None,
) -> dict[str, Any]:
    """Delete a skill with git workflow."""
    skill_manager = get_skill_manager()

    skill = skill_manager.load_skill(skill_id)
    if not skill or not skill.file_path:
        return {"status": "error", "message": f"Skill not found: {skill_id}"}

    skill_path = Path(skill.file_path)
    repo_path = get_skills_repo_path()

    # Git operations (delete file via git rm)
    git_result = await _git_commit_and_push(
        repo_path=repo_path,
        files=[str(skill_path.relative_to(repo_path))],
        commit_message=commit_message or f"chore: remove {skill_id} skill",
        action="delete",
        skill_id=skill_id,
        delete=True,
    )

    # Reindex
    reindex_result = await _trigger_reindex()

    return {
        "status": "completed",
        "action": "delete",
        "skill_id": skill_id,
        **git_result,
        "reindexed": reindex_result.get("success", False),
    }


async def _reindex_skills(force: bool) -> dict[str, Any]:
    """Reindex all skills."""
    indexing_engine = get_indexing_engine()

    try:
        stats = indexing_engine.reindex_all(force=force)
        return {
            "status": "completed",
            "action": "reindex",
            "indexed_count": stats.total_skills,
            "vector_store_size": stats.vector_store_size,
            "graph_nodes": stats.graph_nodes,
            "graph_edges": stats.graph_edges,
            "last_indexed": stats.last_indexed,
            "forced": force,
        }
    except Exception as e:
        logger.exception(f"Reindex failed: {e}")
        return {"status": "error", "message": f"Reindex failed: {e}"}


async def _git_commit_and_push(
    repo_path: Path,
    files: list[str],
    commit_message: str,
    action: str,
    skill_id: str,
    delete: bool = False,
) -> dict[str, Any]:
    """Commit and push changes with authorization check."""
    authorized = is_authorized_pusher()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    try:
        # Change to repo directory
        cwd = str(repo_path)

        if authorized:
            # Direct push to main
            if delete:
                for f in files:
                    subprocess.run(
                        ["git", "rm", f], cwd=cwd, check=True, capture_output=True
                    )
            else:
                subprocess.run(
                    ["git", "add"] + files, cwd=cwd, check=True, capture_output=True
                )

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=cwd,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=cwd,
                check=True,
                capture_output=True,
            )

            # Get commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            commit_hash = result.stdout.strip()[:8]

            return {
                "git_status": "pushed",
                "branch": "main",
                "commit": commit_hash,
                "user": get_git_user(),
            }
        else:
            # Create branch and PR
            branch = f"skill/{action}-{skill_id}-{timestamp}"

            subprocess.run(
                ["git", "checkout", "-b", branch],
                cwd=cwd,
                check=True,
                capture_output=True,
            )

            if delete:
                for f in files:
                    subprocess.run(
                        ["git", "rm", f], cwd=cwd, check=True, capture_output=True
                    )
            else:
                subprocess.run(
                    ["git", "add"] + files, cwd=cwd, check=True, capture_output=True
                )

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=cwd,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "push", "-u", "origin", branch],
                cwd=cwd,
                check=True,
                capture_output=True,
            )

            # Create PR using gh CLI
            pr_result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "create",
                    "--title",
                    commit_message,
                    "--body",
                    f"Automated {action} for skill: {skill_id}\n\nGenerated by mcp-skillset",
                    "--repo",
                    SKILLS_REPO,
                ],
                cwd=cwd,
                capture_output=True,
                text=True,
            )

            pr_url = pr_result.stdout.strip() if pr_result.returncode == 0 else None

            # Return to main
            subprocess.run(["git", "checkout", "main"], cwd=cwd, capture_output=True)

            return {
                "git_status": "pr_created",
                "branch": branch,
                "pr_url": pr_url,
                "user": get_git_user(),
            }

    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e.stderr if hasattr(e, 'stderr') else e}")
        return {
            "git_status": "error",
            "git_error": str(e),
        }


async def _trigger_reindex() -> dict[str, Any]:
    """Trigger reindex after write operations."""
    try:
        indexing_engine = get_indexing_engine()
        indexing_engine.reindex_all(force=True)
        return {"success": True}
    except Exception as e:
        logger.exception(f"Reindex trigger failed: {e}")
        return {"success": False, "error": str(e)}


def _update_frontmatter(
    content: str, description: str | None, tags: list[str] | None
) -> str:
    """Update YAML frontmatter in skill content."""
    # Parse frontmatter
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        return content

    frontmatter, body = match.groups()

    # Update fields
    if description:
        frontmatter = re.sub(
            r"^description:.*$",
            f"description: {description}",
            frontmatter,
            flags=re.MULTILINE,
        )

    if tags:
        tags_str = "\n".join(f"  - {tag}" for tag in tags)
        frontmatter = re.sub(
            r"^tags:.*?(?=^\w|\Z)",
            f"tags:\n{tags_str}\n",
            frontmatter,
            flags=re.MULTILINE | re.DOTALL,
        )

    return f"---\n{frontmatter}\n---\n{body}"


def _normalize_skill_id(name: str) -> str:
    """Normalize skill name to kebab-case.

    Args:
        name: Raw skill name

    Returns:
        Normalized skill ID (lowercase, hyphens)

    Examples:
        "FastAPI Testing" -> "fastapi-testing"
        "My Cool Skill!" -> "my-cool-skill"
    """
    # Convert to lowercase
    normalized = name.lower()

    # Replace spaces and special chars with hyphens
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)

    # Remove leading/trailing hyphens
    normalized = normalized.strip("-")

    # Remove consecutive hyphens
    normalized = re.sub(r"-+", "-", normalized)

    return normalized
