"""Command: mcp - Start MCP server for Claude Code integration."""

from __future__ import annotations

import click

from mcp_skills.cli.shared.console import console


@click.command(name="mcp")
@click.option("--dev", is_flag=True, help="Development mode")
def mcp(dev: bool) -> None:
    """Start MCP server for Claude Code integration.

    Starts the FastMCP server using stdio transport, making skills
    available to Claude Code via Model Context Protocol.

    Usage:
        mcp-skillset mcp

    The server will run in stdio mode and communicate with Claude Code.
    """
    console.print("🚀 [bold green]Starting MCP server for Claude Code...[/bold green]")
    console.print("📡 stdio transport")

    if dev:
        console.print("🔧 [yellow]Development mode enabled[/yellow]")

    # Import and configure MCP server
    from mcp_skills.mcp.server import configure_services
    from mcp_skills.mcp.server import main as mcp_main

    try:
        # Initialize services (SkillManager, IndexingEngine, ToolchainDetector, RepositoryManager)
        console.print("⚙️  Configuring services...")
        configure_services()

        console.print("✅ Services configured")
        console.print("📡 stdio transport active")
        console.print("🎯 Ready for Claude Code connection\n")

        # Start FastMCP server (blocks until terminated)
        mcp_main()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Server stopped by user[/yellow]")
        raise SystemExit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Server failed to start: {e}[/red]")
        import traceback

        if dev:
            traceback.print_exc()
        raise SystemExit(1)
