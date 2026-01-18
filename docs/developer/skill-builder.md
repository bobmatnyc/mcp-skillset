# SkillBuilder Service Usage Guide

## Overview

The **SkillBuilder** service enables programmatic creation of progressive skills for Claude Code. It provides template-based skill generation with validation, security scanning, and deployment capabilities.

## Key Features

- ✅ **Template-Based Generation**: Use Jinja2 templates for consistent skill structure
- ✅ **Multiple Templates**: Base, Web Development, API Development, and Testing templates
- ✅ **Validation**: YAML frontmatter and content validation
- ✅ **Security Scanning**: Detect hardcoded credentials and dangerous patterns
- ✅ **Progressive Disclosure**: Enforce size limits (<100 tokens frontmatter, <5k tokens body)
- ✅ **Deployment**: Auto-deploy to `~/.claude/skills/`

## Quick Start

### Basic Usage

```python
from mcp_skills.services import SkillBuilder

# Create SkillBuilder instance
builder = SkillBuilder()

# Build a skill
result = builder.build_skill(
    name="FastAPI Testing",
    description="Test FastAPI endpoints with pytest and httpx",
    domain="web development",
    tags=["fastapi", "pytest", "testing"],
    deploy=True  # Deploy to ~/.claude/skills/
)

print(f"Status: {result['status']}")
print(f"Skill ID: {result['skill_id']}")
print(f"Path: {result['skill_path']}")
```

### Using Templates

```python
# Use web-development template
result = builder.build_skill(
    name="React Component Development",
    description="Build React components with TypeScript and hooks",
    domain="web development",
    tags=["react", "typescript", "hooks"],
    template="web-development",  # Specify template
    toolchain=["Node.js 18+", "React 18+", "TypeScript 5+"],
    frameworks=["React", "TypeScript"],
)
```

### Available Templates

```python
# List all available templates
templates = builder.list_templates()
print(templates)
# Output: ['base', 'web-development', 'api-development', 'testing']
```

## Template Reference

### 1. Base Template (`base`)

General-purpose template for any domain. Includes:
- Core principles and best practices
- Common patterns and anti-patterns
- Testing and debugging guidance
- Related skills references

**Best For**: Generic skills, custom domains, educational content

### 2. Web Development Template (`web-development`)

Specialized for modern web development. Includes:
- Component-based architecture
- API-first design
- Frontend and backend best practices
- Performance optimization
- Security checklist

**Best For**: React, Vue, Angular, FastAPI, Express.js, web frameworks

### 3. API Development Template (`api-development`)

Focused on API design and implementation. Includes:
- REST API conventions
- Request/response patterns
- Authentication & authorization
- Rate limiting and pagination
- API documentation

**Best For**: REST APIs, GraphQL, gRPC, API design

### 4. Testing Template (`testing`)

Comprehensive testing guidance. Includes:
- Test-Driven Development (TDD)
- Test pyramid strategy
- Unit, integration, and E2E testing
- Test independence and fixtures
- Coverage guidelines

**Best For**: pytest, Jest, Vitest, Playwright, testing frameworks

## Configuration Options

### Required Parameters

- `name` (str): Skill display name
- `description` (str): Activation trigger and usage context (min 20 chars)
- `domain` (str): Technology domain

### Optional Parameters

- `tags` (list[str]): Tags for discovery
- `template` (str): Template name (default: "base")
- `version` (str): Semantic version (default: "1.0.0")
- `category` (str): Skill category (default: domain.title())
- `toolchain` (list[str]): Required tools and versions
- `frameworks` (list[str]): Primary frameworks
- `related_skills` (list[str]): Related skill names
- `author` (str): Skill author (default: "mcp-skillset")
- `license` (str): License identifier (default: "MIT")
- `deploy` (bool): Auto-deploy to ~/.claude/skills/ (default: True)

## Validation

### Automatic Validation

The SkillBuilder automatically validates:

1. **YAML Frontmatter**
   - Valid YAML syntax
   - Required fields present (name, description)
   - Description length (min 20 chars)

2. **Size Limits**
   - Frontmatter: <400 chars (~100 tokens)
   - Body: <20,000 chars (~5,000 tokens)

3. **Security Patterns**
   - No hardcoded credentials
   - No dangerous code execution patterns (`exec`, `eval`)
   - No dynamic imports

### Manual Validation

```python
# Validate skill content
skill_content = """---
name: test-skill
description: Test skill for validation
---
# Content
"""

result = builder.validate_skill(skill_content)

print(f"Valid: {result.valid}")
print(f"Errors: {result.errors}")
print(f"Warnings: {result.warnings}")
```

### Validation Result

```python
{
    "valid": True/False,
    "errors": [
        "Critical errors that prevent deployment"
    ],
    "warnings": [
        "Non-critical issues for improvement"
    ]
}
```

## Deployment

### Automatic Deployment

```python
# Deploy during build
result = builder.build_skill(
    name="My Skill",
    description="Skill description here",
    domain="testing",
    deploy=True  # Default
)

# Skill deployed to: ~/.claude/skills/my-skill/SKILL.md
```

### Manual Deployment

```python
# Generate without deploying
result = builder.build_skill(
    name="My Skill",
    description="Skill description here",
    domain="testing",
    deploy=False  # Don't deploy
)

# Deploy later
skill_content = """..."""
skill_path = builder.deploy_skill(skill_content, "my-skill")
print(f"Deployed to: {skill_path}")
```

### Deployment Location

Skills are deployed to:
```
~/.claude/skills/
└── skill-name/
    └── SKILL.md
```

## Error Handling

### Build Errors

