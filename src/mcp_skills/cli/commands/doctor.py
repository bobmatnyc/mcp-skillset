"""Command: doctor - Check system health and status."""

from __future__ import annotations

import click

from mcp_skills.cli.shared.console import console
from mcp_skills.services.indexing.engine import IndexingEngine
from mcp_skills.services.py_mcp_installer_wrapper import (
    MCPInspector,
    Platform,
    PlatformDetector,
)
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager


def _run_mcp_diagnostics() -> bool:
    """Run MCP platform diagnostics.

    Returns:
        True if all platforms healthy, False if issues found
    """
    console.print("[bold cyan]MCP Platform Diagnostics:[/bold cyan]")

    try:
        # Detect all platforms
        detector = PlatformDetector()
        platforms = detector.detect_all()

        # Filter platforms with sufficient confidence
        detected_platforms = [p for p in platforms if p.confidence > 0.5]

        if not detected_platforms:
            console.print(
                "  [yellow]⚠[/yellow] No MCP platforms detected (confidence > 0.5)"
            )
            console.print("    Run: mcp-skillset install --agent <platform>")
            return False

        console.print(f"  Detected {len(detected_platforms)} platform(s):\n")

        all_healthy = True

        for platform_info in detected_platforms:
            # Display platform header
            platform_name = platform_info.platform.value.replace("_", " ").title()
            console.print(
                f"    [green]✓[/green] {platform_name} "
                f"(confidence: {platform_info.confidence:.2f})"
            )

            # Display config path
            if platform_info.config_path:
                console.print(f"      Config: {platform_info.config_path}")
            else:
                console.print("      [yellow]Config: Not found[/yellow]")
                all_healthy = False

            # Inspect platform
            try:
                inspector = MCPInspector(platform_info)
                report = inspector.inspect()

                # Display server counts
                console.print(
                    f"      Servers: {report.total_servers} configured, "
                    f"{report.valid_servers} valid"
                )

                # Display issues
                errors = [
                    issue for issue in report.issues if issue.severity == "error"
                ]
                warnings = [
                    issue for issue in report.issues if issue.severity == "warning"
                ]

                if errors:
                    console.print(f"      [red]✗[/red] {len(errors)} error(s):")
                    for issue in errors[:3]:  # Show first 3 errors
                        console.print(f"        • {issue.message}")
                    if len(errors) > 3:
                        console.print(f"        • ... and {len(errors) - 3} more")
                    all_healthy = False

                if warnings:
                    console.print(f"      [yellow]⚠[/yellow] {len(warnings)} warning(s):")
                    for issue in warnings[:3]:  # Show first 3 warnings
                        console.print(f"        • {issue.message}")
                    if len(warnings) > 3:
                        console.print(f"        • ... and {len(warnings) - 3} more")

                # Display recommendations
                if report.recommendations:
                    console.print("      Recommendations:")
                    for rec in report.recommendations[:2]:  # Show first 2
                        console.print(f"        • {rec}")
                    if len(report.recommendations) > 2:
                        console.print(
                            f"        • ... and {len(report.recommendations) - 2} more"
                        )

            except Exception as e:
                console.print(f"      [red]✗[/red] Inspection failed: {e}")
                all_healthy = False

            console.print()  # Blank line between platforms

        return all_healthy

    except Exception as e:
        console.print(f"  [red]✗[/red] MCP diagnostics failed: {e}")
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("MCP diagnostics failed")
        return False


@click.command(name="doctor")
@click.option("--mcp-only", is_flag=True, help="Only run MCP platform diagnostics")
@click.option(
    "--full",
    is_flag=True,
    help="Run comprehensive diagnostics including MCP inspection",
)
def doctor(mcp_only: bool, full: bool) -> None:
    """Check system health and status.

    Diagnoses the health of your MCP Skills installation, including:
    - ChromaDB vector store connectivity
    - Knowledge graph status
    - Repository configuration
    - Skill index status
    - MCP platform diagnostics (with --full or --mcp-only)

    Examples:
        mcp-skillset doctor              # Standard health checks
        mcp-skillset doctor --mcp-only   # Only MCP platform checks
        mcp-skillset doctor --full       # All checks including MCP
    """
    console.print("🏥 [bold]System Health Check[/bold]\n")

    all_healthy = True

    # Handle --mcp-only flag
    if mcp_only:
        mcp_healthy = _run_mcp_diagnostics()
        console.print()
        if mcp_healthy:
            console.print("[bold green]✓ All MCP platforms healthy[/bold green]")
        else:
            console.print(
                "[bold yellow]⚠ Some MCP platforms need attention[/bold yellow]"
            )
        return

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

        # 5. Optional MCP platform diagnostics (if --full flag)
        if full:
            mcp_healthy = _run_mcp_diagnostics()
            all_healthy = all_healthy and mcp_healthy
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
