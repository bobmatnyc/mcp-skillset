"""MCP Skills - Dynamic RAG-powered skills for code assistants.

This package provides intelligent, context-aware skills to code assistants
via the Model Context Protocol (MCP) using hybrid RAG (vector + knowledge graph).
"""

from pathlib import Path


__version__ = "0.8.6"
__author__ = "MCP Skills Team"
__license__ = "MIT"

# Read version from VERSION file
_version_file = Path(__file__).parent / "VERSION"
if _version_file.exists():
    __version__ = _version_file.read_text().strip()


__all__ = [
    "__version__",
    "__author__",
    "__license__",
]
