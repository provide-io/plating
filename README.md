# 🍲 Garnish

> A sophisticated documentation generation system for Terraform/OpenTofu providers

Garnish is a powerful documentation system that brings culinary elegance to technical documentation. Just as a chef carefully plates and garnishes a dish, Garnish helps you present your Terraform provider documentation beautifully.

## ✨ Features

- **🎯 Automatic Documentation Generation** - Generate comprehensive docs from your provider code
- **👗 Smart Component Dressing** - Automatically create documentation templates for undocumented components
- **🍽️ Beautiful Plating** - Render documentation with examples, schemas, and rich formatting
- **🔍 Component Discovery** - Automatically find and document resources, data sources, and functions
- **📝 Jinja2 Templates** - Flexible templating with custom functions and filters
- **🔄 Schema Integration** - Extract and format provider schemas automatically

## 📦 Installation

```bash
# Using pip
pip install garnish

# Using uv (recommended)
uv add garnish
```

## 🚀 Quick Start

### 1. Dress Your Components

First, create `.garnish` bundles for your undocumented components:

```bash
# Dress all missing components
garnish dress

# Dress only resources
garnish dress --component-type resource
```

### 2. Customize Templates

Edit the generated templates in `.garnish/docs/`:

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
garnish plate

# Custom output directory
garnish plate --output-dir ./documentation
```

## 📂 Bundle Structure

Each component has a `.garnish` bundle:

```
my_resource.garnish/
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

Garnish provides powerful template functions:

- `{{ "{{ example('name') }}" }}` - Include an example file
- `{{ "{{ schema() }}" }}` - Render component schema
- `{{ "{{ partial('name') }}" }}` - Include a partial template
- `{{ "{{ anchor('text') }}" }}` - Create header anchors

## 🧪 Testing

Test your examples with the built-in test runner:

```bash
# Test all examples
garnish test

# Test specific component types
garnish test --component-type resource
```

## 🔧 Configuration

Configure Garnish in your `pyproject.toml`:

```toml
[tool.garnish]
provider_name = "my_provider"
output_dir = "docs"
component_types = ["resource", "data_source", "function"]
```

## 🏗️ Architecture

Garnish follows a modular architecture:

- **GarnishBundle** - Represents documentation bundles
- **GarnishPlater** - Renders documentation
- **GarnishDresser** - Creates documentation templates
- **GarnishDiscovery** - Finds components and bundles
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

*Garnish - Making documentation as delightful as a well-plated dish* 🍽️