# 🍲 Plating

> A sophisticated documentation generation system for Terraform/OpenTofu providers

Plating is a powerful documentation system that brings culinary elegance to technical documentation. Just as a chef carefully plates a dish, Plating helps you present your Terraform provider documentation beautifully.

## ✨ Features

- **🎯 Automatic Documentation Generation** - Generate comprehensive docs from your provider code
- **✨ Smart Component Adorning** - Automatically create documentation templates for undocumented components
- **🍽️ Beautiful Plating** - Render documentation with examples, schemas, and rich formatting
- **🔍 Component Discovery** - Automatically find and document resources, data sources, and functions
- **📝 Jinja2 Templates** - Flexible templating with custom functions and filters
- **🔄 Schema Integration** - Extract and format provider schemas automatically

## 📦 Installation

**Note:** Plating is in pre-release (v0.3.0). Some documented or roadmap items are exploratory and may change or be removed.

```bash
# Install from PyPI
uv tool install plating
```

**From source (for local changes):**
```bash
git clone https://github.com/provide-io/plating.git
cd plating
uv sync
```

## 🚀 Quick Start

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

Describe your resource here.

## Example Usage

\```terraform
resource "my_provider_my_resource" "example" {
  name = "example"
}
\```

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
│   └── _partial.md             # Reusable partials (optional)
└── examples/
    ├── basic.tf                # Example configurations
    └── advanced.tf             # (optional)
```

**Note:** The `examples/` directory can contain `.tf` files (for resources/data sources) or `.py` files (for Python API examples).

## 🎨 Template Functions

Plating provides powerful template functions:

- `{{ "{{ schema() }}" }}` - Render component schema as markdown table
- `{{ "{{ example('name') }}" }}` - Include an example file in a terraform code block
- `{{ "{{ include('filename') }}" }}` - Include a static partial file
- `{{ "{{ render('filename') }}" }}` - Render a dynamic template partial with current context

## ✅ Validation

Validate your generated documentation:

```bash
# Validate all documentation
plating validate

# Validate specific component types
plating validate --component-type resource
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
