# 🍽️📖 Plating

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package_manager-FF6B35.svg)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![CI](https://github.com/provide-io/plating/actions/workflows/ci.yml/badge.svg)](https://github.com/provide-io/plating/actions)

**Documentation generation system for Terraform/OpenTofu providers**

Plating is a powerful documentation system that brings culinary elegance to technical documentation. Just as a chef carefully plates a dish, Plating helps you present your Terraform provider documentation beautifully.

## ✨ Key Features

- **🎯 Automatic Documentation Generation** - Generate comprehensive docs from your provider code
- **✨ Smart Component Adorning** - Automatically create documentation templates for undocumented components
- **🍽️ Beautiful Plating** - Render documentation with examples, schemas, and rich formatting
- **🔍 Component Discovery** - Automatically find and document resources, data sources, and functions
- **📝 Jinja2 Templates** - Flexible templating with custom functions and filters
- **🔄 Schema Integration** - Extract and format provider schemas automatically
- **🎯 Capability-First Organization** - Group documentation by feature (Math, Utilities, Lens) instead of just type
- **📍 Smart Navigation** - Auto-generated mkdocs.yml with capability-first structure
- **📚 Guide Support** - Built-in support for provider guides and tutorials

## Quick Start

1. Install: `uv tool install plating`
2. Read the [Documentation](https://github.com/provide-io/plating/blob/main/docs/index.md)
3. Try `plating adorn` to create documentation templates

### Installation

**Note:** Plating is in pre-release. Some documented or roadmap items are exploratory and may change or be removed.

> **Version Info:** The version `0.3.0` is a pre-release identifier indicating active development. Expect the API and features to evolve. Some documented or roadmap items are exploratory and may change or be removed.

```bash
# Install from PyPI
uv tool install plating
```

### Quick Install from Git

```bash
# Install directly from GitHub
uv tool install git+https://github.com/provide-io/plating.git
```

## Documentation
- [Documentation index](https://github.com/provide-io/plating/blob/main/docs/index.md)

## Development

### Quick Start

```bash
# Set up environment
uv sync

# Run common tasks
we test           # Run tests
we lint           # Check code
we format         # Format code
we tasks          # See all available commands
```

See [CLAUDE.md](https://github.com/provide-io/plating/blob/main/CLAUDE.md) for detailed development instructions and architecture information.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

Apache 2.0

## 📦 Prerequisites

> **Important:** This project uses `uv` for Python environment and package management.

### Install UV

Visit [UV Documentation](https://github.com/astral-sh/uv) for more information.

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pipx (if you prefer)
pipx install uv

# Update UV to latest version
uv self update
```

## 📚 Usage Examples

### 1. Adorn Your Components

First, create `.plating` bundles for your undocumented components:

```bash
# Adorn all missing components
plating adorn

# Adorn only resources
plating adorn --component-type resource
```

### 2. Customize Templates

Edit the generated templates in `.plating/docs/`:

```markdown
---
page_title: "Resource: my_resource"
---

# my_resource

{{ "{{ example('basic') }}" }}

## Schema

{{ "{{ schema() }}" }}
```

### 3. Generate Documentation

Render your documentation:

```bash
# Generate docs in ./docs directory
plating plate

# Custom output directory
plating plate --output-dir ./documentation
```

## 📂 Bundle Structure

Each component has a `.plating` bundle containing documentation templates, examples, and optional test fixtures. See [Authoring Bundles Guide](https://github.com/provide-io/plating/blob/main/docs/authoring-bundles.md) for complete bundle structure and template function reference.

## 🎯 Capability-First Organization

Organize documentation by **capability** (subcategory) instead of just by component type. Add a `subcategory` field to your template frontmatter, and Plating automatically groups components by capability in the navigation.

See [Capabilities Guide](https://github.com/provide-io/plating/blob/main/docs/capabilities.md) for standard subcategories, custom categories, and guide support.

## 🔍 Validation

Validate your generated documentation:

```bash
# Validate all documentation
plating validate

# Validate in custom directory
plating validate --output-dir ./documentation
```

## 🛡️ Foundation Integration

Plating is built on provide.foundation patterns for enterprise-grade reliability:

- **🔄 Automatic Retries**: Built-in retry policies with exponential backoff for I/O operations
- **📊 Metrics & Observability**: Integrated performance tracking and operation metrics
- **⚡ Circuit Breakers**: Prevents cascading failures in distributed systems
- **📝 Structured Logging**: Foundation logger integration with contextual information
- **🚀 Async-First Design**: High-performance async operations throughout

## 🔧 Advanced Usage

### Filter to Specific Package

By default, Plating searches all installed packages for components. You can filter to a specific package:

```bash
plating adorn --package-name pyvider.components
plating plate --package-name pyvider.components
```

### Generate Executable Examples

Generate standalone executable Terraform examples alongside documentation:

```bash
plating plate --generate-examples
```

Customize example output directories:

```bash
plating plate --generate-examples \
  --examples-dir examples/ \
  --grouped-examples-dir examples/integration/
```

## 🔧 Configuration

Configure Plating in your `pyproject.toml`:

```toml
[tool.plating]
# Provider name (auto-detected if not specified)
provider_name = "my_provider"
```

**Note:** Currently only `provider_name` can be configured in `pyproject.toml`. Other options like `output_dir` and `component_types` must be passed as CLI flags:

```bash
plating plate --output-dir docs --component-type resource
```

## 🏗️ Architecture

Plating follows a modular architecture:

- **PlatingBundle** - Represents documentation bundles
- **PlatingPlater** - Renders documentation
- **PlatingAdorner** - Creates documentation templates
- **PlatingDiscovery** - Finds components and bundles
- **SchemaProcessor** - Extracts provider schemas

## 🙏 Acknowledgments

Built with ❤️ using:
- [attrs](https://www.attrs.org/) - Python classes without boilerplate
- [Jinja2](https://jinja.palletsprojects.com/) - Powerful templating
- [pyvider](https://github.com/provide-io/pyvider) - Terraform provider framework
- [click](https://click.palletsprojects.com/) - Command line interface
- [rich](https://rich.readthedocs.io/) - Beautiful terminal output

---

*Plating - Making documentation as delightful as a well-plated dish* 🍽️

Copyright (c) provide.io LLC.
