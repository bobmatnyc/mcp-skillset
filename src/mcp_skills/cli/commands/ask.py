"""Ask command - LLM-powered help for coding questions."""

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


console = Console()


@click.command()
@click.argument("question", nargs=-1, required=True)
@click.option(
    "--no-context",
    is_flag=True,
    help="Skip skill search for context (faster but less specific)",
)
@click.option(
    "--model",
    default=None,
    help="Override LLM model (e.g., anthropic/claude-3-sonnet)",
)
def ask(question: tuple[str, ...], no_context: bool, model: str | None) -> None:
    """Ask a question about coding practices or skills.

    The ask command uses an LLM to answer questions about coding practices,
    tools, and development workflows. It optionally searches the skill library
    to provide context-aware answers.

    Examples:

    \b
        # Ask about pytest fixtures
        mcp-skillset ask "How do I write pytest fixtures?"

    \b
        # Multiple words without quotes
        mcp-skillset ask How do I mock dependencies in tests

    \b
        # Skip skill context for faster response
        mcp-skillset ask "What are SOLID principles?" --no-context

    \b
        # Use a different model
        mcp-skillset ask "Explain async/await" --model anthropic/claude-3-sonnet

    Configuration:

    \b
        Set your OpenRouter API key via one of:
        - Environment: export OPENROUTER_API_KEY=sk-or-...
        - Config file: mcp-skillset config (LLM settings)
        - .env file: OPENROUTER_API_KEY=sk-or-...

    Get an API key at: https://openrouter.ai/
    """
    from mcp_skills.models.config import MCPSkillsConfig
    from mcp_skills.services.indexing import IndexingEngine
    from mcp_skills.services.llm_service import LLMService
    from mcp_skills.services.skill_manager import SkillManager

    # Join question parts
    question_text = " ".join(question)

    # Display question
    console.print(f"\n[bold cyan]Question:[/bold cyan] {question_text}\n")

    # Load configuration
    try:
        config = MCPSkillsConfig()
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to load configuration: {e}")
        raise SystemExit(1) from e

    # Override model if specified
    if model:
        config.llm.model = model
        console.print(f"[dim]Using model: {model}[/dim]\n")

    # Initialize LLM service
    llm_service = LLMService(config.llm)

    # Check for API key
    if not llm_service.get_api_key():
        console.print("[red]Error:[/red] No OpenRouter API key configured.\n")
        console.print("[yellow]Configure your API key via one of:[/yellow]")
        console.print("  1. Environment: export OPENROUTER_API_KEY=sk-or-...")
        console.print("  2. Config file: mcp-skillset config (LLM settings)")
        console.print("  3. .env file: OPENROUTER_API_KEY=sk-or-...")
        console.print("\n[dim]Get an API key at: https://openrouter.ai/[/dim]")
        raise SystemExit(1)

    # Search for relevant skills to provide context
    context = ""
    if not no_context:
        try:
            with console.status("[cyan]Searching relevant skills...[/cyan]"):
                skill_manager = SkillManager()
                indexing_engine = IndexingEngine(skill_manager=skill_manager)
                results = indexing_engine.search(question_text, top_k=3)

                if results:
                    context_parts = []
                    console.print("[dim]Found relevant skills:[/dim]")

                    for r in results:
                        console.print(f"  • {r.skill.id} (relevance: {r.score:.2f})")

                        # Use skill instructions from search results for context
                        if r.skill and r.skill.instructions:
                            # Limit context to 2000 chars per skill to avoid token limits
                            skill_content = r.skill.instructions[:2000]
                            context_parts.append(
                                f"## {r.skill.name}\n{skill_content}"
                            )

                    context = "\n\n".join(context_parts)
                    console.print()

        except Exception as e:
            # Non-fatal: continue without skill context
            console.print(
                f"[yellow]Warning:[/yellow] Could not search skills: {e}\n"
            )

    # Ask LLM
    try:
        with console.status("[cyan]Thinking...[/cyan]"):
            answer = llm_service.ask(question_text, context)

        # Display answer in a panel with markdown rendering
        console.print(
            Panel(
                Markdown(answer),
                title="[bold green]Answer[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )

    except ValueError as e:
        # Configuration or API errors
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1) from e

    except Exception as e:
        # Unexpected errors
        console.print(f"[red]Error:[/red] Unexpected error: {e}")
        if config.server.log_level == "debug":
            console.print_exception()
        raise SystemExit(1) from e
