# agentskills.io Specification Compatibility

**Status:** ✅ Supported (v0.8.0+)

mcp-skillset supports both native format and [agentskills.io](https://agentskills.io) specification for maximum interoperability with AI code assistants.

## Overview

The agentskills.io specification provides a standardized format for AI agent skills across different platforms (Claude, GitHub Copilot, Cursor, etc.). mcp-skillset implements **backward-compatible** support for this specification.

### Compatibility Level

- ✅ **Parsing**: Reads both mcp-skillset native and agentskills.io formats
- ✅ **Validation**: Warns about spec compliance without breaking existing skills
- ✅ **Optional Fields**: Supports license, compatibility, allowed-tools
- ✅ **Metadata Normalization**: Handles both flat and nested metadata structures

## Supported Formats

### 1. mcp-skillset Native Format (Default)

Flat YAML structure with all fields at top level:

```yaml
---
name: test-driven-development
description: Comprehensive TDD patterns and practices for all languages
category: testing
tags: [testing, tdd, best-practices]
dependencies: []
version: 1.0.0
author: mcp-skillset
---

# Test-Driven Development

Detailed skill instructions...
```

### 2. agentskills.io Specification Format

Nested metadata with spec-compliant fields:

```yaml
---
name: test-driven-development
description: Comprehensive TDD patterns and practices for all languages
license: MIT
compatibility: Requires any modern IDE
metadata:
  version: 1.0.0
  author: mcp-skillset
  tags: [testing, tdd, best-practices]
allowed-tools: Bash(pytest:*) Read Write
---

# Test-Driven Development

Detailed skill instructions...
```

### 3. Mixed Format (Also Supported)

Combination of both formats (top-level fields take precedence):

```yaml
---
name: test-driven-development
description: Comprehensive TDD patterns and practices for all languages
category: testing  # mcp-skillset extension
license: MIT  # agentskills.io spec
metadata:  # agentskills.io nested metadata
  version: 1.0.0
  tags: [testing, tdd]
allowed-tools: Bash Read Write  # agentskills.io spec
---
```

## agentskills.io Specification Fields

### Required Fields

| Field | Format | Max Length | Description |
|-------|--------|------------|-------------|
| `name` | Lowercase-hyphen | 64 chars | Skill identifier (e.g., `test-driven-development`) |
| `description` | Plain text | 1024 chars | Brief description of what the skill does |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `license` | String | SPDX license identifier (e.g., `MIT`, `Apache-2.0`) |
| `compatibility` | String (max 500 chars) | Environment requirements (e.g., `Requires Python 3.8+`) |
| `allowed-tools` | String | Space-delimited list of allowed tools (experimental) |
| `metadata` | Object | Nested metadata (version, author, tags, etc.) |

## Validation Warnings

mcp-skillset validates skills against agentskills.io specification and provides **warnings** (not errors) for non-compliance:

### Name Format Warning

```
⚠️ Name 'My Skill Name' doesn't follow agentskills.io spec format.
   Use lowercase letters, numbers, and hyphens only (e.g., 'my-skill-name')
```

**Recommended**: `my-skill-name` (lowercase-hyphen format)

### Length Limit Warnings

```
⚠️ Name too long (72 chars, agentskills.io spec recommends max 64 chars)
⚠️ Description too long (1100 chars, agentskills.io spec recommends max 1024 chars)
⚠️ Compatibility field too long (520 chars, agentskills.io spec max 500 chars)
```

**Note**: These are warnings only - skills will still work, but may not be fully portable to other platforms.

## Metadata Normalization

mcp-skillset automatically normalizes both formats to a flat structure internally:

```python
# Input: agentskills.io format with nested metadata
frontmatter = {
    "name": "test-skill",
    "description": "Test description",
    "metadata": {
        "version": "1.0.0",
        "author": "Test Author",
        "tags": ["test"]
    }
}

# After normalization (internal representation)
normalized = {
    "name": "test-skill",
    "description": "Test description",
    "version": "1.0.0",  # Flattened from metadata
    "author": "Test Author",  # Flattened from metadata
    "tags": ["test"]  # Flattened from metadata
}
```

### Normalization Rules

1. **Nested metadata flattened**: Fields inside `metadata` object moved to top level
2. **Top-level precedence**: If field exists at both levels, top-level wins
3. **String-to-list conversion**: `tags: "single-tag"` → `tags: ["single-tag"]`
4. **Backward compatible**: Existing flat format skills unchanged

## Building Spec-Compliant Skills

### Using CLI (Planned)

```bash
# Build skill with spec-compliant output
mcp-skillset build-skill \
  --name "test-driven-development" \
  --description "Comprehensive TDD patterns" \
  --spec-compliant \
  --license MIT \
  --compatibility "Requires Python 3.8+"
```

### Using Python API

```python
from mcp_skills.services.skill_builder import SkillBuilder

builder = SkillBuilder()

result = builder.build_skill(
    name="test-driven-development",
    description="Comprehensive TDD patterns and practices",
    domain="testing",
    tags=["testing", "tdd", "best-practices"],
    spec_compliant=True,  # Generate agentskills.io format
    license="MIT",
    compatibility="Requires any modern IDE",
    allowed_tools="Bash(pytest:*) Read Write",
    version="1.0.0",
    author="mcp-skillset"
)

print(result["skill_path"])
```

## Field Mappings

| mcp-skillset Native | agentskills.io Spec | Location | Notes |
|---------------------|---------------------|----------|-------|
| `name` | `name` | Top-level | Required in both |
| `description` | `description` | Top-level | Required in both |
| `category` | N/A | Top-level | mcp-skillset extension |
| `tags` | `tags` | Top-level or `metadata.tags` | Both supported |
| `version` | `version` | Top-level or `metadata.version` | Both supported |
| `author` | `author` | Top-level or `metadata.author` | Both supported |
| `dependencies` | N/A | Top-level | mcp-skillset extension |
| N/A | `license` | Top-level | agentskills.io spec |
| N/A | `compatibility` | Top-level | agentskills.io spec |
| N/A | `allowed-tools` | Top-level | agentskills.io spec (experimental) |
| N/A | `metadata` | Top-level | agentskills.io nested object |

## Best Practices

### For Maximum Portability

1. **Use lowercase-hyphen names**: `test-driven-development` (not `Test Driven Development`)
2. **Keep descriptions concise**: Under 1024 characters
3. **Add license field**: SPDX identifier (e.g., `MIT`, `Apache-2.0`)
4. **Specify compatibility**: Environment/system requirements
5. **Follow progressive disclosure**: ~100 token metadata, <5000 token body

### For mcp-skillset Projects

1. **Use native format**: Flat structure with `category`, `tags`, `dependencies` at top level
2. **Add agentskills.io fields optionally**: Include `license`, `compatibility` for cross-platform use
3. **Validate before publishing**: Run `mcp-skillset validate` to check spec compliance

## Progressive Disclosure Philosophy

Both formats support progressive disclosure:

- **Metadata (~100 tokens)**: Essential fields for skill discovery
- **Instructions (<5000 tokens)**: Full skill content loaded on activation

mcp-skillset does not enforce token limits but provides validation warnings.

## Migration Path

No migration required! Existing skills continue to work:

1. **Existing skills**: Automatically parsed and normalized
2. **New skills**: Choose native or spec-compliant format
3. **Mixed approach**: Use both formats for maximum compatibility

## Examples

### Complete agentskills.io Spec Skill

```yaml
---
name: fastapi-web-development
description: Production-grade FastAPI development with async, Pydantic validation, and testing
license: MIT
compatibility: Requires Python 3.11+, FastAPI 0.100+
metadata:
  version: 1.0.0
  author: mcp-skillset
  tags: [fastapi, python, async, web-api]
  category: web-development
allowed-tools: Bash(pip:*) Read Write
---

# FastAPI Web Development

## When to Use
- Building REST APIs with Python
- Async/await web applications
- Type-safe API development with Pydantic

## Quick Start

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

[Full skill instructions...]
```

### Complete mcp-skillset Native Skill

```yaml
---
name: fastapi-web-development
description: Production-grade FastAPI development with async, Pydantic validation, and testing
category: web-development
tags: [fastapi, python, async, web-api]
dependencies: [test-driven-development, systematic-debugging]
version: 1.0.0
author: mcp-skillset
license: MIT
---

# FastAPI Web Development

[Same content as above...]
```

## Specification References

- **Official Spec**: https://agentskills.io/specification
- **Research Doc**: `docs/research/agentskills-io-compatibility-analysis-2026-01-17.md`
- **Implementation**: `src/mcp_skills/services/validators/skill_validator.py`
- **Tests**: `tests/test_agentskills_io_compatibility.py`

## Changelog

### v0.8.0 (2026-01-17)
- ✅ Add agentskills.io specification support
- ✅ Implement backward-compatible metadata normalization
- ✅ Add validation warnings for spec compliance
- ✅ Support optional fields: license, compatibility, allowed-tools
- ✅ Full test coverage for both formats

## FAQ

**Q: Do I need to migrate existing skills?**
A: No! Existing skills continue to work without changes.

**Q: Which format should I use for new skills?**
A: Use native format for mcp-skillset-only projects. Use agentskills.io format for cross-platform skills.

**Q: Can I use both formats?**
A: Yes! Mixed format is supported. Top-level fields take precedence over nested metadata.

**Q: Are validation warnings errors?**
A: No. Warnings indicate non-compliance with agentskills.io spec but don't prevent skill usage.

**Q: How do I make my skill fully portable?**
A: Follow agentskills.io spec: lowercase-hyphen name, description <1024 chars, add license field.

---

**Related Documentation:**
- [Skill Format Specification](SKILL_FORMAT.md)
- [Building Skills](BUILD_SKILLS.md)
- [Skill Validation](VALIDATION.md)
