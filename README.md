# mcp-skillset

[![PyPI version](https://badge.fury.io/py/mcp-skillset.svg)](https://badge.fury.io/py/mcp-skillset)
[![Python Versions](https://img.shields.io/pypi/pyversions/mcp-skillset)](https://pypi.org/project/mcp-skillset/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](https://github.com/bobmatnyc/mcp-skillset)

**Dynamic RAG-powered skills for code assistants via Model Context Protocol (MCP)**

mcp-skillset is a standalone Python application that provides intelligent, context-aware skills to code assistants through hybrid RAG (vector + knowledge graph). Unlike static skills that load at startup, mcp-skillset enables runtime skill discovery, automatic recommendations based on your project's toolchain, and dynamic loading optimized for your workflow.

## Key Features

- **🚀 Zero Config**: `mcp-skillset setup` handles everything automatically
- **🧠 Intelligent**: Auto-detects your project's toolchain (Python, TypeScript, Rust, Go, etc.)
- **🔍 Dynamic Discovery**: Vector similarity + knowledge graph for better skill finding
- **📦 Multi-Source**: Pulls skills from multiple git repositories
- **⚡ On-Demand Loading**: Skills loaded when needed, not all at startup
- **🔌 MCP Native**: First-class Model Context Protocol integration
- **🔒 Security First**: Multi-layer defense against prompt injection and malicious skills

## Security

MCP Skillset implements comprehensive security validation to protect against malicious skills from public repositories.

### Security Features

- **🛡️ Prompt Injection Detection**: Automatic detection of instruction override attempts, role hijacking, and context escape
- **🔍 Threat Classification**: Multi-level threat detection (BLOCKED, DANGEROUS, SUSPICIOUS)
- **🏷️ Repository Trust Levels**: TRUSTED (official), VERIFIED (community), UNTRUSTED (public)
- **📏 Size Limits**: DoS prevention through content size enforcement
- **🎯 Content Sanitization**: All skills wrapped in clear boundaries to prevent context escape

### Trust Levels

| Level | Description | Security Policy |
|-------|-------------|-----------------|
| **TRUSTED** | Official Anthropic repos | Minimal filtering (only BLOCKED threats) |
| **VERIFIED** | Known community repos | Moderate filtering (BLOCKED + DANGEROUS) |
| **UNTRUSTED** | Public repos (default) | Strict filtering (all threats) |

### Quick Security Check

```bash
# Skills from public repos are automatically validated
mcp-skillset search "python testing"

# View security details in logs
mcp-skillset --debug search "python testing"
```

For detailed security information, threat models, and best practices, see [SECURITY.md](./SECURITY.md).

## Installation

### With Homebrew (macOS/Linux)

The easiest way to install on macOS or Linux:

```bash
brew tap bobmatnyc/tools
brew install mcp-skillset
```

### With pipx (Recommended for non-Homebrew)

[pipx](https://pipx.pypa.io/) is the recommended way to install Python CLI applications:

```bash
pipx install mcp-skillset
```

### With pip

If you prefer pip (not recommended for CLI tools):

```bash
pip install mcp-skillset
```

### From Source

```bash
git clone https://github.com/bobmatnyc/mcp-skillset.git
cd mcp-skillset
pip install -e .
```

### Local Development (Without Installation)

For development, you can run mcp-skillset directly from source without installing:

```bash
# Use the development script
./mcp-skillset-dev --help
./mcp-skillset-dev search "python testing"
./mcp-skillset-dev setup --auto
```

The `mcp-skillset-dev` script:
- Runs the package from source code (not installed version)
- Uses local virtual environment if available
- Sets up PYTHONPATH automatically
- Passes all arguments through to the CLI

This is useful for:
- Testing changes without reinstalling
- Developing new features
- Debugging with source code
- Contributing to the project

**Note**: For production use, install the package normally with `pip install -e .` or `pip install mcp-skillset`.

### First-Run Requirements

**Important**: On first run, mcp-skillset will automatically download a ~90MB sentence-transformer model (`all-MiniLM-L6-v2`) for semantic search. This happens during the initial `mcp-skillset setup` or when you first run any command that requires indexing.

**Requirements**:
- ✅ Active internet connection
- ✅ ~100MB free disk space
- ✅ 2-5 minutes for initial download (depending on connection speed)

**Model Caching**:
- Models are cached in `~/.cache/huggingface/` for future use
- Subsequent runs use the cached model (no download required)
- The cache persists across mcp-skillset updates

## Quick Start

### 1. Setup

Run the interactive setup wizard to configure mcp-skillset for your project:

```bash
mcp-skillset setup
```

**Note**: The first run will download the embedding model (~90MB) before proceeding with setup. Allow 2-5 minutes for this initial download. Subsequent runs will be much faster.

This will:
- Download embedding model (first run only)
- Detect your project's toolchain
- Clone relevant skill repositories
- Build vector + knowledge graph indices
- Configure MCP server integration
- Validate the setup

### 2. Explore Available Skills

Before diving in, explore what's available:

```bash
# Get personalized recommendations based on your project
mcp-skillset recommend

# Search for specific topics
mcp-skillset search "testing patterns"

# Browse all skills interactively
mcp-skillset demo

# List all skills in compact format
mcp-skillset list --compact
```

### 3. Start the MCP Server

```bash
mcp-skillset mcp
```

The server will start and expose skills to your code assistant via MCP protocol.

### 4. Use with Claude Code

Skills are automatically available in Claude Code. Try:
- "What testing skills are available for Python?"
- "Show me debugging skills"
- "Recommend skills for my project"
- "Use the pytest-fixtures skill to help me write better tests"

### Real-World Usage Scenarios

**Scenario 1: Starting a New Python Project**
```bash
# Get setup and testing recommendations
cd ~/my-new-python-project
mcp-skillset recommend

# Search for testing frameworks
mcp-skillset search "python testing frameworks" --limit 5

# Learn about pytest best practices
mcp-skillset info pytest-best-practices

# Start MCP server for Claude integration
mcp-skillset mcp
```

**Scenario 2: Debugging Production Issues**
```bash
# Find debugging techniques
mcp-skillset search "production debugging" --search-mode semantic_focused

# Get systematic debugging approach
mcp-skillset info systematic-debugging

# View example questions
mcp-skillset demo systematic-debugging
```

**Scenario 3: Code Review Preparation**
```bash
# Find code review and quality skills
mcp-skillset search "code review" --category "Best Practices"

# Explore testing and quality skills
mcp-skillset list --category "Testing"

# Enrich your code review prompt
mcp-skillset enrich "Review this code for security and performance issues" --max-skills 3
```

**Scenario 4: Learning New Framework**
```bash
# Search for framework-specific skills
mcp-skillset search "async python patterns"

# Get recommendations for async projects
cd ~/async-project
mcp-skillset recommend --search-mode graph_focused

# Explore related skills interactively
mcp-skillset demo
```

## Project Structure

```
~/.mcp-skillset/
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

mcp-skillset uses a hybrid RAG approach combining:

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

### Global Configuration (`~/.mcp-skillset/config.yaml`)

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
  - url: https://github.com/obra/superpowers.git
    priority: 90
    auto_update: true
  - url: https://github.com/ComposioHQ/awesome-claude-skills.git
    priority: 85
    auto_update: true
  - url: https://github.com/Prat011/awesome-llm-skills.git
    priority: 85
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
mcp-skillset search "python testing" --search-mode semantic_focused

# Use graph-focused mode for recommendations
mcp-skillset recommend --search-mode graph_focused

# Available modes: semantic_focused, graph_focused, balanced, current
```

### Project Configuration (`.mcp-skillset.yaml`)

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

mcp-skillset provides a rich, interactive CLI with comprehensive command-line options and beautiful terminal output powered by Rich and Questionary.

### Quick Reference

| Command | Purpose | Key Options |
|---------|---------|-------------|
| `setup` | Initial configuration wizard | `--auto`, `--project-dir` |
| `config` | View/modify configuration | `--show`, `--set` |
| `index` | Rebuild indices | `--incremental`, `--force` |
| `install` | Install for AI agents | `--agent`, `--dry-run` |
| `mcp` | Start MCP server | `--dev` |
| `search` | Find skills by query | `--limit`, `--category`, `--search-mode` |
| `list` | List all skills | `--category`, `--compact` |
| `info` / `show` | Show skill details | (skill-id argument) |
| `recommend` | Get recommendations | `--search-mode` |
| `demo` | Interactive skill explorer | `--interactive` |
| `repo add` | Add skill repository | `--priority` |
| `repo list` | List repositories | - |
| `repo update` | Update repositories | (optional repo-id) |
| `discover search` | Search GitHub for repos | `--min-stars`, `--limit` |
| `discover trending` | Get trending repos | `--timeframe`, `--topic` |
| `discover topic` | Search by GitHub topic | `--min-stars` |
| `discover verify` | Verify SKILL.md files | (repo-url argument) |
| `discover limits` | Show API rate limits | - |
| `doctor` | Health check | - |
| `stats` | Usage statistics | - |
| `enrich` | Enrich prompts | `--max-skills`, `--full`, `--output` |

**Global options:** `--version`, `--verbose`, `--debug`, `--help`

### Core Commands

#### `setup` - Initial Configuration

Auto-configure mcp-skillset for your project with intelligent toolchain detection.

```bash
# Interactive setup wizard (recommended for first-time setup)
mcp-skillset setup

# Non-interactive setup with defaults (CI/automation)
mcp-skillset setup --auto

# Setup for specific project directory
mcp-skillset setup --project-dir /path/to/project

# Custom config file location
mcp-skillset setup --config ~/.config/mcp-skillset/custom.yaml
```

**What it does:**
- Downloads embedding model (~90MB, first run only)
- Detects project toolchain (Python, TypeScript, Rust, Go, etc.)
- Clones relevant skill repositories
- Builds vector + knowledge graph indices
- Configures MCP server integration
- Validates setup completion

**First-Run Note:** Allow 2-5 minutes for initial model download. Subsequent runs are instant.

#### `config` - Configuration Management

View or modify mcp-skillset configuration settings.

```bash
# Show current configuration (read-only)
mcp-skillset config
mcp-skillset config --show

# Set configuration value interactively
mcp-skillset config --set hybrid_search.preset=semantic_focused
mcp-skillset config --set repositories[0].auto_update=true
```

**Configuration file:** `~/.mcp-skillset/config.yaml`

#### `index` - Rebuild Indices

Rebuild vector and knowledge graph indices from skill repositories.

```bash
# Full rebuild (recommended after adding repositories)
mcp-skillset index

# Incremental indexing (only new/changed skills)
mcp-skillset index --incremental

# Force full reindex (bypass cache)
mcp-skillset index --force
```

**Use cases:**
- After adding new repositories with `repo add`
- When skill content has changed
- Troubleshooting search issues
- Switching embedding models

#### `install` - Agent Integration

Install MCP SkillSet configuration for AI agents with auto-detection.

```bash
# Auto-detect and install for all supported agents
mcp-skillset install

# Install for specific agent
mcp-skillset install --agent claude-desktop
mcp-skillset install --agent claude-code
mcp-skillset install --agent auggie

# Preview installation without making changes
mcp-skillset install --dry-run

# Force overwrite existing configuration
mcp-skillset install --force
```

**Supported agents:**
- `claude-desktop` - Claude Desktop App
- `claude-code` - Claude Code CLI
- `auggie` - Auggie AI Assistant
- `all` - Install for all detected agents

#### `mcp` - MCP Server

Start the Model Context Protocol server for integration with code assistants.

```bash
# Start MCP server (stdio transport)
mcp-skillset mcp

# Development mode (auto-reload on changes)
mcp-skillset mcp --dev
```

**Server details:**
- Transport: stdio (standard input/output)
- Protocol: Model Context Protocol v1.0
- Tools exposed: search_skills, get_skill, recommend_skills, list_categories, update_repositories

### Search & Discovery Commands

#### `search` - Semantic Search

Search for skills using natural language queries with hybrid RAG (vector + knowledge graph).

```bash
# Basic search
mcp-skillset search "python testing"

# Limit results
mcp-skillset search "debugging" --limit 5

# Filter by category
mcp-skillset search "testing" --category "Python"

# Override search mode (semantic vs graph weighting)
mcp-skillset search "async patterns" --search-mode semantic_focused
mcp-skillset search "pytest fixtures" --search-mode graph_focused
```

**Search modes:**
- `current` (default) - 70% semantic, 30% graph
- `semantic_focused` - 90% semantic, 10% graph (best for fuzzy queries)
- `graph_focused` - 30% semantic, 70% graph (best for related skills)
- `balanced` - 50% semantic, 50% graph

**Examples:**
```bash
# Find testing skills for Python
mcp-skillset search "python unit testing frameworks"

# Discover debugging techniques
mcp-skillset search "debugging techniques" --limit 3

# Find skills related to async programming
mcp-skillset search "asynchronous programming" --search-mode graph_focused
```

#### `list` - List All Skills

Display all available skills with filtering options.

```bash
# List all skills
mcp-skillset list

# Filter by category
mcp-skillset list --category "Testing"

# Compact output (table format)
mcp-skillset list --compact
```

**Output formats:**
- Default: Rich panels with descriptions
- Compact: Table view with ID, title, category

#### `info` / `show` - Skill Details

Show detailed information about a specific skill.

```bash
# Show skill details (both commands are identical)
mcp-skillset info pytest-fixtures
mcp-skillset show systematic-debugging

# Output includes:
# - Full skill ID and title
# - Description
# - Category
# - Repository source
# - Full instructions preview
```

#### `recommend` - Smart Recommendations

Get intelligent skill recommendations based on your project's toolchain.

```bash
# Get recommendations for current directory
mcp-skillset recommend

# Override search mode for recommendations
mcp-skillset recommend --search-mode graph_focused
```

**How it works:**
1. Analyzes project directory (package.json, pyproject.toml, Cargo.toml, etc.)
2. Detects primary language and frameworks
3. Searches for relevant skills using detected toolchain
4. Ranks by relevance to your tech stack

**Example output:**
```
🎯 Recommended Skills for Python Project

1. pytest-advanced-fixtures
   Category: Testing | Relevance: 0.92
   Advanced pytest fixture patterns for complex test scenarios

2. python-async-debugging
   Category: Debugging | Relevance: 0.88
   Debug async/await code with modern Python tools
```

#### `demo` - Interactive Skill Explorer

Generate example prompts and explore skills interactively.

```bash
# Interactive menu (browse all skills)
mcp-skillset demo

# Interactive mode explicitly
mcp-skillset demo --interactive

# Generate examples for specific skill
mcp-skillset demo pytest-fixtures
mcp-skillset demo systematic-debugging
```

**Features:**
- Browse all skills with Rich menu
- Auto-generates relevant example questions
- Extracts key concepts from skill instructions
- Shows practical use cases

**Example output:**
```
📚 Demo: pytest-fixtures

Key Concepts:
- Fixture scopes (function, class, module, session)
- Fixture dependencies and chaining
- Parametrized fixtures
- Fixture cleanup and teardown

Example Questions:
1. How do I create a database fixture with session scope?
2. Show me how to parametrize fixtures for multiple test cases
3. What's the best way to chain fixtures together?
```

### Repository Management Commands

#### `repo add` - Add Repository

Add a new skill repository to your configuration.

```bash
# Add repository with default priority
mcp-skillset repo add https://github.com/user/skills.git

# Add with custom priority (higher = searched first)
mcp-skillset repo add https://github.com/user/skills.git --priority 100
```

**Priority levels:**
- 100: Highest (official repositories)
- 50: Medium (default, community repositories)
- 10: Low (experimental repositories)

#### `repo list` - List Repositories

Display all configured skill repositories.

```bash
mcp-skillset repo list
```

**Output includes:**
- Repository URL
- Priority level
- Auto-update status
- Last update timestamp
- Number of skills indexed

#### `repo update` - Update Repositories

Pull latest changes from skill repositories.

```bash
# Update all repositories
mcp-skillset repo update

# Update specific repository by ID
mcp-skillset repo update anthropic-skills
```

**Note:** After updating, run `mcp-skillset index --incremental` to index new skills.

### GitHub Discovery Commands

Automatically discover skill repositories on GitHub.

#### `discover search` - Search GitHub

Search GitHub for skill repositories using natural language queries.

```bash
# Basic search
mcp-skillset discover search "python testing"

# With minimum stars filter
mcp-skillset discover search "fastapi" --min-stars 10

# Limit results
mcp-skillset discover search "react typescript" --limit 20
```

**Features:**
- Natural language search queries
- Automatic SKILL.md verification
- Star count filtering
- Rich metadata display (stars, forks, topics, license)

#### `discover trending` - Get Trending Repos

Find recently updated skill repositories.

```bash
# Weekly trending (default)
mcp-skillset discover trending

# Monthly trending
mcp-skillset discover trending --timeframe month

# Filter by topic
mcp-skillset discover trending --topic claude-skills
```

**Timeframes:** `week`, `month`, `year`

#### `discover topic` - Search by Topic

Search repositories by GitHub topic.

```bash
# Search by topic
mcp-skillset discover topic claude-skills

# With stars filter
mcp-skillset discover topic mcp-skills --min-stars 5
```

**Common topics:**
- `claude-skills` - Claude AI skills
- `anthropic-skills` - Anthropic skills
- `mcp-skills` - MCP protocol skills
- `ai-skills` - General AI skills

#### `discover verify` - Verify Repository

Verify that a repository contains SKILL.md files before adding.

```bash
mcp-skillset discover verify https://github.com/anthropics/skills.git
```

**Output includes:**
- SKILL.md verification status
- Repository metadata (stars, forks, license)
- Topics and description
- Command to add repository if valid

#### `discover limits` - API Rate Limits

Check your current GitHub API rate limit status.

```bash
mcp-skillset discover limits
```

**Rate limits:**
- Unauthenticated: 60 requests/hour
- Authenticated (with token): 5000 requests/hour

**To increase limits:**
```bash
export GITHUB_TOKEN=your_github_token_here
```

**See also:** [GitHub Discovery Documentation](./docs/GITHUB_DISCOVERY.md) for detailed usage and configuration.

### Utility Commands

#### `doctor` - Health Check

Run comprehensive system health check and validation.

```bash
mcp-skillset doctor
```

**Checks performed:**
- Configuration file validity
- Repository accessibility
- Index integrity (vector + knowledge graph)
- Embedding model availability
- Database connectivity
- Disk space and permissions

**Example output:**
```
🏥 MCP SkillSet Health Check

✅ Configuration: OK
✅ Repositories: 3 configured, all accessible
✅ Vector Store: 147 skills indexed
✅ Knowledge Graph: 147 nodes, 423 edges
✅ Embedding Model: all-MiniLM-L6-v2 (cached)
✅ Database: SQLite OK
✅ Disk Space: 2.3 GB available

System Status: Healthy ✅
```

#### `stats` - Usage Statistics

Display usage statistics and metrics.

```bash
mcp-skillset stats
```

**Metrics displayed:**
- Total skills indexed
- Skills by category
- Skills by repository
- Search query counts
- Most used skills
- Index size and memory usage

#### `enrich` - Prompt Enrichment

Enrich prompts with relevant skill context (advanced feature).

```bash
# Enrich a prompt with relevant skills
mcp-skillset enrich "help me write tests for async functions"

# Limit skills included
mcp-skillset enrich "debug memory leak" --max-skills 2

# Include full skill instructions (vs brief summaries)
mcp-skillset enrich "testing strategy" --full

# Set relevance threshold (0.0-1.0)
mcp-skillset enrich "python patterns" --threshold 0.8

# Save enriched prompt to file
mcp-skillset enrich "code review checklist" --output enriched_prompt.txt

# Copy to clipboard (requires pyperclip)
mcp-skillset enrich "refactoring" --clipboard
```

**What it does:**
1. Searches for relevant skills based on your prompt
2. Extracts key concepts and instructions from top matches
3. Augments your prompt with skill context
4. Outputs enriched prompt for use with LLMs

### Global Options

All commands support these global flags:

```bash
# Show version
mcp-skillset --version

# Verbose output
mcp-skillset --verbose search "testing"

# Debug mode (detailed logs)
mcp-skillset --debug search "testing"

# Help for any command
mcp-skillset --help
mcp-skillset search --help
mcp-skillset repo --help
```

### Command Workflows

**First-Time Setup Flow:**
```bash
# 1. Install mcp-skillset
pipx install mcp-skillset

# 2. Run setup wizard
mcp-skillset setup

# 3. Verify installation
mcp-skillset doctor

# 4. Explore available skills
mcp-skillset list
```

**Daily Usage Pattern:**
```bash
# Morning: Get recommendations for your project
cd ~/my-project
mcp-skillset recommend

# Search for specific skill when needed
mcp-skillset search "async debugging"

# View skill details before using
mcp-skillset info python-async-debugging

# Start MCP server for Claude integration
mcp-skillset mcp
```

**Adding New Skill Repository:**
```bash
# 1. Add repository
mcp-skillset repo add https://github.com/user/custom-skills.git

# 2. Rebuild index to include new skills
mcp-skillset index --incremental

# 3. Search new skills
mcp-skillset search "custom skill topic"
```

## Shell Completions

Enable tab completion for the `mcp-skillset` command to speed up your workflow:

### Quick Install

**Bash** (requires Bash 4.4+):
```bash
eval "$(_MCP_SKILLS_COMPLETE=bash_source mcp-skillset)" >> ~/.bashrc
source ~/.bashrc
```

**Zsh** (macOS default):
```zsh
eval "$(_MCP_SKILLS_COMPLETE=zsh_source mcp-skillset)" >> ~/.zshrc
source ~/.zshrc
```

**Fish**:
```fish
echo 'eval (env _MCP_SKILLS_COMPLETE=fish_source mcp-skillset)' >> ~/.config/fish/config.fish
source ~/.config/fish/config.fish
```

### Features

- ✅ Complete all commands and subcommands
- ✅ Complete option flags (`--help`, `--limit`, etc.)
- ✅ Works with `mcp-skillset`, `mcp-skillset repo`, and all other commands

### Verification

Test completions are working:
```bash
mcp-skillset <TAB>        # Shows: config health index info list mcp recommend repo search setup stats
mcp-skillset repo <TAB>   # Shows: add list update
mcp-skillset search --<TAB>  # Shows: --category --help --limit
```

### Documentation

For detailed installation instructions, troubleshooting, and advanced usage, see [docs/SHELL_COMPLETIONS.md](docs/SHELL_COMPLETIONS.md).

## MCP Tools

mcp-skillset exposes these tools to code assistants:

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
git clone https://github.com/bobmatnyc/mcp-skillset.git
cd mcp-skillset
pip install -e ".[dev]"
```

### Running from Source (Development Mode)

Use the `./mcp-skillset-dev` script to run commands directly from source without installation:

```bash
# Run any CLI command
./mcp-skillset-dev --version
./mcp-skillset-dev search "debugging"
./mcp-skillset-dev serve --dev

# All arguments pass through
./mcp-skillset-dev info systematic-debugging
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
mcp-skillset search "testing"

# Source version (no installation required)
./mcp-skillset-dev search "testing"
```

### Run Tests

```bash
make quality
```

### Performance Benchmarks

mcp-skillset includes comprehensive performance benchmarks to track and prevent regressions:

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

mcp-skillset includes comprehensive security scanning to identify vulnerabilities in dependencies and code:

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

### Deployment & Release
See [docs/DEPLOY.md](docs/DEPLOY.md) for the complete deployment and release workflow, including:
- Automated release process with Claude MPM multi-agent coordination
- PyPI publishing with stored credentials
- Homebrew tap management (consolidated bobmatnyc/tools tap)
- Pre-release validation, quality gates, and security scanning
- Post-release verification across all channels
- Rollback procedures and troubleshooting
- Quick reference commands for next release

### Architecture
See [docs/architecture/README.md](docs/architecture/README.md) for detailed architecture design.

### Skills Collections
See [docs/skills/RESOURCES.md](docs/skills/RESOURCES.md) for a comprehensive index of skill repositories compatible with mcp-skillset, including:
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

3. Install mcp-skillset (transfer wheel if needed):
   ```bash
   pip install mcp-skillset  # Or install from wheel
   ```

4. Verify the setup:
   ```bash
   mcp-skillset doctor
   ```

#### 5. Custom Cache Location

If you need to use a different cache directory:
```bash
export HF_HOME=/custom/path/to/cache
export TRANSFORMERS_CACHE=/custom/path/to/cache
mcp-skillset setup
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
1. Check [GitHub Issues](https://github.com/bobmatnyc/mcp-skillset/issues)
2. Review logs: `~/.mcp-skillset/logs/`
3. Run health check: `mcp-skillset doctor`
4. Open a new issue with:
   - Error message and stack trace
   - Output of `mcp-skillset --version`
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

- **PyPI Package**: [mcp-skillset on PyPI](https://pypi.org/project/mcp-skillset/)
- **Documentation**: [GitHub Wiki](https://github.com/bobmatnyc/mcp-skillset/wiki)
- **Issue Tracker**: [GitHub Issues](https://github.com/bobmatnyc/mcp-skillset/issues)
- **MCP Registry**: [MCP Servers](https://registry.modelcontextprotocol.io)
- **Publishing Guide**: [docs/publishing.md](docs/publishing.md)

---

**Status**: ✅ v0.5.0 - Production Ready | **Test Coverage**: 85-96% | **Tests**: 77 passing (48 unit + 29 security)
