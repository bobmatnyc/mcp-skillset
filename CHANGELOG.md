# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-23

### Added

#### Core Features
- Initial release of mcp-skills - dynamic RAG-powered skills for code assistants
- FastMCP-based MCP server with 5 core tools for skill discovery and management
- 11 comprehensive CLI commands for skill and repository management
- Hybrid RAG system combining ChromaDB vector search and NetworkX knowledge graph
- Automatic toolchain detection supporting 24+ frameworks across 5 languages
- SQLite-based metadata storage with automatic JSON migration
- Complete integration test suite covering end-to-end workflows

#### MCP Tools
- `search_skills`: Natural language semantic search over skill descriptions
- `get_skill`: Retrieve full skill instructions and metadata by ID
- `recommend_skills`: Context-aware skill recommendations based on project toolchain
- `list_categories`: Browse skills by category and domain
- `reindex_skills`: Trigger manual reindexing of skill repositories

#### CLI Commands
- `setup`: Interactive setup wizard with toolchain detection and validation
- `search`: Search skills with natural language queries
- `list`: List all available skills with filtering options
- `info`: Display detailed information about specific skills
- `recommend`: Get personalized skill recommendations for current project
- `health`: System health check and diagnostics
- `stats`: Display usage statistics and repository metrics
- `repo add/list/update/remove`: Full repository management capabilities
- `index`: Manual reindexing with incremental update support
- `config`: Display and validate configuration settings

#### Language and Framework Support
- **Languages**: Python, TypeScript, JavaScript, Rust, Go
- **Python Frameworks**: FastAPI, Django, Flask, Pytest, Poetry, uv
- **JavaScript/TypeScript**: React, Next.js, Express, Vite, Node.js
- **Rust**: Cargo, Tokio, Actix
- **Go**: Go modules, Gin, Echo
- **Build Tools**: npm, yarn, pnpm, cargo, go mod, poetry, uv

#### RAG System
- Vector search with sentence-transformers (all-MiniLM-L6-v2 embeddings)
- Knowledge graph for skill relationships and dependencies
- Hybrid scoring: 70% vector similarity + 30% graph connectivity
- Confidence score normalization for toolchain detection
- Persistent ChromaDB vector store with incremental updates

#### Storage and Indexing
- SQLite metadata database for O(1) repository lookups
- Automatic migration from legacy JSON storage format
- Repository metadata tracking (URL, priority, auto-update settings)
- Indexed skill categories and toolchain associations

### Performance
- Complete integration test suite runs in <10 seconds
- O(1) indexed repository lookups via SQLite
- Efficient incremental reindexing for large skill collections
- Fast semantic search with cached embeddings

### Testing
- 48 total tests (37 unit + 11 integration tests)
- Test coverage: 85-96% across all modules
- End-to-end workflow validation
- Repository management integration tests
- Toolchain detection accuracy tests

### Documentation
- Comprehensive README with quick start guide
- Architecture documentation in docs/architecture/
- Skills resources catalog in docs/skills/RESOURCES.md
- API documentation for MCP tools
- CLI command reference with examples

### Developer Experience
- Zero-config setup with `mcp-skills setup`
- Rich terminal UI with progress indicators
- Detailed error messages and troubleshooting hints
- Development mode with auto-reload support
- Makefile with common development tasks

### Configuration
- Global configuration in `~/.mcp-skills/config.yaml`
- Project-local configuration with `.mcp-skills.yaml`
- Environment variable overrides
- Configurable repository priorities
- Auto-update settings per repository

### Known Limitations
- Vector store requires ~100MB disk space for medium-sized skill collections
- Initial indexing takes 5-15 seconds depending on repository size
- ChromaDB currently requires local filesystem access
- Knowledge graph stored in memory (future: persistent backend option)

### Migration Notes
- Automatic migration from JSON to SQLite metadata storage
- Legacy JSON files preserved as backup in `~/.mcp-skills/metadata.json.backup`
- No user action required for migration

## [Unreleased]

### Planned Features
- Qdrant vector store backend support
- Neo4j knowledge graph backend support
- HTTP transport mode for MCP server
- Skill usage analytics and recommendations tuning
- Custom skill repository authentication
- Skill versioning and update tracking
- Offline mode with cached skill bundles

---

[0.1.0]: https://github.com/bobmatnyc/mcp-skills/releases/tag/v0.1.0
