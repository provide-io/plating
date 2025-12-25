# Plating API Documentation

This document provides comprehensive API documentation for the Plating documentation generation system.

## Core Classes

### PlatingBundle

Represents a single `.plating` bundle containing documentation assets.

```python
from plating.plating import PlatingBundle

bundle = PlatingBundle(
    name="my_resource",
    plating_dir=Path("my_resource.plating"),
    component_type="resource"
)
```

#### Properties

- `docs_dir: Path` - Directory containing documentation templates and partials
- `examples_dir: Path` - Directory containing example files (.tf or .py)

#### Methods

- `load_main_template() -> str | None` - Load the main template file
- `load_examples() -> dict[str, str]` - Load all example files as dictionary
- `load_partials() -> dict[str, str]` - Load partial files (starting with `_`)

### Plating (Main API)

The primary API for all plating operations. This is the recommended way to interact with plating.

```python
from plating import Plating, PlatingContext
from plating.types import ComponentType
from pathlib import Path

# Initialize plating API with context
context = PlatingContext(provider_name="my_provider")
api = Plating(context, package_name="pyvider.components")

# Adorn components with templates
result = await api.adorn(component_types=[ComponentType.RESOURCE])
print(f"Generated {result.templates_generated} templates")

# Generate documentation
result = await api.plate(output_dir=Path("docs"))
print(f"Generated {result.files_generated} files")

# Validate documentation
result = await api.validate(output_dir=Path("docs"))
print(f"Validated {result.total} files")
```

#### Methods

- `adorn(output_dir, component_types, templates_only)` - Generate template structure for components
- `plate(output_dir, component_types, force, validate_markdown, project_root)` - Generate documentation from plating bundles
- `validate(output_dir, component_types, project_root)` - Validate generated documentation
- `get_registry_stats()` - Get registry statistics for all components

All methods are async and should be awaited.

### PlatingAdorner

Creates documentation templates and examples for components.

```python
from plating.adorner import PlatingAdorner

adorner = PlatingAdorner(package_name="pyvider.components")

# Adorn missing components
results = await adorner.adorn_missing(component_types=["resource"])
print(f"Adorned {results['resource']} resources")
```

#### Methods

- `adorn_missing(component_types: list[str] | None = None) -> dict[str, int]` - Adorn components with missing bundles

**Note:** Internal methods (prefixed with `_`) are not part of the public API and should not be used directly.

### PlatingDiscovery

Discovers `.plating` bundles from installed packages.

```python
from plating.plating import PlatingDiscovery

discovery = PlatingDiscovery(package_name="pyvider.components")
bundles = discovery.discover_bundles(component_type="resource")
```

#### Methods

- `discover_bundles(component_type: str | None = None) -> list[PlatingBundle]` - Discover all bundles

### SchemaProcessor

Handles schema extraction and processing for documentation generation.

```python
from plating.schema import SchemaProcessor

processor = SchemaProcessor(provider_name="aws")
schema = processor.extract_provider_schema()
processor.parse_provider_schema()
```

#### Methods

- `extract_provider_schema() -> dict[str, Any]` - Extract provider schema using Pyvider discovery
- `parse_provider_schema() -> None` - Parse extracted schema into internal structures
- `_parse_schema_to_markdown(schema: dict[str, Any]) -> str` - Convert schema to markdown

## Template Functions

Plating provides custom Jinja2 template functions for documentation generation.

### schema()

Renders the component schema as a markdown table with attributes, types, and descriptions.

```jinja2
## Arguments

{{ schema() }}
```

**Output:** Generates a markdown table with columns: Argument, Type, Required, Description

### example(name)

Includes an example file by name from the examples directory, wrapped in a terraform code block.

```jinja2
### Basic Usage

{{ example("basic") }}
```

**Parameters:**
- `name` - Filename (without .tf extension) from the bundle's examples/ directory

**Output:** Returns the example wrapped in triple-backtick terraform code block

### include(filename)

Includes a static partial file from the docs directory without processing.

```jinja2
{{ include("_common_note.md") }}
```

**Parameters:**
- `filename` - Name of partial file in the bundle's docs/ directory

**Output:** Raw content of the partial file

### render(filename)

Renders a dynamic template partial with the current template context.

```jinja2
{{ render("_dynamic_section.md") }}
```

**Parameters:**
- `filename` - Name of partial file in the bundle's docs/ directory

**Output:** The partial file processed as a Jinja2 template with full access to context variables (name, type, schema, examples, etc.)

## CLI Interface

### Commands

#### adorn

Create `.plating` bundles for components missing documentation.

```bash
# Adorn all missing components
plating adorn

# Adorn specific component types
plating adorn --component-type resource
plating adorn --component-type data_source
plating adorn --component-type function

# Multiple component types
plating adorn --component-type resource --component-type function

# Filter to specific package
plating adorn --package-name pyvider.components

# Explicit provider name (otherwise auto-detected)
plating adorn --provider-name my_provider
```

#### plate

Generate documentation from `.plating` bundles.

```bash
# Generate to default directory (auto-detected)
plating plate

# Custom output directory
plating plate --output-dir ./documentation

# Filter to specific component types
plating plate --component-type resource --component-type data_source

# Filter to specific package
plating plate --package-name pyvider.components

# Force overwrite existing files
plating plate --force

# Disable validation
plating plate --no-validate

# Specify project root (auto-detected if not provided)
plating plate --project-root /path/to/project

# Generate executable examples alongside documentation
plating plate --generate-examples

# Customize example output directories
plating plate --generate-examples \
  --examples-dir examples/ \
  --grouped-examples-dir examples/integration/
```

