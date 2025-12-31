# py_mcp_installer Installation Flow Analysis

**Date:** 2025-12-17
**Focus:** Understanding installation flow and adding auto-update capability

## Executive Summary

The py_mcp_installer code has a well-designed architecture with clear separation of concerns, but currently requires manual handling of "server already exists" scenarios through uninstall-then-install pattern. The codebase already has all the building blocks needed for auto-update functionality through the `update_server()` method in `ConfigManager`, but it's not exposed through the main `MCPInstaller` API.

## Current Installation Flow

### 1. Entry Point: `MCPInstaller.install_server()` (installer.py:183-323)

**Location:** `src/py_mcp_installer/installer.py`

**Current behavior:**
1. Validates server name and command parameters
2. Auto-detects installation method if not provided
3. Creates `MCPServerConfig` object
4. Validates configuration using inspector
5. Delegates to strategy's `install()` method
6. **Raises exception if server already exists**

### 2. Strategy Layer: `JSONManipulationStrategy.install()` (installation_strategy.py:390-426)

**Location:** `src/py_mcp_installer/installation_strategy.py`

**Current behavior:**
1. Calls `config_manager.add_server(server)`
2. If server exists, `add_server()` raises `ValidationError`
3. Strategy catches `ValidationError` and re-raises as `InstallationError` with message:
   ```python
   raise InstallationError(
       f"Server '{server.name}' already exists",
       recovery_suggestion="Use update operation or remove existing server first",
   )
   ```

### 3. Config Manager Layer: `ConfigManager.add_server()` (config_manager.py:209-269)

**Location:** `src/py_mcp_installer/config_manager.py`

**Current behavior:**
1. Reads current configuration
2. **Checks if server already exists** (line 244):
   ```python
   if server.name in config[servers_key]:
       raise ValidationError(
           f"Server '{server.name}' already exists in configuration",
           recovery_suggestion=(
               "Use update_server() to modify existing server, "
               "or remove it first"
           ),
       )
   ```
3. Builds server dictionary and adds to config
4. Writes config atomically with backup

## Available Methods for Update vs Add

### ConfigManager Methods

**Three distinct methods available:**

1. **`add_server(server: MCPServerConfig)`** (line 209)
   - **Purpose:** Add new server only
   - **Behavior:** Raises `ValidationError` if server exists
   - **Use case:** First-time installation

2. **`update_server(name: str, server: MCPServerConfig)`** (line 305)
   - **Purpose:** Update existing server only
   - **Behavior:** Raises `ValidationError` if server doesn't exist
   - **Use case:** Modifying existing configuration
   - **Key code:**
     ```python
     # Check if server exists
     if servers_key not in config or name not in config[servers_key]:
         raise ValidationError(
             f"Server '{name}' not found in configuration",
             recovery_suggestion="Use add_server() to create new server",
         )
     ```

3. **`get_server(name: str) -> MCPServerConfig | None`** (line 393)
   - **Purpose:** Check if server exists
   - **Returns:** Server config if found, None otherwise
   - **Use case:** Pre-flight check before add/update decision

### InstallationStrategy Methods

Both `JSONManipulationStrategy` and `TOMLManipulationStrategy` have:
- `install(server, scope)` - delegates to `config_manager.add_server()`
- `uninstall(name, scope)` - delegates to `config_manager.remove_server()`
- `list_servers(scope)` - delegates to `config_manager.list_servers()`

**Gap:** No `update()` method in strategies that would delegate to `config_manager.update_server()`

## Current Workaround Pattern (agent_installer.py)

**Location:** `src/mcp_skills/services/agent_installer.py:145-158`

**Pattern in use:**
```python
# Handle force mode by uninstalling first
if force and not dry_run:
    # Ignore uninstall errors (server may not exist)
    with contextlib.suppress(PyMCPInstallerError):
        installer.uninstall_server("mcp-skillset")

# Install the server
result: PyInstallResult = installer.install_server(
    name="mcp-skillset",
    command="mcp-skillset",
    args=["mcp"],
    description="Dynamic RAG-powered skills for code assistants",
)
```

**Issues with current pattern:**
1. Requires caller to implement force mode logic
2. Two separate operations (uninstall + install) instead of atomic update
3. Temporary state where server is removed but not yet re-added
4. Caller must handle exception suppression
5. Not discoverable - users must know this pattern

## Recommended Auto-Update Implementation

### Option 1: Smart Install (Recommended)

**Add `force` parameter to `MCPInstaller.install_server()`:**

```python
def install_server(
    self,
    name: str,
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    description: str = "",
    scope: Scope = Scope.PROJECT,
    method: InstallMethod | None = None,
    force: bool = False,  # NEW PARAMETER
) -> InstallationResult:
```

