# Bug Investigation: list_servers Failure with NativeCLIStrategy

**Date:** 2026-01-01
**Status:** Root cause identified
**Priority:** High
**Component:** py_mcp_installer

## Summary

The `list_servers()` method fails when the installation strategy is `NativeCLIStrategy` because this strategy intentionally raises `NotImplementedError` for the `list_servers()` operation. The current implementation in `installer.py` catches this exception and returns an empty list, but this creates a silent failure that can cause issues during setup workflows.

## Error Details

```
File "/Users/masa/.local/share/uv/tools/mcp-skillset/lib/python3.12/site-packages/mcp_skills/services/py_mcp_installer/src/py_mcp_installer/installer.py", line 411, in list_servers
    return self._strategy.list_servers(scope)
File "/Users/masa/.local/share/uv/tools/mcp-skillset/lib/python3.12/site-packages/mcp_skills/services/py_mcp_installer/src/py_mcp_installer/installation_strategy.py", line 276, in list_servers
    raise NotImplementedError("Native CLI list not supported, use JSON strategy")
```

## Root Cause Analysis

### 1. Strategy Pattern Design

The codebase uses a Strategy pattern with three implementations:

1. **NativeCLIStrategy**: Uses platform CLI commands (e.g., `claude mcp add`)
2. **JSONManipulationStrategy**: Directly reads/writes JSON config files
3. **TOMLManipulationStrategy**: Directly reads/writes TOML config files

### 2. The Problem

**NativeCLIStrategy.list_servers() is intentionally not implemented:**

```python
# installation_strategy.py, line 263-276
def list_servers(self, scope: Scope) -> list[MCPServerConfig]:
    """List servers using native CLI.

    Note: Most CLIs don't provide list functionality,
    so this falls back to JSON reading.

    Args:
        scope: Installation scope

    Returns:
        List of server configurations
    """
    # Most CLIs don't support listing, would need config path
    raise NotImplementedError("Native CLI list not supported, use JSON strategy")
```

**Current error handling in installer.py (lines 410-419):**

```python
def list_servers(self, scope: Scope = Scope.PROJECT) -> list[MCPServerConfig]:
    try:
        return self._strategy.list_servers(scope)
    except NotImplementedError as e:
        # Expected for strategies without native list support (e.g., NativeCLIStrategy)
        # This is not an error - strategies fall back to JSON reading elsewhere
        logger.debug(f"Strategy does not support list_servers: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to list servers: {e}", exc_info=True)
        return []
```

### 3. Platform Strategy Selection

**Claude Code (installer.py, lines 713-721):**
```python
if platform == Platform.CLAUDE_CODE:
    claude_strategy = ClaudeCodeStrategy()
    # Use the strategy's get_strategy method to get actual installer
    return claude_strategy.get_strategy(Scope.PROJECT)
```

**ClaudeCodeStrategy.get_strategy() (claude_code.py, lines 81-104):**
```python
def get_strategy(self, scope: Scope) -> InstallationStrategy:
    # Prefer native CLI if available
    if resolve_command_path("claude"):
        return NativeCLIStrategy(self.platform, "claude")

    # Fallback to JSON manipulation
    config_path = self.get_config_path(scope)
    return JSONManipulationStrategy(self.platform, config_path)
```

**Cursor (installer.py, lines 723-725):**
```python
elif platform == Platform.CURSOR:
    cursor_strategy = CursorStrategy()
    return cursor_strategy.get_strategy(Scope.PROJECT)
```

**CursorStrategy.get_strategy() (cursor.py, lines 76-93):**
```python
def get_strategy(self, scope: Scope) -> InstallationStrategy:
    """Get appropriate installation strategy for scope.

    Cursor only supports JSON manipulation (no native CLI).
    """
    config_path = self.get_config_path(scope)
    return JSONManipulationStrategy(self.platform, config_path)
```

### 4. The Actual Bug

The error message says "Native CLI list not supported" but **Cursor always uses JSONManipulationStrategy**, never NativeCLIStrategy. This suggests one of two scenarios:

**Scenario A: Misidentification**
- The platform detector might be incorrectly identifying Cursor as Claude Code
- If `claude` CLI exists in PATH, ClaudeCodeStrategy would return NativeCLIStrategy
- This would cause the error even though the actual platform is Cursor

**Scenario B: Cursor CLI Exists**
- User might have a `cursor` CLI command installed
- However, CursorStrategy doesn't check for CLI availability (unlike ClaudeCodeStrategy)
- CursorStrategy always returns JSONManipulationStrategy regardless

**Most Likely:** Scenario A - Platform misidentification or the error is actually happening during Claude Code setup, not Cursor setup, despite what the context suggests.

## Code Flow Analysis

