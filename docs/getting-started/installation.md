# Installation

Complete installation guide for Plating.

## Prerequisites

--8<-- ".provide/foundry/docs/_partials/python-requirements.md"

## Installing UV

--8<-- ".provide/foundry/docs/_partials/uv-installation.md"

## Python Version Setup

--8<-- ".provide/foundry/docs/_partials/python-version-setup.md"

## Virtual Environment

--8<-- ".provide/foundry/docs/_partials/virtual-env-setup.md"

## Installing Plating

### From Source (Current Method)

Plating is currently installed from source:

```bash
# Clone the repository
git clone https://github.com/provide-io/plating.git
cd plating

# Set up environment and install
uv sync

# Verify installation
plating --version
```

### As a Dependency (Future)

When Plating is published to PyPI, it will be installable via:

```bash
uv add plating
```

## Verification

After installation, verify everything works:

```bash
# Check Python version
python --version  # Should show 3.11+

# Verify Plating installation
plating --version

# Check CLI commands
plating --help
```

## Dependencies

Plating requires:

- **provide-foundation**: Core foundation services and component discovery
- **pyvider-cty**: Type handling for schemas
- **Jinja2**: Template engine
- **attrs**: Data class definitions
- **rich**: Terminal formatting

These are installed automatically when you run `uv sync`.

## Troubleshooting

--8<-- ".provide/foundry/docs/_partials/troubleshooting-common.md"

### Plating-Specific Issues

**Problem**: `plating: command not found`

**Solution**: Ensure the virtual environment is activated:
```bash
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

**Problem**: `ModuleNotFoundError: No module named 'provide.foundation.hub'`

**Solution**: Ensure all dependencies are installed:
```bash
uv sync --extra all
```

**Problem**: Template rendering fails

**Solution**: Check that pyvider components are installed and discoverable:
```bash
# Check component discovery
python -c "from provide.foundation.hub import get_hub; hub = get_hub(); print(hub.list_providers())"
```

## Next Steps

After installation:

1. **[Quick Start](../quick-start.md)** - 5-minute guide to using Plating
2. **[Getting Started Guide](index.md)** - Comprehensive tutorial
3. **[Authoring Bundles](../authoring-bundles.md)** - Create custom documentation templates
