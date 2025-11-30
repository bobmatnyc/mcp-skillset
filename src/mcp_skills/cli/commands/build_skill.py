"""Command: build-skill - Generate skill templates with validation and deployment."""

from __future__ import annotations

import logging

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_skills.cli.shared.console import console


logger = logging.getLogger(__name__)


@click.command("build-skill")
@click.option("--name", required=False, help="Skill name (e.g., 'FastAPI Testing')")
@click.option("--description", required=False, help="What the skill does")
@click.option("--domain", required=False, help="Domain (e.g., 'web development')")
@click.option("--tags", help="Comma-separated tags (e.g., 'fastapi,testing,pytest')")
@click.option(
    "--template",
    type=click.Choice(["base", "web-development", "api-development", "testing"]),
    default="base",
    help="Template to use",
)
@click.option("--no-deploy", is_flag=True, help="Don't deploy to ~/.claude/skills/")
@click.option("--interactive", is_flag=True, help="Interactive mode with prompts")
@click.option("--preview", is_flag=True, help="Preview without deploying")
def build_skill(
    name: str | None,
    description: str | None,
    domain: str | None,
    tags: str | None,
    template: str,
    no_deploy: bool,
    interactive: bool,
    preview: bool,
) -> None:
    """Build a progressive skill from template.

    This command generates reusable skills from templates that can be loaded
    by Claude in future sessions. Skills follow the progressive disclosure format
    with YAML frontmatter and markdown body.

    Skills are automatically:
    - Generated from domain-specific templates (Jinja2)
    - Validated for structure and security patterns
    - Deployed to ~/.claude/skills/ for immediate availability
    - Integrated with Claude Code's skill loading system

    Template Selection:
    - base: General-purpose skill template
    - web-development: Web development workflows
    - api-development: API design and implementation
    - testing: Testing strategies and TDD

    Examples:
        # Build from command line arguments
        mcp-skillset build-skill \\
          --name "FastAPI Testing" \\
          --description "Test FastAPI endpoints with pytest" \\
          --domain "web development" \\
          --tags "fastapi,pytest,testing" \\
          --template web-development

        # Interactive mode
        mcp-skillset build-skill --interactive

        # Preview without deploying
        mcp-skillset build-skill --name "..." --description "..." --domain "..." --preview
    """
    from mcp_skills.services.skill_builder import SkillBuilder

    console.print("🔨 [bold green]Building Progressive Skill[/bold green]\n")

    try:
        # Initialize SkillBuilder
        builder = SkillBuilder()

        # Interactive mode
        if interactive:
            name = click.prompt("Skill name", type=str)
            description = click.prompt("Description", type=str)
            domain = click.prompt("Domain (e.g., 'web development')", type=str)
            tags_input = click.prompt("Tags (comma-separated)", default="", type=str)
            tags = tags_input if tags_input else None

            # Show available templates
            console.print("\n[bold cyan]Available Templates:[/bold cyan]")
            templates = builder.list_templates()
            for i, tmpl in enumerate(templates, 1):
                console.print(f"  {i}. {tmpl}")

            template_choice = click.prompt(
                "\nSelect template number",
                type=int,
                default=1,
            )
            if 1 <= template_choice <= len(templates):
                template = templates[template_choice - 1]

            # Confirm deployment
            if (
                not preview
                and not no_deploy
                and not click.confirm("\nDeploy to ~/.claude/skills/?", default=True)
            ):
                no_deploy = True

        # Validate required parameters
        if not name:
            console.print("[red]Error: --name is required (or use --interactive)[/red]")
            raise SystemExit(1)
        if not description:
            console.print(
                "[red]Error: --description is required (or use --interactive)[/red]"
            )
            raise SystemExit(1)
        if not domain:
            console.print(
                "[red]Error: --domain is required (or use --interactive)[/red]"
            )
            raise SystemExit(1)

        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []

        # Build skill
        console.print("[bold cyan]Building skill...[/bold cyan]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating from template...", total=None)

            result = builder.build_skill(
                name=name,
                description=description,
                domain=domain,
                tags=tag_list,
                template=template,
                deploy=(not no_deploy and not preview),
            )

            progress.update(task, completed=True)

        # Handle result
        if result["status"] == "error":
            console.print(f"\n[red]✗ Build failed: {result['message']}[/red]")
            if "errors" in result:
                for error in result["errors"]:
                    console.print(f"  • {error}")
            raise SystemExit(1)

        # Display success
        console.print(
            f"\n[green]✓[/green] Skill '{result['skill_id']}' created successfully"
        )

        # Show validation warnings
        if result.get("warnings"):
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in result["warnings"]:
                console.print(f"  ⚠ {warning}")

        # Preview mode: show content
        if preview:
            console.print("\n[bold cyan]Preview:[/bold cyan]")
            console.print("─" * 80)

            # Re-generate for preview (without deployment)
            builder.build_skill(
                name=name,
                description=description,
                domain=domain,
                tags=tag_list,
                template=template,
                deploy=False,
            )

            # Read from temporary location or regenerate
            from mcp_skills.services.skill_builder import SkillBuilder

            preview_builder = SkillBuilder()
            context = preview_builder._build_template_context(
                name=name,
                skill_id=result["skill_id"],
                description=description,
                domain=domain,
                tags=tag_list,
            )
            content = preview_builder._generate_from_template(template, context)

            # Show first 50 lines
            lines = content.split("\n")
            preview_lines = lines[:50]
            console.print("\n".join(preview_lines))
            if len(lines) > 50:
                console.print(f"\n[dim]... ({len(lines) - 50} more lines)[/dim]")

            console.print("─" * 80)
            console.print("\n[yellow]Preview mode: Skill not deployed[/yellow]")
            console.print("Remove --preview flag to deploy to ~/.claude/skills/")

        elif result["skill_path"]:
            console.print("\n[bold]Deployment Path:[/bold]")
            console.print(f"  {result['skill_path']}")

            console.print("\n[bold]Next Steps:[/bold]")
            console.print("  1. Review the skill file")
            console.print("  2. Restart Claude Code to load the skill")
            console.print(
                f"  3. Use the skill by mentioning '{domain}' in your prompts"
            )

        else:
            console.print(
                "\n[yellow]Skill created but not deployed (--no-deploy flag)[/yellow]"
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Build cancelled by user[/yellow]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"\n[red]Build failed: {e}[/red]")
        logger.exception("Skill build failed")
        raise SystemExit(1)
