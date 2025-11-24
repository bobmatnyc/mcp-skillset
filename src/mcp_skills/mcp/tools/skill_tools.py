"""Skill management tools for MCP server.

This module implements MCP tools for skill discovery, search, and
recommendation using the FastMCP SDK.
"""

import logging
from pathlib import Path
from typing import Any

from ..server import (
    get_indexing_engine,
    get_skill_manager,
    get_toolchain_detector,
    mcp,
)


logger = logging.getLogger(__name__)


@mcp.tool()
async def search_skills(
    query: str,
    toolchain: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search for skills using hybrid RAG (70% vector + 30% knowledge graph).

    Searches skill repository using semantic similarity (ChromaDB) combined
    with knowledge graph relationships (NetworkX). This hybrid approach
    provides both fuzzy natural language matching and explicit dependency
    relationships.

    Search Strategy:
    - 70% Vector Search: Semantic similarity via embeddings
    - 30% Knowledge Graph: Structural relationships and dependencies
    - Filters: Optional toolchain, category, and tag filtering

    Common Use Cases:
    - Natural language: "testing tools for python"
    - Category-specific: "security" with category="security"
    - Toolchain-specific: "deployment" with toolchain="typescript"

    Args:
        query: Natural language search query (e.g., "pytest testing patterns")
        toolchain: Filter by toolchain (e.g., "python", "typescript", "rust")
        category: Filter by category (e.g., "testing", "deployment", "security")
        tags: Filter by tags (skills must have all specified tags)
        limit: Maximum number of results (default: 10, max: 50)

    Returns:
        Dictionary containing:
        - status: "completed" or "error"
        - skills: List of matching skills with metadata
        - count: Number of results returned
        - search_method: "hybrid_rag_70_30"
        - filters_applied: Dict of applied filters
        - error: Error message (if failed)

    Example:
        >>> search_skills("pytest testing", toolchain="python", limit=5)
        {
            "status": "completed",
            "skills": [
                {
                    "id": "pytest-skill",
                    "name": "pytest",
                    "description": "Professional pytest testing",
                    "score": 0.92,
                    "category": "testing",
                    "tags": ["python", "pytest", "tdd"]
                }
            ],
            "count": 5,
            "search_method": "hybrid_rag_70_30"
        }

    """
    try:
        engine = get_indexing_engine()

        # Build filters
        filters = {}
        if toolchain:
            filters["toolchain"] = toolchain
        if category:
            filters["category"] = category
        if tags:
            filters["tags"] = tags

        # Cap limit at 50
        limit = min(limit, 50)

        # Perform hybrid search (search is async in IndexingEngine)
        results = engine.search(
            query=query,
            toolchain=toolchain,
            category=category,
            top_k=limit,
        )

        # Convert ScoredSkill objects to dicts
        skills_data = []
        for scored_skill in results:
            skill_dict = {
                "id": scored_skill.skill.id,
                "name": scored_skill.skill.name,
                "description": scored_skill.skill.description,
                "category": scored_skill.skill.category,
                "tags": scored_skill.skill.tags,
                "score": round(scored_skill.score, 3),
                "match_type": scored_skill.match_type,
            }

            # Apply tags filter if specified (post-filter)
            if tags:
                skill_tags_set = set(scored_skill.skill.tags)
                if not all(tag in skill_tags_set for tag in tags):
                    continue

            skills_data.append(skill_dict)

        return {
            "status": "completed",
            "skills": skills_data,
            "count": len(skills_data),
            "search_method": "hybrid_rag_70_30",
            "filters_applied": filters,
        }
    except Exception as e:
        logger.error(f"Failed to search skills: {e}")
        return {
            "status": "error",
            "error": f"Failed to search skills: {str(e)}",
        }


@mcp.tool()
async def get_skill(skill_id: str) -> dict[str, Any]:
    """Get complete skill details including instructions.

    Retrieves full skill data from the skill manager's cache or loads
    from disk if not cached. Returns all skill metadata plus complete
    instruction text in markdown format.

    Args:
        skill_id: Unique skill identifier (e.g., "pytest-skill")

    Returns:
        Dictionary containing:
        - status: "completed" or "error"
        - skill: Complete skill object with all fields
        - source: "cache" or "disk" indicating data source
        - error: Error message (if failed)

    Example:
        >>> get_skill("pytest-skill")
        {
            "status": "completed",
            "skill": {
                "id": "pytest-skill",
                "name": "pytest",
                "description": "Professional pytest testing",
                "instructions": "# Pytest Skill\n\n...",
                "category": "testing",
                "tags": ["python", "pytest", "tdd"],
                "dependencies": [],
                "examples": ["..."],
                "file_path": "/path/to/pytest/SKILL.md",
                "repo_id": "anthropics-skills"
            },
            "source": "cache"
        }

    """
    try:
        skill_manager = get_skill_manager()

        # Load skill (handles caching internally)
        skill = skill_manager.load_skill(skill_id)

        if not skill:
            return {
                "status": "error",
                "error": f"Skill not found: {skill_id}",
            }

        skill_dict = {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "instructions": skill.instructions,
            "examples": skill.examples,
            "category": skill.category,
            "tags": skill.tags,
            "dependencies": skill.dependencies,
            "version": skill.version,
            "author": skill.author,
            "file_path": str(skill.file_path),
            "repo_id": skill.repo_id,
        }

        return {
            "status": "completed",
            "skill": skill_dict,
            "source": "cache" if skill_id in skill_manager._skill_cache else "disk",
        }
    except Exception as e:
        logger.error(f"Failed to get skill: {e}")
        return {
            "status": "error",
            "error": f"Failed to get skill: {str(e)}",
        }


@mcp.tool()
async def recommend_skills(
    current_skill: str | None = None,
    project_path: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Recommend skills based on current context.

    Provides skill recommendations using two strategies:

    1. Project-Based Recommendations (if project_path provided):
       - Uses ToolchainDetector to analyze project structure
       - Recommends skills matching detected toolchains
       - Sorted by relevance to detected patterns

    2. Skill-Based Recommendations (if current_skill provided):
       - Uses knowledge graph to find related skills
       - Considers: dependencies, same category, shared tags
       - Ranked by relationship strength

    At least one of current_skill or project_path must be provided.

    Args:
        current_skill: Base skill ID for recommendations (e.g., "pytest-skill")
        project_path: Project directory path for toolchain detection
        limit: Maximum recommendations (default: 5, max: 20)

    Returns:
        Dictionary containing:
        - status: "completed" or "error"
        - recommendations: List of recommended skills with confidence scores
        - recommendation_type: "project_based" or "skill_based"
        - context: Additional context (detected toolchains or relationships)
        - error: Error message (if failed)

    Example:
        >>> recommend_skills(project_path="/path/to/python/project", limit=5)
        {
            "status": "completed",
            "recommendations": [
                {
                    "id": "pytest-skill",
                    "name": "pytest",
                    "confidence": 0.95,
                    "reason": "Python project with test directory detected"
                }
            ],
            "recommendation_type": "project_based",
            "context": {
                "detected_toolchains": ["python"],
                "detected_patterns": ["testing"]
            }
        }

    """
    try:
        # Validate inputs
        if not current_skill and not project_path:
            return {
                "status": "error",
                "error": "Either current_skill or project_path must be provided",
            }

        # Cap limit at 20
        limit = min(limit, 20)

        # Project-based recommendations
        if project_path:
            detector = get_toolchain_detector()
            engine = get_indexing_engine()

            # Detect toolchains
            project_dir = Path(project_path)
            if not project_dir.exists():
                return {
                    "status": "error",
                    "error": f"Project path does not exist: {project_path}",
                }

            toolchain_info = detector.detect(project_dir)
            if toolchain_info.primary_language == "Unknown":
                return {
                    "status": "completed",
                    "recommendations": [],
                    "recommendation_type": "project_based",
                    "context": {"message": "No toolchains detected in project"},
                }

            # Build query from detected toolchains
            all_languages = [
                toolchain_info.primary_language
            ] + toolchain_info.secondary_languages
            frameworks = toolchain_info.frameworks or []
            query = " ".join(all_languages + frameworks)

            results = engine.search(
                query=query,
                toolchain=toolchain_info.primary_language,
                top_k=limit,
            )

            recommendations = []
            for scored_skill in results:
                recommendations.append(
                    {
                        "id": scored_skill.skill.id,
                        "name": scored_skill.skill.name,
                        "description": scored_skill.skill.description,
                        "confidence": round(scored_skill.score, 3),
                        "reason": f"Matches detected toolchain: {', '.join(all_languages)}",
                        "category": scored_skill.skill.category,
                        "tags": scored_skill.skill.tags,
                    }
                )

            return {
                "status": "completed",
                "recommendations": recommendations,
                "recommendation_type": "project_based",
                "context": {
                    "detected_toolchains": all_languages,
                    "detected_frameworks": frameworks,
                    "confidence": toolchain_info.confidence,
                },
            }

        # Skill-based recommendations (current_skill provided)
        engine = get_indexing_engine()
        skill_manager = get_skill_manager()

        # Get current skill
        base_skill = skill_manager.load_skill(current_skill)
        if not base_skill:
            return {
                "status": "error",
                "error": f"Current skill not found: {current_skill}",
            }

        # Use knowledge graph to find related skills
        related_skills = engine.get_related_skills(skill_id=current_skill, max_depth=2)

        recommendations = []
        for skill in related_skills[:limit]:
            recommendations.append(
                {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "confidence": 0.80,  # Fixed confidence for graph-based recommendations
                    "reason": "Related via knowledge graph",
                    "category": skill.category,
                    "tags": skill.tags,
                }
            )

        return {
            "status": "completed",
            "recommendations": recommendations,
            "recommendation_type": "skill_based",
            "context": {
                "base_skill": current_skill,
                "related_count": len(related_skills),
            },
        }
    except Exception as e:
        logger.error(f"Failed to recommend skills: {e}")
        return {
            "status": "error",
            "error": f"Failed to recommend skills: {str(e)}",
        }


@mcp.tool()
async def list_categories() -> dict[str, Any]:
    """List all available skill categories.

    Returns all predefined skill categories along with skill counts
    for each category. Categories are used to organize skills by
    their primary purpose (testing, deployment, security, etc.).

    Returns:
        Dictionary containing:
        - status: "completed" or "error"
        - categories: List of category objects with names and counts
        - total_categories: Total number of categories
        - error: Error message (if failed)

    Example:
        >>> list_categories()
        {
            "status": "completed",
            "categories": [
                {"name": "testing", "count": 15},
                {"name": "deployment", "count": 8},
                {"name": "security", "count": 6}
            ],
            "total_categories": 11
        }

    """
    try:
        skill_manager = get_skill_manager()

        # Get all skills to count by category
        all_skills = skill_manager.discover_skills()

        # Count skills per category
        category_counts: dict[str, int] = {}
        for skill in all_skills:
            category = skill.category
            category_counts[category] = category_counts.get(category, 0) + 1

        # Build category list
        categories = [
            {"name": category, "count": count}
            for category, count in sorted(category_counts.items())
        ]

        return {
            "status": "completed",
            "categories": categories,
            "total_categories": len(categories),
        }
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        return {
            "status": "error",
            "error": f"Failed to list categories: {str(e)}",
        }


@mcp.tool()
async def reindex_skills(force: bool = False) -> dict[str, Any]:
    """Rebuild skill index (ChromaDB + NetworkX knowledge graph).

    Rebuilds the hybrid search index by:
    1. Discovering all skills from repositories
    2. Generating embeddings for vector search (ChromaDB)
    3. Building knowledge graph for relationship search (NetworkX)

    The indexing process is incremental by default - only updates
    changed skills. Use force=True to rebuild from scratch.

    Args:
        force: Force full reindex even if up-to-date (default: False)

    Returns:
        Dictionary containing:
        - status: "completed" or "error"
        - indexed_count: Number of skills indexed
        - vector_store_size: Size of vector store in bytes
        - graph_nodes: Number of nodes in knowledge graph
        - graph_edges: Number of edges in knowledge graph
        - duration_seconds: Time taken to reindex
        - error: Error message (if failed)

    Example:
        >>> reindex_skills(force=True)
        {
            "status": "completed",
            "indexed_count": 42,
            "vector_store_size": 1048576,
            "graph_nodes": 42,
            "graph_edges": 15,
            "duration_seconds": 2.5
        }

    """
    try:
        import time

        start_time = time.time()

        engine = get_indexing_engine()

        # Reindex all skills (discovers skills internally)
        stats = engine.reindex_all(force=force)

        duration = time.time() - start_time

        return {
            "status": "completed",
            "indexed_count": stats.total_skills,
            "vector_store_size": stats.vector_store_size,
            "graph_nodes": stats.graph_nodes,
            "graph_edges": stats.graph_edges,
            "last_indexed": stats.last_indexed,
            "duration_seconds": round(duration, 2),
            "forced": force,
        }
    except Exception as e:
        logger.error(f"Failed to reindex skills: {e}")
        return {
            "status": "error",
            "error": f"Failed to reindex skills: {str(e)}",
        }
