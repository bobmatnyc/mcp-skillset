# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2025-11-30

### Changed

#### Complete CLI Refactoring ([1M-460](https://linear.app/1m-hyperdev/issue/1M-460))

**Major architectural improvement reducing main.py from 2,644 lines to 67 lines (-97.5%)**

This release represents a complete restructuring of the CLI architecture for improved maintainability, testability, and developer experience. All 14 CLI commands have been extracted into separate, focused modules.

**Impact:**
- **Maintainability**: Each command is now self-contained with clear responsibilities
- **Testability**: Modular structure enables better unit testing
- **Developer Experience**: Easier to understand, modify, and extend individual commands
- **Code Quality**: Eliminated 2,577 lines of monolithic code

**Architectural Changes:**
```
Before: src/mcp_skills/cli/main.py (2,644 lines)
After:  src/mcp_skills/cli/
        ├── main.py (67 lines) - Entry point only
        ├── commands/
        │   ├── build_skill.py - Skill template generation
        │   ├── config.py - Configuration management
        │   ├── demo.py - Interactive demonstration
        │   ├── discover.py - Skill discovery
        │   ├── doctor.py - System diagnostics
        │   ├── enrich.py - Prompt enrichment
        │   ├── index.py - Skill indexing
        │   ├── info.py - Skill information
        │   ├── install.py - Agent installation
        │   ├── list_skills.py - Skill listing
        │   ├── recommend.py - Skill recommendations
        │   ├── repo.py - Repository management
        │   ├── search.py - Skill search
        │   ├── setup.py - Complete setup workflow
        │   └── stats.py - Usage statistics
        └── shared/
            └── console.py - Shared Rich console instance
```

**Commits Included:**
1. `feat: extract final 4 Priority 3 CLI commands (1M-460)`
2. `docs: add CLI refactoring research documents (1M-460)`
3. `feat: integrate all extracted CLI commands into main.py (1M-460)`
4. `feat: extract build-skill and config commands (1M-460)`
5. `feat: add per-repository progress bars for skill downloading`
6. `feat: extract stats and enrich commands (1M-460)`
7. `feat: extract recommend command (1M-460)`
8. `feat: extract 3 medium CLI commands (search, doctor, demo) (1M-460)`
9. `feat: extract first 4 CLI commands into modular structure (1M-460)`
10. `docs: add comprehensive work summary for 2025-11-30 session`
11. `docs: comprehensive architecture review and Linear tickets`
12. `fix: eliminate HuggingFace tokenizers fork warnings during setup`

**No Breaking Changes:**
- All CLI commands work identically to v0.6.x
- No changes to command arguments or behavior
- Safe upgrade from any 0.6.x version

**Upgrade Path:**
```bash
# PyPI
pip install --upgrade mcp-skillset

# Homebrew
brew upgrade mcp-skillset
```

## [0.6.8] - 2025-11-29

