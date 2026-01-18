# mcp-skillset Documentation

Comprehensive documentation for mcp-skillset - dynamic RAG-powered skills for code assistants via MCP.

## Quick Links

- **[Main README](../README.md)** - Installation and quick start guide
- **[Contributing Guidelines](../CONTRIBUTING.md)** - Development workflow and contribution guidelines
- **[Project Summary](../PROJECT_SUMMARY.md)** - Project overview and objectives

## Documentation Structure

### For Users
**[User Documentation](user/)** - Installation and usage guides
- Installation verification
- Security quick start

### For Developers
**[Developer Documentation](developer/)** - Technical documentation for contributors
- Deployment and release procedures
- CLI integration and configuration
- Skill builder and custom skills
- Implementation reports and technical details

### Architecture
**[Architecture Design](architecture/README.md)** - Comprehensive architecture documentation

Technical design and implementation details:
- System architecture and component design
- Hybrid RAG approach (vector store + knowledge graph)
- MCP server implementation
- Toolchain detection system
- Phase-by-phase implementation plan

### Skills Resources
**[Repository Resources](skills/RESOURCES.md)** - Comprehensive skills repository index

Complete catalog of skill repositories:
- **Official Collections**: anthropics/skills (priority 1)
- **Community Collections**: obra/superpowers, claude-mpm-skills, etc.
- **Coding Skills**: Testing, debugging, refactoring, documentation
- **Toolchain Skills**: Python, TypeScript, Rust, Go, Java
- **Operations Skills**: CI/CD, cloud platforms, security, IaC
- **MCP Servers**: Integration capabilities for skill-like functionality
- **Integration Guide**: How to add repositories to mcp-skillset
- **Verification Status**: Tracked status of all repositories

### Release History
**[Releases](releases/)** - Release notes and verification reports
- Version release summaries
- Verification reports
- Package rename documentation

### QA Reports
**[QA Documentation](qa/)** - Test reports and quality assurance
- Feature QA reports
- Ticket test reports
- Evidence documentation

### Research
**[Skills Research](research/skills-research.md)** - Comprehensive skills ecosystem research

Detailed research covering:
- 69+ individual skills analyzed
- Official Anthropic resources and MCP servers
- Community collections and curated lists
- 200+ MCP servers for tool integration
- Language-specific skills (Python, TypeScript, Rust, Go, Java)
- DevOps and operations skills
- Quality indicators and selection criteria
- Installation methods and licensing

### Archive
**[Documentation Archive](archive/)** - Historical documentation
- Work summaries and historical status reports
- Superseded documentation versions

## Documentation Index

