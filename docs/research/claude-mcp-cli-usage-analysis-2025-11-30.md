# Claude MCP CLI Usage Analysis

**Research Date:** 2025-11-30
**Research Focus:** Installation methodology for MCP server configuration across different AI agents
**User Request:** Verify and improve `claude mcp` command usage in install/setup

---

## Executive Summary

**Current State:** ✅ **Already Implemented (v0.6.8)**

The `mcp-skillset` project **already uses** the `claude mcp` CLI for Claude Code installation. The implementation is mature, well-tested, and follows best practices. The current approach:

- ✅ Uses `claude mcp add` for Claude Code installation
- ✅ Calls `claude mcp remove` before add when `--force` flag is used
- ✅ Uses correct command format: `claude mcp add --transport stdio mcp-skillset mcp-skillset mcp`
- ✅ Routes different agents to appropriate installation methods (CLI vs JSON config)
- ✅ Has comprehensive error handling and dry-run support

**Gaps Identified:**
1. ❌ `claude mcp remove` is NOT called automatically for every installation (only with `--force` flag)
2. ❌ No agent-specific best practices for Cursor, Codex, or Gemini (these agents are not currently supported)
3. ⚠️ Only 3 agents are supported: Claude Desktop, Claude Code, Auggie

---

## Phase 1: Current Implementation Analysis

### 1.1 Agent Detection (`agent_detector.py`)

**Supported Agents (lines 71-114):**
```python
AGENT_CONFIGS = [
    AgentConfig(
        name="Claude Desktop",
        id="claude-desktop",
        config_paths={...},
        config_file="claude_desktop_config.json",
    ),
    AgentConfig(
        name="Claude Code",
        id="claude-code",
        config_paths={...},
        config_file="settings.json",
    ),
    AgentConfig(
        name="Auggie",
        id="auggie",
        config_paths={...},
        config_file="config.json",
    ),
]
```

**Findings:**
- **Supported:** Claude Desktop, Claude Code, Auggie
- **Missing:** Cursor, Codex, Gemini CLI
- **Platform Coverage:** macOS (darwin), Windows (win32), Linux
- **Detection Method:** File system checks for config paths

### 1.2 Installation Routing (`agent_installer.py`)

**Installation Method Routing (lines 159-164):**
```python
def install(
    self,
    agent: DetectedAgent,
    force: bool = False,
    dry_run: bool = False,
) -> InstallResult:
    # Route Claude Code to CLI-based installation
    if agent.id == "claude-code":
        return self._install_via_claude_cli(agent, force, dry_run)

    # Use JSON config file manipulation for other agents
    return self._install_via_json_config(agent, force, dry_run)
```

**Findings:**
- ✅ Claude Code uses `claude mcp` CLI
- ✅ Claude Desktop and Auggie use JSON config manipulation
- ✅ Clear separation of installation methods
- ✅ Appropriate routing based on agent capabilities

### 1.3 Claude CLI Installation (`_install_via_claude_cli`)

**CLI Installation Flow (lines 304-419):**

**Step 1: CLI Availability Check (line 339)**
```python
if not shutil.which("claude"):
    return InstallResult(
        success=False,
        error="Claude CLI not found. Please install Claude Code first."
    )
```

**Step 2: Check Existing Installation (lines 349-363)**
```python
if not force:
    result = subprocess.run(
        ["claude", "mcp", "get", "mcp-skillset"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return InstallResult(
            success=False,
            error="mcp-skillset is already installed. Use --force to overwrite."
        )
```

**Step 3: Remove if Force Mode (lines 380-386)**
```python
if force:
    subprocess.run(
        ["claude", "mcp", "remove", "mcp-skillset"],
        capture_output=True,
        text=True,
    )
```

**Step 4: Add MCP Server (lines 388-402)**
```python
result = subprocess.run(
    [
        "claude",
        "mcp",
        "add",
        "--transport",
        "stdio",
        "mcp-skillset",
        "mcp-skillset",
        "mcp",
    ],
    capture_output=True,
    text=True,
)
```

