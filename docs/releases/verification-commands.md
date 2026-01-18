# Verification Commands for Package Rename

## Quick Verification

```bash
# 1. Check package is installed with correct name
source .venv/bin/activate
pip show mcp-skillset | grep Name
# Expected: Name: mcp-skillset

# 2. Verify CLI command works
mcp-skillset --version
# Expected: mcp-skillset, version 0.1.0

# 3. Test main commands
mcp-skillset --help
mcp-skillset search --help
mcp-skillset setup --help

# 4. Verify completions exist
ls -la completions/
# Expected: mcp-skillset-completion.{bash,zsh,fish}

# 5. Test completion generation
./scripts/generate_completions.sh
# Expected: Success for all three shells
```

## Comprehensive Verification

```bash
# Check all documentation references
grep -r "mcp-skillset[^-]" README.md docs/ --include="*.md" | wc -l
# Expected: 0 (all should be mcp-skillset now)

# Check pyproject.toml
grep "^name = " pyproject.toml
# Expected: name = "mcp-skillset"

grep "mcp-skillset = " pyproject.toml
# Expected: mcp-skillset = "mcp_skills.cli.main:cli"

# Verify dev script renamed
ls -la | grep "mcp-skill.*-dev"
# Expected: mcp-skillset-dev

# Check GitHub URLs
grep "github.com/bobmatnyc" pyproject.toml
# Expected: All URLs contain mcp-skillset

# Test Python import
python -c "import mcp_skills; print('✅ Import successful')"
# Expected: ✅ Import successful
```

## Test Installation Flow

```bash
# Simulate fresh install
pip uninstall -y mcp-skillset
pip install -e .

# Verify command available
which mcp-skillset
# Expected: /path/to/.venv/bin/mcp-skillset

# Test basic functionality
mcp-skillset config
mcp-skillset health
```

## Shell Completion Testing

### Bash
```bash
source completions/mcp-skillset-completion.bash
# Type: mcp-skillset <TAB>
# Expected: Shows all commands (config, health, index, info, list, mcp, recommend, repo, search, setup, stats)
```

### Zsh
```bash
source completions/mcp-skillset-completion.zsh
# Type: mcp-skillset <TAB>
# Expected: Shows all commands with descriptions
```

### Fish
```bash
source completions/mcp-skillset-completion.fish
# Type: mcp-skillset <TAB>
# Expected: Shows all commands
```

## Build Testing

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build new package
python -m build

# Check distribution files
ls -la dist/
# Expected: mcp_skillset-0.1.0.tar.gz and mcp_skillset-0.1.0-py3-none-any.whl

# Verify wheel contents
unzip -l dist/mcp_skillset-0.1.0-py3-none-any.whl | grep "scripts"
# Expected: Should show mcp-skillset entry point
```

## PyPI Upload Testing (Dry Run)

```bash
# Install twine if needed
pip install twine

# Check package
twine check dist/*
# Expected: Checking dist/mcp_skillset-0.1.0.tar.gz: PASSED

# Test upload (doesn't actually upload)
# twine upload --repository testpypi dist/*
```

## Regression Testing

```bash
# Run test suite
pytest tests/ -v

# Run specific tests that reference CLI
pytest tests/test_cli.py -v
pytest tests/e2e/test_cli_commands.py -v

# Check for any failing tests due to rename
pytest tests/ -k "setup or cli" -v
```

## Files to Check Manually

1. **README.md**: All command examples use `mcp-skillset`
2. **pyproject.toml**: Package name and CLI entry point correct
3. **docs/SHELL_COMPLETIONS.md**: All references updated
4. **completions/**: Only `mcp-skillset-completion.*` files exist
5. **scripts/generate_completions.sh**: Uses correct command name

## Success Criteria

- ✅ Package name is `mcp-skillset`
- ✅ CLI command is `mcp-skillset`
- ✅ All documentation uses `mcp-skillset`
- ✅ Shell completions work with `mcp-skillset`
- ✅ All tests pass
- ✅ No references to old `mcp-skills` package name
- ✅ GitHub URLs point to `mcp-skillset` repository
- ✅ PyPI badges reference `mcp-skillset`
