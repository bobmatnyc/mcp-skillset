"""Command: demo - Generate example prompts and questions for skills."""

from __future__ import annotations

import builtins

import click

from mcp_skills.cli.shared.console import console
from mcp_skills.services.skill_manager import SkillManager


@click.command()
@click.argument("skill_id", required=False)
@click.option("--interactive", is_flag=True, help="Interactive mode with menu")
def demo(skill_id: str | None, interactive: bool) -> None:
    """Generate example prompts and questions for skills.

    Without skill_id: Shows menu of available skills
    With skill_id: Generates example prompts for that skill

    Examples:
        mcp-skillset demo                  # Interactive menu
        mcp-skillset demo pytest-skill     # Demo for specific skill
        mcp-skillset demo --interactive    # Interactive selection
    """

    def extract_concepts_local(instructions: str) -> list[str]:
        """Extract key concepts from skill instructions."""
        found_concepts = []
        instructions_lower = instructions.lower()

        # Use simple string matching
        keyword_map = {
            "test": "testing",
            "fixture": "fixtures",
            "mock": "mocking",
            "assert": "assertions",
            "debug": "debugging",
            "refactor": "refactoring",
            "performance": "performance",
            "optimization": "performance",
            "security": "security",
            "secure": "security",
            "deploy": "deployment",
            "api": "APIs",
            "database": "database",
            "authentication": "authentication",
            "auth": "authentication",
            "error handling": "error handling",
            "logging": "logging",
            "validation": "validation",
        }

        seen = set()
        for keyword, concept in keyword_map.items():
            if keyword in instructions_lower and concept not in seen:
                found_concepts.append(concept)
                seen.add(concept)

        # Sort and limit
        found_concepts.sort()
        return found_concepts[:10]

    def generate_prompts_local(skill_name: str, concept: str) -> builtins.list[str]:
        """Generate example prompts for a skill and concept."""
        return [
            f"How do I use {concept} with {skill_name}?",
            f"Show me {concept} examples for {skill_name}",
            f"What are best practices for {concept} in {skill_name}?",
            f"Help me understand {concept} with {skill_name}",
        ]

    console.print("🎯 [bold]Skill Demo & Examples[/bold]\n")

    try:
        skill_manager = SkillManager()

        if not skill_id or interactive:
            # Show menu of skills
            skills = skill_manager.discover_skills()

            if not skills:
                console.print("[yellow]No skills found[/yellow]")
                console.print("Run: mcp-skillset setup")
                return

            # Display top skills by category
            console.print("[bold cyan]Available Skills:[/bold cyan]\n")

            from mcp_skills.models.skill import Skill

            by_category: dict[str, builtins.list[Skill]] = {}
            for skill in skills:
                category = skill.category if skill.category else "General"
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(skill)

            # Show top 2 from each category
            skill_options = []
            # Build sorted category list (avoid Click conflicts with sorted/list)
            categories = []
            for cat_name in by_category:
                categories.append(cat_name)
            categories.sort()
            # Prioritize non-general categories
            general_idx = -1
            for idx, cat in enumerate(categories):
                if cat == "General":
                    general_idx = idx
                    break
            if general_idx >= 0:
                categories.pop(general_idx)
                categories.append("General")

            for category in categories[:5]:  # Top 5 categories
                console.print(f"[magenta]{category}:[/magenta]")
                # Manual sort to avoid Click conflicts
                category_skills = []
                for sk in by_category[category]:
                    category_skills.append(sk)
                category_skills.sort(key=lambda s: s.name)
                for skill in category_skills[:2]:
                    skill_options.append(skill)
                    desc = (
                        skill.description[:60] + "..."
                        if len(skill.description) > 60
                        else skill.description
                    )
                    console.print(
                        f"  {len(skill_options)}. {skill.name} - [dim]{desc}[/dim]"
                    )
                console.print()

            if not interactive:
                console.print(
                    "[dim]Tip: Use 'mcp-skillset demo <skill-id>' for specific examples[/dim]"
                )
                return

            # Interactive selection
            choice = click.prompt("Select a skill (number)", type=int, default=1)
            if 1 <= choice <= len(skill_options):
                skill = skill_options[choice - 1]
                skill_id = skill.id
            else:
                console.print("[red]Invalid selection[/red]")
                return

        # Load specific skill
        loaded_skill = skill_manager.load_skill(skill_id)
        if not loaded_skill:
            console.print(f"[red]Skill not found: {skill_id}[/red]")
            return

        # Generate example prompts
        console.print(f"[bold cyan]Demo: {loaded_skill.name}[/bold cyan]\n")
        console.print(f"[dim]{loaded_skill.description}[/dim]\n")

        # Extract key concepts
        concepts = extract_concepts_local(loaded_skill.instructions)

        if concepts:
            console.print("[bold]Example Questions:[/bold]\n")

            # Generate prompts
            for i, concept in enumerate(concepts[:5], 1):
                prompts = generate_prompts_local(loaded_skill.name, concept)
                if prompts:
                    console.print(f"  {i}. [cyan]{prompts[0]}[/cyan]")

            console.print()

        # Show usage hint
        console.print("[bold]How to use:[/bold]")
        if concepts:
            prompts = generate_prompts_local(loaded_skill.name, concepts[0])
            if prompts:
                console.print(f"  Ask Claude: '{prompts[0]}'")
        else:
            console.print(f"  Ask Claude about '{loaded_skill.name}' capabilities")
        console.print()
        console.print(
            f"[dim]Tip: Use 'mcp-skillset info {loaded_skill.id}' for full details[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Demo failed: {e}[/red]")
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Demo failed")
        raise SystemExit(1)
