"""
Discover command group implementation.
"""

import logging
from datetime import UTC, datetime

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mcp_skills.models.config import MCPSkillsConfig
from mcp_skills.services.github_discovery import GitHubDiscovery


console = Console()
logger = logging.getLogger(__name__)


@click.group()
def discover() -> None:
    """Discover skill repositories on GitHub."""
    pass


@discover.command("search")
@click.argument("query")
@click.option("--min-stars", type=int, default=2, help="Minimum star count")
@click.option("--limit", type=int, default=10, help="Maximum results")
def discover_search(query: str, min_stars: int, limit: int) -> None:
    """Search GitHub for skill repositories.

    Search for repositories containing SKILL.md files using natural language.

    Examples:
        mcp-skillset discover search "python testing"
        mcp-skillset discover search "fastapi" --min-stars 10
        mcp-skillset discover search "react typescript" --limit 20
    """
    console.print(f"🔍 [bold]Searching GitHub for:[/bold] {query}")
    console.print(f"⭐ [dim]Minimum stars: {min_stars}[/dim]\n")

    try:
        # Load config for GitHub token
        config = MCPSkillsConfig()
        token = config.github_discovery.github_token

        # Initialize discovery service
        discovery = GitHubDiscovery(github_token=token)

        # Perform search
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching repositories...", total=None)
            repos = discovery.search_repos(query, min_stars=min_stars)
            progress.update(task, completed=True)

        if not repos:
            console.print("[yellow]No repositories found[/yellow]")
            console.print("\nTry:")
            console.print("  • Using different keywords")
            console.print("  • Lowering --min-stars threshold")
            console.print(
                "  • Checking GitHub rate limits: mcp-skillset discover limits"
            )
            return

        # Display results
        repos = repos[:limit]  # Limit results
        table = Table(title=f"Found {len(repos)} Repositories")
        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Updated", style="green")

        for repo in repos:
            # Truncate description
            desc = repo.description or "No description"
            if len(desc) > 50:
                desc = desc[:47] + "..."

            # Format updated time
            days_ago = (datetime.now(UTC) - repo.updated_at).days
            if days_ago == 0:
                updated = "Today"
            elif days_ago == 1:
                updated = "Yesterday"
            elif days_ago < 30:
                updated = f"{days_ago}d ago"
            else:
                updated = f"{days_ago // 30}mo ago"

            table.add_row(
                repo.full_name,
                desc,
                str(repo.stars),
                updated,
            )

        console.print(table)
        console.print("\n[dim]Add repository: mcp-skillset repo add <url>[/dim]")

    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        logger.exception("Discovery search failed")
        raise SystemExit(1)


@discover.command("trending")
@click.option(
    "--timeframe",
    type=click.Choice(["week", "month", "year"]),
    default="week",
    help="Time period",
)
@click.option("--topic", type=str, help="Filter by topic")
@click.option("--limit", type=int, default=10, help="Maximum results")
def discover_trending(timeframe: str, topic: str | None, limit: int) -> None:
    """Get trending skill repositories.

    Shows recently updated repositories with SKILL.md files.

    Examples:
        mcp-skillset discover trending
        mcp-skillset discover trending --timeframe month
        mcp-skillset discover trending --topic claude-skills
    """
    console.print("📈 [bold]Trending Repositories[/bold]")
    console.print(f"📅 [dim]Timeframe: {timeframe}[/dim]")
    if topic:
        console.print(f"🏷️  [dim]Topic: {topic}[/dim]")
    console.print()

    try:
        # Load config for GitHub token
        config = MCPSkillsConfig()
        token = config.github_discovery.github_token

        # Initialize discovery service
        discovery = GitHubDiscovery(github_token=token)

        # Get trending repos
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Finding trending repositories...", total=None)
            repos = discovery.get_trending(timeframe=timeframe, topic=topic)
            progress.update(task, completed=True)

        if not repos:
            console.print("[yellow]No trending repositories found[/yellow]")
            return

        # Display results
        repos = repos[:limit]  # Limit results
        table = Table(title=f"Trending ({len(repos)} found)")
        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Topics", style="magenta")

        for repo in repos:
            # Truncate description
            desc = repo.description or "No description"
            if len(desc) > 40:
                desc = desc[:37] + "..."

            # Format topics
            topics_str = ", ".join(repo.topics[:3])
            if len(repo.topics) > 3:
                topics_str += f" +{len(repo.topics) - 3}"

            table.add_row(
                repo.full_name,
                desc,
                str(repo.stars),
                topics_str,
            )

        console.print(table)
        console.print("\n[dim]Add repository: mcp-skillset repo add <url>[/dim]")

    except Exception as e:
        console.print(f"[red]Trending search failed: {e}[/red]")
        logger.exception("Discovery trending failed")
        raise SystemExit(1)


