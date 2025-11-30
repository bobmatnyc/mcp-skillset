"""
Repo command group implementation.
"""

import logging

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
from rich.table import Table

from mcp_skills.services.repository_manager import RepositoryManager


console = Console()
logger = logging.getLogger(__name__)


@click.group()
def repo() -> None:
    """Manage skill repositories."""
    pass


@repo.command("add")
@click.argument("url")
@click.option("--priority", type=int, default=50, help="Repository priority")
def repo_add(url: str, priority: int) -> None:
    """Add a new skill repository.

    Example: mcp-skillset repo add https://github.com/user/skills.git
    """
    console.print(f"➕ [bold]Adding repository:[/bold] {url}")
    console.print(f"📊 Priority: {priority}\n")

    try:
        repo_manager = RepositoryManager()

        # Extract repo name from URL for display
        repo_name = url.split("/")[-1].replace(".git", "")

        # Add repository with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Cloning {repo_name}", total=100, start=False)

            # Progress callback updates this specific task
            def update_progress(current: int, total: int, _message: str) -> None:
                if total > 0:
                    progress.update(task, completed=current, total=total)
                    if not progress.tasks[task].started:
                        progress.start_task(task)

            try:
                repo = repo_manager.add_repository_with_progress(
                    url, priority=priority, progress_callback=update_progress
                )
                progress.update(task, description=f"✓ {repo_name}", completed=100)

                console.print("[green]✓[/green] Repository added successfully")
                console.print(f"  • ID: {repo.id}")
                console.print(f"  • Skills: {repo.skill_count}")
                console.print(f"  • License: {repo.license}")
                console.print(f"  • Path: {repo.local_path}")

                # Suggest reindexing
                console.print(
                    "\n[dim]Tip: Run 'mcp-skillset index' to index new skills[/dim]"
                )

            except ValueError as e:
                progress.stop()
                console.print(f"[red]✗ Failed to add repository: {e}[/red]")
                raise SystemExit(1)

    except Exception as e:
        console.print(f"[red]Failed to add repository: {e}[/red]")
        logger.exception("Repository add failed")
        raise SystemExit(1)


@repo.command("list")
def repo_list() -> None:
    """List all configured repositories."""
    console.print("📚 [bold]Configured Repositories[/bold]\n")

    try:
        repo_manager = RepositoryManager()
        repos = repo_manager.list_repositories()

        if not repos:
            console.print("[yellow]No repositories configured[/yellow]")
            console.print("\nAdd repositories with:")
            console.print("  mcp-skillset repo add <url>")
            console.print("\nOr run setup:")
            console.print("  mcp-skillset setup")
            return

        # Display repositories in table
        table = Table(title=f"Repositories ({len(repos)} configured)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("URL", style="blue")
        table.add_column("Priority", justify="right", style="magenta")
        table.add_column("Skills", justify="right", style="green")
        table.add_column("Last Updated", style="dim")

        for repo in repos:
            table.add_row(
                repo.id,
                repo.url,
                str(repo.priority),
                str(repo.skill_count),
                repo.last_updated.strftime("%Y-%m-%d %H:%M"),
            )

        console.print(table)

        # Summary
        total_skills = sum(repo.skill_count for repo in repos)
        console.print(
            f"\n[dim]Total: {len(repos)} repositories, {total_skills} skills[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Failed to list repositories: {e}[/red]")
        logger.exception("Repository list failed")
        raise SystemExit(1)


@repo.command("update")
@click.argument("repo_id", required=False)
def repo_update(repo_id: str | None) -> None:
    """Update repositories (pull latest changes).

    If repo_id is provided, update only that repository.
    Otherwise, update all repositories.
    """
    try:
        repo_manager = RepositoryManager()

        if repo_id:
            # Update single repository
            console.print(f"🔄 [bold]Updating repository:[/bold] {repo_id}\n")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Pulling latest changes...", total=None)
                try:
                    repo = repo_manager.update_repository(repo_id)
                    progress.update(task, completed=True)

                    console.print("[green]✓[/green] Repository updated successfully")
                    console.print(f"  • ID: {repo.id}")
                    console.print(f"  • Skills: {repo.skill_count}")
                    console.print(
                        f"  • Last updated: {repo.last_updated.strftime('%Y-%m-%d %H:%M')}"
                    )

                except ValueError as e:
                    progress.stop()
                    console.print(f"[red]✗ Update failed: {e}[/red]")
                    raise SystemExit(1)

        else:
            # Update all repositories
            console.print("🔄 [bold]Updating all repositories...[/bold]\n")

            repos = repo_manager.list_repositories()

            if not repos:
                console.print("[yellow]No repositories configured[/yellow]")
                return

            updated_count = 0
            failed_count = 0
            new_skills = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                for repo in repos:
                    task = progress.add_task(
                        f"Updating {repo.id}", total=100, start=False
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

                    try:
                        old_skill_count = repo.skill_count
                        updated_repo = repo_manager.update_repository_with_progress(
                            repo.id, progress_callback=make_callback(task)
                        )
                        progress.update(task, description=f"✓ {repo.id}", completed=100)

                        updated_count += 1
                        skill_diff = updated_repo.skill_count - old_skill_count
                        new_skills += skill_diff

                        if skill_diff > 0:
                            console.print(
                                f"  [green]✓[/green] {repo.id}: +{skill_diff} new skills"
                            )
                        elif skill_diff < 0:
                            console.print(
                                f"  [yellow]✓[/yellow] {repo.id}: {skill_diff} skills removed"
                            )
                        else:
                            console.print(f"  [green]✓[/green] {repo.id}: up to date")

                    except Exception as e:
                        progress.update(task, description=f"✗ {repo.id}")
                        console.print(f"  [red]✗[/red] {repo.id}: {e}")
                        failed_count += 1

            console.print()
            console.print("[bold]Summary:[/bold]")
            console.print(f"  • Updated: {updated_count}/{len(repos)} repositories")
            if failed_count > 0:
                console.print(f"  • Failed: {failed_count}")
            if new_skills != 0:
                console.print(f"  • New skills: {new_skills}")

            if updated_count > 0:
                console.print(
                    "\n[dim]Tip: Run 'mcp-skillset index' to reindex updated skills[/dim]"
                )

    except Exception as e:
        console.print(f"[red]Update failed: {e}[/red]")
        logger.exception("Repository update failed")
        raise SystemExit(1)