**Implementation logic:**
```python
# Create server config
server = MCPServerConfig(
    name=name,
    command=command,
    args=args or [],
    env=env or {},
    description=description,
)

# Check if server exists
existing_server = self.get_server(name, scope)

if existing_server and force:
    # Update existing server
    logger.info(f"Server '{name}' exists, updating configuration (force=True)")
    # Delegate to strategy's update method (NEW)
    result = self._strategy.update(server, scope)
elif existing_server and not force:
    # Server exists, no force - raise error (current behavior)
    raise InstallationError(
        f"Server '{name}' already exists",
        recovery_suggestion="Use force=True to update existing server",
    )
else:
    # New server - install normally
    result = self._strategy.install(server, scope)
```

**Required changes:**
1. Add `force` parameter to `MCPInstaller.install_server()`
2. Add `update()` method to `InstallationStrategy` base class
3. Implement `update()` in `JSONManipulationStrategy` and `TOMLManipulationStrategy`
4. Update `agent_installer.py` to pass `force=True` instead of manual uninstall

### Option 2: Add Separate Update Method

**Add new method to `MCPInstaller`:**

```python
def update_server(
    self,
    name: str,
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    description: str = "",
    scope: Scope = Scope.PROJECT,
) -> InstallationResult:
    """Update existing MCP server configuration."""
    # Implementation mirrors install_server but uses update strategy
```

**Pros:**
- Explicit API for update operations
- Follows principle of least surprise (separate methods for separate operations)

**Cons:**
- More API surface area
- Requires callers to know when to use `install` vs `update`
- Doesn't solve the "update or install" use case

### Option 3: Add Upsert Method (Alternative)

**Add new convenience method:**

```python
def install_or_update_server(
    self,
    name: str,
    command: str,
    # ... same parameters as install_server
) -> InstallationResult:
    """Install server if new, update if exists (upsert operation)."""
    existing = self.get_server(name, scope)
    if existing:
        return self.update_server(name, command, args, env, description, scope)
    else:
        return self.install_server(name, command, args, env, description, scope)
```

**Pros:**
- Clear intent in method name
- Handles both cases automatically

**Cons:**
- Additional method to maintain
- Could encourage "always upsert" pattern instead of intentional install

## Implementation Recommendation

**Use Option 1: Smart Install with `force` parameter**

**Rationale:**
1. **Minimal API changes:** Single new parameter, no new methods
2. **Clear semantics:** `force=True` clearly indicates "overwrite if exists"
3. **Backward compatible:** Default `force=False` maintains current behavior
4. **Industry standard:** Matches behavior of CLI tools (e.g., `cp -f`, `rm -f`)
5. **Atomic operation:** Update is single operation, not uninstall+install
6. **Preserves backups:** ConfigManager creates backup before update

### Implementation Steps

#### Step 1: Add `update()` to `InstallationStrategy` base class

**File:** `installation_strategy.py`

```python
@abstractmethod
def update(self, server: MCPServerConfig, scope: Scope) -> InstallationResult:
    """Update existing MCP server configuration.

    Args:
        server: Updated server configuration
        scope: Installation scope

    Returns:
        InstallationResult with status and details

    Raises:
        InstallationError: If server doesn't exist or update fails
    """
    pass
```

#### Step 2: Implement `update()` in `JSONManipulationStrategy`

**File:** `installation_strategy.py`

```python
def update(self, server: MCPServerConfig, scope: Scope) -> InstallationResult:
    """Update server by modifying JSON config.

    Args:
        server: Updated server configuration
        scope: Installation scope (unused for JSON)

    Returns:
        InstallationResult with update status

    Raises:
        InstallationError: If server doesn't exist or update fails
    """
    try:
        # Update server using config manager
        self.config_manager.update_server(server.name, server)

        return InstallationResult(
            success=True,
            platform=self.platform,
            server_name=server.name,
            method=InstallMethod.DIRECT,
            message=f"Successfully updated '{server.name}' in {self.config_path}",
            config_path=self.config_path,
        )

    except ValidationError as e:
        # Server doesn't exist
        raise InstallationError(
            f"Server '{server.name}' not found",
            recovery_suggestion="Use install operation to create new server",
        ) from e
    except Exception as e:
        raise InstallationError(
            f"Failed to update server: {e}",
            recovery_suggestion="Check config file permissions and syntax",
        ) from e
```

**Mirror implementation for `TOMLManipulationStrategy`**

#### Step 3: Add `force` parameter to `MCPInstaller.install_server()`

**File:** `installer.py`

