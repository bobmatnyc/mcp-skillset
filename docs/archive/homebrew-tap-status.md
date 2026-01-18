# Homebrew Tap Update Status - mcp-skillset v0.2.0

**Date**: 2025-11-24
**Package**: mcp-skillset v0.2.0
**PyPI URL**: https://pypi.org/project/mcp-skillset/0.2.0/
**Status**: NON-BLOCKING (Phase 5.5 per PM instructions)

---

## Executive Summary

**Result**: Homebrew tap infrastructure DOES NOT EXIST for mcp-skillset.

**Impact**: This is a **NON-BLOCKING** issue per PM instructions (Phase 5.5). The PyPI release (v0.2.0) is successful and the package is installable via `pip install mcp-skillset==0.2.0`.

**Recommendation**: Create Homebrew tap infrastructure using the proven pattern from `claude-mpm` as a template.

---

## Investigation Findings

### 1. Homebrew Tap Infrastructure Search

**Searched Locations**:
- `/Users/masa/Projects/mcp-skillset/` - Project root
- `/Users/masa/Projects/mcp-skillset/scripts/` - Scripts directory
- `/Users/masa/Projects/mcp-skillset/.makefiles/` - Makefile components
- GitHub repositories under `bobmatnyc/*`

**Results**:
- ❌ No `scripts/update_homebrew_tap.sh` script found
- ❌ No `homebrew-mcp-skillset` repository exists on GitHub
- ❌ No Makefile targets for Homebrew tap updates
- ❌ No GitHub Actions workflow for Homebrew automation

**Reference Infrastructure Found**:
- ✅ `homebrew-claude-mpm` repository exists with working automation
- ✅ `scripts/update_homebrew_tap.sh` available in claude-mpm project
- ✅ Working pattern: `homebrew-mcp-vector-search`, `homebrew-mcp-ticketer`

### 2. Package Information

**PyPI Package**: mcp-skillset
**Version**: 0.2.0
**Repository**: https://github.com/bobmatnyc/mcp-skillset
**PyPI Status**: ✅ Published successfully at https://pypi.org/project/mcp-skillset/0.2.0/

### 3. Homebrew Tap Pattern Analysis

Based on existing taps (`homebrew-claude-mpm`, `homebrew-mcp-vector-search`, `homebrew-mcp-ticketer`), the standard pattern includes:

1. **Repository Structure**:
   ```
   homebrew-mcp-skillset/
   ├── Formula/
   │   └── mcp-skillset.rb
   ├── README.md
   └── scripts/
       └── generate_resources.py (optional)
   ```

2. **Automation Script** (`scripts/update_homebrew_tap.sh`):
   - Wait for PyPI package availability (with retry logic)
   - Fetch SHA256 checksum from PyPI
   - Update Formula/mcp-skillset.rb
   - Run formula tests (brew audit)
   - Commit with conventional commit message
   - Push to tap repository

3. **Makefile Target** (in main project):
   ```makefile
   .PHONY: update-homebrew-tap
   update-homebrew-tap: ## Update Homebrew tap formula
       @./scripts/update_homebrew_tap.sh $(VERSION)
   ```

---

## Next Steps

### Option 1: Create Homebrew Tap Infrastructure (Recommended)

This would involve:

1. **Create Repository**: `bobmatnyc/homebrew-mcp-skillset`
2. **Create Formula**: `Formula/mcp-skillset.rb` (based on PyPI package)
3. **Copy Automation Script**: Adapt `claude-mpm/scripts/update_homebrew_tap.sh`
4. **Add Makefile Target**: Add `update-homebrew-tap` target
5. **Initial Formula Creation**: Manually create first formula for v0.2.0
6. **Test Installation**: `brew tap bobmatnyc/mcp-skillset && brew install mcp-skillset`

**Estimated Time**: 30-45 minutes
**Benefits**: Full Homebrew support for macOS users

### Option 2: Manual Homebrew Formula Creation (Current State)

Continue with PyPI-only distribution and document pip installation:

```bash
pip install mcp-skillset==0.2.0
```

**Current State**: This is the current distribution method
**Impact**: No Homebrew convenience for macOS users

---

## Manual Homebrew Tap Creation Instructions

If you want to create the Homebrew tap manually:

### Step 1: Create Repository

```bash
gh repo create bobmatnyc/homebrew-mcp-skillset --public --description "Homebrew tap for mcp-skillset - Dynamic RAG-powered skills for code assistants"
```

