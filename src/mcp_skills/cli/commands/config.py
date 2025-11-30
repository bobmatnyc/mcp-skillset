"""Command: config - Manage mcp-skillset configuration."""

from __future__ import annotations

import logging
from pathlib import Path

import click
from rich.tree import Tree

from mcp_skills.cli.shared.console import console
from mcp_skills.services.indexing.engine import IndexingEngine
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager


logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--show",
    is_flag=True,
    help="Display current configuration (read-only)",
)
@click.option(
    "--set",
    "set_value",
    type=str,
    help="Set configuration value (format: key=value)",
)
def config(show: bool, set_value: str | None) -> None:
    """Configure mcp-skillset settings interactively.

    By default, opens an interactive menu for configuration management.
    Use --show to display current configuration in read-only mode.
    Use --set to change values non-interactively.

    The configuration system manages:
    - Base directory and data storage locations
    - Repository settings and priorities
    - Hybrid search parameters (vector vs. graph weights)
    - Agent installation preferences

    Examples:
        # Interactive menu (default)
        mcp-skillset config

        # Display configuration
        mcp-skillset config --show

        # Set configuration value
        mcp-skillset config --set base_dir=/custom/path
        mcp-skillset config --set search_mode=balanced
    """
    # Handle --set flag (non-interactive)
    if set_value:
        _handle_set_config(set_value)
        return

    # Handle --show flag (read-only display)
    if show:
        _display_configuration()
        return

    # Default: Interactive menu
    try:
        from mcp_skills.cli.config_menu import ConfigMenu

        menu = ConfigMenu()
        menu.run()

    except KeyboardInterrupt:
        console.print("\n[yellow]Configuration cancelled by user[/yellow]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"\n[red]Configuration failed: {e}[/red]")
        logger.exception("Configuration failed")
        raise SystemExit(1)


def _display_configuration() -> None:
    """Display current configuration (--show flag).

    This is the original config command behavior, preserved for
    backward compatibility. Shows a tree view of all configuration
    settings including directories, repositories, vector store, and
    knowledge graph statistics.
    """
    console.print("⚙️  [bold]Current Configuration[/bold]\n")

    try:
        from mcp_skills.models.config import MCPSkillsConfig

        config = MCPSkillsConfig()
        base_dir = config.base_dir

        # Create configuration tree
        tree = Tree("[bold cyan]mcp-skillset Configuration[/bold cyan]")

        # Base directory
        base_node = tree.add(f"📁 Base Directory: [yellow]{base_dir}[/yellow]")

        # Repositories
        repos_dir = config.repos_dir
        repos_node = base_node.add(f"📚 Repositories: [yellow]{repos_dir}[/yellow]")

        try:
            repo_manager = RepositoryManager()
            repos = repo_manager.list_repositories()

            if repos:
                for repo in sorted(repos, key=lambda r: r.priority, reverse=True):
                    repo_info = f"{repo.id} (priority: {repo.priority}, skills: {repo.skill_count})"
                    repos_node.add(f"[green]✓[/green] {repo_info}")
            else:
                repos_node.add("[dim]No repositories configured[/dim]")
        except Exception as e:
            repos_node.add(f"[red]Error loading repositories: {e}[/red]")

        # Vector store
        chromadb_dir = base_dir / "chromadb"
        vector_node = base_node.add(f"🔍 Vector Store: [yellow]{chromadb_dir}[/yellow]")

        try:
            skill_manager = SkillManager()
            indexing_engine = IndexingEngine(skill_manager=skill_manager)
            stats = indexing_engine.get_stats()

            if stats.total_skills > 0:
                vector_node.add(f"[green]✓[/green] {stats.total_skills} skills indexed")
                vector_node.add(
                    f"[green]✓[/green] Size: {stats.vector_store_size // 1024} KB"
                )
            else:
                vector_node.add("[dim]Empty (run: mcp-skillset index)[/dim]")
        except Exception as e:
            vector_node.add(f"[red]Error: {e}[/red]")

        # Knowledge graph
        graph_node = base_node.add("🕸️  Knowledge Graph")

        try:
            if stats.total_skills > 0 and stats.graph_nodes > 0:
                graph_node.add(f"[green]✓[/green] {stats.graph_nodes} nodes")
                graph_node.add(f"[green]✓[/green] {stats.graph_edges} edges")
            else:
                graph_node.add("[dim]Empty (run: mcp-skillset index)[/dim]")
        except Exception as e:
            graph_node.add(f"[red]Error: {e}[/red]")

        # Hybrid search settings
        search_node = base_node.add("⚖️  Hybrid Search")
        preset = config.hybrid_search.preset or "custom"
        search_node.add(f"[green]✓[/green] Mode: {preset}")
        search_node.add(
            f"[green]✓[/green] Vector weight: {config.hybrid_search.vector_weight:.1f}"
        )
        search_node.add(
            f"[green]✓[/green] Graph weight: {config.hybrid_search.graph_weight:.1f}"
        )

        # Metadata file
        metadata_file = base_dir / "repos.json"
        metadata_node = base_node.add(f"📄 Metadata: [yellow]{metadata_file}[/yellow]")

        if metadata_file.exists():
            metadata_node.add("[green]✓[/green] Exists")
        else:
            metadata_node.add("[dim]Not created yet[/dim]")

        console.print(tree)

        # Additional info
        console.print()
        console.print("[bold]Environment:[/bold]")
        console.print(f"  • Python: [cyan]{Path.home()}[/cyan]")
        console.print(f"  • Working directory: [cyan]{Path.cwd()}[/cyan]")

    except Exception as e:
        console.print(f"[red]Failed to display configuration: {e}[/red]")
        logger.exception("Config display failed")
        raise SystemExit(1)


def _handle_set_config(set_value: str) -> None:
    """Handle --set flag for non-interactive configuration changes.

    Args:
        set_value: Configuration key=value pair

    Supported keys:
        - base_dir: Base directory path for all data storage
        - search_mode: Search mode preset (semantic_focused, graph_focused, balanced, current)

    The configuration is saved to ~/.mcp-skillset/config.yaml and takes
    effect immediately for subsequent commands.
    """
    import yaml

    try:
        # Parse key=value
        if "=" not in set_value:
            console.print("[red]Invalid format. Use: key=value[/red]")
            console.print("\nExamples:")
            console.print("  --set base_dir=/custom/path")
            console.print("  --set search_mode=balanced")
            raise SystemExit(1)

        key, value = set_value.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Load existing config
        config_path = Path.home() / ".mcp-skillset" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        existing_config: dict = {}
        if config_path.exists():
            with open(config_path) as f:
                existing_config = yaml.safe_load(f) or {}

        # Handle different keys
        if key == "base_dir":
            base_path = Path(value).expanduser()
            base_path.mkdir(parents=True, exist_ok=True)
            existing_config["base_dir"] = str(base_path)
            console.print(f"[green]✓[/green] Base directory set to: {base_path}")

        elif key == "search_mode":
            from mcp_skills.models.config import MCPSkillsConfig

            # Validate preset
            try:
                preset_config = MCPSkillsConfig._get_preset(value)
                existing_config["hybrid_search"] = {
                    "preset": value,
                    "vector_weight": preset_config.vector_weight,
                    "graph_weight": preset_config.graph_weight,
                }
                console.print(
                    f"[green]✓[/green] Search mode set to: {value} "
                    f"(vector={preset_config.vector_weight:.1f}, "
                    f"graph={preset_config.graph_weight:.1f})"
                )
            except ValueError as e:
                console.print(f"[red]Invalid search mode: {e}[/red]")
                raise SystemExit(1)

        else:
            console.print(f"[red]Unknown configuration key: {key}[/red]")
            console.print("\nSupported keys:")
            console.print("  • base_dir - Base directory path")
            console.print("  • search_mode - Search mode preset")
            raise SystemExit(1)

        # Save updated config
        with open(config_path, "w") as f:
            yaml.dump(existing_config, f, default_flow_style=False, sort_keys=False)

        console.print(f"\n[dim]Configuration saved to {config_path}[/dim]")

    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Failed to set configuration: {e}[/red]")
        logger.exception("Config set failed")
        raise SystemExit(1)
