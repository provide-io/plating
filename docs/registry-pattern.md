# Registry Pattern

Plating uses a registry-based architecture for component discovery and management. This document explains how the registry works and how to interact with it.

## Overview

The PlatingRegistry is a centralized catalog of all components and their documentation bundles. It integrates with foundation's component discovery system to automatically find and register components.

## Architecture

```
PlatingRegistry
├── Component Discovery (via foundation.hub)
├── Bundle Registration (.plating directories)
├── Component Metadata (type, path, schema)
└── Statistics & Queries
```

## How It Works

### 1. Automatic Discovery

When you create a Plating instance, it automatically discovers components:

```python
from plating import Plating, PlatingContext

context = PlatingContext(provider_name="my_provider")
api = Plating(context, package_name="pyvider.components")

# Registry is automatically populated with discovered components
```

### 2. Component Registration

Components are registered by type and name:

```python
# Internal registration happens automatically
registry.register(
    name="my_resource",
    dimension="resource",  # or "data_source", "function", "provider"
    value=bundle_entry
)
```

### 3. Component Queries

The registry provides methods to query components:

```python
# Get all resources
resources = api.registry.get_components(ComponentType.RESOURCE)

# Get specific component
resource = api.registry.get_component(
    ComponentType.RESOURCE,
    "my_resource"
)

# Get components with templates
documented = api.registry.get_components_with_templates(
    ComponentType.RESOURCE
)
```

## Registry Statistics

Get insights into your provider's documentation:

```python
# Via API
stats = await api.get_registry_stats()

# Stats include:
# - Total components by type
# - Documentation coverage
# - Bundle statistics
```

CLI command:

```bash
plating stats --package-name pyvider.components
```

Example output:
```
📊 Registry Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provider: my_provider
Package: pyvider.components

Components:
  Resources:     15 (12 documented)
  Data Sources:  8  (8 documented)
  Functions:     5  (3 documented)

Coverage: 80% (23/28)
```

## Component Types

The registry organizes components into dimensions:

| Type | Dimension | Directory | Description |
|------|-----------|-----------|-------------|
| `ComponentType.RESOURCE` | "resource" | `resources/` | Terraform resources |
| `ComponentType.DATA_SOURCE` | "data_source" | `data-sources/` | Data sources |
| `ComponentType.FUNCTION` | "function" | `functions/` | Provider functions |
| `ComponentType.PROVIDER` | "provider" | `providers/` | Provider config |

## Bundle Discovery

The registry finds `.plating` bundles in installed packages:

```python
# Search pattern for bundles
package_name/
├── resources/
│   ├── my_resource.py
│   └── my_resource.plating/    # Discovered
├── data_sources/
│   └── my_data.plating/        # Discovered
└── functions/
    └── my_function.plating/     # Discovered
```

## Multi-Component Bundles

A single `.plating` directory can contain multiple component bundles:

```
components.plating/
├── resource1/
│   ├── docs/
│   └── examples/
├── resource2/
│   ├── docs/
│   └── examples/
└── data_source1/
    ├── docs/
    └── examples/
```

## Registry Entry Structure

Each registry entry contains:

```python
PlatingRegistryEntry:
  name: str                # Component name
  dimension: str           # Component type
  bundle: PlatingBundle    # Bundle instance
  metadata:
    path: Path            # Bundle directory path
    component_type: str   # Type identifier
    has_template: bool    # Has main template
    has_examples: bool    # Has example files
```

## Package Filtering

Control which packages are searched:

```python
# Search specific package only
api = Plating(context, package_name="pyvider.aws")

# Search all installed packages (slower)
api = Plating(context)  # package_name=None
```

## Registry Resilience

The registry includes foundation resilience patterns:

- **Retry Policy**: Automatic retries for discovery failures
- **Error Recovery**: Continues discovery even if some packages fail
- **Deduplication**: Prevents duplicate component registration
- **Caching**: Component metadata cached per session

## Programmatic Access

```python
import asyncio
from plating import Plating, PlatingContext
from plating.types import ComponentType

async def explore_registry():
    context = PlatingContext(provider_name="my_provider")
    api = Plating(context)

    # Get all resources
    resources = api.registry.get_components(ComponentType.RESOURCE)
    print(f"Found {len(resources)} resources")

    # Check specific component
    resource = api.registry.get_component(
        ComponentType.RESOURCE,
        "my_resource"
    )
    if resource:
        print(f"Resource path: {resource.plating_dir}")
        print(f"Has template: {resource.has_main_template()}")
        print(f"Has examples: {resource.has_examples()}")

    # Get registry statistics
    stats = await api.get_registry_stats()
    print(f"Total components: {stats['total']}")
    print(f"Documented: {stats['documented']}")

asyncio.run(explore_registry())
```

## Custom Discovery

For non-standard package structures, you can extend discovery:

```python
from plating.discovery import PlatingDiscovery

class CustomDiscovery(PlatingDiscovery):
    def discover_bundles(self):
        bundles = super().discover_bundles()
        # Add custom discovery logic
        return bundles
```

## Best Practices

1. **Package Organization**: Follow standard structure for automatic discovery
2. **Naming Conventions**: Use consistent naming for components and bundles
3. **Package Filtering**: Specify package_name for faster discovery
4. **Cache Registry**: Reuse Plating instance to avoid re-discovery

## Troubleshooting

### No Components Found

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check discovery
context = PlatingContext(provider_name="my_provider", log_level="DEBUG")
api = Plating(context)
```

### Duplicate Components

The registry automatically deduplicates components during global discovery. If you see duplicates, check for multiple installations of the same package.

### Performance Issues

For large environments with many packages:

```python
# Always specify package name
api = Plating(context, package_name="specific.package")

# Avoid global discovery
# api = Plating(context)  # Searches all packages
```