### Fixed
- **Installer Default Behavior** ([1M-408](https://linear.app/1m-hyperdev/issue/1M-408))
  - Default installer now excludes Claude Desktop to avoid config conflicts
  - `mcp-skillset install` and `mcp-skillset setup` now only install for Claude Code and Auggie by default
  - Users wanting Claude Desktop must explicitly use `--agent claude-desktop`
  - Prevents conflicts between Claude Desktop and Claude Code (similar config paths)
- **Agent Name Display** ([1M-409](https://linear.app/1m-hyperdev/issue/1M-409))
  - Installer now correctly displays "Claude Code" for Claude Code paths
  - Prevents user confusion about which agent is being configured
  - Added 6 regression tests for agent name detection

### Testing
- 9 new tests added for installer behavior
- `tests/cli/test_install_defaults.py` - Default behavior validation
- `tests/test_agent_installer.py` - Enhanced agent detection tests
- All existing tests pass

### Changed
- `src/mcp_skills/cli/main.py` - Updated install/setup command logic
- Default agents list now excludes Claude Desktop
- Agent detection logic improved for correct name display

## [0.6.7] - 2025-11-29

### Changed
- **BREAKING**: Renamed MCP tools to follow object_verb naming convention
  - `search_skills` → `skills_search` - Search for skills using hybrid RAG
  - `get_skill` → `skill_get` - Get complete skill details by ID
  - `recommend_skills` → `skills_recommend` - Get skill recommendations
  - `list_categories` → `skill_categories` - List all skill categories
  - `reindex_skills` → `skills_reindex` - Rebuild skill index
  - `list_skill_templates` → `skill_templates_list` - List available templates
  - `skill_create` remains unchanged (already follows convention)

### Migration Guide
If you're using these MCP tools directly:

**Before (v0.6.6 and earlier):**
```python
await search_skills(query="pytest", limit=10)
await get_skill(skill_id="pytest-skill")
await recommend_skills(project_path="/path/to/project")
await list_categories()
await reindex_skills(force=True)
await list_skill_templates()
```

**After (v0.6.7+):**
```python
await skills_search(query="pytest", limit=10)
await skill_get(skill_id="pytest-skill")
await skills_recommend(project_path="/path/to/project")
await skill_categories()
await skills_reindex(force=True)
await skill_templates_list()
```

**Note:** If you're using the MCP server through Claude Desktop, Claude Code, or other MCP clients, the tool names in your configuration and prompts will need to be updated to use the new names.

## [0.6.6] - 2025-11-29

### Fixed
- **CRITICAL**: Template files now included in PyPI distribution
- build-skill command now functional (was broken in 0.6.5)
- Added templates/**/*.j2 to package-data in pyproject.toml

## [0.6.5] - 2025-11-29

### Added
- **Progressive Skill Building**: Create custom skills with `build-skill` command
- `build-skill` CLI command with interactive, preview, and standard modes
- `skill_create` MCP tool for AI agent skill generation
- `list_skill_templates` MCP tool for template discovery
- SkillBuilder service with Jinja2 template engine
- 4 specialized skill templates (base, web-development, api-development, testing)
- Comprehensive validation (YAML, security, size limits)
- Auto-deployment to `~/.claude/skills/`
- Template-based skill generation with best practices
- Security validation for skill content
- Progressive loading support (metadata + full body)
- Examples and documentation for skill building

### Changed
- Added `jinja2>=3.1.0` dependency for template rendering
- Updated README with comprehensive skill building documentation
- Enhanced MCP tools section with skill creation tools
- Added Quick Reference entry for build-skill command

### Fixed
- Security validation now properly detects hardcoded credentials
- Template rendering handles special characters correctly
- CLI parameter validation improved

### Security
- Jinja2 autoescape consideration noted for future enhancement
- Security pattern scanning active in SkillBuilder
- No secrets detected in release (0 critical, 0 high vulnerabilities)

## [0.6.4] - 2025-11-29

### Added
- Agent installation now integrated into `setup` command as Step 6
- Automatically detects and configures Claude Desktop, Claude Code, and Auggie
- `--skip-agents` flag for `setup` command to skip automatic agent installation
- True one-command setup experience - `setup` now means "ready to use"

### Changed
- `setup` command now includes 6 steps instead of 5
- Setup process provides complete installation without manual agent configuration
- Updated documentation to reflect new integrated setup workflow
- Improved user experience to match mcp-ticketer's setup approach

### Fixed
- Setup tests now properly validate agent installation step
- Mock objects in tests return correct types (lists instead of Mock objects)

## [0.6.3] - 2025-11-28

### Changed
- Verified MCP server installer for Claude Desktop, Claude Code, and Auggie
- Comprehensive installer validation with timestamped backups
- Security scan: 0 vulnerabilities, 29/29 security tests passing

### Fixed
- Cross-platform path detection improvements
- Atomic configuration updates with automatic rollback

## [0.5.0] - 2025-11-24

### Added

#### Security Features
- Multi-layer security validation system for skill loading
- Prompt injection detection with threat classification (BLOCKED, DANGEROUS, SUSPICIOUS)
- Repository trust levels (TRUSTED, VERIFIED, UNTRUSTED)
- Content sanitization with skill boundary markers
- Size limit enforcement for DoS prevention
- Comprehensive security validator with regex pattern matching
- SECURITY.md with complete threat model and security policy
- Security test suite with 29 comprehensive tests

#### CLI Commands
- `show`: Alias for `info` command for improved user experience
- `demo`: Interactive skill demonstration with auto-generated example prompts
- Updated `setup` command to highlight new demo functionality

#### Service Enhancements
- SkillManager security integration with configurable validation
- Verified repository management (add/remove trusted repos)
- Fixed trust level detection for repository identification

### Changed
- Setup wizard now recommends `demo` command as first step
- Skill loading now validates content security before use
- README updated with security section and trust level documentation

### Fixed
- Fixed 15 SKILL.md files with validation errors
- Corrected repository trust level matching

## [0.1.0] - 2025-11-23

### Added

#### Core Features
- Initial release of mcp-skillset - dynamic RAG-powered skills for code assistants
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
- Zero-config setup with `mcp-skillset setup`
- Rich terminal UI with progress indicators
- Detailed error messages and troubleshooting hints
- Development mode with auto-reload support
- Makefile with common development tasks

### Configuration
- Global configuration in `~/.mcp-skillset/config.yaml`
- Project-local configuration with `.mcp-skillset.yaml`
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
- Legacy JSON files preserved as backup in `~/.mcp-skillset/metadata.json.backup`
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

[0.5.0]: https://github.com/bobmatnyc/mcp-skillset/releases/tag/v0.5.0
[0.1.0]: https://github.com/bobmatnyc/mcp-skillset/releases/tag/v0.1.0
