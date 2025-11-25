# SkillsMP Integration Analysis

## Executive Summary

**Status**: ❌ SkillsMP API integration is **not recommended**
**Reason**: No public API available, and direct GitHub access is superior
**Alternative**: Implement GitHub-based skill discovery instead

## Research Findings

### SkillsMP Platform Overview

- **Type**: Web-based skill marketplace aggregator
- **Skills Indexed**: 13,000+ Claude skills
- **Data Source**: Public GitHub repositories
- **Update Frequency**: Regular GitHub syncing
- **Quality Filter**: Minimum 2 stars requirement
- **Search**: Web interface with AI semantic search
- **Affiliation**: Independent community project (not Anthropic)

### API Availability

**Result**: ❌ No public API found

**Evidence**:
1. `/api` endpoint returns 404
2. No API documentation in search results
3. No programmatic access methods mentioned on website
4. Web search found zero references to SkillsMP API endpoints
5. Platform appears to be web-only interface

### Data Sources Analysis

SkillsMP aggregates skills from public GitHub repositories including:

**Official Anthropic Repos**:
- `github.com/anthropics/skills` - Official skills repository (Apache 2.0)

**Community Repos**:
- `github.com/obra/superpowers` - Community skills
- `github.com/bobmatnyc/claude-mpm-skills` - Community skills
- Many others discovered through GitHub search

**Key Insight**: SkillsMP doesn't host skills - it **indexes** them. All skills are available directly via GitHub.

## Current mcp-skillset Architecture

### Existing GitHub Integration

The project already has robust GitHub repository management:

**File**: `src/mcp_skills/services/repository_manager.py`

**Features**:
- Git repository cloning (GitPython)
- Repository prioritization (0-100)
- Automatic skill counting
- Update mechanism (git pull)
- Metadata storage (SQLite)

**Default Repositories** (already configured):
```python
DEFAULT_REPOS = [
    {
        "url": "https://github.com/anthropics/skills.git",
        "priority": 100,
        "license": "Apache-2.0",
    },
    {
        "url": "https://github.com/obra/superpowers.git",
        "priority": 90,
        "license": "MIT",
    },
    {
        "url": "https://github.com/bobmatnyc/claude-mpm-skills.git",
        "priority": 80,
        "license": "MIT",
    },
]
```

### Existing Discovery Mechanisms

**Vector Search** (ChromaDB):
- 13,000+ skills can be indexed locally
- Semantic search with embeddings
- Fast local queries (no network calls)

**Knowledge Graph** (NetworkX):
- Relationship mapping between skills
- Dependency tracking
- Category organization

**Hybrid Search**:
- Combines vector + graph (configurable weights)
- Already supports smart discovery
- CLI command: `mcp-skillset search <query>`

## Why SkillsMP Integration is Unnecessary

### Argument 1: Data Redundancy
- SkillsMP indexes GitHub repos
- mcp-skillset already clones GitHub repos
- Same data, different access method
- Direct access is faster and more reliable

### Argument 2: Superior Local Search
- mcp-skillset has vector search (semantic)
- mcp-skillset has knowledge graph (relationships)
- mcp-skillset has hybrid search (best of both)
- Local search is instant, no API rate limits

### Argument 3: No Additional Skills
- SkillsMP doesn't create skills
- SkillsMP doesn't host unique skills
- SkillsMP only aggregates public GitHub repos
- All skills accessible via git clone

### Argument 4: Maintenance Burden
- Web scraping is fragile (breaks when UI changes)
- No API means parsing HTML (unreliable)
- Rate limiting risk on web scraping
- Better to use official GitHub APIs

## Recommended Alternative: GitHub Discovery Service

Instead of SkillsMP, implement **GitHub-based automatic discovery**:

### Proposed Feature: GitHub Skills Discovery

**Purpose**: Automatically discover new skill repositories on GitHub

**Implementation Approach**:

#### Option 1: GitHub Search API (Recommended)
```python
# src/mcp_skills/services/github_discovery.py

class GitHubSkillDiscovery:
    """Discover Claude skill repositories on GitHub."""

    def search_skill_repos(self, query: str = "claude skills",
                           min_stars: int = 2) -> list[RepositoryInfo]:
        """
        Search GitHub for skill repositories.

        Uses GitHub Search API:
        - Query: "claude skills" OR "anthropic skills" OR "SKILL.md"
        - Filter: stars >= min_stars
        - Sort: by stars, recently updated

        Returns: List of repository URLs with metadata
        """
        pass

    def discover_by_topic(self, topics: list[str]) -> list[RepositoryInfo]:
        """
        Discover repos by GitHub topics.

        Topics: ["claude-skills", "anthropic", "mcp-skills"]
        """
        pass

    def get_trending_skills(self, timeframe: str = "week") -> list[RepositoryInfo]:
        """Get trending skill repositories."""
        pass
```

#### Option 2: GitHub Topics Discovery
```python
# Discover via GitHub topics
topics = [
    "claude-skills",
    "claude-code",
    "anthropic-skills",
    "mcp-skills"
]

for topic in topics:
    repos = github.search_repositories(f"topic:{topic}")
    # Filter for repos with SKILL.md files
    # Add to repository manager
```

#### Option 3: Awesome Lists Aggregation
```python
# Discover via curated awesome lists
awesome_lists = [
    "awesome-claude",
    "awesome-anthropic",
    "awesome-ai-agents"
]

# Parse awesome-* README files for skill repo links
```

### CLI Commands Design

```bash
# Discover new skill repositories on GitHub
mcp-skillset discover --source github --min-stars 5

# Search GitHub for skills by keyword
mcp-skillset discover search "python testing"

# Get trending skill repos this week
mcp-skillset discover trending --timeframe week

# Discover by GitHub topic
mcp-skillset discover topic claude-skills

# Auto-add discovered repos (with confirmation)
mcp-skillset discover --auto-add --priority 50
```

### Configuration Options

```yaml
# ~/.mcp-skillset/config.yaml

discovery:
  enabled: true
  sources:
    - github  # GitHub Search API
    - topics  # GitHub topics
    - awesome # Awesome lists

  github:
    min_stars: 2
    exclude_archived: true
    exclude_forks: false
    topics:
      - claude-skills
      - anthropic-skills
      - mcp-skills

  auto_update:
    enabled: false  # Don't auto-add without user confirmation
    frequency: weekly
    priority: 50
```

## Implementation Priority: GitHub API Integration

### Phase 1: GitHub Search API Client
**File**: `src/mcp_skills/services/github_discovery.py`

**Features**:
- Search repositories by keyword
- Filter by stars, language, topics
- Verify SKILL.md files exist
- Extract repository metadata

**Dependencies**:
- `PyGithub` or `requests` (GitHub REST API)
- Authentication: Personal Access Token (optional, higher rate limits)

### Phase 2: CLI Commands
**File**: `src/mcp_skills/cli/main.py`

**Add command group**:
```python
@cli.group()
def discover() -> None:
    """Discover new skill repositories."""
    pass

@discover.command("search")
@click.argument("query")
def discover_search(query: str) -> None:
    """Search GitHub for skill repositories."""
    pass
```

### Phase 3: Auto-Discovery
**File**: `src/mcp_skills/services/auto_discovery.py`

**Features**:
- Scheduled discovery runs
- Notification of new repos
- Optional auto-add with approval

## Benefits of GitHub-Based Discovery

### ✅ Advantages

1. **Official API**: GitHub provides stable, documented API
2. **Rate Limits**: 60 requests/hour (unauthenticated), 5000/hour (authenticated)
3. **Reliability**: No web scraping, no parsing fragility
4. **Metadata**: Stars, forks, topics, last updated, license
5. **Filtering**: Built-in search filters (stars, language, date)
6. **Authentication**: Optional PAT for higher limits
7. **Programmatic**: RESTful API with client libraries
8. **Discovery**: Find repos SkillsMP might not have indexed yet

### ✅ Features Enabled

- **Smart Discovery**: Find new skills by stars, recency, topics
- **Trending Skills**: Sort by recently updated or star growth
- **Quality Filtering**: Minimum stars, exclude archived repos
- **License Checking**: Verify Apache-2.0, MIT compatibility
- **Auto-Update**: Periodic checks for new skill repositories
- **Community Curation**: Discover via topics like `claude-skills`