**Findings:**
- ✅ Correct CLI usage: `claude mcp add --transport stdio mcp-skillset mcp-skillset mcp`
- ✅ Checks for existing installation with `claude mcp get`
- ⚠️ **GAP:** `claude mcp remove` only called with `--force` flag, not automatically
- ✅ Proper error handling with stderr capture
- ✅ Dry-run mode supported (lines 365-378)

### 1.4 JSON Config Installation (`_install_via_json_config`)

**Used For:** Claude Desktop, Auggie

**Process:**
1. Load existing config or create new
2. Check if already installed
3. Create backup before modification
4. Add MCP configuration to JSON
5. Validate modified config
6. Write to file with rollback on failure
7. Update .gitignore (best effort)

**Findings:**
- ✅ Safe atomic updates with backup/restore
- ✅ JSON validation before writing
- ✅ Automatic rollback on write failure
- ✅ Proper error handling

### 1.5 Setup Command Integration (`setup.py`)

**Agent Installation in Setup (lines 238-296):**
```python
if not skip_agents:
    agent_detector = AgentDetector()
    # Exclude Claude Desktop by default (config path conflicts with Claude Code)
    all_agents = agent_detector.detect_all()
    found_agents = [
        a for a in all_agents if a.exists and a.id != "claude-desktop"
    ]

    if found_agents:
        installer = AgentInstaller()
        for agent in found_agents:
            result = installer.install(agent)
```

**Findings:**
- ✅ Automatic agent detection during setup
- ✅ Excludes Claude Desktop by default (config conflict with Claude Code)
- ✅ Respects `--skip-agents` flag
- ✅ Non-blocking: setup continues even if agent installation fails

### 1.6 Install Command (`install.py`)

**Agent Selection (lines 18-34):**
```python
@click.option(
    "--agent",
    type=click.Choice(["claude-desktop", "claude-code", "auggie", "all"]),
    default="all",
    help="Which agent to install for (default: claude-code and auggie, excludes claude-desktop)",
)
```

**Default Behavior (lines 67-74):**
```python
if agent == "all":
    # Default behavior: exclude Claude Desktop (config path conflicts with Claude Code)
    all_agents = detector.detect_all()
    detected_agents = [a for a in all_agents if a.id != "claude-desktop"]
else:
    single_agent = detector.detect_agent(agent)
    detected_agents = [single_agent] if single_agent else []
```

**Findings:**
- ✅ Supports `--dry-run` for preview
- ✅ Supports `--force` for overwrite
- ✅ Default excludes Claude Desktop to avoid conflicts
- ✅ Can explicitly install for specific agents

---

## Phase 2: Test Coverage Analysis

**Test File:** `tests/test_agent_installer.py`

**Claude CLI Tests:**
- ✅ `test_claude_cli_installation_success` (lines 393-435)
- ✅ `test_claude_cli_not_found` (lines 437-453)
- ✅ `test_claude_cli_already_installed` (lines 457-485)
- ✅ `test_claude_cli_force_reinstall` (lines 489-525)
- ✅ `test_claude_cli_dry_run` (lines 529-556)
- ✅ `test_claude_cli_dry_run_with_force` (lines 560-581)
- ✅ `test_claude_cli_add_command_fails` (lines 585-610)
- ✅ `test_claude_cli_get_command_fails_allows_install` (lines 614-640)
- ✅ `test_claude_cli_routing_based_on_agent_id` (lines 668-698)

**Coverage:**
- ✅ Success case
- ✅ Error handling (CLI not found, add fails)
- ✅ Already installed detection
- ✅ Force reinstall workflow
- ✅ Dry-run mode
- ✅ Agent routing

---

## Phase 3: Gap Analysis vs Requirements

### Requirement 1: Automatically remove existing config

**User Expectation:**
```bash
claude mcp remove mcp-skillset  # Always called before add
claude mcp add mcp-skillset mcp-skillset mcp
```

**Current Behavior:**
```python
if force:  # Only removes if --force flag used
    subprocess.run(["claude", "mcp", "remove", "mcp-skillset"])

# Then add
subprocess.run(["claude", "mcp", "add", "--transport", "stdio", ...])
```

