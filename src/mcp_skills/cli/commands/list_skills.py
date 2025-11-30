"""Command: list - List all available skills."""

from __future__ import annotations

import click
from rich.table import Table

from mcp_skills.cli.shared.console import console
from mcp_skills.services.skill_manager import SkillManager


@click.command(name="list")
@click.option("--category", type=str, help="Filter by category")
@click.option("--compact", is_flag=True, help="Compact output")
def list_skills(category: str | None, compact: bool) -> None:
    """List all available skills.

    Displays all discovered skills in either detailed table format
    or compact list format. Can be filtered by category.

    Examples:
        mcp-skillset list
        mcp-skillset list --category testing
        mcp-skillset list --compact
    """
    console.print("📋 [bold]Available Skills[/bold]")
    if category:
        console.print(f"📁 [dim]Category: {category}[/dim]\n")
    else:
        console.print()

    try:
        # Initialize skill manager
        skill_manager = SkillManager()

        # Discover skills
        skills = skill_manager.discover_skills()

        # Apply category filter
        if category:
            skills = [s for s in skills if s.category == category]

        if not skills:
            console.print("[yellow]No skills found[/yellow]")
            if category:
                console.print(f"\nNo skills in category: {category}")
                console.print(
                    "Available categories: testing, debugging, refactoring, etc."
                )
            return

        # Display skills
        if compact:
            # Compact output: just names
            for skill in sorted(skills, key=lambda s: s.name):
                console.print(f"  • {skill.name} [dim]({skill.category})[/dim]")
            console.print(f"\n[dim]Total: {len(skills)} skills[/dim]")
        else:
            # Detailed table
            table = Table(title=f"Skills ({len(skills)} found)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="bold")
            table.add_column("Category", style="magenta")
            table.add_column("Description", style="dim")
            table.add_column("Tags", style="yellow")

            for skill in sorted(skills, key=lambda s: (s.category, s.name)):
                # Truncate description
                desc = skill.description[:60]
                if len(skill.description) > 60:
                    desc += "..."

                # Show first 2 tags
                tags_str = ", ".join(skill.tags[:2])
                if len(skill.tags) > 2:
                    tags_str += f" +{len(skill.tags) - 2}"

                table.add_row(
                    skill.id,
                    skill.name,
                    skill.category,
                    desc,
                    tags_str,
                )

            console.print(table)

        console.print("\n[dim]Use 'mcp-skillset info <skill-id>' for details[/dim]")

    except Exception as e:
        console.print(f"[red]List failed: {e}[/red]")
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("List failed")
        raise SystemExit(1)
