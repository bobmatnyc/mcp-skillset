"""
Setup command implementation.
"""

import builtins
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from mcp_skills.models.repository import Repository
from mcp_skills.services.agent_detector import AgentDetector
from mcp_skills.services.agent_installer import AgentInstaller
from mcp_skills.services.indexing import IndexingEngine
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager
from mcp_skills.services.toolchain_detector import ToolchainDetector


console = Console()
logger = logging.getLogger(__name__)

# Store builtin list to avoid shadowing in annotations
ListType = builtins.list


@click.command()
@click.option(
    "--project-dir",
    default=".",
    type=click.Path(exists=True),
    help="Project directory to analyze",
)
@click.option(
    "--config",
    default="~/.mcp-skillset/config.yaml",
    type=click.Path(),
    help="Config file location",
)
@click.option("--auto", is_flag=True, help="Non-interactive setup with defaults")
@click.option(
    "--skip-agents",
    is_flag=True,
    help="Skip automatic installation for AI agents",
)
def setup(project_dir: str, config: str, auto: bool, skip_agents: bool) -> None:
    """Auto-configure mcp-skillset for your project.

    This command will:
    1. Detect your project's toolchain
    2. Clone relevant skill repositories
    3. Index skills with vector + KG
    4. Configure MCP server
    5. Validate setup
    6. Install for AI agents (Claude Code, Auggie by default; excludes Claude Desktop)
    """
    console.print("🚀 [bold green]Starting mcp-skillset setup...[/bold green]")
    console.print(f"📁 Project directory: {project_dir}")
    console.print(f"⚙️  Config location: {config}\n")

    try:
        # 1. Toolchain detection
        console.print("[bold cyan]Step 1/6:[/bold cyan] Detecting project toolchain...")
        detector = ToolchainDetector()
        project_path = Path(project_dir).resolve()
        toolchain = detector.detect(project_path)

        console.print(
            f"  ✓ Primary language: [bold]{toolchain.primary_language}[/bold]"
        )
        if toolchain.frameworks:
            console.print(f"  ✓ Frameworks: {', '.join(toolchain.frameworks)}")
        if toolchain.test_frameworks:
            console.print(
                f"  ✓ Test frameworks: {', '.join(toolchain.test_frameworks)}"
            )
        console.print(f"  ✓ Confidence: {toolchain.confidence:.0%}\n")

        # 2. Repository cloning
        console.print(
            "[bold cyan]Step 2/6:[/bold cyan] Setting up skill repositories..."
        )
        repo_manager = RepositoryManager()

        # Get default repos or prompt user
        if auto:
            repos_to_add = RepositoryManager.DEFAULT_REPOS
            console.print("  Using default repositories (--auto mode)")
        else:
            console.print("\n  Available default repositories:")
            for i, repo in enumerate(RepositoryManager.DEFAULT_REPOS, 1):
                console.print(f"    {i}. {repo['url']} (priority: {repo['priority']})")

            if click.confirm("\n  Clone default repositories?", default=True):
                repos_to_add = RepositoryManager.DEFAULT_REPOS
            else:
                repos_to_add = []
                console.print(
                    "  [dim]You can add repositories later with: mcp-skillset repo add <url>[/dim]"
                )

        # Clone repositories with per-repository progress bars
        added_repos: ListType[Repository] = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            for repo_config in repos_to_add:
                # Extract repo name from URL for display
                repo_name = repo_config["url"].split("/")[-1].replace(".git", "")

                try:
                    # Check if already exists
                    repo_id = repo_manager._generate_repo_id(repo_config["url"])
                    existing = repo_manager.get_repository(repo_id)

                    if existing:
                        console.print(
                            f"  ⊙ Repository already exists: {repo_config['url']}"
                        )
                        added_repos.append(existing)
                    else:
                        # Create task for this repository
                        task_id = progress.add_task(
                            f"Cloning {repo_name}",
                            total=100,  # Will be updated by callback
                            start=False,
                        )

                        # Progress callback updates this specific task
                        def make_callback(tid: int):  # type: ignore[misc]
                            def update_progress(
                                current: int, total: int, _message: str
                            ) -> None:
                                if total > 0:
                                    progress.update(tid, completed=current, total=total)
                                    if not progress.tasks[tid].started:
                                        progress.start_task(tid)

                            return update_progress

                        new_repo = repo_manager.add_repository_with_progress(
                            url=repo_config["url"],
                            priority=repo_config["priority"],
                            license=repo_config.get("license", "Unknown"),
                            progress_callback=make_callback(task_id),
                        )
                        progress.update(
                            task_id, description=f"✓ {repo_name}", completed=100
                        )
                        added_repos.append(new_repo)
                        console.print(f"  ✓ Cloned {new_repo.skill_count} skills")
                except Exception as e:
                    console.print(
                        f"  [red]✗ Failed to clone {repo_config['url']}: {e}[/red]"
                    )
                    logger.error(f"Repository clone failed: {e}")

        if not added_repos:
            console.print(
                "\n  [yellow]No repositories configured. Add some with: mcp-skillset repo add <url>[/yellow]"
            )

        console.print()

        # 3. Indexing
        console.print("[bold cyan]Step 3/6:[/bold cyan] Building skill indices...")
        skill_manager = SkillManager()
        indexing_engine = IndexingEngine(skill_manager=skill_manager)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("  Indexing skills...", total=None)
            try:
                stats = indexing_engine.reindex_all(force=True)
                progress.update(task, completed=True)
                console.print(f"  ✓ Indexed {stats.total_skills} skills")
                console.print(f"  ✓ Vector store: {stats.vector_store_size // 1024} KB")
                console.print(
                    f"  ✓ Knowledge graph: {stats.graph_nodes} nodes, {stats.graph_edges} edges\n"
                )
            except Exception as e:
                progress.stop()
                console.print(f"  [red]✗ Indexing failed: {e}[/red]")
                logger.error(f"Indexing failed: {e}")

        # 4. MCP configuration
        console.print("[bold cyan]Step 4/6:[/bold cyan] Configuring MCP server...")
        base_dir = Path.home() / ".mcp-skillset"
        console.print(f"  ✓ Base directory: {base_dir}")
        console.print(f"  ✓ ChromaDB: {base_dir / 'chromadb'}")
        console.print(f"  ✓ Repositories: {base_dir / 'repos'}\n")

        # 5. Validation
        console.print("[bold cyan]Step 5/6:[/bold cyan] Validating setup...")
        repos = repo_manager.list_repositories()
        skills = skill_manager.discover_skills()

        validation_ok = True
        if not repos:
            console.print("  [red]✗ No repositories configured[/red]")
            validation_ok = False
        else:
            console.print(f"  ✓ {len(repos)} repositories configured")

        if not skills:
            console.print("  [red]✗ No skills discovered[/red]")
            validation_ok = False
        else:
            console.print(f"  ✓ {len(skills)} skills available")

        if stats.total_skills == 0:
            console.print("  [red]✗ No skills indexed[/red]")
            validation_ok = False
        else:
            console.print(f"  ✓ {stats.total_skills} skills indexed")

        console.print()

        # 6. Agent installation (if not skipped)
        agents_installed = 0
        if not skip_agents:
            console.print()
            console.print(
                "[bold cyan]Step 6/6:[/bold cyan] Installing for AI agents..."
            )

            agent_detector = AgentDetector()
            # Exclude Claude Desktop by default (config path conflicts with Claude Code)
            all_agents = agent_detector.detect_all()
            found_agents = [
                a for a in all_agents if a.exists and a.id != "claude-desktop"
            ]

            if found_agents:
                console.print(f"  ✓ Detected {len(found_agents)} agent(s):")
                for agent in found_agents:
                    console.print(f"    • {agent.name}")

                # Ask for confirmation (respect auto flag)
                should_install = auto or click.confirm(
                    "\n  Install mcp-skillset for these agents?", default=True
                )

                if should_install:
                    installer = AgentInstaller()
                    success_count = 0

                    for agent in found_agents:
                        try:
                            result = installer.install(agent)
                            if result.success:
                                console.print(f"    ✓ {agent.name} configured")
                                success_count += 1
                            else:
                                console.print(
                                    f"    ✗ {agent.name} failed: {result.error or 'Unknown error'}"
                                )
                        except Exception as e:
                            console.print(f"    ✗ {agent.name} error: {str(e)}")

                    console.print(
                        f"\n  Installed for {success_count}/{len(found_agents)} agent(s)"
                    )
                    agents_installed = success_count
                else:
                    console.print("  Skipped agent installation")
            else:
                console.print(
                    "  No AI agents detected (Claude Desktop, Claude Code, Auggie)"
                )
                console.print(
                    "  You can install manually later with: mcp-skillset install"
                )
        else:
            console.print(
                "\n[dim]Skipped agent installation (--skip-agents flag)[/dim]"
            )

        console.print()

        # Summary
        if validation_ok:
            console.print("[bold green]✓ Setup complete![/bold green]\n")
            console.print("Next steps:")
            if agents_installed > 0:
                console.print(
                    "  1. [cyan]Restart your AI agent[/cyan] to load mcp-skillset"
                )
                console.print("  2. [cyan]Explore skills:[/cyan] mcp-skillset demo")
                console.print(
                    "  3. [cyan]Search skills:[/cyan] mcp-skillset search 'python testing'"
                )
            else:
                console.print(
                    "  1. [cyan]Install for agents:[/cyan] mcp-skillset install"
                )
                console.print("  2. [cyan]Explore skills:[/cyan] mcp-skillset demo")
                console.print(
                    "  3. [cyan]Search skills:[/cyan] mcp-skillset search 'python testing'"
                )
                console.print(
                    "  4. [cyan]Show skill:[/cyan] mcp-skillset show <skill-id>"
                )
            console.print()
            console.print(
                "[dim]💡 Tip: Try 'mcp-skillset demo' to see example questions for each skill![/dim]"
            )
        else:
            console.print(
                "[bold yellow]⚠ Setup completed with warnings[/bold yellow]\n"
            )
            console.print(
                "Please check the errors above and run setup again if needed."
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled by user[/yellow]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"\n[red]Setup failed: {e}[/red]")
        logger.exception("Setup failed")
        raise SystemExit(1)
