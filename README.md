# GavaConnect SDK for Python

A Python SDK for interacting with the GavaConnect API, providing a simple and intuitive interface for developers.

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://python.org)
[![PyPI Version](https://img.shields.io/pypi/v/gavaconnect-sdk-python)](https://pypi.org/project/gavaconnect-sdk-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Development Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://pypi.org/project/gavaconnect-sdk-python/)

## Features

- 🚀 Simple and intuitive API interface
- 🔒 Secure authentication handling
- 📦 Lightweight with minimal dependencies
- 🧪 Comprehensive test coverage
- 📖 Type hints for better development experience
- 🐍 Python 3.13+ support

## Installation

### Using pip

```bash
pip install gavaconnect-sdk-python
```

### Using uv (recommended)

```bash
uv add gavaconnect-sdk-python
```

### From source

```bash
git clone https://github.com/acoruss/gavaconnect-sdk-python.git
cd gavaconnect-sdk-python
uv install
```

## Quick Start

```python
from gavaconnect import main

# Basic usage example
main()
```

## Development

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setting up development environment

1. Clone the repository:

   ```bash
   git clone https://github.com/acoruss/gavaconnect-sdk-python.git
   cd gavaconnect-sdk-python
   ```

2. Install dependencies:

   ```bash
   uv sync --extra dev
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

### Running tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=gavaconnect

# Run tests with coverage report
uv run pytest --cov=gavaconnect --cov-report=html
```

### Code quality

This project uses several tools to maintain code quality:

- **Ruff**: Fast linting and formatting
- **mypy**: Static type checking
- **bandit**: Security linting
- **pytest**: Testing framework

```bash
# Lint code
uv run ruff check

# Format code
uv run ruff format

# Type checking
uv run mypy gavaconnect

# Security checking
uv run bandit -r gavaconnect
```

### Running the CLI

```bash
# Using uv
uv run gavaconnect-sdk-python

# Or if installed globally
gavaconnect-sdk-python
```

## Documentation

For detailed documentation, please visit our [GitHub repository](https://github.com/acoruss/gavaconnect-sdk-python#readme).

## Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for details.

### Development workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Run code quality checks
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📫 Email: acoruss+sdks@gmail.com
- 🐛 [Issue Tracker](https://github.com/acoruss/gavaconnect-sdk-python/issues)
- 💬 [Discussions](https://github.com/acoruss/gavaconnect-sdk-python/discussions)

## Authors

- **Acoruss** - _Initial work_ - [acoruss](https://github.com/acoruss)
- **Musale Martin** - _Maintainer_ - martinmshale@gmail.com

---

Made with ❤️ by the Acoruss team
