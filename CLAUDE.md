# Claude AI Assistant - Project Context

## Linear Project

**Project:** MCP-SkillSet: Dynamic RAG Skills for Code Assistants
**URL:** https://linear.app/1m-hyperdev/project/mcp-skillset-dynamic-rag-skills-for-code-assistants-0000af8da9b0/overview
**Team:** 1M HyperDev

### Workflow Guidelines

When working on this project:

1. **Review tickets from this Linear project** before starting new work
2. **Assign all new tickets** to this project (Project ID: `0000af8da9b0`)
3. **Reference ticket IDs** in commit messages (e.g., `1M-XXX: description`)
4. **Update ticket status** as work progresses
5. **Link related work** (PRs, commits, documentation) to tickets

### Ticket Management

- **Epic/Project ID:** `0000af8da9b0`
- **Team Key:** `1M`
- **Ticket Prefix:** `1M-XXX`

### Quick Links

- [Project Overview](https://linear.app/1m-hyperdev/project/mcp-skillset-dynamic-rag-skills-for-code-assistants-0000af8da9b0/overview)
- [Active Issues](https://linear.app/1m-hyperdev/team/1M/active)

## Project Information

**Name:** mcp-skillset
**Type:** Python Package / MCP Server
**Purpose:** Dynamic RAG-powered skill discovery and recommendation system for AI code assistants

### Key Technologies

- Python 3.11+
- MCP (Model Context Protocol)
- ChromaDB (vector storage)
- NetworkX (knowledge graph)
- sentence-transformers (embeddings)

### Distribution Channels

- **PyPI:** https://pypi.org/project/mcp-skillset/
- **Homebrew:** `brew install bobmatnyc/tools/mcp-skillset`
- **GitHub:** https://github.com/bobmatnyc/mcp-skillset

### Supported AI Agents

- Claude Desktop
- Claude Code (VS Code extension)
- Auggie (Cursor)

## Development Workflow

1. Check Linear project for active tickets
2. Create/assign tickets for new features or bugs
3. Implement changes with ticket references
4. Test thoroughly (pytest with coverage)
5. Update documentation
6. Create PR with ticket reference
7. Update ticket status upon completion

## Release Process

See `docs/DEPLOY.md` for complete release workflow.

**Current Version:** 0.8.6

### Quick Release Steps

1. Pre-release validation (`make pre-publish`)
2. Security scan
3. Version increment
4. Build and publish to PyPI
5. Update Homebrew tap
6. Post-release verification
7. Update Linear tickets

## Commands Reference

### Setup & Installation
```bash
mcp-skillset setup          # Full setup including agent installation
mcp-skillset install        # Install MCP server for AI agents
mcp-skillset config         # View/edit configuration
```

### Skill Management
```bash
mcp-skillset discover       # Discover skills from repositories
mcp-skillset index          # Index skills for search
mcp-skillset search         # Search skills
mcp-skillset recommend      # Get skill recommendations
```

### Development
```bash
uv run pytest              # Run tests
uv run pytest --cov        # Run tests with coverage
make pre-publish           # Pre-release quality gate
make release-pypi          # Publish to PyPI
```

## Project Structure

```
mcp-skillset/
├── src/mcp_skills/        # Main package
│   ├── cli/               # CLI commands
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   └── storage/           # Storage backends
├── tests/                 # Test suite
├── docs/                  # Documentation
└── .mcp-skillset/         # Local data directory
```

## Important Notes

- All work should be tracked in Linear
- Maintain test coverage above 85%
- Follow conventional commit format
- Update CHANGELOG.md for releases
- Keep README.md synchronized with features
