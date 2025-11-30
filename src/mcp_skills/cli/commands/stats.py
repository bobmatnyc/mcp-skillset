"""Command: stats - Display usage statistics."""

from __future__ import annotations

import logging

import click
from rich.table import Table

from mcp_skills.cli.shared.console import console
from mcp_skills.services.indexing.engine import IndexingEngine
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager


logger = logging.getLogger(__name__)


@click.command()
def stats() -> None:
    """Show usage statistics.

    Displays comprehensive statistics about the mcp-skillset system including:
    - Index metrics (total skills, vector store size, knowledge graph)
    - Repository information (count, skills available, last updated)
    - Detailed repository breakdown with priorities

    This command provides visibility into the current state of your skill
    repository ecosystem and indexing status.

    Examples:
        mcp-skillset stats
    """
    console.print("📊 [bold]Usage Statistics[/bold]\n")

    try:
        # Get index statistics
        skill_manager = SkillManager()
        indexing_engine = IndexingEngine(skill_manager=skill_manager)
        index_stats = indexing_engine.get_stats()

        # Get repository statistics
        repo_manager = RepositoryManager()
        repos = repo_manager.list_repositories()

        # Create statistics table
        table = Table(title="System Statistics", show_header=False)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="bold")

        # Index metrics
        table.add_row("Total Skills Indexed", str(index_stats.total_skills))
        table.add_row(
            "Vector Store Size", f"{index_stats.vector_store_size // 1024} KB"
        )
        table.add_row("Graph Nodes", str(index_stats.graph_nodes))
        table.add_row("Graph Edges", str(index_stats.graph_edges))

        if index_stats.last_indexed != "never":
            table.add_row("Last Indexed", index_stats.last_indexed)
        else:
            table.add_row("Last Indexed", "[yellow]Never[/yellow]")

        # Repository metrics
        table.add_row("", "")  # Separator
        table.add_row("Repositories", str(len(repos)))

        if repos:
            total_skills = sum(repo.skill_count for repo in repos)
            table.add_row("Total Skills Available", str(total_skills))

            # Repository breakdown
            console.print(table)
            console.print()

            # Repositories details
            repo_table = Table(title="Repository Details")
            repo_table.add_column("Repository", style="cyan")
            repo_table.add_column("Priority", justify="right", style="magenta")
            repo_table.add_column("Skills", justify="right", style="green")
            repo_table.add_column("Last Updated", style="dim")

            for repo in sorted(repos, key=lambda r: r.priority, reverse=True):
                repo_table.add_row(
                    repo.id,
                    str(repo.priority),
                    str(repo.skill_count),
                    repo.last_updated.strftime("%Y-%m-%d %H:%M"),
                )

            console.print(repo_table)
        else:
            console.print(table)
            console.print("\n[yellow]No repositories configured[/yellow]")

    except Exception as e:
        console.print(f"[red]Stats failed: {e}[/red]")
        logger.exception("Stats failed")
        raise SystemExit(1)
