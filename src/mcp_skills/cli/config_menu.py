"""Interactive configuration menu for mcp-skillset."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import questionary
import yaml
from questionary import Choice
from rich.console import Console
from rich.tree import Tree

from mcp_skills.models.config import HybridSearchConfig, HookConfig, MCPSkillsConfig
from mcp_skills.services.indexing import IndexingEngine
from mcp_skills.services.repository_manager import RepositoryManager
from mcp_skills.services.skill_manager import SkillManager


logger = logging.getLogger(__name__)
console = Console()


class ConfigMenu:
    """Interactive configuration menu manager.

    Provides a menu-based interface for configuring mcp-skillset settings.

    Design Decision: Menu-based configuration

    Rationale: Interactive menus provide better user experience than manual
    YAML editing, especially for users unfamiliar with configuration syntax.

    Trade-offs:
    - User Experience: Menu navigation vs. direct file editing
    - Validation: Immediate validation vs. error-prone manual editing
    - Discoverability: All options shown vs. documentation reading

    Alternatives Considered:
    1. Direct YAML editing: Rejected due to error-prone nature and lack of validation
    2. Web-based UI: Rejected due to complexity and dependencies
    3. Wizard-style (linear): Rejected due to reduced flexibility for power users

    Extension Points: Menu items can be added by extending MAIN_MENU_CHOICES
    and implementing corresponding handler methods.
    """

    # Configuration file path
    CONFIG_PATH = Path.home() / ".mcp-skillset" / "config.yaml"

    # Main menu choices
    MAIN_MENU_CHOICES = [
        "Base directory configuration",
        "Search settings (hybrid search weights)",
        "Repository management",
        "Hook settings (Claude Code integration)",
        "View current configuration",
        "Reset to defaults",
        "Exit",
    ]

    # Search mode presets
    SEARCH_MODE_CHOICES = [
        Choice("Balanced (50% vector, 50% graph)", value="balanced"),
        Choice("Semantic-focused (90% vector, 10% graph)", value="semantic_focused"),
        Choice("Graph-focused (30% vector, 70% graph)", value="graph_focused"),
        Choice("Current optimized (70% vector, 30% graph)", value="current"),
        Choice("Custom weights", value="custom"),
    ]

    # Repository action choices
    REPO_ACTION_CHOICES = [
        "Add new repository",
        "Remove repository",
        "Change repository priority",
        "Back to main menu",
    ]

    # Hook action choices
    HOOK_ACTION_CHOICES = [
        "Enable/disable hooks",
        "Configure threshold",
        "Configure max skills",
        "Test hook",
        "Back to main menu",
    ]

    def __init__(self) -> None:
        """Initialize configuration menu."""
        self.config = MCPSkillsConfig()
        self.running = True

    def run(self) -> None:
        """Run the interactive configuration menu.

        Main event loop that displays menu and handles user selections.
        Continues until user selects Exit.
        """
        console.print("\n[bold cyan]🔧 Interactive Configuration Menu[/bold cyan]\n")

        while self.running:
            try:
                choice = questionary.select(
                    "What would you like to configure?",
                    choices=self.MAIN_MENU_CHOICES,
                ).ask()

                if choice is None:  # User pressed Ctrl+C
                    self.running = False
                    break

                # Route to appropriate handler
                if choice == self.MAIN_MENU_CHOICES[0]:
                    self._configure_base_directory()
                elif choice == self.MAIN_MENU_CHOICES[1]:
                    self._configure_search_settings()
                elif choice == self.MAIN_MENU_CHOICES[2]:
                    self._configure_repositories()
                elif choice == self.MAIN_MENU_CHOICES[3]:
                    self._configure_hooks()
                elif choice == self.MAIN_MENU_CHOICES[4]:
                    self._view_configuration()
                elif choice == self.MAIN_MENU_CHOICES[5]:
                    self._reset_to_defaults()
                elif choice == self.MAIN_MENU_CHOICES[6]:
                    self.running = False

                if self.running:
                    console.print()  # Add spacing between menu iterations

            except KeyboardInterrupt:
                self.running = False
                console.print("\n[yellow]Configuration cancelled[/yellow]")

        console.print("[green]Configuration menu closed[/green]\n")

    def _configure_base_directory(self) -> None:
        """Configure base directory for mcp-skillset.

        Prompts user for base directory path, validates it's writable,
        and creates the directory if it doesn't exist.
        """
        current_dir = str(self.config.base_dir)

        console.print("\n[bold]Base Directory Configuration[/bold]")
        console.print(f"Current: [cyan]{current_dir}[/cyan]\n")

        new_dir = questionary.path(
            "Enter base directory path (or press Enter to keep current):",
            default=current_dir,
        ).ask()

        if new_dir is None:  # User cancelled
            return

        new_path = Path(new_dir).expanduser()

        # Validate path is writable
        try:
            new_path.mkdir(parents=True, exist_ok=True)

            # Test write access
            test_file = new_path / ".write_test"
            test_file.touch()
            test_file.unlink()

            # Update configuration
            self._save_config({"base_dir": str(new_path)})
            self.config.base_dir = new_path

            console.print(f"\n[green]✓[/green] Base directory updated to: {new_path}")

        except (PermissionError, OSError) as e:
            console.print(f"\n[red]✗[/red] Cannot write to directory: {e}")
            logger.error(f"Base directory validation failed: {e}")

    def _configure_search_settings(self) -> None:
        """Configure hybrid search weight settings.

        Allows users to choose from preset search modes or configure
        custom vector/graph weights.
        """
        console.print("\n[bold]Search Settings Configuration[/bold]")

        # Get current settings
        current_preset = self.config.hybrid_search.preset or "custom"
        current_vector = self.config.hybrid_search.vector_weight
        current_graph = self.config.hybrid_search.graph_weight

        console.print(
            f"Current: [cyan]{current_preset}[/cyan] "
            f"(vector={current_vector:.1f}, graph={current_graph:.1f})\n"
        )

        # Select search mode
        mode = questionary.select(
            "Choose search mode:",
            choices=self.SEARCH_MODE_CHOICES,
        ).ask()

        if mode is None:  # User cancelled
            return

        if mode == "custom":
            # Prompt for custom weights
            self._configure_custom_weights()
        else:
            # Use preset
            preset_config = MCPSkillsConfig._get_preset(mode)

            config_data = {
                "hybrid_search": {
                    "preset": mode,
                    "vector_weight": preset_config.vector_weight,
                    "graph_weight": preset_config.graph_weight,
                }
            }

            self._save_config(config_data)
            self.config.hybrid_search = preset_config

            console.print(
                f"\n[green]✓[/green] Search mode set to: {mode} "
                f"(vector={preset_config.vector_weight:.1f}, "
                f"graph={preset_config.graph_weight:.1f})"
            )

    def _configure_custom_weights(self) -> None:
        """Configure custom vector/graph weights.

        Prompts for vector weight and automatically calculates graph weight
        to ensure they sum to 1.0.
        """
        console.print("\n[bold]Custom Weight Configuration[/bold]")
        console.print("Vector weight + Graph weight must equal 1.0\n")

        # Prompt for vector weight
        vector_weight_str = questionary.text(
            "Enter vector weight (0.0-1.0):",
            default="0.7",
            validate=lambda x: self._validate_weight(x),
        ).ask()

        if vector_weight_str is None:  # User cancelled
            return

        vector_weight = float(vector_weight_str)
        graph_weight = 1.0 - vector_weight

        # Confirm weights
        console.print(
            f"\nWeights: vector={vector_weight:.1f}, graph={graph_weight:.1f}"
        )

        if questionary.confirm("Save these weights?", default=True).ask():
            config_data = {
                "hybrid_search": {
                    "vector_weight": vector_weight,
                    "graph_weight": graph_weight,
                }
            }

            self._save_config(config_data)
            self.config.hybrid_search = HybridSearchConfig(
                vector_weight=vector_weight,
                graph_weight=graph_weight,
                preset="custom",
            )

            console.print("\n[green]✓[/green] Custom weights saved")

    def _configure_repositories(self) -> None:
        """Configure repository settings.

        Provides submenu for adding, removing, or changing priority of
        skill repositories.
        """
        console.print("\n[bold]Repository Management[/bold]\n")

        action = questionary.select(
            "Choose repository action:",
            choices=self.REPO_ACTION_CHOICES,
        ).ask()

        if action is None:  # User cancelled
            return

        if action == self.REPO_ACTION_CHOICES[0]:
            self._add_repository()
        elif action == self.REPO_ACTION_CHOICES[1]:
            self._remove_repository()
        elif action == self.REPO_ACTION_CHOICES[2]:
            self._change_repository_priority()
        # "Back to main menu" does nothing, just returns

    def _add_repository(self) -> None:
        """Add a new repository.

        Prompts for repository URL, name, and priority, then clones
        the repository.
        """
        console.print("\n[bold]Add New Repository[/bold]\n")

        # Prompt for URL
        url = questionary.text(
            "Enter repository URL:",
            validate=lambda x: len(x.strip()) > 0 or "URL cannot be empty",
        ).ask()

        if url is None:  # User cancelled
            return

        # Prompt for priority
        priority_str = questionary.text(
            "Enter priority (0-100):",
            default="50",
            validate=lambda x: self._validate_priority(x),
        ).ask()

        if priority_str is None:  # User cancelled
            return

        priority = int(priority_str)

        # Add repository
        try:
            repo_manager = RepositoryManager()
            repo = repo_manager.add_repository(url, priority=priority)

            console.print("\n[green]✓[/green] Repository added successfully")
            console.print(f"  • ID: {repo.id}")
            console.print(f"  • Skills: {repo.skill_count}")
            console.print(f"  • Priority: {repo.priority}")
            console.print(
                "\n[dim]Tip: Run 'mcp-skillset index' to index new skills[/dim]"
            )

        except Exception as e:
            console.print(f"\n[red]✗[/red] Failed to add repository: {e}")
            logger.error(f"Repository add failed: {e}")

    def _remove_repository(self) -> None:
        """Remove an existing repository.

        Lists current repositories and allows user to select one for removal.
        """
        console.print("\n[bold]Remove Repository[/bold]\n")

        try:
            repo_manager = RepositoryManager()
            repos = repo_manager.list_repositories()

            if not repos:
                console.print("[yellow]No repositories configured[/yellow]")
                return

            # Create choices from repositories
            choices = [
                Choice(
                    f"{repo.id} (priority: {repo.priority}, skills: {repo.skill_count})",
                    value=repo.id,
                )
                for repo in repos
            ]
            choices.append(Choice("Cancel", value=None))

            repo_id = questionary.select(
                "Select repository to remove:",
                choices=choices,
            ).ask()

            if repo_id is None:  # User cancelled
                return

            # Confirm removal
            if questionary.confirm(
                f"Are you sure you want to remove {repo_id}?",
                default=False,
            ).ask():
                repo_manager.remove_repository(repo_id)
                console.print(f"\n[green]✓[/green] Repository {repo_id} removed")
                console.print(
                    "\n[dim]Tip: Run 'mcp-skillset index --force' to rebuild index[/dim]"
                )
            else:
                console.print("\n[yellow]Removal cancelled[/yellow]")

        except Exception as e:
            console.print(f"\n[red]✗[/red] Failed to remove repository: {e}")
            logger.error(f"Repository removal failed: {e}")

    def _change_repository_priority(self) -> None:
        """Change priority of an existing repository.

        Lists current repositories and allows user to select one and
        update its priority.
        """
        console.print("\n[bold]Change Repository Priority[/bold]\n")

        try:
            repo_manager = RepositoryManager()
            repos = repo_manager.list_repositories()

            if not repos:
                console.print("[yellow]No repositories configured[/yellow]")
                return

            # Create choices from repositories
            choices = [
                Choice(
                    f"{repo.id} (current priority: {repo.priority})",
                    value=repo.id,
                )
                for repo in repos
            ]
            choices.append(Choice("Cancel", value=None))

            repo_id = questionary.select(
                "Select repository:",
                choices=choices,
            ).ask()

            if repo_id is None:  # User cancelled
                return

            # Get current priority
            repo = repo_manager.get_repository(repo_id)
            if not repo:
                console.print(f"\n[red]✗[/red] Repository not found: {repo_id}")
                return

            # Prompt for new priority
            priority_str = questionary.text(
                "Enter new priority (0-100):",
                default=str(repo.priority),
                validate=lambda x: self._validate_priority(x),
            ).ask()

            if priority_str is None:  # User cancelled
                return

            new_priority = int(priority_str)

            # Update priority
            repo.priority = new_priority
            repo_manager.metadata_store.update_repository(repo)
            console.print(
                f"\n[green]✓[/green] Priority updated for {repo_id}: "
                f"{repo.priority} → {new_priority}"
            )

        except Exception as e:
            console.print(f"\n[red]✗[/red] Failed to change priority: {e}")
            logger.error(f"Priority change failed: {e}")

    def _configure_hooks(self) -> None:
        """Configure Claude Code hook settings.

        Provides submenu for enabling/disabling hooks, setting threshold,
        and configuring max skills.
        """
        console.print("\n[bold]Hook Settings (Claude Code Integration)[/bold]\n")

        # Show current settings
        hooks_config = getattr(self.config, 'hooks', None)
        if hooks_config:
            console.print(f"Current settings:")
            console.print(f"  • Enabled: [cyan]{hooks_config.enabled}[/cyan]")
            console.print(f"  • Threshold: [cyan]{hooks_config.threshold}[/cyan]")
            console.print(f"  • Max skills: [cyan]{hooks_config.max_skills}[/cyan]")
        else:
            console.print("[dim]Using defaults (enabled, threshold=0.6, max_skills=5)[/dim]")
        console.print()

        action = questionary.select(
            "Choose hook action:",
            choices=self.HOOK_ACTION_CHOICES,
        ).ask()

        if action is None:  # User cancelled
            return

        if action == self.HOOK_ACTION_CHOICES[0]:
            self._toggle_hooks()
        elif action == self.HOOK_ACTION_CHOICES[1]:
            self._configure_hook_threshold()
        elif action == self.HOOK_ACTION_CHOICES[2]:
            self._configure_hook_max_skills()
        elif action == self.HOOK_ACTION_CHOICES[3]:
            self._test_hook()
        # "Back to main menu" does nothing, just returns

    def _toggle_hooks(self) -> None:
        """Toggle hook enabled/disabled state."""
        hooks_config = getattr(self.config, 'hooks', None)
        current_enabled = hooks_config.enabled if hooks_config else True

        new_enabled = questionary.confirm(
            "Enable Claude Code hooks?",
            default=current_enabled,
        ).ask()

        if new_enabled is None:  # User cancelled
            return

        self._save_config({"hooks": {"enabled": new_enabled}})

        # Update in-memory config
        if not hasattr(self.config, 'hooks') or self.config.hooks is None:
            self.config.hooks = HookConfig()
        self.config.hooks.enabled = new_enabled

        status = "[green]enabled[/green]" if new_enabled else "[red]disabled[/red]"
        console.print(f"\n[green]✓[/green] Hooks {status}")

    def _configure_hook_threshold(self) -> None:
        """Configure hook similarity threshold."""
        hooks_config = getattr(self.config, 'hooks', None)
        current_threshold = hooks_config.threshold if hooks_config else 0.6

        console.print("\n[bold]Hook Threshold Configuration[/bold]")
        console.print("Higher threshold = fewer but more relevant skill suggestions")
        console.print("Lower threshold = more suggestions but less precise\n")

        threshold_str = questionary.text(
            "Enter threshold (0.0-1.0):",
            default=str(current_threshold),
            validate=lambda x: self._validate_weight(x),
        ).ask()

        if threshold_str is None:  # User cancelled
            return

        threshold = float(threshold_str)

        self._save_config({"hooks": {"threshold": threshold}})

        # Update in-memory config
        if not hasattr(self.config, 'hooks') or self.config.hooks is None:
            self.config.hooks = HookConfig()
        self.config.hooks.threshold = threshold

        console.print(f"\n[green]✓[/green] Threshold set to: {threshold}")

    def _configure_hook_max_skills(self) -> None:
        """Configure maximum skills to suggest in hooks."""
        hooks_config = getattr(self.config, 'hooks', None)
        current_max = hooks_config.max_skills if hooks_config else 5

        console.print("\n[bold]Max Skills Configuration[/bold]")
        console.print("Maximum number of skills to suggest in hook hints.\n")

        max_skills_str = questionary.text(
            "Enter max skills (1-10):",
            default=str(current_max),
            validate=lambda x: self._validate_max_skills(x),
        ).ask()

        if max_skills_str is None:  # User cancelled
            return

        max_skills = int(max_skills_str)

        self._save_config({"hooks": {"max_skills": max_skills}})

        # Update in-memory config
        if not hasattr(self.config, 'hooks') or self.config.hooks is None:
            self.config.hooks = HookConfig()
        self.config.hooks.max_skills = max_skills

        console.print(f"\n[green]✓[/green] Max skills set to: {max_skills}")

    def _test_hook(self) -> None:
        """Test the hook with a sample prompt."""
        import json
        import subprocess

        console.print("\n[bold]Test Hook[/bold]")
        console.print("Test the enrich-hook command with a sample prompt.\n")

        test_prompt = questionary.text(
            "Enter test prompt:",
            default="Write pytest tests for my API",
        ).ask()

        if test_prompt is None:  # User cancelled
            return

        console.print("\n[dim]Running enrich-hook...[/dim]")

        try:
            # Run the enrich-hook command
            input_data = json.dumps({"user_prompt": test_prompt})
            result = subprocess.run(
                ["mcp-skillset", "enrich-hook"],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = json.loads(result.stdout)
                if output and "systemMessage" in output:
                    console.print(f"\n[green]✓[/green] Hook response:")
                    console.print(f"  [cyan]{output['systemMessage']}[/cyan]")
                else:
                    console.print("\n[yellow]No matching skills found for this prompt[/yellow]")
                    console.print("[dim]Try a more specific prompt or lower the threshold[/dim]")
            else:
                console.print(f"\n[red]✗[/red] Hook failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            console.print("\n[red]✗[/red] Hook timed out (>10s)")
        except FileNotFoundError:
            console.print("\n[red]✗[/red] mcp-skillset command not found")
            console.print("[dim]Make sure mcp-skillset is installed: pip install mcp-skillset[/dim]")
        except json.JSONDecodeError:
            console.print("\n[red]✗[/red] Invalid JSON response from hook")
        except Exception as e:
            console.print(f"\n[red]✗[/red] Test failed: {e}")

    def _view_configuration(self) -> None:
        """Display current configuration.

        Shows the same information as the --show flag.
        """
        console.print("\n[bold cyan]Current Configuration[/bold cyan]\n")

        try:
            # Create configuration tree (same as original config command)
            tree = Tree("[bold cyan]mcp-skillset Configuration[/bold cyan]")

            # Base directory
            base_node = tree.add(
                f"📁 Base Directory: [yellow]{self.config.base_dir}[/yellow]"
            )

            # Repositories
            repos_dir = self.config.repos_dir
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
            chromadb_dir = self.config.base_dir / "chromadb"
            vector_node = base_node.add(
                f"🔍 Vector Store: [yellow]{chromadb_dir}[/yellow]"
            )

            try:
                skill_manager = SkillManager()
                indexing_engine = IndexingEngine(skill_manager=skill_manager)
                stats = indexing_engine.get_stats()

                if stats.total_skills > 0:
                    vector_node.add(
                        f"[green]✓[/green] {stats.total_skills} skills indexed"
                    )
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
                if stats.graph_nodes > 0:
                    graph_node.add(f"[green]✓[/green] {stats.graph_nodes} nodes")
                    graph_node.add(f"[green]✓[/green] {stats.graph_edges} edges")
                else:
                    graph_node.add("[dim]Empty (run: mcp-skillset index)[/dim]")
            except Exception as e:
                graph_node.add(f"[red]Error: {e}[/red]")

            # Hybrid search settings
            search_node = base_node.add("⚖️  Hybrid Search")
            preset = self.config.hybrid_search.preset or "custom"
            search_node.add(f"[green]✓[/green] Mode: {preset}")
            search_node.add(
                f"[green]✓[/green] Vector weight: {self.config.hybrid_search.vector_weight:.1f}"
            )
            search_node.add(
                f"[green]✓[/green] Graph weight: {self.config.hybrid_search.graph_weight:.1f}"
            )

            # Hook settings
            hook_node = base_node.add("🪝 Hook Settings")
            hooks_config = getattr(self.config, 'hooks', None)
            if hooks_config:
                status = "[green]enabled[/green]" if hooks_config.enabled else "[red]disabled[/red]"
                hook_node.add(f"[green]✓[/green] Status: {status}")
                hook_node.add(f"[green]✓[/green] Threshold: {hooks_config.threshold}")
                hook_node.add(f"[green]✓[/green] Max skills: {hooks_config.max_skills}")
            else:
                hook_node.add("[dim]Using defaults (enabled, 0.6, 5)[/dim]")

            console.print(tree)

            # Wait for user to continue
            console.print("\n[dim]Press Enter to continue...[/dim]")
            questionary.text("", qmark="").ask()

        except Exception as e:
            console.print(f"\n[red]✗[/red] Failed to display configuration: {e}")
            logger.error(f"Configuration display failed: {e}")

    def _reset_to_defaults(self) -> None:
        """Reset configuration to defaults.

        Prompts for confirmation before deleting the config file.
        """
        console.print("\n[bold yellow]⚠ Reset to Defaults[/bold yellow]\n")
        console.print("This will reset ALL settings to their default values.")
        console.print("Repositories will not be deleted.\n")

        if questionary.confirm(
            "Are you sure you want to reset configuration?",
            default=False,
        ).ask():
            try:
                if self.CONFIG_PATH.exists():
                    self.CONFIG_PATH.unlink()

                # Reload config with defaults
                self.config = MCPSkillsConfig()

                console.print("\n[green]✓[/green] Configuration reset to defaults")

            except Exception as e:
                console.print(f"\n[red]✗[/red] Failed to reset configuration: {e}")
                logger.error(f"Configuration reset failed: {e}")
        else:
            console.print("\n[yellow]Reset cancelled[/yellow]")

    def _save_config(self, config_data: dict[str, Any]) -> None:
        """Save configuration to YAML file.

        Args:
            config_data: Configuration data to save (merged with existing)

        Design Decision: Immediate persistence

        Rationale: Save changes immediately after each modification to prevent
        data loss if user exits or encounters errors later in the session.

        Trade-off: Multiple file writes vs. transactional save-all-at-once
        """
        try:
            # Ensure config directory exists
            self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

            # Load existing config if it exists
            existing_config: dict[str, Any] = {}
            if self.CONFIG_PATH.exists():
                with open(self.CONFIG_PATH) as f:
                    existing_config = yaml.safe_load(f) or {}

            # Merge new config with existing (deep merge for nested dicts)
            for key, value in config_data.items():
                if isinstance(value, dict) and key in existing_config:
                    # Deep merge for nested dictionaries
                    existing_config[key] = {**existing_config[key], **value}
                else:
                    existing_config[key] = value

            # Write updated config
            with open(self.CONFIG_PATH, "w") as f:
                yaml.dump(existing_config, f, default_flow_style=False, sort_keys=False)

            logger.debug(f"Configuration saved to {self.CONFIG_PATH}")

        except Exception as e:
            console.print(f"\n[red]✗[/red] Failed to save configuration: {e}")
            logger.error(f"Configuration save failed: {e}")
            raise

    @staticmethod
    def _validate_weight(value: str) -> bool | str:
        """Validate weight input (0.0-1.0).

        Args:
            value: Input string to validate

        Returns:
            True if valid, error message string if invalid
        """
        try:
            weight = float(value)
            if 0.0 <= weight <= 1.0:
                return True
            return "Weight must be between 0.0 and 1.0"
        except ValueError:
            return "Please enter a valid number"

    @staticmethod
    def _validate_priority(value: str) -> bool | str:
        """Validate priority input (0-100).

        Args:
            value: Input string to validate

        Returns:
            True if valid, error message string if invalid
        """
        try:
            priority = int(value)
            if 0 <= priority <= 100:
                return True
            return "Priority must be between 0 and 100"
        except ValueError:
            return "Please enter a valid integer"

    @staticmethod
    def _validate_max_skills(value: str) -> bool | str:
        """Validate max skills input (1-10).

        Args:
            value: Input string to validate

        Returns:
            True if valid, error message string if invalid
        """
        try:
            max_skills = int(value)
            if 1 <= max_skills <= 10:
                return True
            return "Max skills must be between 1 and 10"
        except ValueError:
            return "Please enter a valid integer"