**Gap:**
- ⚠️ **PARTIAL IMPLEMENTATION**: Remove is only called with `--force` flag
- Current behavior prevents duplicate installation (returns error if already installed)
- User must explicitly use `--force` to trigger remove/re-add workflow

**Impact:** LOW
- Current approach is safer (prevents accidental overwrites)
- Force flag is required for intentional reinstalls
- Error message clearly tells users to use `--force` if needed

**Recommendation:**
- **Option A (Conservative):** Keep current behavior, document that `--force` triggers remove/add
- **Option B (User Request):** Always call remove before add (may lose user customizations)

### Requirement 2: Re-add using correct command

**User Expectation:**
```bash
claude mcp add mcp-skillset mcp-skillset mcp
```

**Current Implementation:**
```bash
claude mcp add --transport stdio mcp-skillset mcp-skillset mcp
```

**Gap:**
- ✅ **ALREADY CORRECT**: Command format matches user requirement
- ✅ Includes `--transport stdio` flag (explicit, better practice)

**Impact:** NONE
- Current implementation is correct and more explicit

### Requirement 3: Claude Code best practices

**User Expectation:** Use best practices for Claude Code

**Current Implementation:**
- ✅ Uses official `claude mcp` CLI (recommended by Anthropic)
- ✅ Separates MCP config from user settings
- ✅ Validates before installation
- ✅ Checks for existing installation
- ✅ Proper error handling
- ✅ Dry-run support

**Gap:** NONE
- Current implementation follows official best practices
- See `docs/CLAUDE_CLI_INTEGRATION.md` for detailed rationale

### Requirement 4: Best practices for other agents

**User Expectation:** Use best practices for Auggie, Cursor, Codex, Gemini

**Current Support:**
| Agent | Supported? | Method | Best Practice? |
|-------|------------|--------|----------------|
| Claude Desktop | ✅ Yes | JSON config | ✅ Safe with backup/rollback |
| Claude Code | ✅ Yes | `claude mcp` CLI | ✅ Official API |
| Auggie | ✅ Yes | JSON config | ✅ Safe with backup/rollback |
| Cursor | ❌ No | N/A | N/A |
| Codex | ❌ No | N/A | N/A |
| Gemini | ❌ No | N/A | N/A |

**Gap:**
- ❌ **UNSUPPORTED AGENTS**: Cursor, Codex, Gemini are not detected or supported
- No agent config entries in `AGENT_CONFIGS`
- No installation methods implemented

**Impact:** MEDIUM
- Users of Cursor/Codex/Gemini cannot use mcp-skillset
- Requires research into each agent's MCP configuration method

---

## Phase 4: Recommendations

### Recommendation 1: Clarify Remove Behavior

**Issue:** User expects automatic remove before add, but current implementation only removes with `--force`

**Options:**

**A. Keep Current Behavior (RECOMMENDED)**
- Already implemented and tested
- Safer (prevents accidental overwrites)
- Clear error message guides users to use `--force`
- Aligns with standard CLI tool behavior

**Changes Required:** None (documentation only)

**B. Always Remove Before Add**
- Matches user's initial expectation
- More aggressive, could lose user customizations
- Changes current tested behavior

**Changes Required:**
```python
def _install_via_claude_cli(...):
    # Always remove before add (no force check)
    subprocess.run(
        ["claude", "mcp", "remove", "mcp-skillset"],
        capture_output=True,
        text=True,
    )

    # Then add
    result = subprocess.run([...])
```

**Estimated Effort:** 10 minutes (code) + 30 minutes (tests)
**Risk:** LOW (well-tested area, could break existing workflows)

**C. Add `--auto-remove` Flag**
- Explicit user control
- Preserves current safe defaults
- Adds flexibility

**Changes Required:**
```python
@click.option(
    "--auto-remove",
    is_flag=True,
    help="Automatically remove existing installation before adding"
)
def install(agent: str, dry_run: bool, force: bool, auto_remove: bool):
    ...
```