### ❌ Limitations

- **Rate Limits**: 60/hour without auth, 5000/hour with token
- **No Semantic Search**: Keyword-based, not AI-powered like SkillsMP
- **Discovery Only**: Still need to clone repos afterward
- **GitHub-Only**: Won't find skills hosted elsewhere (rare)

## Migration Path: For Users Who Want SkillsMP-Like Discovery

If users specifically want SkillsMP's discovery capabilities:

### Option 1: Manual Discovery via SkillsMP Website
**Workflow**:
1. Browse https://skillsmp.com
2. Find interesting skill repository
3. Copy GitHub URL
4. Run: `mcp-skillset repo add <github-url>`

**Advantages**: Visual browsing, AI search
**Disadvantages**: Manual process, no automation

### Option 2: Web Scraping (Not Recommended)
**Approach**: Parse SkillsMP HTML
**Issues**:
- Fragile (breaks when site changes)
- Potential ToS violation
- Rate limiting risk
- Maintenance burden

**Recommendation**: ❌ Do not implement

### Option 3: Request SkillsMP API (Community Request)
**Approach**: Contact SkillsMP maintainers
**Ask For**: Public API for skill discovery
**Likelihood**: Unknown (independent project)

## Conclusion

### Recommendation: Implement GitHub Discovery, Not SkillsMP Integration

**Reasons**:
1. SkillsMP has no public API
2. SkillsMP data comes from GitHub (same source)
3. GitHub API is stable, documented, and official
4. mcp-skillset already has superior local search
5. GitHub discovery enables finding NEW repos SkillsMP doesn't have

### Next Steps

1. ✅ **Phase 1**: Implement GitHub discovery service
2. ✅ **Phase 2**: Add CLI commands for discovery
3. ✅ **Phase 3**: Add auto-discovery configuration
4. ❌ **Skip**: SkillsMP web scraping/integration

### Documentation Updates

Add to README:
```markdown
## Discovering New Skills

### Automatic Discovery (GitHub)
mcp-skillset can automatically discover new skill repositories on GitHub:

```bash
# Search GitHub for skill repositories
mcp-skillset discover search "python testing"

# Get trending skills this week
mcp-skillset discover trending

# Discover by GitHub topic
mcp-skillset discover topic claude-skills
```

### Manual Discovery (SkillsMP)
Browse https://skillsmp.com to discover skills, then add them:

```bash
mcp-skillset repo add https://github.com/user/skill-repo.git
```
```

## Appendix: SkillsMP Value Proposition

While API integration isn't feasible, SkillsMP provides value as:

### Discovery Platform
- **Web UI**: Easy browsing by category
- **AI Search**: Semantic search (better than GitHub keyword search)
- **Curation**: Quality filtering (2+ stars)
- **Visualization**: Category breakdowns, popularity metrics
- **One-Click Install**: marketplace.json compatibility

### Use Cases for SkillsMP
1. **Initial Discovery**: Browse categories to find interesting skills
2. **Manual Exploration**: Use web search to explore 13,000+ skills
3. **Quality Assurance**: Pre-filtered repos (2+ stars)
4. **Community**: See popular skills, interaction statistics

### Integration Point: Reference in Documentation
**Best Practice**: Document SkillsMP as a discovery tool in README

```markdown
## Skill Discovery

### Browse Skills
Visit [SkillsMP](https://skillsmp.com) to browse 13,000+ Claude skills by category.

### Add Skills from SkillsMP
1. Browse https://skillsmp.com
2. Find a skill you want
3. Copy the GitHub repository URL
4. Add to mcp-skillset:
   ```bash
   mcp-skillset repo add <github-url>
   ```
```

## License Compatibility Check

SkillsMP skills use various licenses:
- **Apache-2.0**: Compatible (permissive)
- **MIT**: Compatible (permissive)
- **GPL**: ⚠️ Check compatibility with your use case

**Recommendation**: Add license checking to GitHub discovery service.

---

**Author**: Claude Code (Engineer Agent)
**Date**: 2025-11-25
**Status**: Research Complete, Implementation Plan Ready
