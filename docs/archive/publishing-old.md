# Publishing mcp-skillset to PyPI

This guide covers the complete process for publishing mcp-skillset to PyPI, including setup, testing, and release procedures.

## Prerequisites

### Required Accounts

1. **PyPI Account**: https://pypi.org/account/register/
2. **TestPyPI Account**: https://test.pypi.org/account/register/ (for testing)

### Required Tools

Install publishing tools:

```bash
pip install --upgrade build twine
```

### API Token Setup

1. **PyPI API Token**:
   - Go to https://pypi.org/manage/account/token/
   - Click "Add API token"
   - Name: "mcp-skillset-publishing"
   - Scope: "Entire account" or "Project: mcp-skillset" (after first upload)
   - Copy the token (starts with `pypi-`)

2. **TestPyPI API Token**:
   - Go to https://test.pypi.org/manage/account/token/
   - Follow same process as above
   - Copy the token (starts with `pypi-`)

### Configure ~/.pypirc

Create or edit `~/.pypirc` with your API tokens:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC... # Your PyPI token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmcC... # Your TestPyPI token
```

**Security**: Set proper permissions:
```bash
chmod 600 ~/.pypirc
```

**Important**: NEVER commit `.pypirc` to version control!

## Pre-Release Checklist

Before publishing, ensure all these items are complete:

### 1. Version Management

Update version in `pyproject.toml`:

```toml
[project]
version = "0.1.0"  # Update this
```

### 2. Documentation Updates

- [ ] Update `CHANGELOG.md` with release notes
- [ ] Update README.md status badge
- [ ] Verify all GitHub URLs are correct
- [ ] Check that documentation links work

### 3. Code Quality

Run full test suite and quality checks:

```bash
# Run all quality checks
make quality

# Or run individually:
make lint        # Check code style
make type        # Type checking
make test        # Run all tests
make test-cov    # Test with coverage report
```

All tests must pass with 85%+ coverage.

### 4. Clean Build Environment

Remove old build artifacts:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Or use make target
make clean
```

## Publishing Process

### Step 1: Build Distribution Packages

Build source distribution and wheel:

```bash
python -m build
```

This creates:
- `dist/mcp-skillset-0.1.0.tar.gz` (source distribution)
- `dist/mcp_skills-0.1.0-py3-none-any.whl` (wheel)

**Verify build contents**:

```bash
# Check source distribution contents
tar tzf dist/mcp-skillset-0.1.0.tar.gz | head -20

# Check wheel contents
unzip -l dist/mcp_skills-0.1.0-py3-none-any.whl
```

Ensure all necessary files are included:
- Source code from `src/mcp_skills/`
- `README.md`
- `LICENSE`
- `CHANGELOG.md`
- `pyproject.toml`

### Step 2: Test with TestPyPI (CRITICAL)

Always test with TestPyPI first to catch issues:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

You'll see output like:
```
Uploading distributions to https://test.pypi.org/legacy/
Uploading mcp_skills-0.1.0-py3-none-any.whl
Uploading mcp-skillset-0.1.0.tar.gz
```

**Test Installation from TestPyPI**:

```bash
# Create clean virtual environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-skillset

# Test basic functionality
mcp-skillset --version
mcp-skillset health
mcp-skillset config

# Clean up
deactivate
rm -rf test-env
```

**Note**: `--extra-index-url https://pypi.org/simple/` is needed because TestPyPI doesn't have all dependencies.

### Step 3: Verify Package Quality

Check the package with twine:

```bash
twine check dist/*
```

This verifies:
- README renders correctly on PyPI
- Metadata is valid
- Distribution files are well-formed

### Step 4: Publish to PyPI

Once TestPyPI installation works correctly:

```bash
# Upload to production PyPI
twine upload dist/*
```

**IMPORTANT**: This action cannot be undone. You cannot reupload the same version number.

### Step 5: Verify Production Installation

Test installation from production PyPI:

```bash
# Create clean virtual environment
python -m venv prod-test-env
source prod-test-env/bin/activate

# Install from PyPI
pip install mcp-skillset

# Verify installation
mcp-skillset --version
mcp-skillset health

# Clean up
deactivate
rm -rf prod-test-env
```

### Step 6: Create Git Tag and GitHub Release

Tag the release in git:

```bash
# Create annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push tag to GitHub
git push origin v0.1.0
```

**Create GitHub Release**:

1. Go to https://github.com/bobmatnyc/mcp-skillset/releases/new
2. Select tag: `v0.1.0`
3. Release title: `v0.1.0 - Initial Release`
4. Description: Copy content from `CHANGELOG.md` for this version
5. Attach distribution files from `dist/` directory
6. Click "Publish release"

## Post-Release Tasks

### 1. Update Development Version

Update `pyproject.toml` to next development version:

```toml
[project]
version = "0.2.0-dev"  # Or "0.1.1-dev" for patch
```

Commit this change:

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0-dev"
git push origin main
```

### 2. Verify PyPI Page

Check your package page:
- https://pypi.org/project/mcp-skillset/
- Verify README renders correctly
- Check metadata (links, classifiers, etc.)
- Verify badges and images display

### 3. Update Documentation

Update any documentation that references installation:
- README.md installation instructions
- GitHub Wiki (if applicable)
- Blog posts or announcements

### 4. Announce Release

Consider announcing on:
- GitHub Discussions
- Project Discord/Slack
- Twitter/social media
- Relevant forums or communities

## Troubleshooting

### Common Issues

#### Issue: "File already exists"

**Problem**: Trying to upload a version that already exists.

**Solution**:
- You cannot replace an existing version on PyPI
- Increment version number in `pyproject.toml`
- Rebuild and re-upload

#### Issue: README not rendering on PyPI

**Problem**: Markdown syntax not supported by PyPI.

**Solution**:
- Ensure `readme = "README.md"` is in `pyproject.toml`
- Use only GitHub-flavored Markdown features
- Test with `twine check dist/*`
- Preview with: `python -m readme_renderer README.md`

#### Issue: Missing dependencies on installation

**Problem**: Dependencies not installed with package.

**Solution**:
- Verify all dependencies listed in `pyproject.toml` under `dependencies`
- Test installation in clean virtual environment
- Check dependency version constraints

#### Issue: Import errors after installation

**Problem**: Package structure not correct.

**Solution**:
- Verify `src/` layout is correct
- Check `[tool.setuptools.packages.find]` in `pyproject.toml`
- Ensure `__init__.py` files exist in all packages

#### Issue: Authentication failure

**Problem**: API token not working.

**Solution**:
- Verify token is correct in `~/.pypirc`
- Check token hasn't expired
- Ensure token has correct scope
- Try regenerating token

### Emergency: Wrong Version Published

If you accidentally publish a broken version:

1. **DO NOT** delete the version from PyPI (not allowed)
2. **Immediately publish a patch version** (e.g., 0.1.1) with fixes
3. Use "yank" feature on PyPI:
   - Go to https://pypi.org/project/mcp-skillset/
   - Click "Manage" → "Options" → "Yank release"
   - This prevents new installations but doesn't break existing ones

### Getting Help

If you encounter issues:

1. Check [PyPI Help](https://pypi.org/help/)
2. Review [Python Packaging Guide](https://packaging.python.org/)
3. Ask in [Python Packaging Discourse](https://discuss.python.org/c/packaging/)
4. File issue on [pypa/packaging-problems](https://github.com/pypa/packaging-problems)

## Security Best Practices

1. **API Tokens**:
   - Use project-scoped tokens when possible
   - Rotate tokens periodically
   - Never commit tokens to version control
   - Use environment variables in CI/CD

2. **Package Security**:
   - Sign releases with GPG (optional but recommended)
   - Enable 2FA on PyPI account
   - Review package before publishing
   - Monitor security advisories

3. **Secrets Management**:
   - Use GitHub Secrets for CI/CD
   - Limit access to publishing credentials
   - Audit who has publishing permissions

## Automated Publishing (Future)

Consider setting up GitHub Actions for automated publishing:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

This requires:
- Creating `PYPI_API_TOKEN` secret in GitHub repository settings
- Publishing happens automatically when you create a GitHub release

## Release Checklist

Use this checklist for each release:

- [ ] All tests passing (`make quality`)
- [ ] Version updated in `pyproject.toml`
- [ ] `CHANGELOG.md` updated with release notes
- [ ] README.md status and badges current
- [ ] Clean build environment (`make clean`)
- [ ] Build distributions (`python -m build`)
- [ ] Check distributions (`twine check dist/*`)
- [ ] Upload to TestPyPI
- [ ] Test install from TestPyPI
- [ ] Upload to PyPI
- [ ] Test install from PyPI
- [ ] Create git tag (`git tag v0.1.0`)
- [ ] Push tag to GitHub
- [ ] Create GitHub Release
- [ ] Update development version
- [ ] Announce release

---

**Last Updated**: 2025-11-23
**Package**: mcp-skillset v0.1.0