**Estimated Effort:** 30 minutes (code) + 1 hour (tests + docs)
**Risk:** LOW (additive change)

### Recommendation 2: Support Additional Agents

**Issue:** Cursor, Codex, Gemini CLI not supported

**Required Research:**

**For Each Agent:**
1. Determine if agent supports MCP protocol
2. Find MCP configuration method (CLI vs config file)
3. Locate config file paths per platform
4. Identify config file format (JSON, TOML, YAML, etc.)
5. Test installation and verification

**Cursor:**
- **What is it?** Fork of VS Code with AI features
- **MCP Support?** Unknown - requires investigation
- **Config Location?** Likely similar to VS Code (`~/.config/Cursor/User/`)
- **Best Practice?** Unknown - need to research official docs

**Codex:**
- **What is it?** Unclear - multiple tools named "Codex"
- **Clarification Needed:** Is this GitHub Copilot? OpenAI Codex? Different product?
- **Cannot proceed without clarification**

**Gemini CLI:**
- **What is it?** Google's Gemini via CLI
- **MCP Support?** Unknown - requires investigation
- **Config Location?** Unknown
- **Best Practice?** Unknown - need to research official docs

**Estimated Effort per Agent:**
- Research: 2-4 hours
- Implementation: 2-4 hours
- Testing: 2-4 hours
- Documentation: 1 hour
- **Total per agent:** 7-13 hours

**Risk:** MEDIUM (unknown agent capabilities, config formats may vary)

### Recommendation 3: Improve Documentation

**Current Documentation:**
- ✅ Comprehensive README with install instructions
- ✅ Detailed `docs/CLAUDE_CLI_INTEGRATION.md` explaining rationale
- ✅ Well-commented code

**Gaps:**
- ⚠️ No explicit documentation of `--force` flag triggering remove/add
- ⚠️ No comparison table of agent support
- ⚠️ No migration guide from direct JSON editing to CLI

**Suggested Additions:**

**A. Add to README.md:**
```markdown
### Installation Behavior

#### Claude Code
- Uses official `claude mcp` CLI
- Checks for existing installation
- Use `--force` to remove and reinstall
- Dry-run: `mcp-skillset install --agent claude-code --dry-run`

#### Other Agents
- Uses JSON config file manipulation
- Automatic backup before modification
- Rollback on failure
```

**B. Add Agent Comparison Table:**
```markdown
| Agent | Method | Auto-Remove | Best Practice | Status |
|-------|--------|-------------|---------------|--------|
| Claude Code | CLI | With --force | ✅ Official API | Supported |
| Claude Desktop | JSON | N/A | ✅ Safe backup/restore | Supported |
| Auggie | JSON | N/A | ✅ Safe backup/restore | Supported |
| Cursor | - | - | - | Not Supported |
| Codex | - | - | - | Not Supported |
| Gemini | - | - | - | Not Supported |
```

**Estimated Effort:** 1 hour
**Risk:** NONE (documentation only)

---

## Phase 5: Implementation Approach

### Option 1: Minimal Changes (RECOMMENDED for immediate release)

**Scope:** Documentation only, no code changes

**Changes:**
1. Update README to clarify `--force` behavior
2. Add agent comparison table
3. Document unsupported agents (Cursor, Codex, Gemini)

**Effort:** 1 hour
**Risk:** NONE
**Impact:** Clarifies current behavior without changing tested code

### Option 2: Add Auto-Remove Flag

**Scope:** Add `--auto-remove` flag for explicit control

**Changes:**
1. Add `--auto-remove` flag to install command
2. Update `_install_via_claude_cli` to respect flag
3. Add tests for new flag
4. Update documentation

**Effort:** 2 hours
**Risk:** LOW (additive change)
**Impact:** Provides user control without changing defaults

### Option 3: Full Agent Support

**Scope:** Add Cursor, Codex, Gemini support

**Changes:**
1. Research each agent's MCP support and config method
2. Add agent configs to `AGENT_CONFIGS`
3. Implement installation methods (CLI or JSON)
4. Add comprehensive tests
5. Update documentation