```python
def install_server(
    self,
    name: str,
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    description: str = "",
    scope: Scope = Scope.PROJECT,
    method: InstallMethod | None = None,
    force: bool = False,  # NEW
) -> InstallationResult:
    """Install MCP server.

    Auto-detects best installation method if not specified. Creates backup
    of existing config before making changes.

    Args:
        name: Unique server identifier (e.g., "mcp-ticketer")
        command: Executable command (e.g., "uv", "/usr/bin/python")
        args: Command arguments (e.g., ["run", "mcp-ticketer", "mcp"])
        env: Environment variables (e.g., {"API_KEY": "..."})
        description: Human-readable description
        scope: Installation scope (PROJECT or GLOBAL)
        method: Installation method (auto-detect if None)
        force: If True, update server if it already exists  # NEW

    Returns:
        InstallationResult with success status and details

    Raises:
        ValidationError: If server configuration is invalid
        InstallationError: If installation fails
    """
    logger.info(f"Installing server: {name}")

    # ... existing validation code ...

    # Create server config
    server = MCPServerConfig(
        name=name,
        command=command,
        args=args or [],
        env=env or {},
        description=description,
    )

    # ... existing validation code ...

    # Check if server exists
    existing_server = self.get_server(name, scope)

    if existing_server:
        if force:
            # Update existing server
            logger.info(f"Server '{name}' exists, updating (force=True)")
            if self.dry_run:
                return InstallationResult(
                    success=True,
                    platform=self._platform_info.platform,
                    server_name=name,
                    method=method,
                    message=f"[DRY RUN] Would update {name}",
                    config_path=self._platform_info.config_path,
                )

            try:
                result = self._strategy.update(server, scope)
                logger.info(f"Successfully updated {name}")
                return result
            except Exception as e:
                logger.error(f"Update failed: {e}", exc_info=True)
                raise InstallationError(
                    f"Failed to update {name}: {e}",
                    "Check logs for details and verify permissions",
                ) from e
        else:
            # Server exists, no force - raise error
            raise InstallationError(
                f"Server '{name}' already exists",
                recovery_suggestion="Use force=True to update existing server",
            )

    # New server - proceed with normal installation
    # ... existing installation code ...
```

#### Step 4: Update `agent_installer.py` to use `force` parameter

**File:** `agent_installer.py`

**Remove manual uninstall logic:**

```python
# OLD CODE (remove):
# Handle force mode by uninstalling first
if force and not dry_run:
    # Ignore uninstall errors (server may not exist)
    with contextlib.suppress(PyMCPInstallerError):
        installer.uninstall_server("mcp-skillset")

# Install the server
try:
    result: PyInstallResult = installer.install_server(
        name="mcp-skillset",
        command="mcp-skillset",
        args=["mcp"],
        description="Dynamic RAG-powered skills for code assistants",
    )
```

**Replace with:**

```python
# NEW CODE:
# Install the server (force=True will auto-update if exists)
try:
    result: PyInstallResult = installer.install_server(
        name="mcp-skillset",
        command="mcp-skillset",
        args=["mcp"],
        description="Dynamic RAG-powered skills for code assistants",
        force=force,  # Pass force parameter through
    )
```

## Benefits of Recommended Approach

1. **Atomic operation:** Single update operation instead of uninstall+install
2. **Backup safety:** ConfigManager creates backup before update (line 129-133)
3. **Cleaner API:** Callers don't need to implement uninstall+install pattern
4. **Better error handling:** Proper exception handling instead of suppression
5. **Clear intent:** `force=True` clearly communicates "overwrite if exists"
6. **Discoverable:** Users see `force` parameter in API documentation
7. **Minimal changes:** Small, focused changes to existing codebase
8. **Backward compatible:** Default `force=False` preserves current behavior

## Code Files Summary

### Key Files Analyzed

1. **`installer.py`** (726 lines)
   - Main API facade: `MCPInstaller` class
   - Entry point: `install_server()` method (line 183)
   - Currently raises error if server exists

2. **`installation_strategy.py`** (620 lines)
   - Strategy pattern for platform-specific installation
   - `JSONManipulationStrategy.install()` (line 390)
   - `TOMLManipulationStrategy.install()` (line 524)
   - Both delegate to `config_manager.add_server()`

3. **`config_manager.py`** (544 lines)
   - Low-level config file operations
   - Three key methods:
     - `add_server()` - raises if exists (line 209)
     - `update_server()` - raises if not exists (line 305)
     - `get_server()` - returns None if not exists (line 393)

4. **`agent_installer.py`** (mcp-skillset codebase)
   - Current workaround implementation
   - Manual uninstall before install (line 145-149)

## Next Steps

1. Implement `update()` method in `InstallationStrategy` base class
2. Implement `update()` in `JSONManipulationStrategy` and `TOMLManipulationStrategy`
3. Add `force` parameter to `MCPInstaller.install_server()`
4. Update `agent_installer.py` to use `force=True` instead of manual uninstall
5. Add tests for update flow
6. Update documentation to explain `force` parameter

## Testing Considerations

**Test cases to add:**

1. **First installation:** `install_server(name="test", force=False)` → success
2. **Duplicate without force:** `install_server(name="test", force=False)` when exists → error
3. **Duplicate with force:** `install_server(name="test", force=True)` when exists → success (update)
4. **Update non-existent:** Direct call to `update()` when server doesn't exist → error
5. **Backup verification:** Confirm backup created before update
6. **Dry-run mode:** `install_server(..., force=True, dry_run=True)` → no actual changes
7. **Config validation:** Ensure updated config is valid JSON/TOML

## References

- py_mcp_installer documentation: `docs/ARCHITECTURE.md` (mentions force flag concept)
- ConfigManager already has atomic write with backups
- InstallationResult type already supports update operations
- ValidationError already suggests using `update_server()`
