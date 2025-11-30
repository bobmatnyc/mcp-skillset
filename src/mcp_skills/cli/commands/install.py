"""
Install command implementation.
"""

import logging

import click
from rich.console import Console

from mcp_skills.services.agent_detector import AgentDetector
from mcp_skills.services.agent_installer import AgentInstaller


console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--agent",
    type=click.Choice(["claude-desktop", "claude-code", "auggie", "all"]),
    default="all",
    help="Which agent to install for (default: claude-code and auggie, excludes claude-desktop)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be installed without making changes",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing mcp-skillset configuration",
)
def install(agent: str, dry_run: bool, force: bool) -> None:
    """Install MCP SkillSet for AI agents with auto-detection.

    Automatically detects installed AI agents (Claude Code, Auggie) and configures
    them to use mcp-skillset as an MCP server. Claude Desktop is excluded by default
    due to config path conflicts with Claude Code.

    The command will:
    1. Scan for installed AI agents on your system
    2. Backup existing configuration files
    3. Add mcp-skillset to the agent's MCP server configuration
    4. Validate the changes

    Use --dry-run to preview changes without modifying files.
    Use --force to overwrite existing mcp-skillset configuration.

    Examples:
        mcp-skillset install                         # Install for Claude Code and Auggie (default)
        mcp-skillset install --agent claude-desktop  # Install for Claude Desktop explicitly
        mcp-skillset install --dry-run               # Preview changes
        mcp-skillset install --force                 # Overwrite existing config
    """
    console.print("🔍 [bold green]MCP SkillSet Agent Installer[/bold green]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    try:
        # Detect agents
        console.print("[bold cyan]Step 1/3:[/bold cyan] Detecting AI agents...")
        detector = AgentDetector()

        if agent == "all":
            # Default behavior: exclude Claude Desktop (config path conflicts with Claude Code)
            # Users can explicitly use --agent claude-desktop if needed
            all_agents = detector.detect_all()
            detected_agents = [a for a in all_agents if a.id != "claude-desktop"]
        else:
            single_agent = detector.detect_agent(agent)
            detected_agents = [single_agent] if single_agent else []

        if not detected_agents:
            console.print(f"[red]No agents found for: {agent}[/red]")
            console.print("\nSupported agents:")
            console.print("  • Claude Desktop - https://claude.ai/download")
            console.print(
                "  • Claude Code (VS Code) - Install from VS Code marketplace"
            )
            console.print("  • Auggie - https://auggie.app")
            return

        # Display detected agents
        found_agents = [a for a in detected_agents if a.exists]
        not_found = [a for a in detected_agents if not a.exists]

        if found_agents:
            console.print(f"\n[green]✓[/green] Found {len(found_agents)} agent(s):")
            for a in found_agents:
                console.print(f"  • {a.name}: {a.config_path}")
        else:
            console.print("\n[yellow]No installed agents found[/yellow]")

        if not_found:
            console.print(f"\n[dim]Not found ({len(not_found)}):[/dim]")
            for a in not_found:
                console.print(f"  • {a.name}")

        if not found_agents:
            console.print(
                "\nPlease install an AI agent first, then run this command again."
            )
            return

        console.print()

        # Confirmation (unless --force or --dry-run)
        if (
            not force
            and not dry_run
            and not click.confirm(
                f"Install mcp-skillset for {len(found_agents)} agent(s)?",
                default=True,
            )
        ):
            console.print("[yellow]Installation cancelled[/yellow]")
            return

        # Install for each agent
        console.print("[bold cyan]Step 2/3:[/bold cyan] Installing mcp-skillset...")
        installer = AgentInstaller()
        results = []

        for detected_agent in found_agents:
            result = installer.install(detected_agent, force=force, dry_run=dry_run)
            results.append(result)

            if result.success:
                console.print(f"  [green]✓[/green] {result.agent_name}")
                if result.backup_path:
                    console.print(f"    [dim]Backup: {result.backup_path}[/dim]")
                if result.changes_made and not dry_run:
                    console.print(f"    [dim]{result.changes_made}[/dim]")
            else:
                console.print(f"  [red]✗[/red] {result.agent_name}: {result.error}")

        console.print()

        # Summary
        console.print("[bold cyan]Step 3/3:[/bold cyan] Summary")
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if successful:
            console.print(
                f"  [green]✓[/green] Successfully installed for {len(successful)} agent(s)"
            )

        if failed:
            console.print(f"  [red]✗[/red] Failed for {len(failed)} agent(s)")

        console.print()

        # Next steps
        if successful and not dry_run:
            console.print("[bold green]✓ Installation complete![/bold green]\n")
            console.print("Next steps:")
            console.print("  1. Restart your AI agent to load the new configuration")
            console.print("  2. The agent will automatically connect to mcp-skillset")
            console.print("  3. Skills will be available through MCP tools\n")
            console.print(
                "[dim]Note: If using Claude Desktop, quit and restart the app completely.[/dim]"
            )
        elif dry_run:
            console.print("[yellow]Dry run complete - no changes were made[/yellow]\n")
            console.print("Run without --dry-run to apply these changes.")

    except KeyboardInterrupt:
        console.print("\n[yellow]Installation cancelled by user[/yellow]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"\n[red]Installation failed: {e}[/red]")
        logger.exception("Installation failed")
        raise SystemExit(1)
