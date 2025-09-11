---
page_title: "PlatingPlater - plating"
subcategory: "Core Components"
description: |-
  Documentation rendering engine for plating bundles.
---

# PlatingPlater

The `PlatingPlater` class is responsible for rendering plating bundles into final documentation. It processes templates, applies examples, and generates markdown output.

## Overview

The plater is the heart of the plating documentation system. It takes plating bundles as input and "plates" them into beautifully formatted documentation, much like a chef plates a dish for presentation.

## Features

- **Template Rendering**: Jinja2-based template processing
- **Example Integration**: Automatic inclusion of code examples
- **Schema Support**: Optional schema extraction and formatting
- **Partial Support**: Reusable template components
- **Custom Functions**: Extended template functions for documentation

## Usage

### Basic Plating

{{ example("basic") }}

### Plating with Schema

{{ example("with_schema") }}

### Batch Plating

{{ example("batch") }}

## Constructor

```python
PlatingPlater(
    bundles: list[PlatingBundle] | None = None,
    schema_processor: SchemaProcessor | None = None
)
```

### Parameters

- **bundles**: List of PlatingBundle objects to render
- **schema_processor**: Optional schema processor for schema extraction

## Methods

### `plate(output_dir: Path, force: bool = False)`

Renders all bundles to the specified output directory.

**Parameters:**
- **output_dir**: Directory where documentation will be written
- **force**: If True, overwrites existing files

**Example:**
```python
plater.plate(Path("./docs"), force=True)
```

## Template Functions

The plater provides several custom Jinja2 functions:

### `example(name)`
Includes an example from the bundle's examples directory.

### `schema()`
Renders the component's schema in markdown format.

### `partial(name)`
Includes a partial template from the docs directory.

## Output Structure

The plater organizes output into subdirectories:

```
docs/
├── resources/       # Resource documentation
├── data-sources/    # Data source documentation
└── functions/       # Function documentation
```

## Error Handling

The plater includes robust error handling:
- **PlatingError**: Raised when rendering fails
- **TemplateError**: Raised for template syntax errors
- Graceful handling of missing templates or examples

## Integration

The PlatingPlater integrates with:
- **SchemaProcessor**: For schema extraction
- **PlatingBundle**: For content loading
- **Template Functions**: For extended functionality

## Best Practices

1. **Force Flag**: Use `force=True` during development
2. **Schema Integration**: Include schema processor for complete docs
3. **Error Monitoring**: Check logs for plating warnings
4. **Output Validation**: Verify generated markdown syntax

## See Also

- [PlatingBundle](../plating) - Bundle structure
- [SchemaProcessor](../schema) - Schema extraction
- [Template Functions](../template_functions) - Available template functions