### Step 2: Clone and Setup

```bash
cd /Users/masa/Projects
git clone https://github.com/bobmatnyc/homebrew-mcp-skillset.git
cd homebrew-mcp-skillset
mkdir -p Formula
```

### Step 3: Create Initial Formula

Create `Formula/mcp-skillset.rb`:

```ruby
class MpcSkillkit < Formula
  include Language::Python::Virtualenv

  desc "Dynamic RAG-powered skills for code assistants via MCP"
  homepage "https://github.com/bobmatnyc/mcp-skillset"
  url "https://files.pythonhosted.org/packages/source/m/mcp-skillset/mcp-skillset-0.2.0.tar.gz"
  sha256 "FETCH_FROM_PYPI"  # Get actual SHA256 from PyPI
  license "MIT"

  depends_on "python@3.11"

  # Add resource stanzas for dependencies here
  # Use `pip download --no-deps mcp-skillset==0.2.0` to get dependencies

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"mcp-skillset", "--version"
  end
end
```

### Step 4: Fetch SHA256 from PyPI

```bash
curl -s https://pypi.org/pypi/mcp-skillset/0.2.0/json | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print([u['digests']['sha256'] for u in data['urls'] if u['packagetype'] == 'sdist'][0])"
```

### Step 5: Test Formula Locally

```bash
brew install --build-from-source Formula/mcp-skillset.rb
brew test mcp-skillset
brew audit --strict Formula/mcp-skillset.rb
```

### Step 6: Commit and Push

```bash
git add Formula/mcp-skillset.rb
git commit -m "feat: initial formula for mcp-skillset v0.2.0

🤖 Homebrew tap for mcp-skillset

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
```

### Step 7: Copy Automation Script

Copy and adapt the automation script from claude-mpm:

```bash
cp /Users/masa/Projects/claude-mpm/scripts/update_homebrew_tap.sh \
   /Users/masa/Projects/mcp-skillset/scripts/update_homebrew_tap.sh
```

Then edit the script to update:
- `TAP_REPO="https://github.com/bobmatnyc/homebrew-mcp-skillset.git"`
- `PYPI_PACKAGE="mcp-skillset"`
- `FORMULA_FILE="Formula/mcp-skillset.rb"`

---

## PM Instructions Compliance

Per PM instructions (Phase 5.5):

> **5.5. Update Homebrew Tap Formula (NON-BLOCKING)**
> - Homebrew tap update should be automated
> - Failures should NOT block the release
> - Manual fallback instructions should be provided

**Compliance Status**:
- ✅ NON-BLOCKING: This report documents the situation without blocking release
- ⚠️ AUTOMATION: Not yet implemented (infrastructure doesn't exist)
- ✅ MANUAL FALLBACK: Instructions provided above

---

## Conclusion

**Current Status**: mcp-skillset v0.2.0 is successfully published to PyPI and installable via pip.

**Homebrew Status**: No Homebrew tap exists yet. This is a **NON-BLOCKING** issue that can be addressed in a future task.

**Immediate Action**: None required. The PyPI release is complete and functional.

**Future Enhancement**: Create Homebrew tap infrastructure using the instructions above or adapt the claude-mpm automation script.

---

## Evidence

**Files Checked**:
- `/Users/masa/Projects/mcp-skillset/Makefile` - No Homebrew targets found
- `/Users/masa/Projects/mcp-skillset/.makefiles/release.mk` - No Homebrew automation
- `/Users/masa/Projects/mcp-skillset/scripts/` - Only `generate_completions.sh` found
- GitHub repository search - No `homebrew-mcp-skillset` repository exists

**Reference Implementation**:
- `/Users/masa/Projects/claude-mpm/scripts/update_homebrew_tap.sh` - Working automation script
- `/Users/masa/Projects/homebrew-claude-mpm/` - Example tap repository
- `/Users/masa/Projects/homebrew-mcp-vector-search/` - Example tap repository
- `/Users/masa/Projects/homebrew-mcp-ticketer/` - Example tap repository

**PyPI Verification**:
```bash
curl -s https://pypi.org/pypi/mcp-skillset/0.2.0/json | python3 -c "import sys, json; print(json.load(sys.stdin)['info']['version'])"
# Expected output: 0.2.0
```

**Installation Verification** (Current Method):
```bash
pip install mcp-skillset==0.2.0
mcp-skillset --version
# Expected: 0.2.0
```