```python
result = builder.build_skill(
    name="Bad Skill",
    description="too short",  # Too short
    domain="testing"
)

if result['status'] == 'error':
    print(f"Error: {result['message']}")
    print(f"Errors: {result.get('errors', [])}")
```

### Common Errors

1. **Validation Errors**
   - Missing required fields
   - Description too short
   - Body too large
   - Security violations

2. **Template Errors**
   - Template not found (falls back to base)
   - Invalid template syntax

3. **Deployment Errors**
   - Permission issues
   - File system errors

## Advanced Usage

### Custom Template Variables

```python
result = builder.build_skill(
    name="Custom Skill",
    description="Skill with custom variables",
    domain="testing",
    # Custom variables passed to template
    custom_section="Additional content",
    special_config={"key": "value"},
)
```

### Programmatic Skill Generation

```python
# Generate skills from configuration
skills_config = [
    {
        "name": "PostgreSQL Optimization",
        "description": "Optimize PostgreSQL queries",
        "domain": "database",
        "tags": ["postgresql", "optimization"],
    },
    {
        "name": "Docker Containerization",
        "description": "Build and deploy Docker containers",
        "domain": "infrastructure",
        "tags": ["docker", "containers"],
    },
]

for config in skills_config:
    result = builder.build_skill(**config)
    print(f"Created: {result['skill_id']}")
```

### Integration with SkillManager

```python
from mcp_skills.services import SkillBuilder, SkillManager

# Build skill
builder = SkillBuilder()
result = builder.build_skill(
    name="My Skill",
    description="Skill description",
    domain="testing",
    deploy=True
)

# Load with SkillManager
manager = SkillManager()
skill = manager.load_skill(result['skill_id'])
print(f"Loaded: {skill.name}")
```

## Best Practices

### 1. Write Clear Descriptions

The `description` field determines when Claude activates the skill. Make it specific:

✅ **Good**: "Test FastAPI endpoints with pytest, httpx, and async support"
❌ **Bad**: "Testing skill"

### 2. Use Appropriate Templates

Choose the template that matches your skill domain:

- **base**: Generic or custom domains
- **web-development**: Web apps, frontend, backend
- **api-development**: REST, GraphQL, API design
- **testing**: Testing frameworks and strategies

### 3. Provide Comprehensive Tags

Tags improve discoverability. Include:

- Technology names (e.g., "fastapi", "react")
- Domain keywords (e.g., "testing", "optimization")
- Use cases (e.g., "async", "authentication")

### 4. Specify Toolchain

List required tools with versions:

```python
toolchain=["Python 3.11+", "FastAPI 0.100+", "pytest 7+"]
```

### 5. Link Related Skills

Help users discover complementary skills:

```python
related_skills=["api-development", "testing", "deployment"]
```

## Example Workflows

### Create FastAPI Testing Skill

```python
result = builder.build_skill(
    name="FastAPI Testing",
    description="Test FastAPI endpoints with pytest, httpx, and async support for modern Python web applications",
    domain="web development",
    tags=["fastapi", "pytest", "testing", "async", "httpx"],
    version="1.0.0",
    category="Web Development",
    toolchain=["Python 3.11+", "FastAPI 0.100+", "pytest 7+", "httpx"],
    frameworks=["FastAPI", "pytest"],
    related_skills=["api-development", "testing", "async-programming"],
    template="web-development",
    deploy=True,
)
```

### Create GraphQL API Skill

```python
result = builder.build_skill(
    name="GraphQL API Design",
    description="Design and implement GraphQL APIs with schema-first approach, resolvers, and Apollo Server",
    domain="api development",
    tags=["graphql", "api", "apollo", "schema", "resolvers"],
    version="1.0.0",
    category="API Development",
    toolchain=["Node.js 18+", "Apollo Server 4", "GraphQL 16+"],
    frameworks=["Apollo Server", "GraphQL"],
    related_skills=["web-development", "testing", "database-optimization"],
    template="api-development",
    deploy=True,
)
```

### Create Playwright E2E Testing Skill

```python
result = builder.build_skill(
    name="Playwright E2E Testing",
    description="End-to-end testing with Playwright for web applications including page objects and fixtures",
    domain="testing",
    tags=["playwright", "e2e", "testing", "automation", "typescript"],
    version="1.0.0",
    category="Testing",
    toolchain=["Node.js 18+", "Playwright 1.40+", "TypeScript 5+"],
    frameworks=["Playwright", "TypeScript"],
    related_skills=["web-development", "testing", "debugging"],
    template="testing",
    deploy=True,
)
```

## Troubleshooting

### Skill Not Activating in Claude Code

1. Verify skill deployed to `~/.claude/skills/skill-name/SKILL.md`
2. Check YAML frontmatter is valid
3. Ensure description includes activation triggers
4. Restart Claude Code to reload skills

### Validation Failures

1. Check error messages in result
2. Verify description is >20 characters
3. Ensure no hardcoded credentials
4. Check body size is <20k characters

### Template Not Found

If template doesn't exist, SkillBuilder falls back to base template. Check available templates:

```python
templates = builder.list_templates()
print(templates)
```

## Next Steps

1. **Explore Examples**: Run `examples/skill_builder_demo.py`
2. **Run Tests**: `pytest tests/services/test_skill_builder.py`
3. **Create Custom Templates**: Add to `src/mcp_skills/templates/skills/`
4. **Integrate with CLI**: Add commands to `src/mcp_skills/cli/`
5. **Create MCP Tool**: Expose via MCP server for agent use

## References

- [Progressive Skills Format Specification](../research/progressive-skills-format-2025-11-29.md)
- [Skill Templates](../skill-templates/README.md)
- [Claude Code Skills Documentation](https://github.com/anthropics/skills)