@discover.command("topic")
@click.argument("topic")
@click.option("--min-stars", type=int, default=2, help="Minimum star count")
@click.option("--limit", type=int, default=10, help="Maximum results")
def discover_topic(topic: str, min_stars: int, limit: int) -> None:
    """Search repositories by GitHub topic.

    Common topics: claude-skills, anthropic-skills, mcp-skills, ai-skills

    Examples:
        mcp-skillset discover topic claude-skills
        mcp-skillset discover topic mcp-skills --min-stars 5
    """
    console.print(f"🏷️  [bold]Searching topic:[/bold] {topic}")
    console.print(f"⭐ [dim]Minimum stars: {min_stars}[/dim]\n")

    try:
        # Load config for GitHub token
        config = MCPSkillsConfig()
        token = config.github_discovery.github_token

        # Initialize discovery service
        discovery = GitHubDiscovery(github_token=token)

        # Search by topic
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching by topic...", total=None)
            repos = discovery.search_by_topic(topic, min_stars=min_stars)
            progress.update(task, completed=True)

        if not repos:
            console.print(f"[yellow]No repositories found for topic '{topic}'[/yellow]")
            console.print("\nTry:")
            console.print("  • Different topic (claude-skills, mcp-skills, ai-skills)")
            console.print("  • Lowering --min-stars threshold")
            return

        # Display results
        repos = repos[:limit]  # Limit results
        table = Table(title=f"Topic: {topic} ({len(repos)} found)")
        table.add_column("Repository", style="cyan", no_wrap=True)
        table.add_column("Description", style="dim")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("License", style="green")

        for repo in repos:
            # Truncate description
            desc = repo.description or "No description"
            if len(desc) > 50:
                desc = desc[:47] + "..."

            table.add_row(
                repo.full_name,
                desc,
                str(repo.stars),
                repo.license or "Unknown",
            )

        console.print(table)
        console.print("\n[dim]Add repository: mcp-skillset repo add <url>[/dim]")

    except Exception as e:
        console.print(f"[red]Topic search failed: {e}[/red]")
        logger.exception("Discovery topic failed")
        raise SystemExit(1)


@discover.command("verify")
@click.argument("repo_url")
def discover_verify(repo_url: str) -> None:
    """Verify a repository contains SKILL.md files.

    Examples:
        mcp-skillset discover verify https://github.com/anthropics/skills.git
        mcp-skillset discover verify https://github.com/user/repo
    """
    console.print(f"🔍 [bold]Verifying repository:[/bold] {repo_url}\n")

    try:
        # Load config for GitHub token
        config = MCPSkillsConfig()
        token = config.github_discovery.github_token

        # Initialize discovery service
        discovery = GitHubDiscovery(github_token=token)

        # Verify repository
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Verifying SKILL.md files...", total=None)
            is_valid = discovery.verify_skill_repo(repo_url)
            progress.update(task, completed=True)

        if is_valid:
            console.print("[green]✓[/green] Repository contains SKILL.md files")

            # Get detailed metadata
            metadata = discovery.get_repo_metadata(repo_url)
            if metadata:
                console.print()
                console.print("[bold]Repository Metadata:[/bold]")
                console.print(f"  • Name: {metadata.full_name}")
                console.print(f"  • Description: {metadata.description or 'None'}")
                console.print(f"  • Stars: {metadata.stars}")
                console.print(f"  • Forks: {metadata.forks}")
                console.print(f"  • License: {metadata.license or 'Unknown'}")
                if metadata.topics:
                    console.print(f"  • Topics: {', '.join(metadata.topics)}")

                console.print()
                console.print("[dim]Add this repository:[/dim]")
                console.print(f"  mcp-skillset repo add {metadata.url}")
        else:
            console.print("[red]✗[/red] No SKILL.md files found in repository")
            console.print("\nThis repository may not contain skills.")
            console.print("Valid skill repositories should have SKILL.md files.")

    except Exception as e:
        console.print(f"[red]Verification failed: {e}[/red]")
        logger.exception("Discovery verify failed")
        raise SystemExit(1)


@discover.command("limits")
def discover_limits() -> None:
    """Show GitHub API rate limit status.

    Displays current rate limit usage for both authenticated
    and unauthenticated requests.
    """
    console.print("📊 [bold]GitHub API Rate Limits[/bold]\n")

    try:
        # Load config for GitHub token
        config = MCPSkillsConfig()
        token = config.github_discovery.github_token

        # Initialize discovery service
        discovery = GitHubDiscovery(github_token=token)

        # Get rate limit status
        status = discovery.get_rate_limit_status()

        # Authentication status
        if token:
            console.print("[green]✓[/green] Authenticated (5000 requests/hour)")
        else:
            console.print("[yellow]⚠[/yellow] Unauthenticated (60 requests/hour)")
            console.print(
                "[dim]Set GITHUB_TOKEN environment variable for higher limits[/dim]\n"
            )

        # Display limits
        table = Table(title="Rate Limit Status")
        table.add_column("Resource", style="cyan")
        table.add_column("Remaining", justify="right", style="green")
        table.add_column("Limit", justify="right", style="yellow")
        table.add_column("Resets", style="magenta")

        # Core API
        core_reset = status["core_reset"].strftime("%H:%M:%S")
        table.add_row(
            "Core API",
            str(status["core_remaining"]),
            str(status["core_limit"]),
            core_reset,
        )

        # Search API
        search_reset = status["search_reset"].strftime("%H:%M:%S")
        table.add_row(
            "Search API",
            str(status["search_remaining"]),
            str(status["search_limit"]),
            search_reset,
        )

        console.print(table)

        # Warnings
        if status["search_remaining"] < 5:
            console.print(
                f"\n[yellow]⚠ Search API rate limit almost exhausted. "
                f"Resets at {search_reset}[/yellow]"
            )

        if status["core_remaining"] < 10:
            console.print(
                f"\n[yellow]⚠ Core API rate limit low. "
                f"Resets at {core_reset}[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Failed to get rate limits: {e}[/red]")
        logger.exception("Discovery limits failed")
        raise SystemExit(1)
