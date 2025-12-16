"""py-mcp-installer-service Integration Wrapper.

This module provides a clean import wrapper for the py-mcp-installer-service
submodule, exposing its API for use within mcp-skillset.

The wrapper handles sys.path manipulation to make the submodule's src directory
importable and re-exports all necessary classes, types, and exceptions.

Usage:
    from mcp_skills.services.py_mcp_installer_wrapper import (
        MCPInstaller,
        Platform,
        InstallationResult,
    )

Design Decision: Centralized import point
- All py-mcp-installer imports go through this wrapper
- Prevents sys.path pollution across the codebase
- Makes submodule dependency explicit and auditable
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add py-mcp-installer src directory to sys.path
_submodule_src = (
    Path(__file__).parent / "py_mcp_installer" / "src"
)

if _submodule_src.exists() and str(_submodule_src) not in sys.path:
    sys.path.insert(0, str(_submodule_src))

# Re-export core classes
from py_mcp_installer import MCPDoctor, MCPInspector, MCPInstaller  # noqa: E402

# Re-export platform detection
from py_mcp_installer import PlatformDetector  # noqa: E402

# Re-export types
from py_mcp_installer import (  # noqa: E402
    DiagnosticIssue,
    DiagnosticReport,
    InspectionReport,
    InstallationResult,
    InstallMethod,
    MCPServerConfig,
    Platform,
    PlatformInfo,
    Scope,
    ServerDiagnostic,
    ValidationIssue,
)

# Re-export exceptions
from py_mcp_installer import (  # noqa: E402
    AtomicWriteError,
    BackupError,
    CommandNotFoundError,
    ConfigurationError,
    InstallationError,
    PlatformDetectionError,
    PlatformNotSupportedError,
    PyMCPInstallerError,
    ValidationError,
)

__all__ = [
    # Core classes
    "MCPInstaller",
    "MCPInspector",
    "MCPDoctor",
    "PlatformDetector",
    # Types
    "Platform",
    "PlatformInfo",
    "InstallationResult",
    "MCPServerConfig",
    "DiagnosticReport",
    "DiagnosticIssue",
    "ServerDiagnostic",
    "ValidationIssue",
    "InspectionReport",
    "Scope",
    "InstallMethod",
    # Exceptions
    "PyMCPInstallerError",
    "ConfigurationError",
    "InstallationError",
    "ValidationError",
    "PlatformDetectionError",
    "PlatformNotSupportedError",
    "CommandNotFoundError",
    "BackupError",
    "AtomicWriteError",
]
