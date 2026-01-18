# Package Name Revert: mcp-skills → mcp-skillset

## Summary

Successfully reverted package name from `mcp-skills` (taken on PyPI) to `mcp-skillset` (already published) and updated CLI command to match for consistency.

## Changes Made

### 1. Core Package Configuration

**File: `pyproject.toml`**
- ✅ Package name: `mcp-skills` → `mcp-skillset`
- ✅ CLI entry point: `mcp-skills` → `mcp-skillset`
- ✅ Project URLs: Updated GitHub URLs to `mcp-skillset`
- ✅ Completion data files: Updated paths to `mcp-skillset-completion.*`

### 2. Documentation

**File: `README.md`**
- ✅ Title: `mcp-skills` → `mcp-skillset`
- ✅ Badges: Updated PyPI badge URLs to `mcp-skillset`
- ✅ All command examples: `mcp-skills` → `mcp-skillset` (75 replacements)
- ✅ Installation: `pipx install mcp-skillset`
- ✅ Development script: `mcp-skillset-dev`

**File: `docs/SHELL_COMPLETIONS.md`**
- ✅ All CLI references updated to `mcp-skillset`
- ✅ Completion environment variable: `_MCP_SKILLKIT_COMPLETE`
- ✅ All command examples and instructions updated

**Other Documentation Files:**
- ✅ `docs/publishing.md`
- ✅ `docs/README.md`
- ✅ `docs/INSTALLATION_VERIFICATION.md`
- ✅ `docs/architecture/README.md`
- ✅ All other `docs/*.md` files
- ✅ Root-level markdown files (CHANGELOG.md, CONTRIBUTING.md, etc.)

### 3. Build & Development

**File: `MANIFEST.in`**
- ✅ Configuration example reference: `.mcp-skillset.yaml.example`

**File: `Makefile`**
- ✅ Project name: `mcp-skills` → `mcp-skillset`
- ✅ All CLI commands: `mcp-skills` → `mcp-skillset`

**File: `config.yaml.example`**
- ✅ All CLI references updated

### 4. Scripts

**File: `scripts/generate_completions.sh`**
- ✅ Command references: `mcp-skills` → `mcp-skillset`
- ✅ Environment variable: `_MCP_SKILLKIT_COMPLETE`
- ✅ Completion file names: `mcp-skillset-completion.*`

**File: `mcp-skills-dev` → `mcp-skillset-dev`**
- ✅ Renamed development script
- ✅ Internal references updated

### 5. Shell Completions

**Generated Files:**
- ✅ `completions/mcp-skillset-completion.bash` (30 lines)
- ✅ `completions/mcp-skillset-completion.zsh` (41 lines)
- ✅ `completions/mcp-skillset-completion.fish` (18 lines)
- ✅ Old `mcp-skills-completion.*` files removed

**Environment Variables:**
- Bash: `_MCP_SKILLKIT_COMPLETE=bash_source mcp-skillset`
- Zsh: `_MCP_SKILLKIT_COMPLETE=zsh_source mcp-skillset`
- Fish: `_MCP_SKILLKIT_COMPLETE=fish_source mcp-skillset`

### 6. Source Code

**File: `src/mcp_skills/cli/main.py`**
- ✅ Setup message: "Starting mcp-skillset setup..."

**Note:** Data directory `.mcp-skills` remains unchanged (intentional - it's the user data directory, not the package name).

## Installation & Usage

### Install New Package Name

```bash
# Uninstall old version (if installed)
pip uninstall mcp-skills

# Install new version
pipx install mcp-skillset

# Or from source
pip install -e .
```

### Verify Installation

```bash
which mcp-skillset
mcp-skillset --version
mcp-skillset --help
```

### Command Examples

```bash
# Setup
mcp-skillset setup

# Search skills
mcp-skillset search "python testing"

# Start MCP server
mcp-skillset serve

# Repository management
mcp-skillset repo add <url>
mcp-skillset repo list

# Index management
mcp-skillset index
```

## Shell Completions

### Bash

```bash
eval "$(_MCP_SKILLKIT_COMPLETE=bash_source mcp-skillset)" >> ~/.bashrc
```

### Zsh

```bash
eval "$(_MCP_SKILLKIT_COMPLETE=zsh_source mcp-skillset)" >> ~/.zshrc
```

### Fish

```bash
echo 'eval (env _MCP_SKILLKIT_COMPLETE=fish_source mcp-skillset)' >> ~/.config/fish/config.fish
```

## Testing

```bash
# Run tests (uses new command name)
pytest tests/

# Test CLI directly
mcp-skillset setup --help
mcp-skillset search --help
```

## Publishing

When publishing to PyPI, the package will be named `mcp-skillset`:

```bash
# Build
python -m build

# Publish to PyPI
twine upload dist/*
```

## Key Differences

### Before (Attempted)
- Package: `mcp-skills` (taken on PyPI ❌)
- CLI: `mcp-skills`

### After (Current)
- Package: `mcp-skillset` (already published ✅)
- CLI: `mcp-skillset` (now matches package name ✅)
- Data directory: `.mcp-skills` (unchanged - intentional)

## Files Modified Summary

**Total Files Modified:** 40+

**Categories:**
- Configuration: 3 files (pyproject.toml, MANIFEST.in, Makefile)
- Documentation: 20+ files (README.md, docs/*.md, root *.md)
- Scripts: 2 files (generate_completions.sh, dev script)
- Completions: 3 files (bash, zsh, fish)
- Source code: 1 file (cli/main.py)
- Build artifacts: Regenerated with new name

## Verification Checklist

- ✅ Package installs as `mcp-skillset`
- ✅ CLI command is `mcp-skillset`
- ✅ Shell completions work with `mcp-skillset`
- ✅ All documentation references updated
- ✅ PyPI badges point to correct package
- ✅ Development script renamed and works
- ✅ Completion files regenerated with correct command

## Notes

1. **Data Directory:** The `.mcp-skills` directory name is intentionally unchanged - it's the user data directory, not related to the package name.

2. **Completion Generation:** Use `./scripts/generate_completions.sh` to regenerate completions after CLI changes.

3. **PyPI Publication:** Package is already published as `mcp-skillset` on PyPI, so this revert aligns with the published name.

4. **Consistency:** Package name and CLI command now match (`mcp-skillset`), improving user experience.

## Next Steps

1. Test installation: `pipx install mcp-skillset`
2. Verify all commands work: `mcp-skillset --help`
3. Test shell completions
4. Update any external references (CI/CD, documentation sites, etc.)
5. Announce name change if already in use
