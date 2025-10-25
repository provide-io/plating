# Contributing to Plating

Thank you for your interest in contributing to Plating! This document provides guidelines and instructions for contributors.

## Development Setup

### Prerequisites

Plating uses [UV](https://github.com/astral-sh/uv) for Python environment and package management.

#### Install UV

**macOS and Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Getting Started

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/provide-io/plating.git
   cd plating
   ```

2. **Set up development environment:**
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # or .venv\Scripts\activate  # Windows
   uv sync --dev
   ```

3. **Verify installation:**
   ```bash
   python -m plating.cli --help
   pytest tests/ -v

   # Note: 2 tests may be skipped if optional dependencies are not installed
   # This is expected behavior and not a problem
   ```

## Development Workflow

### Code Quality

We maintain high code quality standards with automated tools:

```bash
# Format code
ruff format src/plating tests

# Check linting
ruff check src/plating tests

# Type checking
mypy src/plating

# Run all quality checks
uv run pytest tests/
```

### Code Style Guidelines

- **Python Version:** 3.11+
- **Line Length:** 111 characters
- **Type Hints:** Modern typing (`dict`, `list`, `set` instead of `Dict`, `List`, `Set`)
- **Import Style:** Absolute imports (`from plating.X import Y`)
- **No Hardcoded Defaults:** Use `defaults.py` or `constants.py` for configuration values

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_cli.py

# Run with coverage
pytest tests/ --cov=plating --cov-report=html

# Run tests matching pattern
pytest -k test_adorn
```

### Architecture Guidelines

1. **PlatingBundle System:** Core abstraction for `.plating` directories
2. **Async-First Design:** Primary renderer is async with sync adapters
3. **Attrs for Data Classes:** Use `@attrs.define` instead of `@dataclass`
4. **Pyvider Integration:** Leverage hub for component discovery
5. **Error Handling:** Use `provide.foundation` patterns

## Contributing Process

### 1. Issue Discussion

- Check existing issues before creating new ones
- Discuss significant changes in issues before implementing
- Use issue templates when available

### 2. Development

- Create feature branches from `develop`
- Follow code style guidelines
- Add tests for new functionality
- Update documentation as needed

### 3. Pull Request

- **Target Branch:** `develop` (not `main`)
- **Title Format:** `feat: add component discovery caching` or `fix: handle missing schema gracefully`
- **Description:** Include issue reference, change summary, and testing notes

### 4. Review Process

- All PRs require review before merging
- Address reviewer feedback promptly  
- Ensure CI checks pass
- Maintain clean commit history

## Key Components

### Core Modules

- **`plating.py`:** Main Plating API class with adorn/plate/validate operations
- **`cli.py`:** Command-line interface
- **`registry.py`:** Component registry and bundle management
- **`adorner/`:** Component template generation system
- **`core/`:** Core documentation generation logic
- **`schema/`:** Schema extraction and processing
- **`templating/`:** Jinja2 template engine and functions
- **`discovery/`:** Bundle and component discovery
- **`types.py`:** Type definitions and data models
- **`errors.py`:** Custom exception classes

### Template System

- **Jinja2 Templates:** Located in `.plating/docs/` directories
- **Custom Functions:** `schema()`, `example()`, `include()`, `render()`
- **Partials:** Files starting with `_` for reusable content

### Testing Strategy

- **Unit Tests:** Individual component testing
- **Integration Tests:** End-to-end workflow validation
- **CLI Tests:** Command-line interface testing
- **Mock Strategy:** Mock pyvider.hub for isolated testing

## Documentation

### Code Documentation

- **Docstrings:** All public functions and classes
- **Type Hints:** Complete type annotations
- **Examples:** Include usage examples in docstrings

### User Documentation

- Update README.md for user-facing changes
- Include code examples in documentation
- Maintain CHANGELOG.md with all changes

## Release Process

1. **Version Bump:** Update `VERSION` file
2. **Changelog:** Update `CHANGELOG.md` with release notes
3. **Testing:** Run full test suite
4. **Tag Release:** Create version tag
5. **PyPI Upload:** Automated via CI/CD

## Getting Help

- **GitHub Issues:** Bug reports and feature requests
- **Discussions:** General questions and ideas
- **Code Review:** PR feedback and suggestions

## License

By contributing to Plating, you agree that your contributions will be licensed under the Apache 2.0 License.

## Recognition

Contributors are recognized in:
- CHANGELOG.md for significant contributions
- GitHub contributors page
- Release notes for major features

Thank you for contributing to Plating! 🍽️