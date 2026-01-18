# Claude CLI Integration for MCP SkillSet

**Created:** 2025-11-30
**Ticket:** [1M-432](https://linear.app/1m-hyperdev/issue/1M-432)
**Status:** Implemented in v0.6.8

---

## Overview

MCP SkillSet now integrates with Claude Code using the official `claude mcp` CLI commands instead of directly manipulating JSON configuration files. This approach provides a more stable, maintainable, and future-proof installation method.

### Why Use Claude CLI?

The Claude CLI provides an official, supported API for managing MCP servers in Claude Code. Prior to this change, mcp-skillset directly modified `settings.json` files, which had several drawbacks:

**Problems with JSON File Manipulation:**
- ❌ **Brittle**: Config format changes could break the installer
- ❌ **Unofficial**: Not using a documented, supported API
- ❌ **Risky**: Could corrupt user settings unrelated to MCP
- ❌ **Unmaintainable**: Hard to debug when issues occur
- ❌ **Unclear ownership**: Mixed user settings with MCP configuration

**Benefits of Claude CLI:**
- ✅ **Official API**: Stable, documented, supported by Anthropic
- ✅ **Forward-compatible**: CLI updates handled by Claude Code team
- ✅ **Built-in validation**: CLI validates configuration before applying
- ✅ **Automatic handling**: Restart/reload logic handled internally
- ✅ **Clear separation**: MCP config separate from user settings
- ✅ **Cross-platform**: Works consistently across operating systems
- ✅ **Future-proof**: Less likely to break with Claude Code updates

---

## Architecture

### Routing Logic

The `AgentInstaller` service now routes installation based on agent type:

```python
def install(agent: DetectedAgent, force: bool, dry_run: bool) -> InstallResult:
    """Install MCP SkillSet for detected agent."""

    if agent.id == "claude-code":
        # Use Claude CLI for Claude Code
        return self._install_via_claude_cli(agent, force, dry_run)
    else:
        # Use JSON manipulation for Claude Desktop and Auggie
        return self._install_via_json_config(agent, force, dry_run)
```

### CLI Installation Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Check if claude CLI is available (which claude)      │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Check if mcp-skillset already installed              │
│    (claude mcp get mcp-skillset)                        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 3. If --force flag: Remove existing                     │
│    (claude mcp remove mcp-skillset)                     │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Add MCP server via CLI                               │
│    (claude mcp add --transport stdio                    │
│     mcp-skillset mcp-skillset mcp)                      │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Return success/failure result                        │
└─────────────────────────────────────────────────────────┘
```

### Error Handling

The CLI integration includes comprehensive error handling:

1. **CLI Not Found**: Clear error message with installation instructions
2. **Already Installed**: Prevents duplicate installation unless `--force` used
3. **CLI Execution Failure**: Captures stderr and provides context
4. **Dry Run Mode**: Shows what would happen without making changes

---

## Implementation Details

### Command Used

```bash
claude mcp add --transport stdio mcp-skillset mcp-skillset mcp
```

**Breakdown:**
- `claude mcp add` - Add MCP server command
- `--transport stdio` - Use stdio transport (stdin/stdout communication)
- `mcp-skillset` (1st argument) - Server name/identifier
- `mcp-skillset` (2nd argument) - Command to execute
- `mcp` (3rd argument) - Argument to pass to command

**Equivalent Configuration:**
```json
{
  "mcpServers": {
    "mcp-skillset": {
      "command": "mcp-skillset",
      "args": ["mcp"],
      "env": {}
    }
  }
}
```

### Key Methods

**`_install_via_claude_cli()`**
- Checks CLI availability using `shutil.which("claude")`
- Verifies existing installation using `claude mcp get`
- Handles force reinstall by removing then adding
- Supports dry-run mode for preview
- Returns detailed `InstallResult` with status and messages

**`_check_claude_cli_available()`**
- Helper method to verify `claude` command exists
- Returns boolean indicating availability
- Used for early validation before attempting operations

---

## Backward Compatibility

### Multi-Agent Support

The implementation maintains backward compatibility with other agents:

| Agent | Installation Method | Config Location |
|-------|-------------------|-----------------|
| **Claude Code** | Claude CLI | Managed by CLI (likely `~/.claude/`) |
| **Claude Desktop** | JSON config | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Auggie** | JSON config | `~/Library/Application Support/Auggie/config.json` |

### Migration Path

Users upgrading from previous versions:

**Scenario 1: Fresh Installation**
- New users automatically use Claude CLI for Claude Code
- No migration needed

**Scenario 2: Existing Installation (JSON Method)**
- Running `mcp-skillset install --force` will:
  1. Remove JSON-based configuration (if exists)
  2. Install via Claude CLI
  3. Recommend restarting Claude Code

**Scenario 3: Manual Configuration**
- Users can continue using JSON configuration
- CLI installation is optional but recommended

---

## Future Considerations

### Phase 2: CLI-Only Approach (v1.0.0+)

**Timeline:** Major version bump (v1.0.0)

**Potential Changes:**
1. Deprecate JSON manipulation for Claude Code entirely
2. Require Claude CLI for Claude Code installation
3. Add CLI requirements to Claude Desktop (if Anthropic provides)
4. Investigate CLI options for Auggie

**Benefits:**
- Simpler codebase (single installation method)
- More maintainable (no JSON parsing/validation)
- Official APIs only
- Better error messages from CLI tools

**Blockers:**
- Waiting for Claude Desktop CLI support
- Waiting for Auggie CLI support (if applicable)
- Need to ensure widespread Claude CLI availability

### Configuration Storage

**Current State:**
- Claude CLI manages configuration internally
- Exact storage location not documented (likely `~/.claude/`)
- Users don't need to know internals

**Future Investigation:**
- Document actual config file location
- Investigate if CLI provides export/import functionality
- Consider adding `mcp-skillset config export` command

---

## Testing Strategy

### Unit Tests

**File:** `tests/cli/test_install.py`

**Test Cases:**
1. ✅ CLI available, server not installed → Success
2. ✅ CLI available, server already installed → Error (use --force)
3. ✅ CLI available, --force flag → Remove then add
4. ✅ CLI available, --dry-run flag → Show command without running
5. ✅ CLI not available → Clear error message
6. ✅ CLI add command fails → Proper error handling

### Integration Tests

**Manual Testing Checklist:**
- [ ] Clean Claude Code installation
- [ ] Run `mcp-skillset setup`
- [ ] Verify `claude mcp list` shows mcp-skillset
- [ ] Test skill discovery in Claude Code
- [ ] Run `mcp-skillset install --force`
- [ ] Verify reinstallation works
- [ ] Run `mcp-skillset install --dry-run`
- [ ] Verify no changes made
- [ ] Test with Claude Desktop (should use JSON method)

### Regression Testing

**Key Scenarios:**
1. Fresh installation on clean system
2. Upgrade from previous version (JSON → CLI)
3. Force reinstall over existing installation
4. Dry-run mode verification
5. Multi-agent setup (Claude Code + Claude Desktop)

---

## Troubleshooting

### Common Issues

#### Issue: "Claude CLI not found"

**Symptom:** Installation fails with "Claude CLI not found" error.

**Solution:**
1. Verify Claude Code is installed and up to date
2. Check if `claude` command is available: `which claude`
3. Add to PATH if necessary:
   ```bash
   export PATH="/path/to/claude/bin:$PATH"
   ```
4. Verify CLI is working: `claude --version`

#### Issue: "mcp-skillset is already installed"

**Symptom:** Setup or install command fails saying server already exists.

**Solution:**
Use the `--force` flag to reinstall:
```bash
mcp-skillset install --agent claude-code --force
```

#### Issue: Skills not loading in Claude Code

**Symptom:** Installation succeeds but skills don't appear.

**Solutions:**
1. Restart Claude Code completely (close and reopen VS Code)
2. Verify installation: `claude mcp list`
3. Check MCP server logs in Claude Code
4. Run `mcp-skillset doctor` to check system health

---

## CLI Command Reference

### Add MCP Server

```bash
# Basic installation
claude mcp add --transport stdio mcp-skillset mcp-skillset mcp

# With environment variables
claude mcp add --transport stdio \
  --env MCP_SKILLSET_DEBUG=true \
  mcp-skillset \
  mcp-skillset \
  mcp
```

### Remove MCP Server

```bash
claude mcp remove mcp-skillset
```

### List MCP Servers

```bash
claude mcp list
```

### Get Server Details

```bash
claude mcp get mcp-skillset
```

---

## Related Documentation

- **Setup Command Analysis**: [docs/research/setup-command-analysis-2025-11-30.md](../research/setup-command-analysis-2025-11-30.md)
- **Agent Installer Service**: [src/mcp_skills/services/agent_installer.py](../../src/mcp_skills/services/agent_installer.py)
- **Installation Guide**: [README.md](../../README.md#installation)
- **Deployment Guide**: [DEPLOY.md](./DEPLOY.md)

---

## References

### Code Files

- `src/mcp_skills/cli/main.py` - Setup and install commands
- `src/mcp_skills/services/agent_installer.py` - Installation logic
- `src/mcp_skills/services/agent_detector.py` - Agent detection
- `tests/cli/test_install.py` - Installation tests

### External Resources

- Claude CLI Documentation: `claude --help`
- Claude MCP Commands: `claude mcp --help`
- Linear Ticket: [1M-432](https://linear.app/1m-hyperdev/issue/1M-432)

---

**Last Updated:** 2025-11-30
**Version:** v0.6.8
**Maintained By:** bobmatnyc
