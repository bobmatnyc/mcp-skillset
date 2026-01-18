# Deployment & Release Guide

**Last Updated**: 2025-11-25
**Current Version**: v0.5.1
**Package**: mcp-skillset

---

## Overview

This guide documents the complete automated release workflow for mcp-skillset, orchestrated by Claude MPM with multi-agent coordination. The process ensures quality, security, and consistency across all distribution channels (PyPI and Homebrew).

**Release Workflow**:
1. Pre-release validation (Research Agent)
2. Documentation updates (Documentation Agent)
3. Quality assurance testing (QA Agent)
4. Security scanning (Security Agent)
5. Version bump and build
6. Publish to PyPI (automated)
7. Update Homebrew tap (automated)
8. Post-release verification

**Key Features**:
- ✅ **Fully Automated**: PyPI and Homebrew updates with stored credentials
- ✅ **Multi-Agent**: PM orchestrates specialized agents for each phase
- ✅ **Quality Gates**: Testing and security validation before release
- ✅ **Rollback Ready**: Documented procedures for issues
- ✅ **Consolidated Tap**: Single `homebrew-tools` tap for all tools

---

## Prerequisites

### Required Tools

1. **Python Development**:
   ```bash
   # Python 3.11+ (matches project requirements)
   python --version  # Should be 3.11 or higher

   # Recommended: Install uv for fastest development
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Or: pip install uv

   # Build and publishing tools (uv handles these internally)
   # If not using uv: pip install --upgrade build twine
   ```

2. **Git & GitHub**:
   ```bash
   # Verify git configuration
   git config user.name
   git config user.email

   # Install GitHub CLI (for releases)
   brew install gh
   gh auth login
   ```

3. **Homebrew** (for formula testing):
   ```bash
   # macOS: Should be installed
   brew --version

   # Linux: Install if needed
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

### Required Access

1. **PyPI Account & Token**:
   - Account: https://pypi.org/account/register/
   - Create API token: https://pypi.org/manage/account/token/
   - Scope: "Project: mcp-skillset" (or "Entire account" before first upload)

2. **GitHub Access**:
   - Write access to `bobmatnyc/mcp-skillset` repository
   - Write access to `bobmatnyc/homebrew-tools` repository
   - Personal access token with `repo` scope

3. **Local Repositories**:
   ```bash
   # Main project
   cd ~/Projects/mcp-skillset

   # Homebrew tap (for manual updates)
   cd ~/Projects/homebrew-tools
   ```

---

## PyPI Credentials Setup

### One-Time Configuration

The PyPI authentication is configured once and used for all future releases.

**Step 1: Store Token in .env.local**

Create or edit `.env.local` in the project root:

```bash
# .env.local (never commit this file!)
PYPI_API_TOKEN=pypi-AgEIcHlwaS5vcmcC...your-actual-token...
```

**Important**: The `.env.local` file is gitignored and should NEVER be committed.

**Step 2: Configure ~/.pypirc**

Create or update `~/.pypirc` with your token:

```bash
# Option A: Manual creation
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...your-actual-token...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...your-testpypi-token...
EOF

# Set secure permissions
chmod 600 ~/.pypirc
```

```bash
# Option B: Using environment variable from .env.local
# Load token from .env.local and create ~/.pypirc
source .env.local && cat > ~/.pypirc << EOF
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = $PYPI_API_TOKEN

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-testpypi-token-here
EOF

