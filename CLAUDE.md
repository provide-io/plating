# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Plating is a documentation generation system for Terraform/OpenTofu providers that was extracted from the tofusoup project. It automatically generates Terraform Registry-compliant documentation by discovering components via pyvider.hub and processing Jinja2 templates.

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
uv sync --extra dev
# Or for editable install:
uv pip install -e ".[dev]"
```

### Running Tests
```bash
pytest tests                  # Run all tests
pytest tests/test_cli.py      # Run specific test file
pytest -k test_scaffold       # Run tests matching pattern
pytest -xvs                   # Stop on first failure, verbose output
```

### Code Quality
```bash
ruff format src/plating tests    # Format code
ruff check src/plating tests     # Check linting
mypy src/plating                 # Type checking
```

## Architecture

### Core Components

**PlatingBundle System** (`plating.py`)
- Central abstraction representing a `.plating` directory containing documentation assets
- Each bundle maps to a provider component (resource, data_source, or function)
- Structure: `component_name.plating/` with `docs/` (templates) and `examples/` (Terraform files)

**Discovery System** (`plating.py:PlatingDiscovery`)
- Searches installed packages for `.plating` directories
- Uses `pyvider.hub` for component discovery (hard dependency)
- Supports multi-component bundles (subdirectories within .plating)

**Template Processing** (`async_renderer.py`, `templates.py`)
- Async rendering pipeline using Jinja2
- Custom template functions: `schema()`, `example()`, `include()`, `render()`
- Processes provider schema from pyvider components
- Two renderer implementations: async (primary) and sync (backward compatibility)

**Schema Extraction** (`schema.py`)
- Extracts provider schemas via pyvider.hub component discovery
- Converts component schemas to markdown documentation
- Handles resources, data sources, and functions differently

**Test Runner** (`test_runner.py`)
- Simplified version without tofusoup's stir dependency
- Executes terraform init/apply/destroy on example files
- Sequential execution (no parallel support after stir removal)

### Key Design Patterns

1. **Absolute Imports**: All imports use `from plating.X import Y` (no relative imports)

2. **Attrs for Data Classes**: Uses `@attrs.define` instead of dataclasses

3. **Pyvider Integration**: 
   - Depends on pyvider.hub for component discovery
   - Uses pyvider.telemetry for logging
   - Requires pyvider-cty and pyvider-hcl

4. **Async-First Design**: Primary renderer is async with sync adapter for compatibility

## Important Dependencies

- **pyvider.hub**: Component discovery (cannot be removed without major refactoring)
- **pyvider.telemetry**: Logging system (kept from tofusoup)
- **attrs**: Data class definitions (design choice, not dataclasses)
- **Jinja2**: Template engine
- **rich**: Terminal UI output

## Common Development Tasks

### Adding New Template Functions
1. Add function to `template_functions.py`
2. Register in `TemplateEngine` class
3. Update `async_renderer.py` to include in env.globals

### Testing Plating Commands
```bash
# Test without installation
python -m plating.cli --help
python -m plating.cli scaffold --component-type resource
python -m plating.cli render --output-dir docs
```

### Working with Sibling Packages
If pyvider packages are in sibling directories:
```bash
uv pip install -e ../pyvider-components
uv pip install -e ../pyvider-telemetry
# etc.
```

## Testing Philosophy

- CLI tests mock the underlying functions (scaffold_plating, generate_docs)
- No integration tests for actual Terraform execution after stir removal
- Focus on unit testing individual components

## Known Limitations

1. Test runner is simplified - no parallel execution or rich UI (was dependent on tofusoup.stir)
2. Tightly coupled to pyvider ecosystem for component discovery
3. No plugin system for alternative schema extractors