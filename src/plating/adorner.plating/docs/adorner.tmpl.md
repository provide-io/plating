---
page_title: "PlatingAdorner - plating"
subcategory: "Core Components"
description: |-
  Automatic .plating bundle creation for components.
---

# PlatingAdorner

The `PlatingAdorner` class automatically creates `.plating` directories for components that don't have documentation yet. It "adorns" components with the necessary bundle structure.

## Overview

The adorner automates the creation of plating bundles by:
1. Discovering components via pyvider hub
2. Finding components without existing bundles
3. Generating template documentation based on component metadata
4. Creating example Terraform configurations

## Features

- **Automatic Discovery**: Finds undocumented components
- **Template Generation**: Creates documentation templates from docstrings
- **Example Creation**: Generates basic Terraform examples
- **Batch Processing**: Adorns multiple components at once
- **Component Filtering**: Focus on specific component types

## Usage

### Adorn Missing Components

{{ example("basic") }}

### Adorn Specific Component Types

{{ example("filtered") }}

### Manual Component Adorning

{{ example("manual") }}

## Methods

### `adorn_missing(component_types: list[str] = None)`

Discovers and adorns all components without existing bundles.

**Parameters:**
- **component_types**: Optional list of types to process ("resource", "data_source", "function")

**Returns:** Dictionary with counts of adorned components by type

**Example:**
```python
results = await adorner.adorn_missing(["resource"])
print(f"Adorned {results['resource']} resources")
```

## Generated Structure

For each component, the adorner creates:

```
component_name.plating/
├── docs/
│   └── component_name.tmpl.md  # Generated template
└── examples/
    └── example.tf               # Basic example
```

## Template Generation

Templates are generated with:
- Component description from docstring
- Appropriate frontmatter
- Standard sections (Example Usage, Arguments, Attributes)
- Terraform import instructions (for resources)
- Schema placeholder

## Example Generation

Examples include:
- Basic resource/data source configuration
- Common required arguments
- Output declarations
- Best practice patterns

## Integration

The PlatingAdorner integrates with:
- **ComponentDiscovery**: For finding components
- **PlatingDiscovery**: For checking existing bundles
- **TemplateGenerator**: For creating content
- **ComponentFinder**: For locating source files

## CLI Usage

The adorner is available via CLI:

```bash
# Adorn all missing components
plating adorn

# Adorn only resources
plating adorn --component-type resource

# Adorn multiple types
plating adorn --component-type resource --component-type data_source
```

## Best Practices

1. **Review Generated Content**: Templates are starting points
2. **Enhance Examples**: Add real-world scenarios
3. **Document Edge Cases**: Include important warnings
4. **Maintain Consistency**: Follow documentation standards

## Error Handling

The adorner handles:
- Missing source files gracefully
- Invalid component types
- File system errors
- Component discovery failures

## See Also

- [TemplateGenerator](../templates) - Template creation
- [ComponentFinder](../finder) - Source file location
- [PlatingBundle](../plating) - Bundle structure