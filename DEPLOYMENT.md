# Deployment Guide

This guide explains how to publish Halt packages to PyPI and npm.

## Prerequisites

### PyPI Setup

1. Create accounts on:
   - [PyPI](https://pypi.org/account/register/)
   - [Test PyPI](https://test.pypi.org/account/register/) (optional, for testing)

2. Generate API tokens:
   - Go to Account Settings → API tokens
   - Create a token with "Entire account" scope
   - Save the token securely

3. Add secrets to GitHub:
   - Go to repository Settings → Secrets and variables → Actions
   - Add `PYPI_TOKEN` with your PyPI token
   - Add `TEST_PYPI_TOKEN` with your Test PyPI token (optional)

### npm Setup

1. Create an [npm account](https://www.npmjs.com/signup)

2. Generate an access token:
   - Go to Account Settings → Access Tokens
   - Create a "Automation" token
   - Save the token securely

3. Add secret to GitHub:
   - Go to repository Settings → Secrets and variables → Actions
   - Add `NPM_TOKEN` with your npm token

## Automated Release Process

### Option 1: Using GitHub Release Workflow (Recommended)

1. Go to Actions → "Create Release"
2. Click "Run workflow"
3. Enter the version number (e.g., `0.2.0`)
4. Select if it's a pre-release
5. Click "Run workflow"

This will:
- Update version in both packages
- Create a Git tag
- Create a GitHub release
- Automatically trigger publishing workflows

### Option 2: Manual GitHub Release

1. Create a new release on GitHub:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

2. Go to GitHub → Releases → "Draft a new release"
3. Select the tag you just created
4. Fill in release notes
5. Publish the release

This will automatically trigger both publishing workflows.

## Manual Publishing

### Python Package (PyPI)

```bash
cd packages/python

# Update version in pyproject.toml
# version = "0.2.0"

# Build the package
python -m build

# Check the package
twine check dist/*

# Upload to Test PyPI (optional)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### TypeScript Package (npm)

```bash
cd packages/typescript

# Update version in package.json
npm version 0.2.0 --no-git-tag-version

# Build the package
npm run build

# Run tests
npm test

# Publish to npm
npm publish --access public
```

## Testing Before Release

### Test PyPI (Python)

```bash
# Upload to Test PyPI
cd packages/python
twine upload --repository testpypi dist/*

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ halt

# Test the package
python -c "from halt import RateLimiter; print('Success!')"
```

### npm Tag (TypeScript)

```bash
# Publish with a beta tag
cd packages/typescript
npm publish --tag beta

# Install the beta version
npm install halt@beta

# Test the package
node -e "const { RateLimiter } = require('halt'); console.log('Success!');"

# Promote to latest when ready
npm dist-tag add halt@0.2.0 latest
```

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.2.0): New features, backward compatible
- **PATCH** (0.1.1): Bug fixes, backward compatible

## Pre-release Versions

For beta/alpha releases:

```bash
# Python
version = "0.2.0b1"  # Beta 1
version = "0.2.0rc1" # Release candidate 1

# TypeScript
npm version 0.2.0-beta.1
npm version 0.2.0-rc.1
```

## Rollback

If you need to rollback a release:

### PyPI
PyPI doesn't allow deleting releases, but you can:
1. Publish a new patch version with the fix
2. Mark the problematic version as "yanked" (prevents new installs)

### npm
```bash
# Deprecate a version
npm deprecate halt@0.2.0 "This version has critical bugs. Please upgrade to 0.2.1"

# Unpublish (only within 72 hours)
npm unpublish halt@0.2.0
```

## Monitoring

After publishing:

1. **PyPI**: Check [https://pypi.org/project/halt/](https://pypi.org/project/halt/)
2. **npm**: Check [https://www.npmjs.com/package/halt](https://www.npmjs.com/package/halt)
3. **GitHub**: Monitor the Actions tab for workflow status
4. **Downloads**: Track download statistics on package registries

## Troubleshooting

### PyPI Upload Fails

- Check your API token is correct
- Ensure version number is unique (can't reuse versions)
- Verify package builds correctly: `twine check dist/*`

### npm Publish Fails

- Check your npm token is correct
- Ensure you're logged in: `npm whoami`
- Verify package.json is valid
- Check if package name is available

### CI/CD Workflow Fails

- Check GitHub Actions logs
- Verify secrets are set correctly
- Ensure version numbers are updated
- Check for test failures

## Support

For issues with deployment:
1. Check the [GitHub Actions logs](https://github.com/yourusername/halt/actions)
2. Review this deployment guide
3. Open an issue on GitHub
