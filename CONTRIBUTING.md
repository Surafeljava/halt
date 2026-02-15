# Contributing to Halt

Thank you for your interest in contributing to Halt! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- Git

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/halt.git
cd halt

# Install Python package in development mode
cd packages/python
pip install -e ".[dev]"

# Install TypeScript package
cd ../typescript
npm install
```

## Development Workflow

### Python Development

```bash
cd packages/python

# Run tests
pytest

# Run tests with coverage
pytest --cov=halt

# Lint code
ruff check halt/

# Format code
black halt/

# Type check
mypy halt/
```

### TypeScript Development

```bash
cd packages/typescript

# Build
npm run build

# Run tests
npm test

# Run tests in watch mode
npm test -- --watch

# Lint
npm run lint

# Type check
npm run type-check
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clear, concise commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass
- Follow the existing code style

### 3. Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add sliding window algorithm
fix: correct token bucket refill calculation
docs: update README with new examples
test: add tests for fixed window edge cases
chore: update dependencies
```

### 4. Submit a Pull Request

1. Push your branch to GitHub
2. Open a Pull Request against `main`
3. Fill out the PR template
4. Wait for review

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use `black` for formatting
- Use `ruff` for linting

### TypeScript

- Follow the existing style
- Use TypeScript strict mode
- Maximum line length: 100 characters
- Use Prettier for formatting (if configured)

## Testing

### Python

```python
# Test file: tests/test_feature.py
import pytest
from halt import RateLimiter, InMemoryStore, Policy

def test_feature():
    policy = Policy(name="test", limit=10, window=60)
    limiter = RateLimiter(store=InMemoryStore(), policy=policy)
    # ... test code
```

### TypeScript

```typescript
// Test file: tests/feature.test.ts
import { describe, it, expect } from 'vitest';
import { RateLimiter, InMemoryStore, Policy } from '../src';

describe('Feature', () => {
  it('should work correctly', () => {
    const policy: Policy = { name: 'test', limit: 10, window: 60 };
    const limiter = new RateLimiter({ store: new InMemoryStore(), policy });
    // ... test code
  });
});
```

## Documentation

- Update README.md if adding new features
- Add docstrings/JSDoc comments for public APIs
- Include examples for new functionality
- Update the walkthrough if making significant changes

## Release Process

Releases are automated via GitHub Actions:

1. Create a release using the "Create Release" workflow
2. This will:
   - Update version numbers in both packages
   - Create a Git tag
   - Create a GitHub release
   - Trigger publishing workflows

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
