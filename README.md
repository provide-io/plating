# 🍽️ Plating

> A sophisticated documentation generation system for Terraform/OpenTofu providers

Plating is a powerful documentation system that brings culinary elegance to technical documentation. Just as a chef carefully plates and garnishes a dish, Plating helps you present your Terraform provider documentation beautifully.

## ✨ Features

- **🎯 Automatic Documentation Generation** - Generate comprehensive docs from your provider code
- **✨ Smart Component Adorning** - Automatically create documentation templates for undocumented components
- **🍽️ Beautiful Plating** - Render documentation with examples, schemas, and rich formatting
- **🔍 Component Discovery** - Automatically find and document resources, data sources, and functions
- **📝 Jinja2 Templates** - Flexible templating with custom functions and filters
- **🔄 Schema Integration** - Extract and format provider schemas automatically

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

## 🚀 Getting Started

### Development Setup

```bash
# Clone the repository
git clone https://github.com/provide-io/plating.git
cd plating

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
uv sync
```

### Installing as a Package

```bash
# Install from PyPI
uv add plating

# Or install from source
uv add git+https://github.com/provide-io/plating.git
```

## 📚 Usage Examples

### 1. Dress Your Components

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

Each component has a `.plating` bundle:

```
my_resource.plating/
├── docs/
│   ├── my_resource.tmpl.md    # Main template
│   └── _partial.md             # Reusable partials
├── examples/
│   ├── basic.tf                # Example configurations
│   └── advanced.tf
└── fixtures/                   # Test data
    └── test_config.json
```

## 🎨 Template Functions

Plating provides powerful template functions:

- `{{ "{{ example('name') }}" }}` - Include an example file
- `{{ "{{ schema() }}" }}` - Render component schema
- `{{ "{{ partial('name') }}" }}` - Include a partial template
- `{{ "{{ anchor('text') }}" }}` - Create header anchors

## 🔍 Validation

Validate your generated documentation:

```bash
# Validate all documentation
plating validate

# Validate in custom directory
plating validate --output-dir ./documentation
```

## 🔧 Configuration

Configure Plating in your `pyproject.toml`:

```toml
[tool.plating]
provider_name = "my_provider"
output_dir = "docs"
component_types = ["resource", "data_source", "function"]
```

## 🏗️ Architecture

Plating follows a modular architecture:

- **PlatingBundle** - Represents documentation bundles
- **PlatingPlater** - Renders documentation
- **PlatingAdorner** - Creates documentation templates
- **PlatingDiscovery** - Finds components and bundles
- **SchemaProcessor** - Extracts provider schemas

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

Apache 2.0

## 🙏 Acknowledgments

Built with ❤️ using:
- [attrs](https://www.attrs.org/) - Python classes without boilerplate
- [Jinja2](https://jinja.palletsprojects.com/) - Powerful templating
- [pyvider](https://github.com/provide-io/pyvider) - Terraform provider framework
- [click](https://click.palletsprojects.com/) - Command line interface
- [rich](https://rich.readthedocs.io/) - Beautiful terminal output

---

*Plating - Making documentation as delightful as a well-plated dish* 🍽️