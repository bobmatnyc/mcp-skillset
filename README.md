# mcp-skills

[![PyPI version](https://badge.fury.io/py/mcp-skills.svg)](https://badge.fury.io/py/mcp-skills)
[![Python Versions](https://img.shields.io/pypi/pyversions/mcp-skills)](https://pypi.org/project/mcp-skills/)
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

### From PyPI

```bash
pip install mcp-skills
```

### From Source

```bash
git clone https://github.com/bobmatnyc/mcp-skills.git
cd mcp-skills
pip install -e .
```

## Quick Start

### 1. Setup

Run the interactive setup wizard to configure mcp-skills for your project:

```bash
mcp-skills setup
```

This will:
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

### Run Tests

```bash
make quality
```

### Linting and Formatting

```bash
make lint-fix
```

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

- **PyPI Package**: [mcp-skills on PyPI](https://pypi.org/project/mcp-skills/)
- **Documentation**: [GitHub Wiki](https://github.com/bobmatnyc/mcp-skills/wiki)
- **Issue Tracker**: [GitHub Issues](https://github.com/bobmatnyc/mcp-skills/issues)
- **MCP Registry**: [MCP Servers](https://registry.modelcontextprotocol.io)
- **Publishing Guide**: [docs/publishing.md](docs/publishing.md)

---

**Status**: ✅ v0.1.0 - Production Ready | **Test Coverage**: 85-96% | **Tests**: 48 passing
