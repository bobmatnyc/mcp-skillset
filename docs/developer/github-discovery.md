# GitHub Repository Discovery

Automatic discovery of skill repositories on GitHub using the GitHub REST API v3.

## Overview

The GitHub Discovery service enables you to:
- **Search** for skill repositories using natural language queries
- **Browse** trending repositories by timeframe (week/month/year)
- **Filter** repositories by topic, stars, and other criteria
- **Verify** that repositories contain valid SKILL.md files
- **Get metadata** including stars, forks, license, and topics

## Installation

The discovery feature is included in mcp-skillset by default. No additional dependencies are required.

## Configuration

### GitHub Token (Optional but Recommended)

For higher rate limits (5000 requests/hour vs 60), set a GitHub personal access token:

**Method 1: Environment Variable**
```bash
export GITHUB_TOKEN=your_github_token_here
```

**Method 2: Configuration File**

Edit `~/.mcp-skillset/config.yaml`:

```yaml
github_discovery:
  enabled: true
  min_stars: 2
  github_token: ${GITHUB_TOKEN}  # Reads from environment
  topics:
    - claude-skills
    - anthropic-skills
    - mcp-skills
    - ai-skills
```

### Getting a GitHub Token

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Generate new token (classic)
3. Select scopes: `public_repo` (read-only access to public repositories)
4. Copy token and set as environment variable

**Note:** Tokens are optional. Without a token, you're limited to 60 requests/hour.

## CLI Commands

### Search Repositories

Search for skill repositories using natural language queries:

```bash
# Basic search
mcp-skillset discover search "python testing"

# With minimum stars filter
mcp-skillset discover search "fastapi" --min-stars 10

# Limit results
mcp-skillset discover search "react typescript" --limit 20
```

**Output:**
```
Found 5 Repositories
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┓
┃ Repository       ┃ Description       ┃ Stars ┃ Updated  ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━┩
│ user/repo        │ Python testing... │   45  │ 5d ago   │
└──────────────────┴───────────────────┴───────┴──────────┘
```

### Browse Trending Repositories

Get recently updated skill repositories:

```bash
# Weekly trending (default)
mcp-skillset discover trending

# Monthly trending
mcp-skillset discover trending --timeframe month

# Filter by topic
mcp-skillset discover trending --topic claude-skills

# Limit results
mcp-skillset discover trending --limit 20
```

### Search by Topic

Find repositories tagged with specific GitHub topics:

```bash
# Search by topic
mcp-skillset discover topic claude-skills

# With stars filter
mcp-skillset discover topic mcp-skills --min-stars 5
```

**Common Topics:**
- `claude-skills` - Skills for Claude AI assistant
- `anthropic-skills` - Anthropic-related skills
- `mcp-skills` - Model Context Protocol skills
- `ai-skills` - General AI assistant skills

### Verify Repository

Check if a repository contains SKILL.md files:

```bash
mcp-skillset discover verify https://github.com/anthropics/skills.git
```

**Output:**
```
✓ Repository contains SKILL.md files

Repository Metadata:
  • Name: anthropics/skills
  • Description: Claude AI skills repository
  • Stars: 150
  • Forks: 20
  • License: Apache-2.0
  • Topics: claude-skills, python, mcp

Add this repository:
  mcp-skillset repo add https://github.com/anthropics/skills.git
```

### Check Rate Limits

View your current GitHub API rate limit status:

```bash
mcp-skillset discover limits
```

**Output:**
```
GitHub API Rate Limits

✓ Authenticated (5000 requests/hour)

Rate Limit Status
┏━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┓
┃ Resource  ┃ Remaining┃ Limit ┃ Resets   ┃
┡━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━┩
│ Core API  │   4950   │  5000 │ 14:30:00 │
│ Search API│    28    │    30 │ 14:15:00 │
└───────────┴──────────┴───────┴──────────┘
```

## Python API

Use the GitHub discovery service programmatically:

```python
from mcp_skills.services.github_discovery import GitHubDiscovery

# Initialize (with optional token)
discovery = GitHubDiscovery(github_token="your_token_here")

# Search repositories
repos = discovery.search_repos("python testing", min_stars=5)
for repo in repos:
    print(f"{repo.full_name}: {repo.stars} stars")

# Get trending repositories
trending = discovery.get_trending(timeframe="week")

# Search by topic
claude_repos = discovery.search_by_topic("claude-skills")

# Verify repository
is_valid = discovery.verify_skill_repo(
    "https://github.com/anthropics/skills.git"
)

# Get detailed metadata
metadata = discovery.get_repo_metadata(
    "https://github.com/anthropics/skills.git"
)

# Check rate limits
status = discovery.get_rate_limit_status()
print(f"Remaining: {status['search_remaining']}/{status['search_limit']}")
```

## Workflow: Discover and Add Repositories

### 1. Search for Relevant Skills

```bash
# Find Python testing repositories
mcp-skillset discover search "python testing" --min-stars 5
```

### 2. Verify Repository Quality

```bash
# Check if repository has SKILL.md files
mcp-skillset discover verify https://github.com/user/repo.git
```

### 3. Add to Your Configuration

```bash
# Add discovered repository
mcp-skillset repo add https://github.com/user/repo.git --priority 80
```

### 4. Index New Skills

```bash
# Rebuild index to include new skills
mcp-skillset index --force
```

### 5. Verify Installation

```bash
# Check new skills are available
mcp-skillset list
```

## Rate Limiting

### Limits by Authentication

| Authentication | Core API | Search API |
|---------------|----------|------------|
| Unauthenticated | 60/hour | 10/hour |
| Authenticated (Token) | 5000/hour | 30/hour |

### Best Practices

1. **Use a GitHub Token**: Dramatically increases rate limits
2. **Cache Results**: Responses are cached for 1 hour automatically
3. **Monitor Limits**: Use `mcp-skillset discover limits` to check status
4. **Batch Operations**: Combine multiple searches when possible

### Handling Rate Limit Exceeded

If you exceed the rate limit:

1. **Wait**: Rate limits reset hourly (check reset time with `discover limits`)
2. **Add Token**: Set `GITHUB_TOKEN` environment variable
3. **Use Cache**: Cached results don't count against rate limits

## Error Handling

### Common Errors

**Network Errors**
```bash
# Error: Network unreachable
# Solution: Check internet connection, retry
```

**Rate Limit Exceeded**
```bash
# Error: GitHub API rate limit exceeded
# Solution: Wait for reset time or add GitHub token
```

**Invalid Repository URL**
```bash
# Error: Invalid git URL
# Solution: Use HTTPS format: https://github.com/owner/repo.git
```

**No SKILL.md Files Found**
```bash
# Error: Repository verification failed
# Solution: Repository doesn't contain SKILL.md files
```

## Caching

### Automatic Caching

All API responses are automatically cached for 1 hour:
- **Location**: `~/.mcp-skillset/cache/`
- **TTL**: 3600 seconds (1 hour)
- **Storage**: In-memory (cleared on restart)

### Benefits

- Faster repeated searches
- Reduced API calls
- No rate limit impact for cached results

### Cache Invalidation

Cache entries expire automatically after 1 hour. To force fresh results:
- Wait for cache expiration
- Restart `mcp-skillset` command

## Advanced Usage

### Custom Search Filters

Combine multiple filters for precise results:

```bash
# High-quality, recently updated Python repos
mcp-skillset discover search "python" --min-stars 50 | \
  mcp-skillset discover trending --timeframe week
```

### Batch Repository Addition

Discover and add multiple repositories:

```bash
# Search and review
mcp-skillset discover topic claude-skills --limit 20

# Add selected repositories
for url in $(cat repos.txt); do
    mcp-skillset repo add "$url" --priority 80
done

# Reindex all at once
mcp-skillset index --force
```

### Integration with CI/CD

Automatically discover new skills in CI pipelines:

```yaml
# .github/workflows/discover-skills.yml
name: Discover New Skills
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  discover:
    runs-on: ubuntu-latest
    steps:
      - name: Discover trending skills
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          mcp-skillset discover trending --timeframe week > trending.txt
          # Review and add selected repositories
```

## Troubleshooting

### Discovery Commands Not Found

**Problem:** `mcp-skillset discover` command not recognized

**Solution:**
```bash
# Reinstall mcp-skillset
pip install --upgrade mcp-skillset

# Verify installation
mcp-skillset --version
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'mcp_skills'`

**Solution:**
```bash
# Install in development mode
pip install -e .

# Or install from PyPI
pip install mcp-skillset
```

### Rate Limit Issues

**Problem:** Constantly hitting rate limits

**Solution:**
```bash
# Add GitHub token for higher limits
export GITHUB_TOKEN=your_token_here

# Verify authentication
mcp-skillset discover limits
```

### No Results Found

**Problem:** Search returns no repositories

**Solutions:**
1. Lower `--min-stars` threshold
2. Use broader search terms
3. Check rate limits: `mcp-skillset discover limits`
4. Try different topics: `claude-skills`, `mcp-skills`, `ai-skills`

## Examples

### Example 1: Find FastAPI Skills

```bash
# Search for FastAPI-related skills
mcp-skillset discover search "fastapi web development" --min-stars 10

# Verify promising repository
mcp-skillset discover verify https://github.com/user/fastapi-skills.git

# Add if valid
mcp-skillset repo add https://github.com/user/fastapi-skills.git --priority 85

# Index new skills
mcp-skillset index
```

### Example 2: Weekly Trending Review

```bash
# Get weekly trending repos
mcp-skillset discover trending --timeframe week --limit 20

# Filter by Claude-specific skills
mcp-skillset discover topic claude-skills

# Check rate limit status
mcp-skillset discover limits
```

### Example 3: Comprehensive Search

```bash
# Search multiple topics
for topic in claude-skills mcp-skills anthropic-skills; do
    echo "=== Topic: $topic ==="
    mcp-skillset discover topic "$topic" --min-stars 5
    echo
done
```

## Performance Considerations

### Search Performance

- **Cold Search**: 500-1000ms (API call + verification)
- **Cached Search**: <10ms (served from cache)
- **Verification**: 200-400ms per repository

### Optimization Tips

1. **Use Caching**: Repeated searches are instant
2. **Batch Searches**: Combine related queries
3. **Lower Precision**: Use `--min-stars 2` for more results
4. **Limit Results**: Use `--limit 10` to reduce API calls

## Security Considerations

### GitHub Token Security

**Do:**
- Store tokens in environment variables
- Use read-only tokens (no write permissions needed)
- Rotate tokens regularly
- Use GitHub token secrets in CI/CD

**Don't:**
- Commit tokens to version control
- Share tokens in plaintext
- Use tokens with write access
- Hardcode tokens in scripts

### Repository Verification

All discovered repositories are verified for SKILL.md files before recommendation, but:

- Review repository content before adding
- Check license compatibility
- Verify repository authenticity
- Audit code for security issues

## See Also

- [Repository Management](./REPOSITORY_MANAGEMENT.md)
- [Skills Search](./SKILLS_SEARCH.md)
- [Configuration Guide](./CONFIGURATION.md)
- [GitHub REST API Documentation](https://docs.github.com/en/rest)

## Contributing

Have ideas for improving GitHub discovery?

1. Open an issue: [GitHub Issues](https://github.com/bobmatnyc/mcp-skillset/issues)
2. Submit a pull request
3. Join discussions in the community

## Support

- **Documentation**: [mcp-skillset docs](https://github.com/bobmatnyc/mcp-skillset)
- **Issues**: [GitHub Issues](https://github.com/bobmatnyc/mcp-skillset/issues)
- **Community**: [Discussions](https://github.com/bobmatnyc/mcp-skillset/discussions)
