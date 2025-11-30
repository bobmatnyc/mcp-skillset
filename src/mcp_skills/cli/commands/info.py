"""Command: info/show - Show detailed information about a skill."""

from __future__ import annotations

import click
from rich.panel import Panel

from mcp_skills.cli.shared.console import console
from mcp_skills.services.skill_manager import SkillManager


@click.command()
@click.argument("skill_id")
def info(skill_id: str) -> None:
    """Show detailed information about a skill.

    Displays comprehensive information about a specific skill including
    metadata, description, instructions preview, dependencies, and examples.

    Examples:
        mcp-skillset info pytest-skill
        mcp-skillset info tdd-workflow
    """
    console.print(f"ℹ️  [bold]Skill Information:[/bold] {skill_id}\n")

    try:
        # Initialize skill manager
        skill_manager = SkillManager()

        # Load skill
        skill = skill_manager.load_skill(skill_id)

        if not skill:
            console.print(f"[red]Skill not found: {skill_id}[/red]")
            console.print("\nTry:")
            console.print("  • mcp-skillset list - to see all available skills")
            console.print("  • mcp-skillset search <query> - to search for skills")
            return

        # Metadata panel
        metadata_content = f"[bold cyan]Name:[/bold cyan] {skill.name}\n"
        metadata_content += f"[bold cyan]ID:[/bold cyan] {skill.id}\n"
        metadata_content += f"[bold cyan]Category:[/bold cyan] {skill.category}\n"
        metadata_content += f"[bold cyan]Repository:[/bold cyan] {skill.repo_id}\n"

        if skill.version:
            metadata_content += f"[bold cyan]Version:[/bold cyan] {skill.version}\n"
        if skill.author:
            metadata_content += f"[bold cyan]Author:[/bold cyan] {skill.author}\n"

        if skill.tags:
            metadata_content += (
                f"[bold cyan]Tags:[/bold cyan] {', '.join(skill.tags)}\n"
            )

        metadata_panel = Panel(
            metadata_content.rstrip(),
            title="Metadata",
            border_style="cyan",
        )
        console.print(metadata_panel)

        # Description panel
        desc_panel = Panel(
            skill.description,
            title="Description",
            border_style="green",
        )
        console.print(desc_panel)

        # Instructions panel (truncated)
        instructions_preview = skill.instructions[:500]
        if len(skill.instructions) > 500:
            instructions_preview += "\n\n[dim]... (truncated, see full file for complete instructions)[/dim]"

        instructions_panel = Panel(
            instructions_preview,
            title="Instructions (Preview)",
            border_style="yellow",
        )
        console.print(instructions_panel)

        # Dependencies panel (if any)
        if skill.dependencies:
            deps_content = "\n".join(f"  • {dep}" for dep in skill.dependencies)
            deps_panel = Panel(
                deps_content,
                title="Dependencies",
                border_style="magenta",
            )
            console.print(deps_panel)

        # Examples panel (if any)
        if skill.examples:
            examples_content = (
                f"\n{len(skill.examples)} example(s) available in full instructions"
            )
            examples_panel = Panel(
                examples_content,
                title="Examples",
                border_style="blue",
            )
            console.print(examples_panel)

        # File path
        console.print(f"\n[dim]File: {skill.file_path}[/dim]")

    except Exception as e:
        console.print(f"[red]Info failed: {e}[/red]")
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Info failed")
        raise SystemExit(1)


@click.command(name="show")
@click.argument("skill_id")
def show(skill_id: str) -> None:
    """Show detailed information about a skill (alias for 'info').

    This is an alias for the 'info' command, providing the same
    detailed skill information display.

    Examples:
        mcp-skillset show pytest-skill
        mcp-skillset show tdd-workflow
    """
    ctx = click.get_current_context()
    ctx.invoke(info, skill_id=skill_id)
