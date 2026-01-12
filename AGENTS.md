# AGENTS.md

This file provides guidance for AI assistants when working with code in this repository.

## Project Overview

Plating is a documentation generation system for Terraform/OpenTofu providers. It automatically generates Terraform Registry-compliant documentation by discovering components via pyvider.hub and processing Jinja2 templates.

## Development Setup

### Environment Setup
```bash
# Clone the repository (if not already done)
git clone https://github.com/provide-io/plating.git
cd plating

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies with dev extras
uv sync --all-groups
# Or for editable install:
uv pip install -e ".[dev]"
```

### Running Tests
```bash
uv run pytest tests                  # Run all tests
uv run pytest tests/test_cli.py      # Run specific test file
uv run pytest -k test_adorn          # Run tests matching pattern
uv run pytest -xvs                   # Stop on first failure, verbose output
```

### Code Quality
```bash
uv run ruff format src/plating tests    # Format code
uv run ruff check src/plating tests     # Check linting
uv run mypy src/plating                 # Type checking
```

## Architecture

### Core Components

**PlatingBundle System** (`plating.py`)
- Central abstraction representing a `.plating` directory containing documentation assets
- Each bundle maps to a provider component (resource, data_source, or function)
- Structure: `component_name.plating/` with `docs/` (templates) and `examples/` (Terraform files)

**Discovery System** (`plating.py:PlatingDiscovery`)
- Searches installed packages for `.plating` directories
- Uses `provide.foundation.hub` for component discovery
- Supports multi-component bundles (subdirectories within .plating)

**Template Processing** (`templating/engine.py`)
- Async-only rendering pipeline using Jinja2
- Custom template functions: `schema()`, `example()`, `include()`, `render()`
- Processes provider schema from foundation hub component discovery
- Uses `run_in_executor` for blocking file I/O operations

**Schema Extraction** (`schema/processor.py`)
- Extracts provider schemas via foundation.hub component discovery
- Converts component schemas to markdown documentation
- Handles resources, data sources, and functions differently

**Test Runner** (`test_runner.py`)
- Executes terraform init/apply/destroy on example files
- Sequential execution only

### Key Design Patterns

1. **Absolute Imports**: All imports use `from plating.X import Y` (no relative imports)

2. **Attrs for Data Classes**: Uses `@attrs.define` instead of dataclasses

3. **Foundation Integration**:
   - Uses `provide.foundation.hub` for component discovery
   - Uses `provide.foundation` for logging (`pout`, `perr`, `logger`)
   - Requires pyvider-cty for type handling

4. **Async-Only Design**: All rendering and I/O operations are async
   - Uses `asyncio.to_thread()` and `run_in_executor()` for blocking file operations
   - No synchronous API - async is the only supported interface

## Important Dependencies

- **provide.foundation**: Core foundation services
  - `foundation.hub`: Component discovery and registry
  - `foundation` output functions: `pout`, `perr`, `logger`
  - Resilience patterns: retry, circuit breaker, metrics
- **pyvider-cty**: Type handling for Terraform/OpenTofu schemas
- **attrs**: Data class definitions (design choice, not dataclasses)
- **Jinja2**: Template engine for documentation rendering
- **rich**: Terminal UI formatting (via foundation)

## Common Development Tasks

### Adding New Template Functions
1. Add function to `template_functions.py`
2. Register in `TemplateEngine` class
3. Update `async_renderer.py` to include in env.globals

### Testing Plating Commands
```bash
# Test without installation
python -m plating.cli --help
python -m plating.cli adorn --component-type resource
python -m plating.cli plate --output-dir docs
```

### Working with Sibling Packages
If pyvider packages are in sibling directories:
```bash
uv pip install -e ../pyvider-components
uv pip install -e ../pyvider-telemetry
# etc.
```

## Testing Philosophy

- CLI tests mock the underlying functions
- Focus on unit testing individual components
- Integration tests use mocked dependencies

## Known Limitations

1. Test runner supports sequential execution only - no parallel execution
2. Tightly coupled to pyvider ecosystem for component discovery
3. No plugin system for alternative schema extractors
