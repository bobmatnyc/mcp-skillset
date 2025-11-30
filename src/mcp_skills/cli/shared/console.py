"""Shared Rich console instance for all CLI commands."""

from rich.console import Console


# Singleton console instance used by all commands
# This ensures consistent formatting and output handling
console = Console()
