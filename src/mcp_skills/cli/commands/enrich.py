"""Command: enrich - Enrich prompts with relevant skill instructions."""

from __future__ import annotations

import logging
from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_skills.cli.shared.console import console
from mcp_skills.services.prompt_enricher import PromptEnricher
from mcp_skills.services.skill_manager import SkillManager


logger = logging.getLogger(__name__)


@click.command()
@click.argument("prompt", nargs=-1, required=True)
@click.option(
    "--max-skills",
    default=3,
    type=int,
    help="Maximum number of skills to include (default: 3)",
)
@click.option(
    "--detailed",
    is_flag=True,
    help="Include full skill instructions (default: brief summaries)",
)
@click.option(
    "--threshold",
    default=0.7,
    type=float,
    help="Relevance threshold 0.0-1.0 (default: 0.7)",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Save enriched prompt to file",
)
@click.option(
    "--copy",
    is_flag=True,
    help="Copy enriched prompt to clipboard (requires pyperclip)",
)
def enrich(
    prompt: tuple[str, ...],
    max_skills: int,
    detailed: bool,
    threshold: float,
    output: str | None,
    copy: bool,
) -> None:
    """Enrich a prompt with relevant skill instructions.

    Automatically finds and injects relevant skill knowledge into your prompt
    to provide better context for AI assistants.

    The command extracts keywords from your prompt, searches for relevant skills,
    and formats an enriched prompt with skill instructions.

    Process:
      1. Extract keywords from prompt text
      2. Search for relevant skills using hybrid RAG
      3. Format enriched prompt with skill instructions
      4. Optionally save to file or copy to clipboard

    Examples:

        # Basic enrichment with top 3 skills
        mcp-skillset enrich "Create a REST API with authentication"

        # Include more skills and full details
        mcp-skillset enrich "Write tests for user service" --max-skills 5 --detailed

        # Save to file
        mcp-skillset enrich "Deploy to AWS" --output prompt.md

        # Copy to clipboard
        mcp-skillset enrich "Optimize database queries" --copy

        # Quoted prompts for complex sentences
        mcp-skillset enrich "Create a FastAPI endpoint that validates user input and returns JSON"
    """
    # Join prompt tuple into single string
    prompt_text = " ".join(prompt)

    console.print("🔍 [bold]Enriching prompt...[/bold]\n")
    console.print(f"[dim]Prompt: {prompt_text}[/dim]\n")

    try:
        # Initialize services
        skill_manager = SkillManager()
        enricher = PromptEnricher(skill_manager)

        # Step 1: Extract keywords
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting keywords...", total=None)
            keywords = enricher.extract_keywords(prompt_text)
            progress.update(task, completed=True)

        console.print(
            f"  [green]✓[/green] Extracted keywords: {', '.join(keywords[:5])}"
        )
        if len(keywords) > 5:
            console.print(f"    [dim]... and {len(keywords) - 5} more[/dim]")

        # Step 2: Search for skills
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Searching skills...", total=None)
            skills = enricher.search_skills(keywords, max_skills)
            progress.update(task, completed=True)

        console.print(f"  [green]✓[/green] Found {len(skills)} relevant skill(s)")

        if not skills:
            console.print(
                "\n[yellow]No relevant skills found. Try different keywords or lower the threshold.[/yellow]"
            )
            console.print("\nSuggestions:")
            console.print("  • Use more specific technical terms")
            console.print("  • Try --threshold 0.5 for broader results")
            console.print("  • Run: mcp-skillset search <keywords> to test")
            return

        # Step 3: Enrich prompt
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Enriching prompt...", total=None)
            result = enricher.enrich(
                prompt_text,
                max_skills=max_skills,
                detailed=detailed,
            )
            progress.update(task, completed=True)

        console.print("  [green]✓[/green] Enrichment complete\n")

        # Display enriched prompt
        console.print("─" * 80)
        console.print(result.enriched_text)
        console.print("─" * 80)

        # Handle output options
        saved_to_file = False
        copied_to_clipboard = False

        if output:
            try:
                output_path = Path(output)
                enricher.save_to_file(result.enriched_text, output_path)
                console.print(f"\n[green]✓[/green] Saved to: {output_path}")
                saved_to_file = True
            except OSError as e:
                console.print(f"\n[red]✗ Failed to save file: {e}[/red]")

        if copy:
            if enricher.copy_to_clipboard(result.enriched_text):
                console.print("\n[green]✓[/green] Copied to clipboard")
                copied_to_clipboard = True
            else:
                console.print(
                    "\n[yellow]⚠ Clipboard copy failed (install pyperclip: pip install pyperclip)[/yellow]"
                )

        # Summary
        console.print(
            f"\n[dim]Enriched with {len(result.skills_found)} skill(s) "
            f"({len(skills)} candidates, threshold: {threshold})[/dim]"
        )
        console.print(f"[dim]Keywords: {', '.join(result.keywords[:10])}[/dim]")

        if not saved_to_file and not copied_to_clipboard:
            console.print(
                "\n[dim]Tip: Use --output FILE to save or --copy to clipboard[/dim]"
            )

    except Exception as e:
        console.print(f"\n[red]Enrichment failed: {e}[/red]")
        logger.exception("Enrichment failed")
        raise SystemExit(1)