#### validate

Validate generated documentation.

```bash
# Validate all documentation
plating validate

# Validate in custom directory
plating validate --output-dir ./documentation

# Validate specific component types
plating validate --component-type resource --component-type data_source

# Filter to specific package
plating validate --package-name pyvider.components
```

#### info

Show registry information and statistics.

```bash
# Show registry info with auto-detected provider
plating info

# Show info for specific provider (otherwise auto-detected)
plating info --provider-name my_provider

# Filter to specific package (default: search all installed packages)
plating info --package-name pyvider.components
```

#### stats

Show detailed registry statistics.

```bash
# Show all statistics (searches all installed packages)
plating stats

# Filter to specific package
plating stats --package-name pyvider.components
```

## Configuration

Configure Plating behavior in `pyproject.toml`:

```toml
[tool.plating]
# Provider name for schema extraction (auto-detected if not specified)
provider_name = "my_provider"
```

**Important:** Currently only `provider_name` is read from `pyproject.toml`. All other options must be passed as CLI flags:

### CLI-Only Options

| Option | Flag | Commands | Description |
|--------|------|----------|-------------|
| Output directory | `--output-dir PATH` | plate, validate | Where to write/read docs |
| Component types | `--component-type TYPE` | adorn, plate, validate | Filter by type (repeatable) |
| Package filter | `--package-name NAME` | all | Filter to specific package |
| Force overwrite | `--force` | plate | Overwrite existing files |
| Validation | `--validate/--no-validate` | plate | Enable/disable validation |
| Project root | `--project-root PATH` | plate | Specify project root |
| Generate examples | `--generate-examples` | plate | Create executable examples |
| Examples directory | `--examples-dir PATH` | plate | Output dir for examples |
| Grouped examples | `--grouped-examples-dir PATH` | plate | Output dir for integration examples |

## Error Handling

Plating provides structured error handling with custom exception types.

### Exception Hierarchy

- `PlatingError` - Base error for all plating operations
  - `BundleError` - Bundle-related errors
  - `PlatingRenderError` - Template rendering errors
  - `SchemaError` - Schema extraction/processing errors

### Error Handling Example

```python
from plating.errors import PlatingError, BundleError, PlatingRenderError

try:
    plater.plate(output_dir)
except PlatingRenderError as e:
    logger.error(f"Template rendering failed: {e}")
except BundleError as e:
    logger.error(f"Bundle error: {e}")
except PlatingError as e:
    logger.error(f"Plating operation failed: {e}")
```

## Integration with Pyvider

Plating integrates deeply with the Pyvider ecosystem:

### Component Discovery

```python
from pyvider.hub import ComponentDiscovery, hub

# Discover components
discovery = ComponentDiscovery(hub)
await discovery.discover_all()
components = hub.list_components()
```

### Schema Extraction

```python
# Extract component schema
schema = component.get_schema()
schema_dict = attrs.asdict(schema)
```

### Telemetry Integration

```python
from provide.foundation import logger, pout

# Structured logging
logger.info("Processing component", component_name=name)

# User-friendly output  
pout(f"✨ Adorning {component_name}...")
```

## Testing

### Mocking Components

```python
from unittest.mock import Mock

# Mock component for testing
mock_component = Mock()
mock_component.__doc__ = "Test component documentation"
mock_component.get_schema.return_value = test_schema
```

### Test Utilities

```python
import tempfile
from pathlib import Path

# Create temporary bundle for testing
with tempfile.TemporaryDirectory() as tmp_dir:
    bundle_dir = Path(tmp_dir) / "test.plating"
    bundle_dir.mkdir()
    
    # Create test bundle
    bundle = PlatingBundle(
        name="test",
        plating_dir=bundle_dir,
        component_type="resource"
    )
```

## Advanced Usage

### Custom Template Functions

Register custom template functions:

```python
from jinja2 import Environment

def custom_function(value):
    return f"Custom: {value}"

# Add to environment
env = Environment()
env.globals["custom"] = custom_function
```

### Batch Processing

Process multiple providers:

```python
providers = ["aws", "azure", "gcp"]

for provider in providers:
    schema_processor = SchemaProcessor(provider_name=provider)
    discovery = PlatingDiscovery(f"pyvider.{provider}")
    bundles = discovery.discover_bundles()
    
    plater = PlatingPlater(bundles=bundles, schema_processor=schema_processor)
    plater.plate(Path(f"docs/{provider}"))
```

### Async Operations

All adorning operations are async:

```python
import asyncio

async def main():
    adorner = PlatingAdorner()
    results = await adorner.adorn_missing()
    print(f"Adorned {sum(results.values())} components")

asyncio.run(main())
```

## Performance Considerations

- **Bundle Loading**: Lazy loading of templates and examples
- **Schema Caching**: Schema extraction results are cached per session
- **Async Operations**: Component discovery and adorning are async
- **Memory Usage**: Large schemas may consume significant memory during processing

## Troubleshooting

### Common Issues

1. **Module Not Found**: Ensure pyvider packages are installed
2. **Schema Extraction Fails**: Check component discovery setup
3. **Template Rendering Errors**: Verify Jinja2 syntax in templates
4. **Missing Bundles**: Run `plating adorn` to create missing documentation

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use provide.foundation
from provide.foundation import logger
logger.setLevel(logging.DEBUG)
```

### Validation

Validate bundle structure:

```python
bundle = PlatingBundle(name="test", plating_dir=path, component_type="resource")

# Check required directories exist
assert bundle.docs_dir.exists()
assert bundle.examples_dir.exists()

# Validate template loads
template = bundle.load_main_template()
assert template is not None
```