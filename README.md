# Garnish

Documentation generation system for Terraform/OpenTofu providers.

## Overview

Garnish is a comprehensive documentation generation tool that automatically creates Terraform Registry-compliant documentation from provider code. It discovers components via pyvider.hub, processes templates and examples, and generates professional documentation.

## Features

- 🔍 **Automatic Discovery**: Discovers resources, data sources, and functions via pyvider.hub
- 📝 **Template Processing**: Supports Jinja2 templates with custom functions and filters
- 🏗️ **Scaffolding**: Automatically creates missing `.garnish` directories and templates
- 🧪 **Example Testing**: Tests Terraform examples to ensure they work
- 🎨 **Rich Output**: Beautiful terminal output using the rich library
- 📦 **Bundle System**: Organizes documentation assets in `.garnish` bundles

## Installation

```bash
pip install -e .
```

Or with development dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

### Generate Documentation

```bash
# Render documentation to the docs directory
garnish render

# Specify a custom output directory
garnish render --output-dir /path/to/docs

# Force generation even if not in a provider directory
garnish render --force
```

### Scaffold Missing Documentation

```bash
# Scaffold all missing .garnish directories
garnish scaffold

# Scaffold only specific component types
garnish scaffold --component-type resource
garnish scaffold --component-type data_source --component-type function
```

### Test Examples

```bash
# Run tests on all example files
garnish test

# Test specific component types
garnish test --component-type resource

# Output test results to a file
garnish test --output-file results.json --output-format json
```

## Project Structure

Garnish expects the following structure in your provider project:

```
your-provider/
├── src/
│   └── your_provider/
│       ├── resources/
│       │   └── example_resource.garnish/
│       │       ├── docs/
│       │       │   └── example_resource.tmpl.md
│       │       └── examples/
│       │           └── example.tf
│       ├── data_sources/
│       │   └── example_data.garnish/
│       │       ├── docs/
│       │       │   └── example_data.tmpl.md
│       │       └── examples/
│       │           └── example.tf
│       └── functions/
│           └── example_function.garnish/
│               ├── docs/
│               │   └── example_function.tmpl.md
│               └── examples/
│                   └── example.tf
└── docs/  # Generated documentation goes here
```

## Template System

Garnish uses Jinja2 templates with custom functions:

- `{{ schema() }}` - Inserts the component's schema documentation
- `{{ example("filename") }}` - Inserts an example from the examples directory
- `{{ include("partial.md") }}` - Includes a partial template

Example template:

```markdown
---
page_title: "Resource: {{ name }}"
description: |-
  {{ description }}
---

# {{ name }} (Resource)

{{ description }}

## Example Usage

{{ example("example") }}

## Schema

{{ schema() }}
```

## Configuration

Garnish uses pyvider components for discovery and schema extraction. Ensure your provider is properly configured with pyvider.

## Note

This project was extracted from the tofusoup project. For advanced test execution with rich UI and parallel testing, consider using tofusoup's test runner.

## License

Apache-2.0

## Contributing

Contributions are welcome! Please ensure all tests pass and code is formatted with ruff.

```bash
# Format code
ruff format src/garnish tests

# Check linting
ruff check src/garnish tests

# Run tests
pytest tests
```