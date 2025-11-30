"""Command: doctor - Check system health and status."""

from __future__ import annotations

import click

from mcp_skills.cli.shared.console import console
from mcp_skills.services.indexing.engine import IndexingEngine
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager


@click.command(name="doctor")
def doctor() -> None:
    """Check system health and status.

    Diagnoses the health of your MCP Skills installation, including:
    - ChromaDB vector store connectivity
    - Knowledge graph status
    - Repository configuration
    - Skill index status

    Examples:
        mcp-skillset doctor
    """
    console.print("🏥 [bold]System Health Check[/bold]\n")

    all_healthy = True

    try:
        # 1. Check ChromaDB connection
        console.print("[bold cyan]ChromaDB Vector Store:[/bold cyan]")
        try:
            skill_manager = SkillManager()
            indexing_engine = IndexingEngine(skill_manager=skill_manager)
            stats = indexing_engine.get_stats()

            if stats.total_skills > 0:
                console.print(
                    f"  [green]✓[/green] Connected ({stats.total_skills} skills indexed)"
                )
                console.print(
                    f"  [green]✓[/green] Storage: {stats.vector_store_size // 1024} KB"
                )
            else:
                console.print(
                    "  [yellow]⚠[/yellow] Connected but empty (run: mcp-skillset index)"
                )
                all_healthy = False
        except Exception as e:
            console.print(f"  [red]✗[/red] Connection failed: {e}")
            all_healthy = False

        console.print()

        # 2. Check knowledge graph
        console.print("[bold cyan]Knowledge Graph:[/bold cyan]")
        try:
            if stats.graph_nodes > 0:
                console.print(
                    f"  [green]✓[/green] {stats.graph_nodes} nodes, {stats.graph_edges} edges"
                )
            else:
                console.print(
                    "  [yellow]⚠[/yellow] Empty graph (run: mcp-skillset index)"
                )
                all_healthy = False
        except Exception as e:
            console.print(f"  [red]✗[/red] Graph check failed: {e}")
            all_healthy = False

        console.print()

        # 3. Check repository status
        console.print("[bold cyan]Repositories:[/bold cyan]")
        try:
            repo_manager = RepositoryManager()
            repos = repo_manager.list_repositories()

            if repos:
                console.print(
                    f"  [green]✓[/green] {len(repos)} repositories configured"
                )
                total_skills = sum(repo.skill_count for repo in repos)
                console.print(
                    f"  [green]✓[/green] {total_skills} total skills available"
                )
            else:
                console.print(
                    "  [yellow]⚠[/yellow] No repositories configured (run: mcp-skillset setup)"
                )
                all_healthy = False
        except Exception as e:
            console.print(f"  [red]✗[/red] Repository check failed: {e}")
            all_healthy = False

        console.print()

        # 4. Check skill index status
        console.print("[bold cyan]Skill Index:[/bold cyan]")
        try:
            skills = skill_manager.discover_skills()

            if skills:
                console.print(f"  [green]✓[/green] {len(skills)} skills discovered")
                if stats.last_indexed != "never":
                    console.print(
                        f"  [green]✓[/green] Last indexed: {stats.last_indexed}"
                    )
                else:
                    console.print(
                        "  [yellow]⚠[/yellow] Never indexed (run: mcp-skillset index)"
                    )
                    all_healthy = False
            else:
                console.print("  [yellow]⚠[/yellow] No skills discovered")
                all_healthy = False
        except Exception as e:
            console.print(f"  [red]✗[/red] Index check failed: {e}")
            all_healthy = False

        console.print()

        # Summary
        if all_healthy:
            console.print("[bold green]✓ All systems healthy[/bold green]")
        else:
            console.print("[bold yellow]⚠ Some systems need attention[/bold yellow]")
            console.print("\nRecommended actions:")
            console.print("  • Run: mcp-skillset setup")
            console.print("  • Run: mcp-skillset index --force")

    except Exception as e:
        console.print(f"\n[red]Health check failed: {e}[/red]")
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Health check failed")
        raise SystemExit(1)


@click.command(name="health", hidden=True)
def health() -> None:
    """Check system health and status (deprecated: use 'doctor' instead)."""
    console.print(
        "[yellow]Warning: 'health' is deprecated, use 'doctor' instead[/yellow]\n"
    )
    # Invoke the doctor command directly
    ctx = click.get_current_context()
    ctx.invoke(doctor)
