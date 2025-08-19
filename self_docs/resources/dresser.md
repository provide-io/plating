---
page_title: "GarnishDresser - garnish"
subcategory: "Core Components"
description: |-
  Automatic .garnish bundle creation for components.
---

# GarnishDresser

The `GarnishDresser` class automatically creates `.garnish` directories for components that don't have documentation yet. It "dresses" components with the necessary bundle structure.

## Overview

The dresser automates the creation of garnish bundles by:
1. Discovering components via pyvider hub
2. Finding components without existing bundles
3. Generating template documentation based on component metadata
4. Creating example Terraform configurations

## Features

- **Automatic Discovery**: Finds undocumented components
- **Template Generation**: Creates documentation templates from docstrings
- **Example Creation**: Generates basic Terraform examples
- **Batch Processing**: Dresses multiple components at once
- **Component Filtering**: Focus on specific component types

## Usage

### Dress Missing Components



### Dress Specific Component Types



### Manual Component Dressing



## Methods

### `dress_missing(component_types: list[str] = None)`

Discovers and dresses all components without existing bundles.

**Parameters:**
- **component_types**: Optional list of types to process ("resource", "data_source", "function")

**Returns:** Dictionary with counts of dressed components by type

**Example:**
```python
results = await dresser.dress_missing(["resource"])
print(f"Dressed {results['resource']} resources")
```

## Generated Structure

For each component, the dresser creates:

```
component_name.garnish/
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

The GarnishDresser integrates with:
- **ComponentDiscovery**: For finding components
- **GarnishDiscovery**: For checking existing bundles
- **TemplateGenerator**: For creating content
- **ComponentFinder**: For locating source files

## CLI Usage

The dresser is available via CLI:

```bash
# Dress all missing components
garnish dress

# Dress only resources
garnish dress --component-type resource

# Dress multiple types
garnish dress --component-type resource --component-type data_source
```

## Best Practices

1. **Review Generated Content**: Templates are starting points
2. **Enhance Examples**: Add real-world scenarios
3. **Document Edge Cases**: Include important warnings
4. **Maintain Consistency**: Follow documentation standards

## Error Handling

The dresser handles:
- Missing source files gracefully
- Invalid component types
- File system errors
- Component discovery failures

## See Also

- [TemplateGenerator](../templates) - Template creation
- [ComponentFinder](../finder) - Source file location
- [GarnishBundle](../garnish) - Bundle structure