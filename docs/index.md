# Plating Documentation

Welcome to Plating - A sophisticated documentation generation system for Terraform/OpenTofu providers.

## Features

Plating provides:

- **Automatic Documentation Generation**: Generate comprehensive docs from your provider code
- **Smart Component Adorning**: Automatically create documentation templates for undocumented components
- **Beautiful Plating**: Render documentation with examples, schemas, and rich formatting
- **Component Discovery**: Automatically find and document resources, data sources, and functions
- **Jinja2 Templates**: Flexible templating with custom functions and filters
- **Schema Integration**: Extract and format provider schemas automatically

## Quick Start

### Installation

**Note:** Plating is currently in pre-release (v0.0.1000-0). Install from source:

<div class="termy">

```console
$ git clone https://github.com/provide-io/plating.git
$ cd plating
$ uv sync
// Installing dependencies...
Successfully installed plating

$ plating --help
Plating - Modern async documentation generator
```

</div>

**Coming soon to PyPI:** `uv add plating`

### Adorn Components with Templates

Create `.plating` bundles for your undocumented components:

<div class="termy">

```console
$ plating adorn --component-type resource
// Discovering components...
🎨 Adorning 5 component types...
📦 Processing 10 resource(s)...
✅ Generated 8 templates
📦 Processed 10 components
```

</div>

### Generate Documentation

Render your documentation from templates:

<div class="termy">

```console
$ plating plate --output-dir docs/
// Discovering plating bundles...
🍽️ Plating documentation...
✅ Generated 10 files in 0.52s
📦 Processed 10 bundles
📄 Generated files:
  • docs/resources/example_resource.md
  • docs/data-sources/example_data.md
  • docs/functions/example_function.md
  ... and 7 more
```

</div>

### Validate Documentation

Validate your generated documentation:

<div class="termy">

```console
$ plating validate --output-dir docs/
// Validating documentation in docs/...
📊 Validation results:
  • Total files: 10
  • Passed: 10
  • Failed: 0
  • Duration: 0.23s
✅ All validations passed
```

</div>

### Python API Usage

```python
from plating import Plating, PlatingContext
from plating.types import ComponentType
from pathlib import Path

# Initialize plating API
context = PlatingContext(provider_name="my_provider")
api = Plating(context, package_name="pyvider.components")

# Adorn components with templates
result = await api.adorn(component_types=[ComponentType.RESOURCE])
print(f"Generated {result.templates_generated} templates")

# Plate documentation
result = await api.plate(output_dir=Path("docs"))
print(f"Generated {result.files_generated} files")
```

## API Reference

For complete API documentation, see the [API Reference](api/index.md).

## Component Types

- **Resources**: Terraform resources (e.g., `aws_s3_bucket`)
- **Data Sources**: Terraform data sources (e.g., `aws_ami`)
- **Functions**: Provider functions (e.g., `timestamp()`)
- **Providers**: Provider configuration documentation