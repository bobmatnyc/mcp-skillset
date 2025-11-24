# mcp-skills

[![PyPI version](https://badge.fury.io/py/mcp-skillkit.svg)](https://badge.fury.io/py/mcp-skillkit)
[![Python Versions](https://img.shields.io/pypi/pyversions/mcp-skillkit)](https://pypi.org/project/mcp-skillkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](https://github.com/bobmatnyc/mcp-skills)

**Dynamic RAG-powered skills for code assistants via Model Context Protocol (MCP)**

mcp-skills is a standalone Python application that provides intelligent, context-aware skills to code assistants through hybrid RAG (vector + knowledge graph). Unlike static skills that load at startup, mcp-skills enables runtime skill discovery, automatic recommendations based on your project's toolchain, and dynamic loading optimized for your workflow.

## Key Features

- **🚀 Zero Config**: `mcp-skills setup` handles everything automatically
- **🧠 Intelligent**: Auto-detects your project's toolchain (Python, TypeScript, Rust, Go, etc.)
- **🔍 Dynamic Discovery**: Vector similarity + knowledge graph for better skill finding
- **📦 Multi-Source**: Pulls skills from multiple git repositories
- **⚡ On-Demand Loading**: Skills loaded when needed, not all at startup
- **🔌 MCP Native**: First-class Model Context Protocol integration

## Installation

### With pipx (Recommended)

[pipx](https://pipx.pypa.io/) is the recommended way to install Python CLI applications:

```bash
pipx install mcp-skillkit
```

**Note**: The package name on PyPI is `mcp-skillkit`, but the CLI command is `mcp-skills`:
- Install: `pipx install mcp-skillkit`
- Run: `mcp-skills --help`

### With pip

If you prefer pip (not recommended for CLI tools):

```bash
pip install mcp-skillkit
```

### From Source

```bash
git clone https://github.com/bobmatnyc/mcp-skills.git
cd mcp-skills
pip install -e .
```

### Troubleshooting Installation

**Error: "No apps associated with package mcp-skills"**
- You're trying to install the wrong package name
- The correct package name is `mcp-skillkit` (not `mcp-skills`)
- Install with: `pipx install mcp-skillkit`

### Local Development (Without Installation)

For development, you can run mcp-skills directly from source without installing:

```bash
# Use the development script
./mcp-skills-dev --help
./mcp-skills-dev search "python testing"
./mcp-skills-dev setup --auto
```

The `mcp-skills-dev` script:
- Runs the package from source code (not installed version)
- Uses local virtual environment if available
- Sets up PYTHONPATH automatically
- Passes all arguments through to the CLI

This is useful for:
- Testing changes without reinstalling
- Developing new features
- Debugging with source code
- Contributing to the project

**Note**: For production use, install the package normally with `pip install -e .` or `pip install mcp-skillkit`.

### First-Run Requirements

**Important**: On first run, mcp-skills will automatically download a ~90MB sentence-transformer model (`all-MiniLM-L6-v2`) for semantic search. This happens during the initial `mcp-skills setup` or when you first run any command that requires indexing.

**Requirements**:
- ✅ Active internet connection
- ✅ ~100MB free disk space
- ✅ 2-5 minutes for initial download (depending on connection speed)

**Model Caching**:
- Models are cached in `~/.cache/huggingface/` for future use
- Subsequent runs use the cached model (no download required)
- The cache persists across mcp-skills updates

## Quick Start

### 1. Setup

Run the interactive setup wizard to configure mcp-skills for your project:

```bash
mcp-skills setup
```

**Note**: The first run will download the embedding model (~90MB) before proceeding with setup. Allow 2-5 minutes for this initial download. Subsequent runs will be much faster.

This will:
- Download embedding model (first run only)
- Detect your project's toolchain
- Clone relevant skill repositories
- Build vector + knowledge graph indices
- Configure MCP server integration
- Validate the setup

### 2. Start the MCP Server

```bash
mcp-skills serve
```

The server will start and expose skills to your code assistant via MCP protocol.

### 3. Use with Claude Code

Skills are automatically available in Claude Code. Try:
- "What testing skills are available for Python?"
- "Show me debugging skills"
- "Recommend skills for my project"

## Project Structure

```
~/.mcp-skills/
├── config.yaml              # User configuration
├── repos/                   # Cloned skill repositories
│   ├── anthropics/skills/
│   ├── obra/superpowers/
│   └── custom-repo/
├── indices/                 # Vector + KG indices
│   ├── vector_store/
│   └── knowledge_graph/
└── metadata.db             # SQLite metadata
```

## Architecture

mcp-skills uses a hybrid RAG approach combining:

**Vector Store** (ChromaDB):
- Fast semantic search over skill descriptions
- Embeddings generated with sentence-transformers
- Persistent local storage with minimal configuration

**Knowledge Graph** (NetworkX):
- Skill relationships and dependencies
- Category and toolchain associations
- Related skill discovery

**Toolchain Detection**:
- Automatic detection of programming languages
- Framework and build tool identification
- Intelligent skill recommendations

## Configuration

### Global Configuration (`~/.mcp-skills/config.yaml`)

```yaml
# Hybrid Search Configuration
# Controls weighting between vector similarity and knowledge graph relationships
hybrid_search:
  # Option 1: Use a preset (recommended)
  preset: current  # current, semantic_focused, graph_focused, or balanced

  # Option 2: Specify custom weights (must sum to 1.0)
  # vector_weight: 0.7  # Weight for vector similarity (0.0-1.0)
  # graph_weight: 0.3   # Weight for knowledge graph (0.0-1.0)

repositories:
  - url: https://github.com/anthropics/skills.git
    priority: 100
    auto_update: true

vector_store:
  backend: chromadb
  embedding_model: all-MiniLM-L6-v2

server:
  transport: stdio
  log_level: info
```

#### Hybrid Search Modes

The hybrid search system combines vector similarity (semantic search) with knowledge graph relationships (dependency traversal) to find relevant skills. You can tune the weighting to optimize for different use cases:

**Available Presets:**

| Preset | Vector | Graph | Best For | Use Case |
|--------|--------|-------|----------|----------|
| `current` | 70% | 30% | **General purpose** (default) | Balanced skill discovery with slight semantic emphasis |
| `semantic_focused` | 90% | 10% | Natural language queries | "help me debug async code" → emphasizes semantic understanding |
| `graph_focused` | 30% | 70% | Related skill discovery | Starting from "pytest" → discovers pytest-fixtures, pytest-mock |
| `balanced` | 50% | 50% | Equal weighting | General purpose when unsure which approach is better |

**When to use each mode:**

- **`current`** (default): Best for most users. Proven through testing to work well for typical skill discovery patterns.
- **`semantic_focused`**: Use when you have vague requirements or want fuzzy semantic matching. Good for concept-based searches like "help me with error handling" or "testing strategies".
- **`graph_focused`**: Use when you want to explore skill ecosystems and dependencies. Perfect for "what else works with X?" queries.
- **`balanced`**: Use when you want equal emphasis on both approaches, or as a starting point for experimentation.

**Configuration Examples:**

```yaml
# Use preset (recommended)
hybrid_search:
  preset: current

# OR specify custom weights
hybrid_search:
  vector_weight: 0.8
  graph_weight: 0.2
```

**CLI Override:**

You can override the config file setting using the `--search-mode` flag:

```bash
# Use semantic-focused mode for this search
mcp-skills search "python testing" --search-mode semantic_focused

# Use graph-focused mode for recommendations
mcp-skills recommend --search-mode graph_focused

# Available modes: semantic_focused, graph_focused, balanced, current
```

### Project Configuration (`.mcp-skills.yaml`)

```yaml
project:
  name: my-project
  toolchain:
    primary: Python
    frameworks: [Flask, SQLAlchemy]

auto_load:
  - systematic-debugging
  - test-driven-development
```

## CLI Commands

```bash
# Setup and Configuration
mcp-skills setup                    # Interactive setup wizard
mcp-skills config                   # Show configuration

# Server
mcp-skills serve                    # Start MCP server (stdio)
mcp-skills serve --http             # Start HTTP server
mcp-skills serve --dev              # Development mode (auto-reload)

# Skills Management
mcp-skills search "testing"         # Search skills
mcp-skills list                     # List all skills
mcp-skills info pytest-skill        # Show skill details
mcp-skills recommend                # Get recommendations

# Repositories
mcp-skills repo add <url>           # Add repository
mcp-skills repo list                # List repositories
mcp-skills repo update              # Update all repositories

# Indexing
mcp-skills index                    # Rebuild indices
mcp-skills index --incremental      # Index only new skills

# Utilities
mcp-skills health                   # Health check
mcp-skills stats                    # Usage statistics
```

## Shell Completions

Enable tab completion for the `mcp-skills` command to speed up your workflow:

### Quick Install

**Bash** (requires Bash 4.4+):
```bash
eval "$(_MCP_SKILLS_COMPLETE=bash_source mcp-skills)" >> ~/.bashrc
source ~/.bashrc
```

**Zsh** (macOS default):
```zsh
eval "$(_MCP_SKILLS_COMPLETE=zsh_source mcp-skills)" >> ~/.zshrc
source ~/.zshrc
```

**Fish**:
```fish
echo 'eval (env _MCP_SKILLS_COMPLETE=fish_source mcp-skills)' >> ~/.config/fish/config.fish
source ~/.config/fish/config.fish
```

### Features

- ✅ Complete all commands and subcommands
- ✅ Complete option flags (`--help`, `--limit`, etc.)
- ✅ Works with `mcp-skills`, `mcp-skills repo`, and all other commands

### Verification

Test completions are working:
```bash
mcp-skills <TAB>        # Shows: config health index info list mcp recommend repo search setup stats
mcp-skills repo <TAB>   # Shows: add list update
mcp-skills search --<TAB>  # Shows: --category --help --limit
```

### Documentation

For detailed installation instructions, troubleshooting, and advanced usage, see [docs/SHELL_COMPLETIONS.md](docs/SHELL_COMPLETIONS.md).

## MCP Tools

mcp-skills exposes these tools to code assistants:

- **search_skills**: Natural language skill search
- **get_skill**: Load full skill instructions by ID
- **recommend_skills**: Get recommendations for current project
- **list_categories**: List all skill categories
- **update_repositories**: Pull latest skills from git

## Development

### Requirements

- Python 3.11+
- Git

### Setup Development Environment

```bash
git clone https://github.com/bobmatnyc/mcp-skills.git
cd mcp-skills
pip install -e ".[dev]"
```

### Running from Source (Development Mode)

Use the `./mcp-skills-dev` script to run commands directly from source without installation:

```bash
# Run any CLI command
./mcp-skills-dev --version
./mcp-skills-dev search "debugging"
./mcp-skills-dev serve --dev

# All arguments pass through
./mcp-skills-dev info systematic-debugging
```

**How it works**:
1. Sets `PYTHONPATH` to include `src/` directory
2. Activates local `.venv` if present
3. Runs `python -m mcp_skills.cli.main` with all arguments

**When to use**:
- ✅ Rapid iteration during development
- ✅ Testing changes without reinstalling
- ✅ Debugging with source code modifications
- ❌ Production deployments (use `pip install` instead)

**Installed vs. Source**:
```bash
# Installed version (from pip install -e .)
mcp-skills search "testing"

# Source version (no installation required)
./mcp-skills-dev search "testing"
```

### Run Tests

```bash
make quality
```

### Performance Benchmarks

mcp-skills includes comprehensive performance benchmarks to track and prevent regressions:

```bash
# Run all benchmarks (includes slow tests)
make benchmark

# Run fast benchmarks only (skip 10k skill tests)
make benchmark-fast

# Compare current performance with baseline
make benchmark-compare
```

**Benchmark Categories**:
- **Indexing Performance**: Measure time to index 100, 1000, and 10000 skills
- **Search Performance**: Track query latency (p50, p95, p99) for vector and hybrid search
- **Database Performance**: Benchmark SQLite operations (lookup, query, batch insert)
- **Memory Usage**: Monitor memory consumption during large-scale operations

**Baseline Thresholds**:
- Index 100 skills: < 10 seconds
- Index 1000 skills: < 100 seconds
- Search query (p50): < 100ms
- Search query (p95): < 500ms
- SQLite lookup by ID: < 1ms

**Benchmark Results**:
- Results are saved to `.benchmarks/` directory (git-ignored)
- Use `make benchmark-compare` to detect performance regressions
- CI/CD can be configured to fail on significant performance degradation

**Example Output**:
```
-------------------------- benchmark: 15 tests --------------------------
Name (time in ms)                    Min      Max     Mean   StdDev
---------------------------------------------------------------------
test_vector_search_latency_100      45.2     52.1    47.8     2.1
test_lookup_by_id_single             0.3      0.8     0.4     0.1
test_hybrid_search_end_to_end       89.5    105.2    94.3     5.2
---------------------------------------------------------------------
```

### Linting and Formatting

```bash
make lint-fix
```

### Security Scanning

mcp-skills includes comprehensive security scanning to identify vulnerabilities in dependencies and code:

#### Automated Security (Dependabot + GitHub Actions)

**Dependabot** automatically:
- Scans dependencies weekly for vulnerabilities
- Creates pull requests for security updates
- Groups minor/patch updates for easier review

**GitHub Actions** runs security scans on every push:
- Safety: Python dependency vulnerability scanner
- pip-audit: PyPI package vulnerability auditor
- Bandit: Python code security linter
- detect-secrets: Secret detection scanner

#### Manual Security Scanning

```bash
# Basic security scan (Safety + pip-audit)
make security-check

# Comprehensive security audit with reports
make security-check-full

# Install security scanning tools
make security-install

# Pre-publish with security checks
make pre-publish
```

#### Security Reports

After running `make security-check-full`, reports are saved to `.security-reports/`:
- `safety-report.json` - Dependency vulnerabilities
- `pip-audit-report.json` - Package vulnerabilities
- `bandit-report.json` - Code security issues

#### Security Policy

For vulnerability reporting and security best practices, see [.github/SECURITY.md](.github/SECURITY.md).

**Key security features:**
- Automated dependency scanning (Dependabot)
- Weekly security scans (GitHub Actions)
- Pre-publish security gate
- Secret detection (detect-secrets)
- Code security linting (Bandit)

## Documentation

### Architecture
See [docs/architecture/README.md](docs/architecture/README.md) for detailed architecture design.

### Skills Collections
See [docs/skills/RESOURCES.md](docs/skills/RESOURCES.md) for a comprehensive index of skill repositories compatible with mcp-skills, including:
- Official Anthropic skills
- Community collections (obra/superpowers, claude-mpm-skills, etc.)
- Toolchain-specific skills (Python, TypeScript, Rust, Go, Java)
- Operations & DevOps skills
- MCP servers that provide skill-like capabilities

## Troubleshooting

### Model Download Issues

If you encounter problems downloading the embedding model on first run:

#### 1. Check Internet Connection

The model is downloaded from HuggingFace Hub. Verify you can reach:
```bash
curl -I https://huggingface.co
```

#### 2. Manual Model Download

Pre-download the model manually if automatic download fails:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

This downloads the model to `~/.cache/huggingface/` and verifies it works.

#### 3. Proxy Configuration

If behind a corporate proxy, configure environment variables:
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
export HF_ENDPOINT=https://huggingface.co  # Or your mirror
```

#### 4. Offline/Air-Gapped Installation

For environments without internet access:

**On a machine with internet:**
1. Download the model:
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
   ```

2. Package the model cache:
   ```bash
   cd ~/.cache/huggingface
   tar -czf sentence-transformers-model.tar.gz hub/
   ```

**On the air-gapped machine:**
1. Transfer `sentence-transformers-model.tar.gz` to the target machine

2. Extract to the HuggingFace cache directory:
   ```bash
   mkdir -p ~/.cache/huggingface
   cd ~/.cache/huggingface
   tar -xzf /path/to/sentence-transformers-model.tar.gz
   ```

3. Install mcp-skills (transfer wheel if needed):
   ```bash
   pip install mcp-skillkit  # Or install from wheel
   ```

4. Verify the setup:
   ```bash
   mcp-skills health
   ```

#### 5. Custom Cache Location

If you need to use a different cache directory:
```bash
export HF_HOME=/custom/path/to/cache
export TRANSFORMERS_CACHE=/custom/path/to/cache
mcp-skills setup
```

#### 6. Disk Space Issues

Check available space in the cache directory:
```bash
df -h ~/.cache/huggingface
```

The model requires ~90MB, but allow ~100MB for temporary files during download.

#### 7. Permission Issues

Ensure the cache directory is writable:
```bash
mkdir -p ~/.cache/huggingface
chmod 755 ~/.cache/huggingface
```

### Common Issues

#### "Connection timeout" during model download
- Check internet connection and firewall settings
- Try manual download (see step 2 above)
- Configure proxy if behind corporate network (see step 3 above)

#### "No space left on device"
- Check disk space: `df -h ~/.cache`
- Clear old HuggingFace cache: `rm -rf ~/.cache/huggingface/*`
- Use custom cache location (see step 5 above)

#### "Permission denied" on cache directory
- Fix permissions: `chmod 755 ~/.cache/huggingface`
- Or use custom cache location with proper permissions

#### Slow initial setup
- First run downloads ~90MB and builds indices
- Expected time: 2-10 minutes depending on connection speed and number of skills
- Subsequent runs use cached model and are much faster

### Getting Help

If you encounter issues not covered here:
1. Check [GitHub Issues](https://github.com/bobmatnyc/mcp-skills/issues)
2. Review logs: `~/.mcp-skills/logs/`
3. Run health check: `mcp-skills health`
4. Open a new issue with:
   - Error message and stack trace
   - Output of `mcp-skills --version`
   - Operating system and Python version
   - Steps to reproduce

## Contributing

Contributions welcome! Please read our contributing guidelines first.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `make quality` to ensure tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io)
- Inspired by [Claude Skills](https://github.com/anthropics/skills)
- Uses [ChromaDB](https://www.trychroma.com/) for vector search
- Embeddings via [sentence-transformers](https://www.sbert.net/)

## Links

- **PyPI Package**: [mcp-skillkit on PyPI](https://pypi.org/project/mcp-skillkit/)
- **Documentation**: [GitHub Wiki](https://github.com/bobmatnyc/mcp-skills/wiki)
- **Issue Tracker**: [GitHub Issues](https://github.com/bobmatnyc/mcp-skills/issues)
- **MCP Registry**: [MCP Servers](https://registry.modelcontextprotocol.io)
- **Publishing Guide**: [docs/publishing.md](docs/publishing.md)

---

**Status**: ✅ v0.1.0 - Production Ready | **Test Coverage**: 85-96% | **Tests**: 48 passing
