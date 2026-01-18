# MCP Tool Definitions Analysis - 2026-01-17

## Executive Summary

The mcp-skillset project defines 2 consolidated MCP tools (v2.0 architecture) that replaced 7 legacy tools for 60% token reduction. The tools are defined in `/Users/masa/Projects/mcp-skillset/src/mcp_skills/mcp/tools/` and use FastMCP SDK for registration.

**Current Status:**
- ✅ Tools are well-documented with comprehensive docstrings
- ✅ Parameter enumerations are clear in code but not fully exposed in descriptions
- ⚠️ MCPSearch discoverability could be improved with semantic keywords
- ⚠️ Valid parameter values are documented in code but not enumerated in tool descriptions

## File Locations

### Primary Tool Definitions
1. **find_tool.py** - `/Users/masa/Projects/mcp-skillset/src/mcp_skills/mcp/tools/find_tool.py`
   - Defines `find()` tool
   - 547 lines with comprehensive routing logic

2. **skill_tool.py** - `/Users/masa/Projects/mcp-skillset/src/mcp_skills/mcp/tools/skill_tool.py`
   - Defines `skill()` tool
   - 560 lines with CRUD operations and git workflow

3. **__init__.py** - `/Users/masa/Projects/mcp-skillset/src/mcp_skills/mcp/tools/__init__.py`
   - Imports and registers tools with FastMCP

### Server Integration
- **server.py** - `/Users/masa/Projects/mcp-skillset/src/mcp_skills/mcp/server.py`
   - FastMCP server initialization
   - Service configuration and dependency injection

### Test Files
- **test_mcp_tools.py** - `/Users/masa/Projects/mcp-skillset/tests/e2e/test_mcp_tools.py`
   - 678 lines of comprehensive E2E tests
   - Demonstrates all usage patterns

## Tool 1: `find()` - Unified Discovery Tool

### Current Definition

```python
@mcp.tool()
async def find(
    query: str | None = None,
    by: str = "semantic",
    toolchain: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    skill_id: str | None = None,
    project_path: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Find skills using semantic search, knowledge graph, or metadata queries.

    Unified discovery tool replacing 4 separate tools with a single entry point.
    Use the 'by' parameter to select search method.

    Search Methods (by parameter):
    - semantic: Vector + graph hybrid search (default, 70% vector + 30% graph)
    - graph: Knowledge graph traversal only (relationship-based)
    - category: List categories or filter by category
    - template: List available skill templates
    - recommend: Get recommendations based on skill or project
    ...
```

### Valid Parameter Values

#### `by` parameter (Search Methods)
```python
VALID_BY_VALUES = [
    "semantic",    # Default: Hybrid RAG (70% vector + 30% graph)
    "graph",       # Knowledge graph traversal only
    "category",    # List/filter by category
    "template",    # List skill templates
    "recommend",   # Get recommendations
]
```

#### `toolchain` parameter (Language/Framework Filters)
Based on codebase analysis, detected toolchains include:
```python
SUPPORTED_TOOLCHAINS = [
    # Languages
    "python",
    "typescript",
    "javascript",
    "rust",
    "go",
    "java",
    "php",
    "ruby",

    # Frameworks (detected in code)
    "fastapi",
    "flask",
    "django",
    "nextjs",
    "react",
    "vue",
    "svelte",
]
```

#### `category` parameter (Skill Categories)
From test data and documentation:
```python
SKILL_CATEGORIES = [
    "testing",
    "architecture",
    "debugging",
    "refactoring",
    "deployment",
    "security",
    "performance",
    "best-practices",
    "api-development",
    "web-development",
    "uncategorized",
]
```

#### `template` results (Skill Templates)
Hardcoded in `SKILL_TEMPLATES` constant:
```python
AVAILABLE_TEMPLATES = [
    {
        "name": "base",
        "description": "General-purpose skill template",
        "use_cases": ["general patterns", "best practices"],
    },
    {
        "name": "web-development",
        "description": "Web development patterns",
        "use_cases": ["frontend", "backend", "fullstack"],
    },
    {
        "name": "api-development",
        "description": "REST/GraphQL API patterns",
        "use_cases": ["API design", "endpoint patterns"],
    },
    {
        "name": "testing",
        "description": "Testing strategies and TDD",
        "use_cases": ["unit tests", "integration", "TDD"],
    },
]
```

### Capabilities by Mode

#### Mode: `by="semantic"` (Default)
- **Algorithm:** Hybrid RAG (70% vector embedding + 30% knowledge graph)
- **Input:** `query` (required), optional filters: `toolchain`, `category`, `tags`
- **Output:** Ranked skills with relevance scores
- **Use Cases:**
  - Natural language queries: "pytest testing patterns"
  - Fuzzy matching: "fast API async patterns"
  - Multi-word semantic search

#### Mode: `by="graph"`
- **Algorithm:** Knowledge graph traversal only
- **Input:** `query` or filters (at least one required)
- **Output:** Skills connected via graph relationships
- **Use Cases:**
  - Relationship-based discovery
  - Finding related/complementary skills
  - Toolchain-specific browsing