### When list_servers() is called:

1. **installer.py:394** - `list_servers(scope)` is called
2. **installer.py:411** - Delegates to `self._strategy.list_servers(scope)`
3. **If NativeCLIStrategy:**
   - Raises `NotImplementedError`
   - Caught at line 412-416
   - Returns empty list `[]`
4. **If JSONManipulationStrategy:**
   - Calls `self.config_manager.list_servers()`
   - Returns actual server list

### Problem with current design:

**Silent failure:** When NativeCLIStrategy is selected, `list_servers()` returns `[]` instead of reading from JSON config. This means:

- `get_server(name, scope)` will always return `None` (line 439)
- Server existence checks fail
- Duplicate server detection doesn't work
- Setup validation appears to succeed but servers aren't found

## Dependencies

### Methods that depend on list_servers():

1. **get_server()** (line 421-443): Relies on list_servers() to find specific server
2. **install_server()** (line 318): Checks for existing server using get_server()
3. Any setup/validation logic that verifies server installation

### Impact:

When NativeCLIStrategy is selected:
- ✅ **install()** works (uses CLI directly)
- ✅ **uninstall()** works (uses CLI directly)
- ✅ **update()** works (uses CLI directly)
- ❌ **list_servers()** fails silently (returns empty list)
- ❌ **get_server()** fails silently (returns None)
- ❌ **Duplicate detection** broken (can install same server twice)

## Files That Need Modification

### Primary Files:

1. **installer.py** (lines 394-419)
   - `list_servers()` method needs to fallback to JSON reading when NativeCLIStrategy is used
   - OR should use a hybrid strategy

2. **claude_code.py** (lines 81-142)
   - `get_strategy()` should return a strategy that supports both CLI and JSON operations
   - OR should maintain reference to config path for fallback operations

3. **installation_strategy.py** (lines 123-388)
   - NativeCLIStrategy needs a fallback mechanism for list_servers()
   - Requires config_path to read JSON as fallback

### Supporting Files:

4. **platform_detector.py** (investigation needed)
   - May need better platform detection to avoid misidentification

## Recommended Fix Approaches

### Option 1: Hybrid Strategy (Recommended)

Create a `HybridStrategy` that wraps both NativeCLIStrategy and JSONManipulationStrategy:

```python
class HybridStrategy(InstallationStrategy):
    """Strategy that uses CLI for write operations, JSON for read operations."""

    def __init__(self, cli_strategy: NativeCLIStrategy, json_strategy: JSONManipulationStrategy):
        self.cli_strategy = cli_strategy
        self.json_strategy = json_strategy

    def install(self, server: MCPServerConfig, scope: Scope) -> InstallationResult:
        # Use CLI for installation
        return self.cli_strategy.install(server, scope)

    def uninstall(self, name: str, scope: Scope) -> InstallationResult:
        # Use CLI for uninstallation
        return self.cli_strategy.uninstall(name, scope)

    def update(self, server: MCPServerConfig, scope: Scope) -> InstallationResult:
        # Use CLI for updates
        return self.cli_strategy.update(server, scope)

    def list_servers(self, scope: Scope) -> list[MCPServerConfig]:
        # Use JSON for listing (CLI doesn't support this)
        return self.json_strategy.list_servers(scope)

    def validate(self) -> bool:
        # Valid if either strategy is valid
        return self.cli_strategy.validate() or self.json_strategy.validate()
```

**ClaudeCodeStrategy.get_strategy() modification:**

```python
def get_strategy(self, scope: Scope) -> InstallationStrategy:
    config_path = self.get_config_path(scope)
    json_strategy = JSONManipulationStrategy(self.platform, config_path)

    # If CLI is available, use hybrid strategy
    if resolve_command_path("claude"):
        cli_strategy = NativeCLIStrategy(self.platform, "claude")
        return HybridStrategy(cli_strategy, json_strategy)

    # Otherwise use JSON only
    return json_strategy
```

**Pros:**
- Clean separation of concerns
- No changes to existing strategies
- Maintains CLI preference for write operations
- Reliable read operations via JSON
- Easy to test

**Cons:**
- Adds another strategy class
- Slightly more complex architecture

### Option 2: NativeCLIStrategy Fallback (Alternative)

Modify NativeCLIStrategy to accept an optional config_path and fallback to JSON reading:

```python
class NativeCLIStrategy(InstallationStrategy):
    def __init__(self, platform: Platform, cli_command: str, config_path: Path | None = None):
        self.platform = platform
        self.cli_command = cli_command
        self.config_path = config_path
        self._json_fallback = None
        if config_path:
            self._json_fallback = JSONManipulationStrategy(platform, config_path)

    def list_servers(self, scope: Scope) -> list[MCPServerConfig]:
        """List servers using JSON fallback."""
        if self._json_fallback:
            return self._json_fallback.list_servers(scope)
        else:
            raise NotImplementedError("Native CLI list not supported, use JSON strategy")
```