**Effort:** 21-39 hours (7-13 hours per agent × 3 agents)
**Risk:** MEDIUM (unknown capabilities)
**Impact:** Expands user base significantly

---

## Conclusions

### Current State Assessment

**✅ STRENGTHS:**
1. **Claude Code installation is already correct** - uses `claude mcp` CLI with proper command
2. **Well-architected** - clear separation between CLI and JSON installation methods
3. **Comprehensive testing** - 9 test cases covering Claude CLI integration
4. **Safe defaults** - prevents accidental overwrites without `--force` flag
5. **Good documentation** - detailed rationale in CLAUDE_CLI_INTEGRATION.md

**⚠️ MINOR GAPS:**
1. **Auto-remove only with --force** - user expects automatic remove, current requires explicit flag
2. **Unsupported agents** - Cursor, Codex, Gemini not supported (requires research)
3. **Documentation could be clearer** - --force behavior not obvious in README

**❌ NO CRITICAL ISSUES FOUND**

### Priority Recommendations

**Priority 1: Clarify Documentation (1 hour)**
- Add agent comparison table to README
- Document `--force` flag behavior clearly
- List unsupported agents

**Priority 2: Decision on Auto-Remove Behavior**
- **Option A:** Keep current (recommended - safer)
- **Option B:** Add `--auto-remove` flag (user control)
- **Option C:** Always remove (matches user expectation but riskier)

**Priority 3: Agent Support Research**
- Investigate Cursor MCP support
- Clarify which "Codex" the user means
- Research Gemini CLI MCP capabilities

### Estimated Effort Summary

| Task | Effort | Risk | Impact |
|------|--------|------|--------|
| Documentation updates | 1 hour | None | Medium |
| Add `--auto-remove` flag | 2 hours | Low | Low |
| Cursor support research | 7-13 hours | Medium | Medium |
| Codex support (TBD) | 7-13 hours | Medium | Medium |
| Gemini support research | 7-13 hours | Medium | Medium |
| **Total (minimal)** | **1 hour** | **None** | **Medium** |
| **Total (with auto-remove)** | **3 hours** | **Low** | **Medium** |
| **Total (full support)** | **24-42 hours** | **Medium** | **High** |

---

## Next Steps

### Immediate Actions (Research Complete)

1. **Report findings to user** ✅ (this document)
2. **Get user clarification:**
   - Which "Codex" is meant? (GitHub Copilot? OpenAI Codex? Other?)
   - Is auto-remove critical or can we use `--force` flag?
   - Priority: Documentation vs new agent support vs auto-remove?

### After User Decision

**If Documentation Only:**
- Update README with agent table
- Document `--force` behavior
- List unsupported agents
- Estimated: 1 hour

**If Auto-Remove Flag:**
- Implement `--auto-remove` option
- Add tests
- Update docs
- Estimated: 2 hours

**If Agent Support:**
- Research Cursor/Gemini MCP capabilities
- Clarify Codex identity
- Implement detection and installation
- Add tests
- Update docs
- Estimated: 21-39 hours

---

## References

**Code Files Analyzed:**
- `src/mcp_skills/cli/commands/install.py` - Install command
- `src/mcp_skills/cli/commands/setup.py` - Setup command
- `src/mcp_skills/services/agent_installer.py` - Installation logic
- `src/mcp_skills/services/agent_detector.py` - Agent detection
- `tests/test_agent_installer.py` - Test coverage

**Documentation Reviewed:**
- `README.md` - User-facing documentation
- `docs/CLAUDE_CLI_INTEGRATION.md` - Implementation rationale
- `docs/DEPLOY.md` - Release process

**Key Discoveries:**
1. Claude CLI integration already implemented (v0.6.8)
2. Remove behavior is conditional (--force flag)
3. Only 3 agents supported (Claude Desktop, Claude Code, Auggie)
4. Well-tested implementation with 9 CLI-specific test cases
5. Safe defaults prevent accidental overwrites

---

**Research conducted by:** Claude Code (Research Agent)
**Date:** 2025-11-30
**Status:** Complete - Awaiting User Decision on Priority
