"""Command: recommend - Get skill recommendations for current project."""

from __future__ import annotations

from pathlib import Path

import click
from rich.table import Table

from mcp_skills.cli.shared.console import console
from mcp_skills.models.config import MCPSkillsConfig
from mcp_skills.services.indexing.engine import IndexingEngine
from mcp_skills.services.skill_manager import SkillManager
from mcp_skills.services.toolchain_detector import ToolchainDetector


@click.command()
@click.option(
    "--search-mode",
    type=click.Choice(
        ["semantic_focused", "graph_focused", "balanced", "current"],
        case_sensitive=False,
    ),
    help="Hybrid search weighting preset (overrides config file)",
)
def recommend(search_mode: str | None) -> None:
    """Get skill recommendations for current project.

    Analyzes the current directory's toolchain (language, frameworks, tools)
    and recommends relevant skills from the skill repository.

    Search Modes:
      - semantic_focused: Optimize for semantic similarity (90% vector, 10% graph)
      - graph_focused: Optimize for relationships (30% vector, 70% graph)
      - balanced: Equal weighting (50% vector, 50% graph)
      - current: Default optimized preset (70% vector, 30% graph)

    If --search-mode is not specified, loads from config.yaml or uses default.

    Examples:
        mcp-skillset recommend
        mcp-skillset recommend --search-mode semantic_focused
    """
    console.print("💡 [bold]Skill Recommendations[/bold]")
    if search_mode:
        console.print(f"⚖️  [dim]Search mode: {search_mode}[/dim]")
    console.print()

    try:
        # Detect current directory toolchain
        detector = ToolchainDetector()
        current_dir = Path.cwd()
        toolchain = detector.detect(current_dir)

        # Display detected toolchain
        console.print("[bold cyan]Detected Toolchain:[/bold cyan]")
        console.print(f"  • Language: {toolchain.primary_language}")
        if toolchain.frameworks:
            console.print(f"  • Frameworks: {', '.join(toolchain.frameworks)}")
        if toolchain.test_frameworks:
            console.print(f"  • Testing: {', '.join(toolchain.test_frameworks)}")
        console.print(f"  • Confidence: {toolchain.confidence:.0%}\n")

        # Get recommendations with config
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

        # Build query from toolchain
        query_parts = [toolchain.primary_language]
        query_parts.extend(toolchain.frameworks[:2])  # Add top 2 frameworks
        query = " ".join(query_parts)

        # Search for relevant skills
        results = indexing_engine.search(query, top_k=10)

        if not results:
            console.print("[yellow]No recommendations available[/yellow]")
            console.print("\nTry:")
            console.print("  • Running: mcp-skillset setup")
            console.print("  • Adding repositories: mcp-skillset repo add <url>")
            console.print("  • Rebuilding index: mcp-skillset index --force")
            return

        # Display recommendations
        table = Table(title=f"Recommended Skills ({len(results)} found)")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Relevance", justify="right", style="green")
        table.add_column("Description", style="dim")

        for result in results:
            skill = result.skill
            relevance_str = f"{result.score:.2f}"

            # Truncate description
            desc = skill.description[:50]
            if len(skill.description) > 50:
                desc += "..."

            table.add_row(
                skill.name,
                skill.category,
                relevance_str,
                desc,
            )

        console.print(table)
        console.print("\n[dim]Use 'mcp-skillset info <skill-id>' for details[/dim]")

    except Exception as e:
        console.print(f"[red]Recommendations failed: {e}[/red]")
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Recommendations failed")
        raise SystemExit(1)