**Pros:**
- Minimal changes
- Backwards compatible
- No new classes

**Cons:**
- Violates single responsibility principle
- NativeCLIStrategy becomes stateful
- Mixes CLI and JSON concerns

### Option 3: Installer-level Fallback (Simplest)

Modify `MCPInstaller.list_servers()` to fallback to JSON reading:

```python
def list_servers(self, scope: Scope = Scope.PROJECT) -> list[MCPServerConfig]:
    """List all installed MCP servers."""
    try:
        return self._strategy.list_servers(scope)
    except NotImplementedError as e:
        # NativeCLIStrategy doesn't support listing, fallback to JSON
        logger.debug(f"Strategy does not support list_servers: {e}")
        logger.debug("Falling back to JSON config reading")

        # Create temporary JSON strategy for reading
        config_path = self._platform_info.config_path
        if not config_path:
            logger.warning("No config path available for fallback")
            return []

        json_strategy = JSONManipulationStrategy(
            self._platform_info.platform,
            config_path
        )
        return json_strategy.list_servers(scope)
    except Exception as e:
        logger.error(f"Failed to list servers: {e}", exc_info=True)
        return []
```

**Pros:**
- Quick fix
- No changes to strategy classes
- Works immediately

**Cons:**
- Installer becomes aware of strategy implementation details
- Violates separation of concerns
- Other methods (get_server, etc.) still broken

## Impact Analysis

### Current Behavior:

**When NativeCLIStrategy is selected:**
```python
installer.list_servers()  # Returns []
installer.get_server("mcp-ticketer")  # Returns None (even if installed)
```

**Setup workflow impact:**
```python
# During setup
installer.install_server("mcp-skillset", ...)  # Works via CLI
servers = installer.list_servers()  # Returns [] instead of ["mcp-skillset"]
if "mcp-skillset" not in [s.name for s in servers]:
    # Validation fails even though installation succeeded!
    raise SetupError("Installation failed")
```

### With Fix (Option 1 - Hybrid Strategy):

```python
installer.list_servers()  # Returns ["mcp-skillset", ...]
installer.get_server("mcp-ticketer")  # Returns MCPServerConfig(...)
```

## Testing Recommendations

### Unit Tests:

1. **Test NativeCLIStrategy with fallback:**
```python
def test_native_cli_list_servers_with_fallback():
    strategy = HybridStrategy(cli_strategy, json_strategy)
    servers = strategy.list_servers(Scope.PROJECT)
    assert len(servers) > 0
    assert servers[0].name == "test-server"
```

2. **Test platform strategy selection:**
```python
def test_claude_code_strategy_returns_hybrid():
    strategy = ClaudeCodeStrategy()
    installer_strategy = strategy.get_strategy(Scope.PROJECT)
    assert isinstance(installer_strategy, HybridStrategy)
```

### Integration Tests:

1. **Test full install -> list workflow:**
```python
def test_install_and_list_with_cli():
    installer = MCPInstaller.auto_detect()
    installer.install_server("test-server", ...)
    servers = installer.list_servers()
    assert any(s.name == "test-server" for s in servers)
```

## Next Steps

1. **Verify platform detection:** Check if Cursor is being misidentified as Claude Code
2. **Implement Option 1 (HybridStrategy):** Cleanest long-term solution
3. **Add tests:** Ensure list_servers() works with all strategy types
4. **Update documentation:** Clarify strategy selection behavior
5. **Add logging:** Better visibility into which strategy is selected and why

## Additional Notes

### Why NativeCLIStrategy doesn't support list_servers():

The comment in the code explains:
```python
# Most CLIs don't provide list functionality, would need config path
```

This is accurate - CLI commands like `claude mcp add` exist for write operations, but there's typically no `claude mcp list` command. To list servers, you must read the JSON config file.

### Design Philosophy:

The Strategy pattern is well-designed for write operations (install/uninstall/update) where different platforms have different CLI commands. However, read operations (list_servers) are more uniform - they all need to read config files. This suggests that **read operations should use a different mechanism than write operations**.

## Conclusion

The bug is a design limitation rather than a coding error. The Strategy pattern works well for write operations but fails for read operations when NativeCLIStrategy is selected. The recommended fix is to implement a HybridStrategy that uses CLI for writes and JSON for reads, providing the best of both worlds.

**Priority:** High - This breaks setup validation and server existence checks
**Effort:** Medium - Requires new HybridStrategy class and tests
**Risk:** Low - Changes are isolated to strategy selection logic
