"""Command: index - Rebuild skill indices (vector + knowledge graph)."""

from __future__ import annotations

import click
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mcp_skills.cli.shared.console import console
from mcp_skills.services.indexing.engine import IndexingEngine
from mcp_skills.services.skill_manager import SkillManager


@click.command()
@click.option("--incremental", is_flag=True, help="Index only new/changed skills")
@click.option("--force", is_flag=True, help="Force full reindex")
def index(incremental: bool, force: bool) -> None:
    """Rebuild skill indices (vector + knowledge graph).

    Creates or updates the search indices used for skill discovery.
    Includes both vector embeddings (semantic search) and knowledge
    graph (relationship search).

    By default, performs incremental indexing.
    Use --force for full reindex.

    Examples:
        mcp-skillset index
        mcp-skillset index --force
        mcp-skillset index --incremental
    """
    if force:
        console.print("🔨 [bold]Full reindex (forced)[/bold]\n")
    elif incremental:
        console.print("🔨 [bold]Incremental indexing[/bold]\n")
    else:
        console.print("🔨 [bold]Indexing skills...[/bold]\n")

    try:
        # Initialize services
        skill_manager = SkillManager()
        indexing_engine = IndexingEngine(skill_manager=skill_manager)

        # Perform indexing with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Building indices...", total=None)

            try:
                # Reindex (force=True clears existing indices first)
                stats = indexing_engine.reindex_all(force=force)
                progress.update(task, completed=True)

                # Display results
                console.print("[green]✓[/green] Indexing complete\n")

                # Statistics table
                table = Table(title="Indexing Statistics", show_header=False)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="bold")

                table.add_row("Skills Indexed", str(stats.total_skills))
                table.add_row(
                    "Vector Store Size", f"{stats.vector_store_size // 1024} KB"
                )
                table.add_row("Graph Nodes", str(stats.graph_nodes))
                table.add_row("Graph Edges", str(stats.graph_edges))
                table.add_row("Last Indexed", stats.last_indexed)

                console.print(table)

                if stats.total_skills == 0:
                    console.print("\n[yellow]No skills were indexed[/yellow]")
                    console.print("\nPossible reasons:")
                    console.print(
                        "  • No repositories configured (run: mcp-skillset setup)"
                    )
                    console.print("  • Repositories are empty")
                    console.print("  • No SKILL.md files found")

            except Exception as e:
                progress.stop()
                console.print(f"[red]✗ Indexing failed: {e}[/red]")
                import logging

                logger = logging.getLogger(__name__)
                logger.exception("Indexing failed")
                raise SystemExit(1)

    except Exception as e:
        console.print(f"[red]Indexing failed: {e}[/red]")
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Indexing failed")
        raise SystemExit(1)