chmod 600 ~/.pypirc
```

**Step 3: Verify Configuration**

```bash
# Test that twine can authenticate (dry run)
twine check dist/* 2>/dev/null || echo "No dist files yet (that's OK)"

# Verify .pypirc permissions
ls -l ~/.pypirc
# Should show: -rw-------  (600 permissions)
```

**Security Notes**:
- ✅ `.env.local` is gitignored (never committed)
- ✅ `~/.pypirc` has 600 permissions (owner read/write only)
- ✅ Tokens are project-scoped (limits damage if leaked)
- ⚠️ Rotate tokens periodically (every 6-12 months)
- ⚠️ NEVER commit tokens to version control

**Future Uploads**: Once configured, all future releases automatically use these credentials:
```bash
twine upload dist/*  # No password prompt!
```

---

## Release Workflow

### Phase 1: Pre-Release Validation

**Agent**: Research Agent
**Purpose**: Ensure project state is ready for release

**Tasks**:
1. **Dependency Check**: Verify all dependencies are up-to-date
2. **CLI Standards Validation**: Check CLI follows best practices
3. **Breaking Changes Review**: Identify any breaking changes since last release
4. **Documentation Completeness**: Verify all new features are documented

**Research Agent Actions**:
```bash
# Run automated checks
mcp-skillset health  # Verify system health
make lint            # Code style validation
make type            # Type checking
make test            # Run test suite
```

**Expected Output**:
- Research report with findings
- GO/NO-GO recommendation
- List of items to address before release

**Example** (v0.5.1):
```
✅ All tests passing (85%+ coverage)
✅ No dependency conflicts
✅ CLI follows standards
⚠️ Update CHANGELOG.md with v0.5.1 notes
```

---

### Phase 2: Documentation Updates

**Agent**: Documentation Agent
**Purpose**: Prepare user-facing documentation for release

**Tasks**:
1. **CHANGELOG.md**: Add release notes for new version
2. **README.md**: Update badges, version references, installation instructions
3. **Version References**: Update any hardcoded version strings in docs

**Documentation Agent Actions**:
- Review commits since last release
- Categorize changes (Added, Changed, Fixed, Deprecated, Removed, Security)
- Write user-friendly release notes
- Update version badges and links

**CHANGELOG.md Format** (Keep a Changelog style):
```markdown
## [0.5.1] - 2025-11-25

### Added
- New feature descriptions

### Changed
- Modifications to existing features

### Fixed
- Bug fixes and corrections

### Security
- Security improvements
```

**Example** (v0.5.1):
```markdown
## [0.5.1] - 2025-11-25

### Fixed
- Updated installation instructions to use consolidated homebrew-tools tap
- Corrected Homebrew installation command from individual taps to unified tap

### Changed
- Simplified Homebrew installation: `brew tap bobmatnyc/tools && brew install mcp-skillset`
- Consolidated all tools (claude-mpm, mcp-vector-search, mcp-ticketer, mcp-skillset, ai-trackdown-pytools) into single tap
```

---

### Phase 3: Quality Gate

**Agent**: QA Agent
**Purpose**: Comprehensive testing before release

**Test Suites**:
1. **Unit Tests**: `make test` (85%+ coverage required)
2. **Integration Tests**: MCP server functionality
3. **End-to-End Tests**: Complete workflow validation
4. **CLI Tests**: All commands and options
5. **Installation Tests**: Fresh install verification

**QA Agent Actions**:
```bash
# Run full quality checks
make quality

# Individual checks
make lint        # Linting (ruff, mypy)
make type        # Type checking
make test        # Unit tests
make test-cov    # Coverage report

# CLI command testing
mcp-skillset --version
mcp-skillset health
mcp-skillset config
mcp-skillset setup --dry-run
```

**Quality Gates** (All must pass):
- ✅ All tests passing
- ✅ 85%+ test coverage
- ✅ No linting errors
- ✅ Type checking passes
- ✅ CLI commands functional
- ✅ MCP server starts successfully

**Example QA Report** (v0.5.1):
```
✅ Unit Tests: 127/127 passing (87% coverage)
✅ Integration Tests: 15/15 passing
✅ E2E Tests: 8/8 passing
✅ CLI Tests: All 11 commands functional
✅ Claude CLI Integration: Manual testing passed
✅ Linting: Clean (ruff, mypy)
✅ Type Checking: No errors
```

**Claude CLI Integration Testing**:
- Test installation via CLI (`claude mcp add`)
- Verify `claude mcp list` shows mcp-skillset after setup
- Test force reinstall (`--force` flag)
- Test dry-run mode (`--dry-run` flag)
- Verify backward compatibility with JSON config for other agents

---

### Phase 4: Security Scan

**Agent**: Security Agent
**Purpose**: Validate security before public release

**Security Checks**:
1. **Dependency Vulnerabilities**: Check for known CVEs
2. **Secret Scanning**: Ensure no credentials in code
3. **Input Validation**: Verify all user inputs sanitized
4. **Prompt Injection**: Test security validator with threat patterns
5. **File Permissions**: Check sensitive file permissions

**Security Agent Actions**:
```bash
# Dependency security scan
pip install safety
safety check --json

# Git secret scanning
git secrets --scan

# Security test suite
pytest tests/security/ -v

# Manual checks
grep -r "api_key\|password\|secret" . --exclude-dir=.git --exclude-dir=venv
```

**Security Gates** (All must pass):
- ✅ No critical vulnerabilities in dependencies
- ✅ No secrets in code or git history
- ✅ Security tests passing (29/29 for v0.5.0)
- ✅ Prompt injection detection working
- ✅ Content sanitization functional

**Example Security Report** (v0.5.1):
```
✅ Dependencies: No known vulnerabilities
✅ Secret Scanning: Clean
✅ Security Tests: 29/29 passing
✅ Prompt Injection: All threat levels detected correctly
✅ Trust Levels: TRUSTED/VERIFIED/UNTRUSTED working as expected
```

---

### Phase 5: Commit & Build

**Agent**: PM (orchestrates)
**Purpose**: Version bump, git commit, and build distributions

**Step 5.1: Version Bump**

Update version in these files:
- `pyproject.toml` → `version = "0.5.1"`
- `VERSION` → `0.5.1`
- `src/mcp_skills/VERSION` → `0.5.1`

```bash
# PM coordinates version updates across all files
# Example for v0.5.1:
# 1. Update pyproject.toml
# 2. Update VERSION files
# 3. Verify consistency
```

**Step 5.2: Git Commit**

```bash
# Stage version changes
git add pyproject.toml VERSION src/mcp_skills/VERSION

# Create version bump commit
git commit -m "chore: bump version to 0.5.1"

# Create git tag
git tag -a v0.5.1 -m "Release version 0.5.1"

# Push commit and tag
git push origin main
git push origin v0.5.1
```

**Example Commits** (v0.5.1):
```
ab1ab44 chore: bump version to 0.5.1
b40ef9c fix: update pyproject.toml version to 0.5.1
```

**Step 5.3: Build Distributions**

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build

# Verify build contents
ls -lh dist/
# Expected:
# mcp_skillset-0.5.1-py3-none-any.whl
# mcp_skillset-0.5.1.tar.gz
```

**Step 5.4: Verify Build Quality**

```bash
# Check distributions with twine
twine check dist/*

# Expected output:
# Checking dist/mcp_skillset-0.5.1-py3-none-any.whl: PASSED
# Checking dist/mcp_skillset-0.5.1.tar.gz: PASSED
```

---

### Phase 6: Publish to PyPI

**Agent**: PM (automated)
**Purpose**: Upload distributions to PyPI

**Authentication**: Uses `~/.pypirc` (configured in setup phase)

**Upload Process**:

```bash
# Upload to PyPI (no password prompt with ~/.pypirc)
twine upload dist/*

# Expected output:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading mcp_skillset-0.5.1-py3-none-any.whl
# 100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 50.0/50.0 kB • 00:00
# Uploading mcp_skillset-0.5.1.tar.gz
# 100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.0/45.0 kB • 00:00
# View at: https://pypi.org/project/mcp-skillset/0.5.1/
```

**Verification**:

```bash
# Verify package is live on PyPI
curl -s https://pypi.org/pypi/mcp-skillset/0.5.1/json | python3 -c "import sys, json; print(json.load(sys.stdin)['info']['version'])"
# Expected: 0.5.1

# Get SHA256 for Homebrew formula
curl -s https://pypi.org/pypi/mcp-skillset/0.5.1/json | python3 -c "import sys, json; data = json.load(sys.stdin); print([u['digests']['sha256'] for u in data['urls'] if u['packagetype'] == 'sdist'][0])"
# Expected for v0.5.1: de320ea9b26de2f9aff530f4b1b9dafefc5daf915229a7b7da970928eea90c94
```

**PyPI Page**: https://pypi.org/project/mcp-skillset/0.5.1/

**What Happens**:
- ✅ Package uploaded to PyPI
- ✅ README.md rendered on package page
- ✅ Badges and links displayed
- ✅ Available for `pip install mcp-skillset`

**Example** (v0.5.1):
```
✅ Published: https://pypi.org/project/mcp-skillset/0.5.1/
✅ SHA256: de320ea9b26de2f9aff530f4b1b9dafefc5daf915229a7b7da970928eea90c94
✅ Installation: pip install mcp-skillset==0.5.1
```

---

### Phase 7: Update Homebrew Tap

**Agent**: PM (automated)
**Purpose**: Update consolidated homebrew-tools tap with new version

**Consolidated Tap**: `bobmatnyc/homebrew-tools`

All tools use a single consolidated tap:
- `claude-mpm` (v4.26.1)
- `mcp-vector-search` (v0.12.8)
- `mcp-ticketer` (v1.2.10)
- `mcp-skillset` (v0.5.1)
- `ai-trackdown-pytools` (v0.1.0)

**Repository**: https://github.com/bobmatnyc/homebrew-tools

**Formula Location**: `Formula/mcp-skillset.rb`

**Update Process**:

```bash
# Navigate to homebrew-tools repository
cd ~/Projects/homebrew-tools

# Pull latest changes
git pull origin main

# Update mcp-skillset.rb with new version and SHA256
# (Usually automated, but can be done manually)

# Formula content:
cat > Formula/mcp-skillset.rb << 'EOF'
class McpSkillset < Formula
  include Language::Python::Virtualenv

  desc "Dynamic RAG-powered skills for code assistants via Model Context Protocol"
  homepage "https://github.com/bobmatnyc/mcp-skillset"
  url "https://files.pythonhosted.org/packages/source/m/mcp-skillset/mcp_skillset-0.5.1.tar.gz"
  sha256 "de320ea9b26de2f9aff530f4b1b9dafefc5daf915229a7b7da970928eea90c94"
  license "MIT"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/mcp-skillset --version")
  end
end
EOF

# Test formula locally
brew install --build-from-source ./Formula/mcp-skillset.rb
brew test mcp-skillset
brew audit --strict ./Formula/mcp-skillset.rb

# Commit and push
git add Formula/mcp-skillset.rb
git commit -m "feat: update mcp-skillset to v0.5.1"
git push origin main
```

**Installation After Update**:

```bash
# Users can install/upgrade with:
brew tap bobmatnyc/tools
brew install mcp-skillset

# Or upgrade existing installation:
brew upgrade mcp-skillset
```

**Verification**:

```bash
# Test installation from tap
brew uninstall mcp-skillset 2>/dev/null || true
brew install bobmatnyc/tools/mcp-skillset
mcp-skillset --version
# Expected: 0.5.1
```

**Example** (v0.5.1):
```
✅ Formula updated in homebrew-tools
✅ Committed: cb3cbe2 feat: update mcp-skillset to v0.5.1
✅ Installation: brew tap bobmatnyc/tools && brew install mcp-skillset
```

---

### Phase 8: Post-Release Verification

**Agent**: PM + QA Agent
**Purpose**: Verify release across all channels

**Verification Checklist**:

**1. PyPI Installation**:
```bash
# Create clean virtual environment
python -m venv test-release-env
source test-release-env/bin/activate

# Install from PyPI
pip install mcp-skillset==0.5.1

# Verify installation
mcp-skillset --version  # Should show 0.5.1
mcp-skillset health     # Should pass
mcp-skillset config     # Should show config

# Clean up
deactivate
rm -rf test-release-env
```

**2. Homebrew Installation**:
```bash
# Uninstall if present
brew uninstall mcp-skillset 2>/dev/null || true

# Install from tap
brew tap bobmatnyc/tools
brew install mcp-skillset

# Verify installation
mcp-skillset --version  # Should show 0.5.1
mcp-skillset health     # Should pass

# Verify formula
brew info mcp-skillset
```

**3. GitHub Release**:
```bash
# Create GitHub release
gh release create v0.5.1 \
  --title "v0.5.1 - Homebrew Consolidation" \
  --notes "$(cat CHANGELOG.md | sed -n '/## \[0.5.1\]/,/## \[0.5.0\]/p' | head -n -1)" \
  dist/*

# Verify release
gh release view v0.5.1
```

**4. Documentation Pages**:
- ✅ PyPI page renders correctly: https://pypi.org/project/mcp-skillset/0.5.1/
- ✅ GitHub release created: https://github.com/bobmatnyc/mcp-skillset/releases/tag/v0.5.1
- ✅ README badges updated
- ✅ CHANGELOG.md includes v0.5.1

**5. Functional Testing**:
```bash
# Test key features with fresh install
mcp-skillset setup --dry-run
mcp-skillset search "python testing"
mcp-skillset info python-testing
mcp-skillset demo
```

**Expected Results**:
- ✅ PyPI: Package installable and functional
- ✅ Homebrew: Formula installs correctly
- ✅ GitHub: Release created with artifacts
- ✅ Docs: All pages updated and accessible
- ✅ CLI: All commands working

**Example Verification Report** (v0.5.1):
```
✅ PyPI Installation: Success (0.5.1)
✅ Homebrew Installation: Success (0.5.1)
✅ GitHub Release: Created https://github.com/bobmatnyc/mcp-skillset/releases/tag/v0.5.1
✅ PyPI Page: Rendering correctly
✅ CLI Commands: All functional
✅ MCP Server: Starts successfully
✅ Integration: Claude Code integration working
```

---

## Homebrew Tap Management

### Consolidated Tap Strategy

All bobmatnyc tools use a **single consolidated tap**: `bobmatnyc/homebrew-tools`

**Benefits**:
- ✅ Single tap for users (`brew tap bobmatnyc/tools`)
- ✅ Centralized formula management
- ✅ Reduced maintenance overhead
- ✅ Consistent versioning and updates
- ✅ Simplified user experience

**Repository**: https://github.com/bobmatnyc/homebrew-tools

**Tools Included** (5 formulas):
1. **claude-mpm** (v4.26.1) - Claude Multi-Agent Project Manager
2. **mcp-vector-search** (v0.12.8) - Semantic code search with MCP
3. **mcp-ticketer** (v1.2.10) - Universal ticket management for AI agents
4. **mcp-skillset** (v0.5.1) - Dynamic RAG-powered skills for code assistants
5. **ai-trackdown-pytools** (v0.1.0) - AI project tracking and task management

### Installation Instructions

**For Users**:
```bash
# Add the tap (one time)
brew tap bobmatnyc/tools

# Install any or all tools
brew install mcp-skillset
brew install claude-mpm
brew install mcp-vector-search
brew install mcp-ticketer
brew install ai-trackdown-pytools
```

**For Developers**:
```bash
# Clone the tap repository
cd ~/Projects
git clone https://github.com/bobmatnyc/homebrew-tools.git

# Test formula locally
cd homebrew-tools
brew install --build-from-source ./Formula/mcp-skillset.rb

# Run formula tests
brew test mcp-skillset

# Audit formula
brew audit --strict ./Formula/mcp-skillset.rb
```

### Formula Structure

**Location**: `Formula/mcp-skillset.rb`

**Key Components**:
1. **Class Name**: `McpSkillset` (CamelCase, matches filename)
2. **Description**: One-line summary
3. **Homepage**: GitHub repository URL
4. **URL**: PyPI source distribution URL
5. **SHA256**: Checksum from PyPI
6. **License**: MIT
7. **Dependencies**: `python@3.11`
8. **Install Method**: `virtualenv_install_with_resources`
9. **Test**: Version check

**Example Formula** (v0.5.1):
```ruby
class McpSkillset < Formula
  include Language::Python::Virtualenv

  desc "Dynamic RAG-powered skills for code assistants via Model Context Protocol"
  homepage "https://github.com/bobmatnyc/mcp-skillset"
  url "https://files.pythonhosted.org/packages/source/m/mcp-skillset/mcp_skillset-0.5.1.tar.gz"
  sha256 "de320ea9b26de2f9aff530f4b1b9dafefc5daf915229a7b7da970928eea90c94"
  license "MIT"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/mcp-skillset --version")
  end
end
```

### Updating a Formula

**When**: After PyPI release of new version

**Process**:
1. Wait for PyPI package to be available (2-5 minutes)
2. Fetch SHA256 from PyPI
3. Update formula with new version and SHA256
4. Test locally
5. Commit and push to tap repository

**Commands**:
```bash
# Get SHA256 from PyPI
VERSION=0.5.1
curl -s https://pypi.org/pypi/mcp-skillset/$VERSION/json | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print([u['digests']['sha256'] for u in data['urls'] if u['packagetype'] == 'sdist'][0])"

# Update formula (automated or manual)
cd ~/Projects/homebrew-tools
# Edit Formula/mcp-skillset.rb with new version and SHA256

# Test
brew install --build-from-source ./Formula/mcp-skillset.rb
brew test mcp-skillset
brew audit --strict ./Formula/mcp-skillset.rb

# Commit
git add Formula/mcp-skillset.rb
git commit -m "feat: update mcp-skillset to v$VERSION"
git push origin main
```

**Automation**: Future releases may automate this with a script similar to `update_homebrew_tap.sh` from claude-mpm.

### Real-World Example: v0.6.1 Release

**Date**: 2025-11-25
**Type**: Patch release (template validation fix)

**Homebrew Update Process** (actual commands used):

```bash
# 1. Get SHA256 from PyPI
curl -sL https://pypi.org/pypi/mcp-skillset/0.6.1/json | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['urls'][0]['digests']['sha256'])"
# Output: 330e8252e7a9d919b1ba0826022e0110faaec9afd3004116bad5b3a7b1e039ee

# 2. Navigate to homebrew-tools tap
cd /Users/masa/Projects/homebrew-tools

# 3. Update formula (automated via Edit)
# Updated Formula/mcp-skillset.rb:
#   - url: mcp_skillset-0.6.0.tar.gz → mcp_skillset-0.6.1.tar.gz
#   - sha256: 38380332b... → 330e8252e7a9d919b1ba0826022e0110faaec9afd...

# 4. Commit and push
git add Formula/mcp-skillset.rb
git commit -m "feat: update mcp-skillset to v0.6.1

- Updated URL to mcp_skillset-0.6.1.tar.gz
- Updated SHA256 checksum
- Fixes template validation errors in skill repositories

Release notes: https://github.com/bobmatnyc/mcp-skillset/releases/tag/v0.6.1

🤖👥 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
```

**Result**:
- ✅ Formula updated: https://github.com/bobmatnyc/homebrew-tools/blob/main/Formula/mcp-skillset.rb
- ✅ Commit: `1bd662a` (feat: update mcp-skillset to v0.6.1)
- ✅ Users can now: `brew upgrade mcp-skillset` to get v0.6.1

**Key Points**:
1. Homebrew formula in `homebrew-tools` tap (NOT `homebrew-mcp-skillset`)
2. SHA256 must match PyPI's source distribution checksum
3. Formula updates can be done immediately after PyPI publication
4. Test locally with: `brew install --build-from-source ./Formula/mcp-skillset.rb`

---

## Rollback Procedures

### When to Rollback

Consider rollback if:
- ❌ Critical bug discovered in new version
- ❌ Installation failures on PyPI or Homebrew
- ❌ Security vulnerability introduced
- ❌ Breaking changes not properly documented
- ❌ Data loss or corruption issues

**Important**: You **cannot delete** or **replace** a PyPI version. Rollback options are limited.

### PyPI Rollback Options

**Option 1: Yank the Release (Recommended)**

Yanking prevents new installations but doesn't break existing ones:

```bash
# Via web interface:
# 1. Go to https://pypi.org/project/mcp-skillset/
# 2. Navigate to the problematic version
# 3. Click "Options" → "Yank release"
# 4. Provide reason for yanking

# Or via command line (requires twine 4.0+):
twine upload --skip-existing --repository pypi dist/*
# Then yank via web interface
```

**What Yanking Does**:
- ✅ Prevents `pip install mcp-skillset` from installing yanked version
- ✅ Allows `pip install mcp-skillset==0.5.1` if explicitly specified
- ✅ Shows warning when yanked version is installed
- ❌ Does NOT delete the version
- ❌ Does NOT break existing installations

**Option 2: Publish a Patch Release**

Release a new version immediately:

```bash
# Example: Fix critical bug in 0.5.1 with 0.5.2
# 1. Fix the bug
# 2. Bump version to 0.5.2
# 3. Follow release workflow
# 4. Yank 0.5.1
# 5. Document in CHANGELOG.md

# CHANGELOG.md
## [0.5.2] - 2025-11-25

### Fixed
- **CRITICAL**: Fixed [describe issue] introduced in 0.5.1

## [0.5.1] - 2025-11-25 [YANKED]

**Yanked due to**: [describe issue]
```

### Homebrew Rollback

Homebrew formulas can be reverted easily:

```bash
# Navigate to homebrew-tools
cd ~/Projects/homebrew-tools

# Revert to previous version (example: revert to 0.5.0)
git revert HEAD  # Or specific commit

# Or manually edit Formula/mcp-skillset.rb:
# 1. Change version to 0.5.0
# 2. Update SHA256 to 0.5.0's checksum
# 3. Update URL to 0.5.0's source distribution

# Example:
cat > Formula/mcp-skillset.rb << 'EOF'
class McpSkillset < Formula
  include Language::Python::Virtualenv

  desc "Dynamic RAG-powered skills for code assistants via Model Context Protocol"
  homepage "https://github.com/bobmatnyc/mcp-skillset"
  url "https://files.pythonhosted.org/packages/source/m/mcp-skillset/mcp_skillset-0.5.0.tar.gz"
  sha256 "PREVIOUS_VERSION_SHA256"
  license "MIT"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/mcp-skillset --version")
  end
end
EOF

# Test rollback
brew uninstall mcp-skillset
brew install --build-from-source ./Formula/mcp-skillset.rb
mcp-skillset --version  # Should show 0.5.0

# Commit rollback
git add Formula/mcp-skillset.rb
git commit -m "fix: rollback mcp-skillset to v0.5.0 due to critical bug in v0.5.1"
git push origin main
```

### GitHub Release Rollback

GitHub releases can be edited or deleted:

```bash
# Delete release
gh release delete v0.5.1 --yes

# Or edit release to mark as broken
gh release edit v0.5.1 \
  --title "v0.5.1 - YANKED (Critical Bug)" \
  --notes "**WARNING**: This release has been yanked due to [issue].

Please install v0.5.2 instead:
\`\`\`bash
pip install mcp-skillset==0.5.2
\`\`\`

Original release notes:
[original notes]"
```

### Communication Strategy

When rolling back:

1. **Update CHANGELOG.md**:
   ```markdown
   ## [0.5.1] - 2025-11-25 [YANKED]

   **Yanked due to**: Critical bug causing [issue]
   **Recommended version**: 0.5.2 or 0.5.0
   ```

2. **Update README.md**:
   Add notice at top if issue is severe:
   ```markdown
   > **⚠️ NOTICE**: Version 0.5.1 has been yanked due to [issue].
   > Please use version 0.5.2 or 0.5.0.
   ```

3. **Create GitHub Issue**:
   Document the problem and rollback:
   ```
   Title: Version 0.5.1 Yanked - Critical Bug

   Description of issue, steps to reproduce, and workaround.
   ```

4. **Notify Users** (if applicable):
   - GitHub Discussions
   - Project Discord/Slack
   - Social media
   - Direct notification to affected users

---

## Troubleshooting

### PyPI Issues

#### Issue: "File already exists"

**Symptom**: Upload fails with "File already exists" error.

**Cause**: Trying to upload a version that already exists on PyPI.

**Solution**:
```bash
# You CANNOT replace an existing version
# Must increment version number

# Option 1: Patch version
# pyproject.toml: version = "0.5.2"

# Option 2: Pre-release version (for testing)
# pyproject.toml: version = "0.5.2a1"

# Rebuild and re-upload
rm -rf dist/ build/ *.egg-info
python -m build
twine upload dist/*
```

#### Issue: "Invalid or non-existent authentication"

**Symptom**: Upload fails with authentication error.

**Cause**: `~/.pypirc` missing, incorrect, or has wrong permissions.

**Solution**:
```bash
# Check .pypirc exists and has correct permissions
ls -l ~/.pypirc
# Should be: -rw------- (600)

# Fix permissions if needed
chmod 600 ~/.pypirc

# Verify token is correct
cat ~/.pypirc | grep "password"

# Regenerate token if needed:
# 1. Go to https://pypi.org/manage/account/token/
# 2. Create new token
# 3. Update ~/.pypirc with new token
```

#### Issue: README not rendering on PyPI

**Symptom**: README shows as plain text or errors on PyPI page.

**Cause**: Markdown syntax not supported by PyPI.

**Solution**:
```bash
# Test README rendering locally
pip install readme-renderer
python -m readme_renderer README.md -o /tmp/readme.html
open /tmp/readme.html  # View rendered output

# Common issues:
# - GitHub-specific syntax (alerts, etc.)
# - Invalid HTML in markdown
# - Relative links to non-existent files

# Validate with twine
twine check dist/*
```

### Homebrew Issues

#### Issue: Formula installation fails

**Symptom**: `brew install mcp-skillset` fails.

**Cause**: Various (wrong SHA256, missing dependencies, Python version issues).

**Diagnosis**:
```bash
# Install with verbose debugging
brew install --verbose --debug mcp-skillset

# Check formula syntax
brew audit --strict ./Formula/mcp-skillset.rb

# Common issues:
# 1. Wrong SHA256 (get correct one from PyPI)
# 2. Python version mismatch
# 3. Missing dependencies
# 4. Formula syntax errors
```

**Solution**:
```bash
# Fix SHA256
# Get correct SHA256 from PyPI:
curl -s https://pypi.org/pypi/mcp-skillset/0.5.1/json | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print([u['digests']['sha256'] for u in data['urls'] if u['packagetype'] == 'sdist'][0])"

# Update formula and test
brew install --build-from-source ./Formula/mcp-skillset.rb
brew test mcp-skillset
```

#### Issue: Formula test fails

**Symptom**: `brew test mcp-skillset` fails.

**Cause**: Binary not in expected location or doesn't respond to `--version`.

**Diagnosis**:
```bash
# Check where binary is installed
brew --prefix mcp-skillset
ls -la $(brew --prefix mcp-skillset)/bin/

# Test binary manually
$(brew --prefix mcp-skillset)/bin/mcp-skillset --version
```

**Solution**:
```ruby
# Update formula test block if needed
test do
  assert_match version.to_s, shell_output("#{bin}/mcp-skillset --version")
end
```

### Build Issues

#### Issue: Build fails with dependency errors

**Symptom**: `python -m build` fails with dependency resolution errors.

**Cause**: Conflicting dependency versions in `pyproject.toml`.

**Solution**:
```bash
# Create clean virtual environment
python -m venv clean-build-env
source clean-build-env/bin/activate

# Install build dependencies
pip install --upgrade pip setuptools wheel build

# Try build again
python -m build

# If still fails, check dependency conflicts
pip install pipdeptree
pipdeptree

# Clean up
deactivate
rm -rf clean-build-env
```

#### Issue: Tests fail during build

**Symptom**: Build succeeds but tests fail afterward.

**Cause**: Environment differences, missing test dependencies.

**Solution**:
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests locally
pytest -v

# Check test coverage
pytest --cov=src/mcp_skills --cov-report=term-missing

# Fix failing tests before release
```

### Git/GitHub Issues

#### Issue: Tag already exists

**Symptom**: `git tag v0.5.1` fails because tag exists.

**Solution**:
```bash
# Delete local tag
git tag -d v0.5.1

# Delete remote tag (if pushed)
git push origin :refs/tags/v0.5.1

# Create new tag
git tag -a v0.5.1 -m "Release version 0.5.1"
git push origin v0.5.1
```

#### Issue: GitHub release creation fails

**Symptom**: `gh release create` fails with authentication or validation error.

**Solution**:
```bash
# Re-authenticate with GitHub CLI
gh auth login

# Verify authentication
gh auth status

# Retry release creation
gh release create v0.5.1 \
  --title "v0.5.1" \
  --notes "Release notes here" \
  dist/*
```

---

## Quick Reference

### Commands for Next Release

**Complete release workflow** (v0.5.2 example):

```bash
# 1. Pre-release checks
make quality
mcp-skillset health

# 2. Update version
# Edit: pyproject.toml, VERSION, src/mcp_skills/VERSION
# New version: 0.5.2

# 3. Update documentation
# Edit: CHANGELOG.md, README.md

# 4. Clean and build
rm -rf dist/ build/ *.egg-info
python -m build

# 5. Verify build
twine check dist/*
ls -lh dist/

# 6. Commit version bump
git add .
git commit -m "chore: bump version to 0.5.2"
git tag -a v0.5.2 -m "Release version 0.5.2"
git push origin main
git push origin v0.5.2

# 7. Publish to PyPI (uses ~/.pypirc)
twine upload dist/*

# 8. Get SHA256 for Homebrew
curl -s https://pypi.org/pypi/mcp-skillset/0.5.2/json | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print([u['digests']['sha256'] for u in data['urls'] if u['packagetype'] == 'sdist'][0])"

# 9. Update Homebrew formula
cd ~/Projects/homebrew-tools
# Edit Formula/mcp-skillset.rb (version, url, sha256)
brew install --build-from-source ./Formula/mcp-skillset.rb
brew test mcp-skillset
git add Formula/mcp-skillset.rb
git commit -m "feat: update mcp-skillset to v0.5.2"
git push origin main

# 10. Create GitHub release
cd ~/Projects/mcp-skillset
gh release create v0.5.2 \
  --title "v0.5.2" \
  --notes "$(cat CHANGELOG.md | sed -n '/## \[0.5.2\]/,/## \[0.5.1\]/p' | head -n -1)" \
  dist/*

# 11. Verify release
pip install --upgrade mcp-skillset
mcp-skillset --version  # Should show 0.5.2
brew upgrade mcp-skillset
```

### Version Number Reference

Current: **v0.5.1**

**Files to Update**:
- `/Users/masa/Projects/mcp-skillset/pyproject.toml`
- `/Users/masa/Projects/mcp-skillset/VERSION`
- `/Users/masa/Projects/mcp-skillset/src/mcp_skills/VERSION`
- `/Users/masa/Projects/mcp-skillset/CHANGELOG.md`

**Repositories**:
- Main: https://github.com/bobmatnyc/mcp-skillset
- Homebrew: https://github.com/bobmatnyc/homebrew-tools

**Distribution**:
- PyPI: https://pypi.org/project/mcp-skillset/
- Homebrew: `brew tap bobmatnyc/tools && brew install mcp-skillset`

### Key URLs

**v0.5.1 Release**:
- PyPI: https://pypi.org/project/mcp-skillset/0.5.1/
- GitHub: https://github.com/bobmatnyc/mcp-skillset/releases/tag/v0.5.1
- Homebrew: https://github.com/bobmatnyc/homebrew-tools/blob/main/Formula/mcp-skillset.rb
- SHA256: `de320ea9b26de2f9aff530f4b1b9dafefc5daf915229a7b7da970928eea90c94`

**Commits**:
- Version bump: `ab1ab44` (chore: bump version to 0.5.1)
- PyPI fix: `b40ef9c` (fix: update pyproject.toml version to 0.5.1)
- Docs update: `8cfd733` (docs: update installation to use consolidated homebrew-tools tap)

---

## Related Documentation

- **Publishing Guide**: [docs/publishing.md](publishing.md) - Detailed PyPI publishing process
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md) - How to contribute to the project
- **CHANGELOG**: [CHANGELOG.md](../CHANGELOG.md) - All version history
- **README**: [README.md](../README.md) - Project overview and installation

---

**Last Updated**: 2025-11-25
**Maintained By**: bobmatnyc
**Next Review**: After next release (v0.5.2 or later)
