# Shell Completions for mcp-skillset

This guide provides detailed instructions for installing and using shell completions for the `mcp-skillset` CLI across bash, zsh, and fish shells.

## Overview

Shell completions enable tab completion for the `mcp-skillset` command, making it faster and easier to:
- Discover available commands and subcommands
- Complete option flags (e.g., `--help`, `--force`)
- Avoid typos and syntax errors
- Speed up workflow with fewer keystrokes

**What's Supported:**
- ✅ All 11 main commands (`setup`, `mcp`, `search`, `list`, `info`, `recommend`, `health`, `stats`, `repo`, `index`, `config`)
- ✅ Subcommands (e.g., `repo add`, `repo list`, `repo update`)
- ✅ Option flags for each command
- ✅ Dynamic completion where applicable

## Requirements

### Bash
- **Version**: Bash 4.4 or later
- **Check version**: `bash --version`
- **Upgrade**: On macOS, use `brew install bash` to get a modern version

### Zsh
- **Version**: Zsh 5.0 or later (typically pre-installed on modern systems)
- **Check version**: `zsh --version`

### Fish
- **Version**: Fish 3.0 or later
- **Check version**: `fish --version`
- **Install**: `brew install fish` (macOS) or see [Fish Shell](https://fishshell.com)

## Installation

### Method 1: Direct Evaluation (Recommended for Testing)

This method evaluates the completion script every time you start a shell. It's easy to set up but has a slight startup cost.

#### Bash

Add to `~/.bashrc`:
```bash
eval "$(_MCP_SKILLS_COMPLETE=bash_source mcp-skillset)"
```

Then reload your shell:
```bash
source ~/.bashrc
```

#### Zsh

Add to `~/.zshrc`:
```zsh
eval "$(_MCP_SKILLS_COMPLETE=zsh_source mcp-skillset)"
```

Then reload your shell:
```zsh
source ~/.zshrc
```

#### Fish

Add to `~/.config/fish/config.fish`:
```fish
eval (env _MCP_SKILLS_COMPLETE=fish_source mcp-skillset)
```

Then reload your shell:
```fish
source ~/.config/fish/config.fish
```

### Method 2: Pre-Generated Completion Files (Recommended for Production)

This method uses pre-generated completion files for faster shell startup. The completion files are located in the `completions/` directory of the repository.

#### Bash

**Option A: Source the completion file directly**

Add to `~/.bashrc`:
```bash
source /path/to/mcp-skillset/completions/mcp-skillset-completion.bash
```

**Option B: Copy to system completion directory**

```bash
# For user-specific completions
mkdir -p ~/.local/share/bash-completion/completions
cp /path/to/mcp-skillset/completions/mcp-skillset-completion.bash \
   ~/.local/share/bash-completion/completions/mcp-skillset

# Or for system-wide completions (requires sudo)
sudo cp /path/to/mcp-skillset/completions/mcp-skillset-completion.bash \
        /etc/bash_completion.d/mcp-skillset
```

Then reload:
```bash
source ~/.bashrc
```

#### Zsh

**Option A: Source the completion file directly**

Add to `~/.zshrc`:
```zsh
source /path/to/mcp-skillset/completions/mcp-skillset-completion.zsh
```

**Option B: Copy to zsh fpath**

```bash
# Create user completion directory if it doesn't exist
mkdir -p ~/.zsh/completion

# Copy completion file
cp /path/to/mcp-skillset/completions/mcp-skillset-completion.zsh \
   ~/.zsh/completion/_mcp-skillset

# Add to fpath in ~/.zshrc (before compinit)
fpath=(~/.zsh/completion $fpath)
autoload -U compinit && compinit
```

Then reload:
```zsh
source ~/.zshrc
```

#### Fish

Fish automatically loads completions from `~/.config/fish/completions/`:

```bash
# Create fish completions directory
mkdir -p ~/.config/fish/completions

# Copy completion file
cp /path/to/mcp-skillset/completions/mcp-skillset-completion.fish \
   ~/.config/fish/completions/mcp-skillset.fish
```

Fish will automatically load it on next shell start.

### Method 3: Install from Package

If you installed `mcp-skillset` via pip/pipx, the completion files are included in the package:

```bash
# Find where mcp-skillset is installed
pip show mcp-skillset

# Completion files are in: <site-packages>/mcp_skills/completions/
```

Then follow Method 2 instructions above, replacing `/path/to/mcp-skillset/completions/` with the actual package location.

## Verification

After installation, verify completions are working:

### Test Command Completion

Type `mcp-skillset ` and press **TAB**. You should see:
```
config    health    index     info      list      mcp       recommend repo      search    setup     stats
```

### Test Subcommand Completion

Type `mcp-skillset repo ` and press **TAB**. You should see:
```
add    list    update
```

### Test Option Completion

Type `mcp-skillset search --` and press **TAB**. You should see:
```
--category  --help  --limit
```

## Troubleshooting

### Completions Not Working

#### Bash

**Problem**: No completions appear when pressing TAB

**Solutions**:
1. **Check Bash version**: Requires Bash 4.4+
   ```bash
   bash --version
   # If < 4.4, upgrade: brew install bash
   ```

2. **Verify bash-completion is installed**:
   ```bash
   # macOS with Homebrew
   brew install bash-completion@2

   # Add to ~/.bash_profile
   [[ -r "/opt/homebrew/etc/profile.d/bash_completion.sh" ]] && . "/opt/homebrew/etc/profile.d/bash_completion.sh"
   ```

3. **Check if completion function is loaded**:
   ```bash
   type _mcp_skills_completion
   # Should output: _mcp_skills_completion is a function
   ```

4. **Manually source the completion file**:
   ```bash
   source /path/to/mcp-skillset/completions/mcp-skillset-completion.bash
   complete -p mcp-skillset  # Verify it's registered
   ```

#### Zsh

**Problem**: No completions appear when pressing TAB

**Solutions**:
1. **Ensure compinit is loaded**:
   Add to `~/.zshrc` (before sourcing completions):
   ```zsh
   autoload -U compinit && compinit
   ```

2. **Clear completion cache**:
   ```zsh
   rm -f ~/.zcompdump*
   compinit
   ```

3. **Verify completion function is loaded**:
   ```zsh
   which _mcp_skills_completion
   # Should output: _mcp_skills_completion () { ... }
   ```

4. **Check fpath includes completion directory**:
   ```zsh
   echo $fpath | tr ' ' '\n' | grep completion
   ```

#### Fish

**Problem**: No completions appear when pressing TAB

**Solutions**:
1. **Verify completion file is in correct location**:
   ```bash
   ls ~/.config/fish/completions/mcp-skillset.fish
   ```

2. **Test completion function directly**:
   ```fish
   complete -C "mcp-skillset "
   ```

3. **Reload fish completions**:
   ```fish
   fish_update_completions
   ```

### Slow Shell Startup

If using Method 1 (direct evaluation), shell startup may be slower because the completion script is generated every time.

**Solution**: Switch to Method 2 (pre-generated files) for faster startup:
```bash
# Generate completions once
cd /path/to/mcp-skillset
./scripts/generate_completions.sh

# Then use the generated files (Method 2)
```

### Completions Not Updating After CLI Changes

If you've updated mcp-skillset and completions aren't reflecting new commands:

**Solution**: Regenerate completion files:
```bash
cd /path/to/mcp-skillset

# If using development version
pip install -e .

# Regenerate completions
./scripts/generate_completions.sh

# Reload your shell
source ~/.bashrc  # or ~/.zshrc, or restart fish
```

### "command not found: mcp-skillset"

The completion system requires `mcp-skillset` to be in your PATH.

**Solutions**:
1. **Verify installation**:
   ```bash
   which mcp-skillset
   pip show mcp-skillset
   ```

2. **Install if missing**:
   ```bash
   pipx install mcp-skillset
   # or
   pip install mcp-skillset
   ```

3. **Ensure shell PATH includes pip bin directory**:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"  # For pip --user
   export PATH="$HOME/.local/share/pipx/venvs/mcp-skillset/bin:$PATH"  # For pipx
   ```

## Advanced Usage

### Custom Completion Installation Location

You can install completions to any location and source them:

```bash
# Generate completions to custom directory
./scripts/generate_completions.sh

# Copy to your preferred location
cp completions/mcp-skillset-completion.bash ~/my-completions/

# Source in your shell config
echo 'source ~/my-completions/mcp-skillset-completion.bash' >> ~/.bashrc
```

### Multiple Shell Support

If you use multiple shells (e.g., bash and zsh), install completions for each:

```bash
# Bash
echo 'source /path/to/mcp-skillset/completions/mcp-skillset-completion.bash' >> ~/.bashrc

# Zsh
echo 'source /path/to/mcp-skillset/completions/mcp-skillset-completion.zsh' >> ~/.zshrc

# Fish
cp /path/to/mcp-skillset/completions/mcp-skillset-completion.fish \
   ~/.config/fish/completions/mcp-skillset.fish
```

### Disabling Completions

To temporarily disable completions without uninstalling:

#### Bash
```bash
complete -r mcp-skillset
```

#### Zsh
```zsh
compdef -d mcp-skillset
```

#### Fish
```bash
complete -c mcp-skillset --erase
```

To permanently disable, remove the source line from your shell config file.

## Uninstallation

### Bash

Remove the source line from `~/.bashrc`:
```bash
# Remove this line:
# source /path/to/mcp-skillset/completions/mcp-skillset-completion.bash
# or
# eval "$(_MCP_SKILLS_COMPLETE=bash_source mcp-skillset)"
```

Then reload:
```bash
source ~/.bashrc
```

### Zsh

Remove the source line from `~/.zshrc`:
```zsh
# Remove this line:
# source /path/to/mcp-skillset/completions/mcp-skillset-completion.zsh
# or
# eval "$(_MCP_SKILLS_COMPLETE=zsh_source mcp-skillset)"
```

Then reload:
```zsh
source ~/.zshrc
```

### Fish

Remove the completion file:
```bash
rm ~/.config/fish/completions/mcp-skillset.fish
```

Fish will automatically detect the removal.

## Development

### Regenerating Completions

After modifying the CLI structure (adding commands, options, etc.), regenerate completions:

```bash
# From project root
./scripts/generate_completions.sh
```

This script:
1. Checks for installed `mcp-skillset` command
2. Generates completion files for bash, zsh, and fish
3. Saves them to `completions/` directory
4. Reports line counts and success status

### Testing Completions

To test completions without installing:

#### Bash
```bash
source completions/mcp-skillset-completion.bash
mcp-skillset <TAB>
```

#### Zsh
```zsh
source completions/mcp-skillset-completion.zsh
mcp-skillset <TAB>
```

#### Fish
```fish
source completions/mcp-skillset-completion.fish
mcp-skillset <TAB>
```

## Technical Details

### How Click Completions Work

The `mcp-skillset` CLI uses Click's built-in completion system:

1. **Environment Variable**: `_MCP_SKILLS_COMPLETE` tells Click to output completion code
2. **Shell-Specific Format**: Each shell has its own completion script format
3. **Dynamic Generation**: Click introspects the CLI structure to generate completions
4. **Lazy Evaluation**: Completions are computed at runtime based on current context

### Completion Modes

- `bash_source` / `zsh_source` / `fish_source`: Generate shell-specific completion script
- `bash_complete` / `zsh_complete` / `fish_complete`: Generate completions for current context (used internally)

### Security Considerations

The completion scripts execute the `mcp-skillset` command to generate context-aware completions. This is safe because:
- Only completion metadata is output (no command execution)
- The scripts are generated from trusted source (Click library)
- No user input is evaluated during completion

## Further Reading

- [Click Documentation - Shell Completion](https://click.palletsprojects.com/en/stable/shell-completion/)
- [Bash Completion Manual](https://github.com/scop/bash-completion)
- [Zsh Completion System](https://zsh.sourceforge.io/Doc/Release/Completion-System.html)
- [Fish Completion Tutorial](https://fishshell.com/docs/current/completions.html)

## Support

If you encounter issues with shell completions:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Verify your shell version meets requirements
3. Try Method 1 (direct evaluation) for debugging
4. Open an issue on [GitHub](https://github.com/bobmatnyc/mcp-skillset/issues) with:
   - Shell name and version
   - Installation method used
   - Output of `type _mcp_skills_completion` (bash/zsh) or `complete -C "mcp-skillset"` (fish)
   - Error messages or unexpected behavior
