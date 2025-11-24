# Security Scanning - Quick Start Guide

**tl;dr**: Run `make security-check` before committing. Dependabot handles the rest automatically.

## For Developers (Day-to-Day)

### Before Committing
```bash
# Quick security scan (30 seconds)
make security-check

# If you changed dependencies, run full audit
make security-check-full
```

### Before Publishing/Releasing
```bash
# Full quality gate with security checks
make pre-publish
```

### If You See a Dependabot PR
1. Review the changes
2. Check if it's a security update (labeled `security`)
3. Run tests: `make quality`
4. Merge if tests pass

## For Maintainers

### Weekly Tasks
- Review Dependabot PRs (Mondays after 9 AM EST)
- Check GitHub Actions security workflow results
- Prioritize PRs labeled `security`

### Monthly Tasks
- Review `.security-reports/` for trends
- Update `.secrets.baseline` if needed
- Check for outdated security tool versions

### Critical Vulnerabilities
1. Dependabot will create a PR immediately
2. GitHub Security tab will show an alert
3. Review and merge ASAP (target: within 24 hours)

## Quick Reference

### Makefile Targets
```bash
make security-check           # Basic scan (Safety + pip-audit)
make security-check-full      # Full audit with reports
make security-install         # Install security tools
make pre-publish             # Quality + security + secrets gate
```

### GitHub Actions Workflows

**Security Scan** (`.github/workflows/security.yml`):
- Runs on: Push, PR, weekly, manual
- Tools: Safety, pip-audit, Bandit, detect-secrets
- Reports: Artifacts tab (30-day retention)

**CI** (`.github/workflows/ci.yml`):
- Runs on: Push, PR
- Tests: Python 3.11, 3.12, 3.13
- Quality: Linting, type checking, coverage

### Dependabot Configuration

**Schedule**: Weekly (Mondays 9:00 AM EST)
**Scope**: Python packages + GitHub Actions
**PR Limit**: 5 open PRs max
**Grouping**: Minor/patch updates grouped together

## Security Reports

### Local Reports (`.security-reports/`)
```bash
# After running make security-check-full
ls -la .security-reports/
cat .security-reports/safety-report.json | jq .
```

### GitHub Artifacts
1. Go to Actions tab
2. Click on "Security Scan" workflow run
3. Download artifacts (safety-report, pip-audit-report, bandit-report)

## Troubleshooting

### "New secrets detected"
```bash
# Update baseline
detect-secrets scan > .secrets.baseline
git add .secrets.baseline
```

### "Command not found: safety"
```bash
# Install security tools
make security-install

# Or manually
pip install safety pip-audit bandit
```

### Dependabot PR Conflicts
1. Update your branch: `git pull origin main`
2. Rebase the PR if needed
3. Re-run tests

## What Each Tool Does

| Tool | Purpose | When It Runs |
|------|---------|--------------|
| **Dependabot** | Auto-update vulnerable dependencies | Weekly (Mondays) |
| **Safety** | Check dependencies against vulnerability DB | Every commit, PR, weekly |
| **pip-audit** | Official PyPA vulnerability scanner | Every commit, PR, weekly |
| **Bandit** | Find security issues in Python code | Every commit, PR, weekly |
| **detect-secrets** | Prevent secrets from being committed | Pre-publish |

## Common Scenarios

### Scenario 1: Regular Development
```bash
# Make code changes
vim src/mcp_skills/some_file.py

# Before committing
make security-check

# Commit if clean
git commit -m "feat: add new feature"
```

### Scenario 2: Adding New Dependency
```bash
# Add to pyproject.toml
vim pyproject.toml

# Install
pip install -e .

# Run full security audit
make security-check-full

# Check reports
cat .security-reports/safety-report.json | jq .
```

### Scenario 3: Preparing Release
```bash
# Run full quality gate
make pre-publish

# If all checks pass
make safe-release-build

# Publish
python -m twine upload dist/*
```

### Scenario 4: Responding to Security Alert
```bash
# GitHub will alert you via:
# - Dependabot PR
# - Security tab notification
# - Email (if configured)

# Review the PR
git fetch origin pull/123/head:security-update-123
git checkout security-update-123

# Test
make quality

# Merge via GitHub UI
```

## Red Flags (Stop and Fix)

🚨 **Critical vulnerabilities found**: Merge Dependabot PR immediately
🚨 **Secret detected**: Remove secret, rotate credentials, update baseline
🚨 **Bandit high severity issue**: Fix code security issue before merging
🚨 **Pre-publish fails**: Do not publish until fixed

## Green Lights (Safe to Proceed)

✅ All security checks pass
✅ No critical or high vulnerabilities
✅ No secrets detected
✅ Bandit reports no issues
✅ Dependabot PRs merged regularly

## Getting Help

1. **Documentation**: See `.github/SECURITY.md` for detailed security policy
2. **Workflow Logs**: Check GitHub Actions logs for detailed error messages
3. **Local Reports**: Review `.security-reports/*.json` files
4. **Project Issues**: Open GitHub issue with `security` label

## Configuration Files

- `.github/dependabot.yml` - Dependabot configuration
- `.github/workflows/security.yml` - Security scan workflow
- `.github/workflows/ci.yml` - CI workflow
- `.github/SECURITY.md` - Security policy and reporting
- `Makefile` - Security targets (security-check, etc.)
- `pyproject.toml` - Security tools in dev dependencies

## Best Practices Checklist

- [ ] Run `make security-check` before every commit
- [ ] Review Dependabot PRs weekly
- [ ] Respond to security alerts within 24-48 hours
- [ ] Keep `.secrets.baseline` updated
- [ ] Run `make pre-publish` before releases
- [ ] Check GitHub Security tab monthly
- [ ] Update security tools quarterly

---

**Last Updated**: 2025-01-24
**See Also**: [.github/SECURITY.md](.github/SECURITY.md) for comprehensive security documentation
