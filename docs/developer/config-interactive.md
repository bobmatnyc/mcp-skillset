# Interactive Configuration Guide

The `mcp-skillset config` command has been enhanced with an interactive menu-based configuration system while maintaining full backward compatibility.

## Usage Modes

### 1. Interactive Menu (Default)

Run without any flags to launch the interactive menu:

```bash
mcp-skillset config
```

This opens a menu-driven interface where you can:

- Configure base directory
- Adjust search settings (hybrid search weights)
- Manage repositories
- View current configuration
- Reset to defaults

### 2. Read-Only Display (Backward Compatible)

Use the `--show` flag to display current configuration without making changes:

```bash
mcp-skillset config --show
```

This preserves the original behavior of the `config` command.

### 3. Non-Interactive Configuration

Use the `--set` flag to change configuration values from the command line:

```bash
# Set base directory
mcp-skillset config --set base_dir=/custom/path

# Change search mode preset
mcp-skillset config --set search_mode=balanced
```

## Interactive Menu Features

### Main Menu Options

1. **Base directory configuration**
   - Change the base directory for mcp-skillset
   - Validates path is writable
   - Creates directory if it doesn't exist

2. **Search settings (hybrid search weights)**
   - Choose from preset modes:
     - Balanced (50% vector, 50% graph)
     - Semantic-focused (90% vector, 10% graph)
     - Graph-focused (30% vector, 70% graph)
     - Current optimized (70% vector, 30% graph)
     - Custom weights (manual configuration)

3. **Repository management**
   - Add new repository (URL + priority)
   - Remove existing repository
   - Change repository priority

4. **View current configuration**
   - Display full configuration tree
   - Shows all settings, repositories, indices

5. **Reset to defaults**
   - Clears all custom settings
   - Restores default configuration
   - Requires confirmation

6. **Exit**
   - Close the configuration menu

### Navigation

- Use arrow keys to navigate menu options
- Press Enter to select
- Press Ctrl+C or Esc to cancel/exit
- All changes are saved immediately

## Search Mode Presets

### Balanced (50% vector, 50% graph)
Equal weighting between semantic similarity and relationship discovery. Good general-purpose setting.

### Semantic-focused (90% vector, 10% graph)
Optimized for natural language queries and fuzzy matching. Best for concept search and semantic similarity.

### Graph-focused (30% vector, 70% graph)
Optimized for discovering related skills and dependency traversal. Best for finding connected components.

### Current optimized (70% vector, 30% graph)
Default preset optimized through testing. Provides slight semantic emphasis while maintaining relationship awareness.

### Custom weights
Manually configure vector and graph weights. Weights must sum to 1.0.

## Configuration Persistence

All configuration changes are saved to `~/.mcp-skillset/config.yaml` immediately after modification.

### Configuration File Format

```yaml
# Base directory
base_dir: /custom/path

# Hybrid search settings
hybrid_search:
  preset: balanced
  vector_weight: 0.5
  graph_weight: 0.5
```

## Examples

### Example 1: Configure Base Directory

```bash
$ mcp-skillset config
? What would you like to configure?
  > Base directory configuration
    Search settings (hybrid search weights)
    Repository management
    View current configuration
    Reset to defaults
    Exit

# Select "Base directory configuration"
? Enter base directory path: /custom/mcp-skillset
✓ Base directory updated to: /custom/mcp-skillset
```

### Example 2: Change Search Mode

```bash
$ mcp-skillset config
? What would you like to configure?
    Base directory configuration
  > Search settings (hybrid search weights)
    ...

# Select "Search settings"
? Choose search mode:
  > Balanced (50% vector, 50% graph)
    Semantic-focused (90% vector, 10% graph)
    Graph-focused (30% vector, 70% graph)
    Current optimized (70% vector, 30% graph)
    Custom weights

# Select "Balanced"
✓ Search mode set to: balanced (vector=0.5, graph=0.5)
```

### Example 3: Add Repository

```bash
$ mcp-skillset config
? What would you like to configure?
    ...
  > Repository management

? Choose repository action:
  > Add new repository
    Remove repository
    Change repository priority
    Back to main menu

? Enter repository URL: https://github.com/myuser/skills.git
? Enter priority (0-100): 80

✓ Repository added successfully
  • ID: myuser/skills
  • Skills: 15
  • Priority: 80

Tip: Run 'mcp-skillset index' to index new skills
```

### Example 4: Non-Interactive Mode

```bash
# Quick configuration changes
$ mcp-skillset config --set search_mode=semantic_focused
✓ Search mode set to: semantic_focused (vector=0.9, graph=0.1)
Configuration saved to /Users/user/.mcp-skillset/config.yaml

# View configuration
$ mcp-skillset config --show
⚙️  Current Configuration

mcp-skillset Configuration
└── 📁 Base Directory: /Users/user/.mcp-skillset
    ...
    ├── ⚖️  Hybrid Search
    │   ├── ✓ Mode: semantic_focused
    │   ├── ✓ Vector weight: 0.9
    │   └── ✓ Graph weight: 0.1
```

## Backward Compatibility

The original `config` command behavior is preserved through the `--show` flag:

```bash
# Old behavior (still works)
mcp-skillset config --show

# New interactive behavior (default)
mcp-skillset config
```

Scripts and automation can use `--show` for read-only access and `--set` for programmatic configuration changes.

## Technical Details

### Configuration Loading Priority

1. Explicit CLI arguments (highest priority)
2. Environment variables (`MCP_SKILLS_*`)
3. Config file (`~/.mcp-skillset/config.yaml`)
4. Defaults (lowest priority)

### Immediate Persistence

All configuration changes are saved immediately to prevent data loss if the user exits or encounters errors later in the session.

### Deep Merge for Nested Dictionaries

When saving configuration, nested dictionaries (like `hybrid_search`) are deep-merged to preserve existing keys that weren't modified.

### Input Validation

- **Base directory**: Validates path is writable, creates if doesn't exist
- **Search weights**: Must be between 0.0-1.0 and sum to 1.0
- **Repository priority**: Must be between 0-100
- **Repository URL**: Must be non-empty string

### Error Handling

- Invalid inputs show error messages with guidance
- Failed operations don't modify configuration
- All errors are logged for debugging
- Graceful handling of Ctrl+C and ESC

## Testing

Comprehensive test coverage includes:

- Menu navigation (mocked prompts)
- Configuration changes (all settings)
- Input validation
- Persistence logic
- Backward compatibility (--show and --set flags)
- Deep merge behavior
- Error handling

Run tests:

```bash
pytest tests/test_config_interactive.py -v
```

## Dependencies

- `questionary>=2.0.1` - Interactive prompts and menus
- `pyyaml>=6.0` - YAML configuration file handling
- `rich>=13.0.0` - Terminal UI formatting
- `click>=8.0` - CLI framework

## Future Enhancements

Potential additions for future versions:

- Import/export configuration profiles
- Multi-repository bulk operations
- Advanced search weight optimization
- Configuration templates
- Validation for all config sections
- Undo/redo for configuration changes
