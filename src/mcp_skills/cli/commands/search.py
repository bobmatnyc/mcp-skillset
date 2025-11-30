"""Command: search - Search for skills using natural language query."""

from __future__ import annotations

import click
from rich.table import Table

from mcp_skills.cli.shared.console import console
from mcp_skills.models.config import MCPSkillsConfig
from mcp_skills.services.indexing.engine import IndexingEngine
from mcp_skills.services.skill_manager import SkillManager


@click.command()
@click.argument("query")
@click.option("--limit", type=int, default=10, help="Maximum results")
@click.option("--category", type=str, help="Filter by category")
@click.option(
    "--search-mode",
    type=click.Choice(
        ["semantic_focused", "graph_focused", "balanced", "current"],
        case_sensitive=False,
    ),
    help="Hybrid search weighting preset (overrides config file)",
)
def search(
    query: str, limit: int, category: str | None, search_mode: str | None
) -> None:
    """Search for skills using natural language query.

    Uses hybrid search combining vector embeddings (semantic similarity)
    and knowledge graph (relationship similarity) to find relevant skills.

    Search Modes:
      - semantic_focused: Optimize for semantic similarity (90% vector, 10% graph)
      - graph_focused: Optimize for relationships (30% vector, 70% graph)
      - balanced: Equal weighting (50% vector, 50% graph)
      - current: Default optimized preset (70% vector, 30% graph)

    If --search-mode is not specified, loads from config.yaml or uses default.

    Examples:
        mcp-skillset search "testing skills for Python"
        mcp-skillset search "fastapi" --category testing
        mcp-skillset search "pytest" --limit 20 --search-mode semantic_focused
    """
    console.print(f"🔍 [bold]Searching for:[/bold] {query}")
    if category:
        console.print(f"📁 [dim]Category filter: {category}[/dim]")
    if search_mode:
        console.print(f"⚖️  [dim]Search mode: {search_mode}[/dim]")
    console.print()

    try:
        # Initialize services with config
        skill_manager = SkillManager()

        # Load config and optionally override with CLI flag
        config = MCPSkillsConfig()
        if search_mode:
            # Override config with CLI flag
            config.hybrid_search = config._get_preset(search_mode)
            console.print(
                f"[dim]Using {search_mode} preset: "
                f"vector={config.hybrid_search.vector_weight:.1f}, "
                f"graph={config.hybrid_search.graph_weight:.1f}[/dim]\n"
            )

        indexing_engine = IndexingEngine(skill_manager=skill_manager, config=config)

        # Perform search
        results = indexing_engine.search(query, category=category, top_k=limit)

        if not results:
            console.print("[yellow]No results found[/yellow]")
            console.print("\nTry:")
            console.print("  • Using different keywords")
            console.print("  • Removing category filter")
            console.print("  • Running: mcp-skillset index --force")
            return

        # Display results in table
        table = Table(title=f"Search Results ({len(results)} found)")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Score", justify="right", style="green")
        table.add_column("Tags", style="dim")

        for result in results:
            skill = result.skill
            score_str = f"{result.score:.2f}"
            tags_str = ", ".join(skill.tags[:3])  # Show first 3 tags
            if len(skill.tags) > 3:
                tags_str += f" +{len(skill.tags) - 3}"

            table.add_row(
                skill.name,
                skill.category,
                score_str,
                tags_str,
            )

        console.print(table)
        console.print("\n[dim]Use 'mcp-skillset info <skill-id>' for details[/dim]")

    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Search failed")
        raise SystemExit(1)
