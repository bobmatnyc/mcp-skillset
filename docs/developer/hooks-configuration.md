# Hook Configuration Guide

## Overview

The hook configuration menu allows you to customize how Claude Code integrates with mcp-skillset through prompt enrichment hooks. This interactive menu provides an easy way to enable/disable hooks, adjust matching thresholds, and test your configuration.

## Accessing Hook Settings

### Via CLI
```bash
mcp-skillset config
```

Then select: **Hook settings (Claude Code integration)**

### Menu Structure
```
Main Menu
├── Base directory configuration
├── Search settings (hybrid search weights)
├── Repository management
├── Hook settings (Claude Code integration)  ← Select this
├── View current configuration
├── Reset to defaults
└── Exit
```

## Configuration Options

### 1. Enable/Disable Hooks

**Purpose:** Turn hook enrichment on or off globally.

**When to use:**
- Disable hooks temporarily for debugging
- Enable hooks after initial setup
- Test Claude Code behavior with/without skill hints

**How to configure:**
1. Select "Enable/disable hooks"
2. Choose Yes/No
3. Configuration is saved immediately

**Default:** Enabled (true)

### 2. Configure Threshold

**Purpose:** Set the similarity threshold for skill matching.

**Range:** 0.0 to 1.0

**Behavior:**
- **Higher threshold (0.7-1.0)**: Fewer but more relevant skill suggestions
- **Medium threshold (0.5-0.7)**: Balanced suggestions
- **Lower threshold (0.0-0.5)**: More suggestions but less precise

**Recommended values:**
- `0.8` - Very precise matches only
- `0.6` - Good balance (default)
- `0.4` - More exploratory suggestions

**How to configure:**
1. Select "Configure threshold"
2. Enter value between 0.0 and 1.0
3. Configuration is saved immediately

**Default:** 0.6

### 3. Configure Max Skills

**Purpose:** Set the maximum number of skills to suggest in hook hints.

**Range:** 1 to 10

**Behavior:**
- **Fewer skills (1-3)**: Concise, focused suggestions
- **Medium skills (4-6)**: Balanced (default)
- **More skills (7-10)**: Comprehensive suggestions

**How to configure:**
1. Select "Configure max skills"
2. Enter value between 1 and 10
3. Configuration is saved immediately

**Default:** 5

### 4. Test Hook

**Purpose:** Test the hook with a sample prompt to verify configuration.

**How to use:**
1. Select "Test hook"
2. Enter a test prompt (e.g., "Write pytest tests for my API")
3. View the enriched system message

**Example test prompts:**
- "Write pytest tests for my API" → Should suggest testing skills
- "Deploy to production" → Should suggest deployment/ops skills
- "Set up Docker containers" → Should suggest Docker/infrastructure skills
- "Implement OAuth authentication" → Should suggest security/auth skills

**Troubleshooting:**
- **No matches found?** Try lowering the threshold
- **Too many irrelevant matches?** Try raising the threshold
- **Hook timed out?** Check that mcp-skillset is indexed

## Configuration File

Settings are stored in `~/.mcp-skillset/config.yaml`:

```yaml
hooks:
  enabled: true
  threshold: 0.6
  max_skills: 5
```

## Viewing Current Settings

### In Hook Menu
Current settings are displayed at the top of the hook menu:

```
Hook Settings (Claude Code Integration)

Current settings:
  • Enabled: True
  • Threshold: 0.6
  • Max skills: 5
```

### In Configuration View
Select "View current configuration" from main menu to see all settings including hooks:

```
📁 Base Directory: /Users/user/.mcp-skillset
  ...
  🪝 Hook Settings
    ✓ Status: enabled
    ✓ Threshold: 0.6
    ✓ Max skills: 5
```

## Use Cases

### Use Case 1: High Precision Mode

**Scenario:** You only want very relevant skill suggestions.

**Configuration:**
- Threshold: 0.8
- Max skills: 3

**Result:** Only top 3 most relevant skills suggested, high confidence matches only.

### Use Case 2: Exploratory Mode

**Scenario:** You're learning and want to discover related skills.

**Configuration:**
- Threshold: 0.4
- Max skills: 8

**Result:** More skill suggestions, including tangentially related ones.

### Use Case 3: Focused Mode

**Scenario:** You know exactly what you need and want minimal distractions.

**Configuration:**
- Threshold: 0.7
- Max skills: 1

**Result:** Single most relevant skill suggested.

### Use Case 4: Debugging Mode

**Scenario:** Testing Claude Code without skill hints.

**Configuration:**
- Enabled: False

**Result:** Hooks disabled, Claude Code works without mcp-skillset hints.

## Input Validation

### Threshold Validation
- ✅ Valid: 0.0, 0.5, 0.6, 1.0
- ❌ Invalid: -0.1, 1.1, "abc"
- Error message: "Weight must be between 0.0 and 1.0"

### Max Skills Validation
- ✅ Valid: 1, 5, 10
- ❌ Invalid: 0, 11, "abc", 5.5
- Error message: "Max skills must be between 1 and 10"

## Troubleshooting

### Hook not working?
1. Check that hooks are enabled
2. Verify mcp-skillset is installed: `which mcp-skillset`
3. Test with "Test hook" option
4. Check logs: Look for hook-related errors

### Too many/few suggestions?
- Adjust threshold up (fewer) or down (more)
- Adjust max_skills to control quantity

### Hook timeout?
- Ensure skills are indexed: `mcp-skillset index`
- Check ChromaDB is accessible
- Verify no disk space issues

### Configuration not persisting?
- Check write permissions on `~/.mcp-skillset/config.yaml`
- Verify base directory is writable
- Try "Reset to defaults" then reconfigure

## Advanced Configuration

### Manual YAML Editing

You can also manually edit `~/.mcp-skillset/config.yaml`:

```yaml
hooks:
  enabled: true
  threshold: 0.75
  max_skills: 7
```

**Important:** Validate syntax with `mcp-skillset config --show` after manual edits.

### Environment Variables

Override config with environment variables:

```bash
export MCP_SKILLS_HOOKS__ENABLED=false
export MCP_SKILLS_HOOKS__THRESHOLD=0.8
export MCP_SKILLS_HOOKS__MAX_SKILLS=3
```

## Best Practices

1. **Start with defaults** - The default settings (0.6 threshold, 5 max skills) work well for most users
2. **Test after changes** - Use "Test hook" to verify behavior
3. **Adjust gradually** - Change threshold in 0.1 increments
4. **Monitor relevance** - If suggestions feel off, tweak threshold
5. **Use view config** - Regularly check your settings with "View current configuration"

## Integration with Claude Code

When hooks are enabled, mcp-skillset enriches your prompts with skill hints:

**Your prompt:**
```
Write pytest tests for my API
```

**Enriched system message (example):**
```
Consider using these relevant skills:
- toolchains-python-testing (pytest patterns and fixtures)
- toolchains-python-api-testing (API testing strategies)
```

Claude Code then has context about available skills when responding to your request.

## Support

For issues or questions:
- GitHub Issues: https://github.com/bobmatnyc/mcp-skillset/issues
- Documentation: https://github.com/bobmatnyc/mcp-skillset/tree/main/docs
- Demo script: `python examples/demo_hook_config.py`
