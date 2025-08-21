# Contributing to GavaConnect SDK for Python

Thank you for your interest in contributing to the GavaConnect SDK for Python! We welcome contributions from the community and are pleased to have you aboard.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)
- [Getting Help](#getting-help)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to acoruss+sdks@gmail.com.

### Our Standards

- **Be respectful**: Treat everyone with respect and kindness
- **Be inclusive**: Welcome newcomers and help them learn
- **Be collaborative**: Work together towards common goals
- **Be constructive**: Provide helpful feedback and suggestions
- **Be professional**: Maintain professional standards in all interactions

## Getting Started

### Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git
- A GitHub account

### Types of Contributions

We welcome several types of contributions:

- 🐛 **Bug Reports**: Help us identify and fix issues
- ✨ **Feature Requests**: Suggest new functionality
- 📝 **Documentation**: Improve or add documentation
- 🧪 **Tests**: Add or improve test coverage
- 🔧 **Code**: Fix bugs or implement features
- 🎨 **Design**: Improve user experience and interface

## Development Setup

1. **Fork the repository**

   ```bash
   # Fork the repo on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/gavaconnect-sdk-python.git
   cd gavaconnect-sdk-python
   ```

2. **Add upstream remote**

   ```bash
   git remote add upstream https://github.com/acoruss/gavaconnect-sdk-python.git
   ```

3. **Install dependencies**

   ```bash
   # Using uv (recommended)
   uv install --dev

   # Or using pip
   pip install -e ".[dev]"
   ```

4. **Activate the virtual environment**

   ```bash
   source .venv/bin/activate  # If using uv
   # Or activate your virtual environment if using pip
   ```

5. **Verify the setup**
   ```bash
   uv run pytest
   uv run ruff check
   uv run mypy gavaconnect
   ```

## Making Changes

### Workflow

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make your changes**

   - Write clear, concise code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**

   ```bash
   # Run all tests
   uv run pytest

   # Run with coverage
   uv run pytest --cov=gavaconnect --cov-report=html

   # Check code quality
   uv run ruff check
   uv run ruff format
   uv run mypy gavaconnect
   uv run bandit -r gavaconnect
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

### Commit Message Convention

We use conventional commits for clear and consistent commit messages:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `style:` Code style changes (formatting, etc.)
- `chore:` Maintenance tasks
- `ci:` CI/CD changes

Examples:

```
feat: add authentication support for API calls
fix: resolve connection timeout issue
docs: update installation instructions
test: add unit tests for authentication module
```

## Code Standards

### Code Style

- **Line length**: Maximum 88 characters
- **Formatting**: Use Ruff for code formatting
- **Import sorting**: Automatic with Ruff
- **Type hints**: Required for all public functions and methods

### Code Quality Tools

We use the following tools to maintain code quality:

- **Ruff**: Linting and formatting
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **pytest**: Testing framework

### Pre-commit Checks

Before submitting your changes, ensure all checks pass:

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check --fix

# Type checking
uv run mypy gavaconnect

# Security scanning
uv run bandit -r gavaconnect

# Run tests
uv run pytest --cov=gavaconnect
```

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names that explain what is being tested
- Follow the `test_*.py` naming convention
- Use pytest fixtures for common setup
- Aim for high test coverage (>90%)

### Test Categories

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_main.py

# Run tests with coverage
uv run pytest --cov=gavaconnect --cov-report=html

# Run tests in parallel (if you have pytest-xdist installed)
uv run pytest -n auto
```

## Submitting Changes

### Pull Request Process

1. **Update your branch**

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**

   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request**
   - Go to GitHub and create a pull request
   - Use a clear and descriptive title
   - Fill out the pull request template
   - Link any related issues

### Pull Request Template

When creating a pull request, please include:

- **Description**: What changes are you making and why?
- **Type of change**: Bug fix, new feature, documentation, etc.
- **Testing**: How have you tested your changes?
- **Checklist**: Confirm you've completed all required steps

### Review Process

1. **Automated checks**: All CI checks must pass
2. **Code review**: At least one maintainer will review your code
3. **Testing**: Ensure all tests pass and coverage is maintained
4. **Documentation**: Update documentation if needed
5. **Approval**: Once approved, a maintainer will merge your PR

## Release Process

Releases are managed by the maintainers and follow semantic versioning:

- **Patch** (0.0.x): Bug fixes and small improvements
- **Minor** (0.x.0): New features that are backward compatible
- **Major** (x.0.0): Breaking changes

The release process is automated using GitHub Actions and follows these steps:

1. Version bump in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a GitHub release
4. Publish to PyPI

## Getting Help

### Documentation

- Check the [README.md](README.md) for basic usage
- Review existing issues and pull requests
- Look at the code and tests for examples

### Communication

- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions or discuss ideas
- **Email**: Contact maintainers at acoruss+sdks@gmail.com

### Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [pytest Documentation](https://docs.pytest.org/)
- [uv Documentation](https://docs.astral.sh/uv/)

## Recognition

Contributors will be recognized in several ways:

- Listed in the project's contributors
- Mentioned in release notes for significant contributions
- Invited to join the maintainer team for outstanding contributors

---

Thank you for contributing to GavaConnect SDK for Python! Your efforts help make this project better for everyone. 🚀

**Questions?** Don't hesitate to ask! We're here to help you succeed.