#### Mode: `by="category"`
- **Behavior:**
  - No `category` param: List all categories with counts
  - With `category` param: Filter skills by category
- **Output:**
  - Without param: `{"categories": [...], "total_categories": N}`
  - With param: `{"category": "testing", "skills": [...], "count": N}`

#### Mode: `by="template"`
- **Behavior:** List available skill templates
- **Input:** No additional params needed
- **Output:** Array of template metadata (name, description, use_cases)

#### Mode: `by="recommend"`
- **Requirement:** Either `skill_id` OR `project_path` (mutually exclusive)
- **Behaviors:**
  - **Project-based:** Detects toolchain from `project_path`, recommends relevant skills
  - **Skill-based:** Finds related skills via knowledge graph (max_depth=2)
- **Output:** Recommendations with confidence scores and reasoning

### Usage Examples

```python
# 1. Semantic search
find(query="pytest testing patterns", by="semantic", limit=5)

# 2. Filter by toolchain
find(query="testing", by="semantic", toolchain="python", limit=10)

# 3. Filter by category
find(query="security", by="semantic", category="best-practices")

# 4. Filter by tags (AND logic)
find(query="python", by="semantic", tags=["python", "testing"])

# 5. Graph-only search
find(query="security", by="graph", toolchain="python")

# 6. List all categories
find(by="category")

# 7. Search within category
find(by="category", category="testing", limit=10)

# 8. List templates
find(by="template")

# 9. Project recommendations
find(by="recommend", project_path="/path/to/project", limit=5)

# 10. Skill-based recommendations
find(by="recommend", skill_id="pytest-skill", limit=5)
```

## Tool 2: `skill()` - Unified CRUD Tool

### Current Definition

```python
@mcp.tool()
async def skill(
    action: str,
    skill_id: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Perform skill read operations.

    Actions:
    - read: Get complete skill details
    - reindex: Rebuild search indices

    Note: Write operations (create/update/delete) are available via CLI only.
    Use `mcp-skillset build-skill` for creating skills.
```

### Valid Parameter Values

#### `action` parameter
```python
VALID_ACTIONS = [
    # Available via MCP
    "read",      # Get complete skill details
    "reindex",   # Rebuild search indices

    # CLI-only (intentionally disabled in MCP)
    "create",    # Create new skill (returns error with CLI guidance)
    "update",    # Update existing skill (returns error)
    "delete",    # Delete skill (returns error)
]
```

**Design Decision:** Write operations disabled in MCP to:
1. Enforce git workflow via CLI
2. Prevent unintended skill modifications
3. Maintain skill quality through review process

### Capabilities by Action

#### Action: `read`
- **Input:** `skill_id` (required)
- **Output:** Complete skill object with:
  - Metadata: id, name, description, category, tags, version, author
  - Content: instructions, examples, dependencies
  - Source: file_path, repo_id
- **Use Case:** View full skill details before deployment

#### Action: `reindex`
- **Input:** `force` (optional, default: false)
- **Output:** Indexing statistics:
  - indexed_count
  - vector_store_size
  - graph_nodes
  - graph_edges
  - last_indexed
  - forced (boolean)
- **Behavior:**
  - `force=false`: Incremental reindex (only changed skills)
  - `force=true`: Full reindex (all skills)
- **Use Cases:**
  - After discovering new skills
  - After repository updates
  - Troubleshooting search issues

### Usage Examples

```python
# 1. Read skill details
skill(action="read", skill_id="pytest-skill")

# 2. Incremental reindex
skill(action="reindex", force=False)

# 3. Force full reindex
skill(action="reindex", force=True)

# 4. Create skill (returns error with CLI guidance)
skill(action="create", ...)
# Returns: {"status": "error", "message": "Use CLI: mcp-skillset build-skill"}
```

## Current Tool Discoverability Analysis

### Strengths
1. ✅ **Clear Parameter Documentation:** Docstrings enumerate all valid values for `by` parameter
2. ✅ **Comprehensive Examples:** 10+ usage examples in docstrings
3. ✅ **Consistent Error Messages:** Invalid parameters return helpful error messages with valid options
4. ✅ **Type Hints:** All parameters have proper Python type annotations

### Gaps for MCPSearch
1. ⚠️ **Semantic Keywords Missing:** Descriptions don't include common search terms
   - Missing: "recommend", "suggestion", "template", "reindex", "rebuild"
   - Missing: Language names: "python", "typescript", "rust", "go"
   - Missing: Domain terms: "testing", "deployment", "security", "api"

2. ⚠️ **Parameter Values Not Enumerated in Description:** Valid values documented in docstring body but not in first paragraph
   - `by` values: semantic, graph, category, template, recommend
   - Common toolchains: python, typescript, rust, go, javascript
   - Example categories: testing, debugging, security, architecture

