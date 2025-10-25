# Quick Start Guide

Get up and running with Plating in 5 minutes.

## Installation

Plating requires Python 3.11+ and uses UV for package management.

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Plating
git clone https://github.com/provide-io/plating.git
cd plating
uv sync
```

## Basic Usage

Plating follows a simple three-step workflow:

### 1. Adorn - Create Templates

Generate documentation templates for components that don't have them:

```bash
plating adorn --provider-name my_provider
```

This creates `.plating` bundles with template files for your components.

### 2. Plate - Generate Documentation

Transform templates into Terraform Registry-compliant documentation:

```bash
plating plate --output-dir docs/
```

### 3. Validate - Check Quality

Ensure generated documentation meets standards:

```bash
plating validate --output-dir docs/
```

## Python API Example

```python
import asyncio
from pathlib import Path
from plating import Plating, PlatingContext
from plating.types import ComponentType

async def generate_docs():
    # Initialize with context
    context = PlatingContext(
        provider_name="my_provider",
        log_level="INFO"
    )

    # Create API instance
    api = Plating(context, package_name="pyvider.components")

    # Step 1: Create templates for missing documentation
    adorn_result = await api.adorn(
        component_types=[ComponentType.RESOURCE]
    )
    print(f"✅ Created {adorn_result.templates_generated} templates")

    # Step 2: Generate documentation (with automatic validation)
    plate_result = await api.plate(
        output_dir=Path("docs"),
        validate_markdown=True  # Validates during generation
    )
    print(f"📄 Generated {plate_result.files_generated} files")

    # Optional: Run standalone validation if needed
    # validate_result = await api.validate(output_dir=Path("docs"))
    # print(f"✓ Validation: {validate_result.passed}/{validate_result.total} passed")

    return plate_result.success

# Run the async function
if __name__ == "__main__":
    success = asyncio.run(generate_docs())
    exit(0 if success else 1)
```

## Bundle Structure

Each component gets a `.plating` bundle:

```
my_resource.plating/
├── docs/
│   └── my_resource.tmpl.md    # Documentation template
├── examples/
│   └── basic.tf                # Usage examples
└── fixtures/
    └── data.json               # Test data (optional)
```

## Template Functions

In your `.tmpl.md` files, use these built-in functions:

```markdown
# my_resource

{{ example("basic") }}        <!-- Include examples/basic.tf -->

## Schema

{{ schema() }}                <!-- Generate schema table -->
```

## Next Steps

- [Author bundles](authoring-bundles.md) - Create custom documentation
- [CLI reference](cli-reference.md) - All command options
- [Complete examples](examples.md) - Real-world usage patterns
- [API reference](api-reference.md) - Full API documentation

## Common Commands

```bash
# Adorn specific component types
plating adorn --component-type resource --component-type data_source

# Generate with validation
plating plate --validate --force

# Filter to specific package
plating adorn --package-name pyvider.aws

# Show registry statistics
plating stats
```