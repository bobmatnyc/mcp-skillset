"""Main CLI entry point for mcp-skillset."""

from __future__ import annotations

import logging
import os


# Disable tokenizers parallelism to avoid fork warnings
# Must be set before any HuggingFace tokenizers are loaded
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configure logging to suppress noisy messages during CLI usage
# Only show WARNING and above for third-party libs, ERROR for our services
# Users can enable verbose output with MCP_SKILLSET_DEBUG=1
if os.environ.get("MCP_SKILLSET_DEBUG") == "1":
    logging.basicConfig(level=logging.DEBUG)
else:
    # Suppress most log output for clean CLI experience
    logging.basicConfig(level=logging.CRITICAL)
    # Allow warnings for critical issues only
    logging.getLogger("mcp_skills").setLevel(logging.CRITICAL)

import click

from mcp_skills import __version__

# Import all extracted commands
from mcp_skills.cli.commands.ask import ask
from mcp_skills.cli.commands.build_skill import build_skill
from mcp_skills.cli.commands.config import config
from mcp_skills.cli.commands.demo import demo
from mcp_skills.cli.commands.discover import discover
from mcp_skills.cli.commands.doctor import doctor, health
from mcp_skills.cli.commands.enrich import enrich
from mcp_skills.cli.commands.enrich_hook import enrich_hook
from mcp_skills.cli.commands.index import index
from mcp_skills.cli.commands.info import info, show
from mcp_skills.cli.commands.install import install
from mcp_skills.cli.commands.list_skills import list_skills
from mcp_skills.cli.commands.mcp_server import mcp
from mcp_skills.cli.commands.recommend import recommend
from mcp_skills.cli.commands.repo import repo
from mcp_skills.cli.commands.search import search
from mcp_skills.cli.commands.setup import setup
from mcp_skills.cli.commands.stats import stats


@click.group()
@click.version_option(version=__version__, prog_name="mcp-skillset")
def cli() -> None:
    """MCP Skills - Dynamic RAG-powered skills for code assistants.

    Provides intelligent, context-aware skills via Model Context Protocol
    using hybrid RAG (vector + knowledge graph).
    """
    pass


# Register all extracted commands
cli.add_command(setup)
cli.add_command(install)
cli.add_command(mcp)
cli.add_command(search)
cli.add_command(list_skills)
cli.add_command(info)
cli.add_command(show)
cli.add_command(recommend)
cli.add_command(demo)
cli.add_command(doctor)
cli.add_command(health)
cli.add_command(stats)
cli.add_command(repo)
cli.add_command(index)
cli.add_command(enrich)
cli.add_command(enrich_hook)
cli.add_command(config)
cli.add_command(build_skill)
cli.add_command(discover)
cli.add_command(ask)


if __name__ == "__main__":
    cli()