3. ⚠️ **Use Case Patterns Not Highlighted:** Common workflows not surfaced as keywords
   - "browse skills by category"
   - "get skill templates"
   - "rebuild search index"
   - "find related skills"

## Recommendations for Improved MCPSearch Discoverability

### 1. Enhanced `find()` Description

**Current (first paragraph):**
```
Find skills using semantic search, knowledge graph, or metadata queries.
```

**Recommended:**
```
Find skills using semantic search, knowledge graph, recommendations, categories, or templates.
Search by query, toolchain (python/typescript/rust/go), category (testing/deployment/security),
or get recommendations based on project. List available skill templates or browse by category.
```

**Keyword Coverage:**
- Search methods: semantic, graph, recommend, category, template
- Toolchains: python, typescript, rust, go, javascript
- Categories: testing, deployment, security, architecture, debugging
- Actions: search, recommend, browse, list, template

### 2. Enhanced `skill()` Description

**Current:**
```
Perform skill read operations.
```

**Recommended:**
```
Read skill details or reindex search indices. Get complete skill information including
instructions, examples, and dependencies. Rebuild vector and graph indices after
discovering new skills. (Create/update/delete via CLI only: mcp-skillset build-skill)
```

**Keyword Coverage:**
- Actions: read, reindex, rebuild, get, view
- Components: vector, graph, indices, instructions, examples
- CLI fallback: create, update, delete, build-skill

### 3. Parameter Value Enumeration

Add explicit parameter value lists to descriptions:

```python
@mcp.tool()
async def find(
    query: str | None = None,
    by: str = "semantic",  # Valid: semantic|graph|category|template|recommend
    toolchain: str | None = None,  # Common: python|typescript|rust|go|javascript
    category: str | None = None,  # Common: testing|deployment|security|architecture
    tags: list[str] | None = None,
    skill_id: str | None = None,
    project_path: str | None = None,
    limit: int = 10,  # Range: 1-50
) -> dict[str, Any]:
```

### 4. Use Case Pattern Keywords

Add common workflow keywords to descriptions:

**find() workflows:**
- "search skills by natural language query"
- "browse skills by category"
- "list available skill templates"
- "get project-based recommendations"
- "find related skills via knowledge graph"
- "filter by programming language"

**skill() workflows:**
- "view complete skill details"
- "read skill instructions and examples"
- "rebuild search indices"
- "force reindex all skills"

## Implementation Priority

### High Priority (Maximum MCPSearch Impact)
1. **Add semantic keywords to first paragraph** - Ensures keyword matching works
2. **Enumerate valid parameter values inline** - Makes options discoverable
3. **Include common toolchains and categories** - Improves domain-specific searches

### Medium Priority
4. **Add use case pattern keywords** - Helps users discover capabilities
5. **Document parameter ranges** - Clarifies limits (e.g., limit: 1-50)

### Low Priority
6. **Expand examples section** - Already comprehensive in docstrings
7. **Add more edge case documentation** - Covered in tests

## Technical Context

### Tool Registration Flow
```
1. FastMCP SDK initialized in server.py
   └─> mcp = FastMCP("mcp-skillset")

2. Tools imported in __init__.py
   └─> from . import find_tool, skill_tool

3. Tools decorated with @mcp.tool()
   └─> Auto-registered with FastMCP server

4. Server started with stdio transport
   └─> mcp.run(transport="stdio")
```

### Service Dependencies
Both tools depend on global service instances configured at startup:
- **SkillManager:** Loads skills from disk/cache
- **IndexingEngine:** Vector search (ChromaDB) + Knowledge graph (NetworkX)
- **ToolchainDetector:** Project analysis for recommendations
- **RepositoryManager:** Git repository management

### Error Handling Patterns
All tools follow consistent error response structure:
```python
{
    "status": "error",
    "error": "Human-readable error message",
    "valid_methods": [...],  # For invalid enum values
    "context": {...}  # Additional debugging info
}
```

## Related Files

### Configuration
- `/Users/masa/Projects/mcp-skillset/src/mcp_skills/models/config.py` - MCPSkillsConfig
- `/Users/masa/Projects/mcp-skillset/CLAUDE.md` - Project documentation

### Tests
- `/Users/masa/Projects/mcp-skillset/tests/e2e/test_mcp_tools.py` - E2E tool tests
- `/Users/masa/Projects/mcp-skillset/tests/test_mcp_server.py` - Server integration tests

### Documentation
- `/Users/masa/Projects/mcp-skillset/README.md` - User-facing documentation
- `/Users/masa/Projects/mcp-skillset/docs/architecture/README.md` - Architecture docs

## Next Steps

1. Update tool descriptions with enhanced keywords
2. Add inline parameter value enumerations
3. Test MCPSearch with new descriptions
4. Document common search patterns in README
5. Consider adding MCPSearch-specific metadata to tool definitions

---

**Research Date:** 2026-01-17
**Project Version:** 0.7.8
**Tool Architecture:** v2.0 (Consolidated)
**MCP SDK:** FastMCP