### Getting Started
1. [Installation](../README.md#installation) - Install mcp-skillset from PyPI or source
2. [Quick Start](../README.md#quick-start) - Setup wizard and basic usage
3. [Configuration](../README.md#configuration) - Global and project configuration

### Core Concepts
1. [Architecture Overview](architecture/README.md#system-architecture) - System design
2. [Hybrid RAG Approach](architecture/README.md#hybrid-rag-architecture) - Vector + KG search
3. [Toolchain Detection](architecture/README.md#toolchain-detection) - Auto-detection system
4. [Skill Discovery](architecture/README.md#skill-discovery-process) - How skills are found

### Skills Management
1. [Repository Index](skills/RESOURCES.md) - All available skill repositories
2. [Adding Repositories](skills/RESOURCES.md#integration-guide) - Add new skill sources
3. [Priority System](skills/RESOURCES.md#priority-system) - Repository precedence
4. [Verification Status](skills/RESOURCES.md#verification-status) - Repository validation

### Development
1. [Contributing](../CONTRIBUTING.md) - Development workflow
2. [Architecture Design](architecture/README.md) - Technical implementation
3. [Component Design](architecture/README.md#component-design) - Individual components

### Research & Background
1. [Skills Ecosystem Research](research/skills-research.md) - Comprehensive analysis
2. [Official Anthropic Resources](research/skills-research.md#official-anthropic-resources) - Official skills
3. [Community Collections](research/skills-research.md#community-collections-and-curated-lists) - Community skills
4. [MCP Servers](research/skills-research.md#mcp-servers-essential-tool-integrations) - Tool integrations

## Key Features

### Dynamic RAG-Powered Skills
- **Vector Search**: Semantic similarity search over skill descriptions
- **Knowledge Graph**: Skill relationships, dependencies, categories
- **Hybrid Approach**: Combines vector + graph for better discovery
- **On-Demand Loading**: Skills loaded when needed, not at startup

### Intelligent Recommendations
- **Toolchain Detection**: Auto-detects Python, TypeScript, Rust, Go, Java, etc.
- **Framework Detection**: Recognizes Flask, Django, React, Next.js, etc.
- **Context-Aware**: Recommends skills based on project context
- **Priority System**: Resolves conflicts via repository priorities

### Multi-Source Integration
- **Git Repositories**: Clone and index skills from multiple sources
- **Automatic Updates**: Configurable auto-update for repositories
- **Priority Management**: Higher priority repositories override lower
- **Conflict Resolution**: Smart handling of duplicate skills

### MCP Native
- **First-Class MCP**: Built on Model Context Protocol
- **Standard Protocol**: Works with any MCP-compatible code assistant
- **Stdio Transport**: Standard input/output communication
- **Resource Provider**: Exposes skills as MCP resources

## Common Tasks

### Installing mcp-skillset
```bash
# Recommended: Use uv for fastest installation
uv tool install mcp-skillset

# Alternative: Use pipx
pipx install mcp-skillset

# Fallback: Use pip
pip install mcp-skillset
```

### Initial Setup
```bash
mcp-skillset setup
```

### Starting the Server
```bash
mcp-skillset serve
```

### Managing Repositories
```bash
# Add a repository
mcp-skillset repo add https://github.com/anthropics/skills --priority 100

# List repositories
mcp-skillset repo list

# Update all repositories
mcp-skillset repo update
```

### Searching Skills
```bash
# Search for skills
mcp-skillset search "testing"

# Get skill details
mcp-skillset info pytest-skill

# Get recommendations
mcp-skillset recommend
```

## Technology Stack

- **Python 3.11+**: Core implementation language
- **MCP Python SDK**: Model Context Protocol integration
- **ChromaDB/Qdrant**: Vector store for semantic search
- **NetworkX/Neo4j**: Knowledge graph for relationships
- **sentence-transformers**: Embedding generation
- **SQLite**: Metadata and configuration storage
- **GitPython**: Repository management

## Project Structure

```
mcp-skillset/
├── docs/                      # Documentation
│   ├── README.md             # This file
│   ├── architecture/         # Architecture design
│   │   └── README.md         # Detailed architecture
│   ├── research/             # Research and analysis
│   │   └── skills-research.md # Skills ecosystem research
│   └── skills/               # Skills resources
│       └── RESOURCES.md      # Repository index
├── src/                      # Source code
│   └── mcp_skills/           # Main package
├── tests/                    # Test suite
├── README.md                 # Main README
├── CONTRIBUTING.md           # Contributing guidelines
└── PROJECT_SUMMARY.md        # Project summary

~/.mcp-skillset/                # User data directory
├── config.yaml               # User configuration
├── repos/                    # Cloned skill repositories
│   ├── anthropics-skills/
│   ├── obra-superpowers/
│   └── custom-repo/
├── indices/                  # Vector + KG indices
│   ├── vector_store/
│   └── knowledge_graph/
└── metadata.db              # SQLite metadata
```

## Support

- **Issue Tracker**: [GitHub Issues](https://github.com/bobmatnyc/mcp-skillset/issues)
- **Documentation**: [GitHub Wiki](https://github.com/bobmatnyc/mcp-skillset/wiki)
- **MCP Registry**: [Model Context Protocol](https://registry.modelcontextprotocol.io)

## Contributing

We welcome contributions! Please see:
- [CONTRIBUTING.md](../CONTRIBUTING.md) for development workflow
- [Architecture Design](architecture/README.md) for technical details
- [Skills Resources](skills/RESOURCES.md) to propose new repositories

## License

MIT License - see [LICENSE](../LICENSE) for details

---

**Last Updated**: 2026-01-18
**Status**: Active development - v0.7.9
**Maintained by**: mcp-skillset project
