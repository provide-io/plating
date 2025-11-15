---
page_title: "GarnishBundle - garnish"
subcategory: "Core Components"
description: |-
  Core bundle abstraction for garnish documentation system.
---

# GarnishBundle

The `GarnishBundle` class represents a single `.garnish` directory containing documentation templates, examples, and fixtures for a component.

## Overview

A garnish bundle is the fundamental unit of documentation in the garnish system. Each bundle corresponds to a single component (resource, data source, or function) and contains all the assets needed to generate its documentation.

## Bundle Structure

```
component_name.garnish/
├── docs/
│   ├── component_name.tmpl.md  # Main template
│   └── _partial.md              # Optional partials
├── examples/
│   ├── basic.tf                 # Example configurations
│   └── advanced.tf
└── fixtures/                    # Optional test fixtures
    └── test_data.json
```

## Usage

### Creating a Bundle

```python
from pathlib import Path
from garnish.garnish import GarnishBundle

# Create a bundle for a resource component
bundle = GarnishBundle(
    name="s3_bucket",
    garnish_dir=Path("./resources/s3_bucket.garnish"),
    component_type="resource"
)

# Access bundle properties
print(f"Bundle name: {bundle.name}")
print(f"Docs directory: {bundle.docs_dir}")
print(f"Component type: {bundle.component_type}")
```

### Loading Bundle Assets

```python
# Load the main template
template = bundle.load_main_template()
if template:
    print(f"Template loaded: {len(template)} characters")

# Load all examples
examples = bundle.load_examples()
for name, content in examples.items():
    print(f"Example '{name}': {len(content)} characters")

# Load partials for template inclusion
partials = bundle.load_partials()
print(f"Found {len(partials)} partials")
```

### Using with Plater

```python
from garnish.plater import GarnishPlater

# Create bundles manually or via discovery
bundles = [bundle]

# Plate the documentation
plater = GarnishPlater(bundles=bundles)
output_dir = Path("./docs")
plater.plate(output_dir, force=True)

print(f"Documentation generated in {output_dir}")
```

## Properties

### `docs_dir`
Returns the path to the documentation directory within the bundle.

### `examples_dir`
Returns the path to the examples directory within the bundle.

### `fixtures_dir`
Returns the path to the fixtures directory within the bundle.

## Methods

### `load_main_template()`
Loads the main template file from the docs directory.

**Returns:** Template content as string, or `None` if not found.

### `load_examples()`
Loads all example files from the examples directory.

**Returns:** Dictionary mapping example names to their content.

### `load_fixtures()`
Loads all fixture files from the fixtures directory.

**Returns:** Dictionary mapping fixture paths to their content.

### `load_partials()`
Loads all partial templates from the docs directory.

**Returns:** Dictionary mapping partial names to their content.

## Attributes

- **name** (`str`): The name of the component
- **garnish_dir** (`Path`): Path to the .garnish directory
- **component_type** (`str`): Type of component ("resource", "data_source", or "function")

## Best Practices

1. **Naming Convention**: Bundle directories should be named `{component_name}.garnish`
2. **Template Organization**: Keep the main template focused; use partials for reusable content
3. **Example Quality**: Provide both basic and advanced examples
4. **Documentation Style**: Follow Terraform registry documentation conventions

## Integration

The GarnishBundle integrates with:
- **GarnishDiscovery**: For automatic bundle discovery
- **GarnishPlater**: For rendering documentation
- **GarnishDresser**: For creating new bundles

## See Also

- [GarnishPlater](../plater) - Documentation rendering
- [GarnishDiscovery](../discovery) - Bundle discovery
- [GarnishDresser](../dresser) - Bundle creation