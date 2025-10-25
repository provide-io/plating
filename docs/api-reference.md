# API Reference

Complete API reference for the Plating documentation system.

## Core Classes

### Plating

The main API class for all documentation operations.

```python
from plating import Plating, PlatingContext

context = PlatingContext(provider_name="my_provider")
api = Plating(context, package_name="pyvider.components")
```

#### Constructor

```python
Plating(
    context: PlatingContext,
    package_name: str | None = None
) -> None
```

**Parameters:**
- `context`: PlatingContext with configuration (required)
- `package_name`: Package to search for components, or None to search all packages

#### Methods

##### adorn()

Generate documentation templates for components.

```python
async def adorn(
    output_dir: Path | None = None,
    component_types: list[ComponentType] | None = None,
    templates_only: bool = False
) -> AdornResult
```

**Parameters:**
- `output_dir`: Directory for templates (default: `.plating`)
- `component_types`: Component types to process
- `templates_only`: Only generate templates, skip discovery

**Returns:** AdornResult with generation statistics

##### plate()

Generate documentation from templates.

```python
async def plate(
    output_dir: Path | None = None,
    component_types: list[ComponentType] | None = None,
    force: bool = False,
    validate_markdown: bool = True,
    project_root: Path | None = None
) -> PlateResult
```

**Parameters:**
- `output_dir`: Output directory (default: auto-detected)
- `component_types`: Component types to process
- `force`: Overwrite existing files
- `validate_markdown`: Run validation after generation
- `project_root`: Project root directory

**Returns:** PlateResult with file paths and status

##### validate()

Validate generated documentation.

```python
async def validate(
    output_dir: Path | None = None,
    component_types: list[ComponentType] | None = None,
    project_root: Path | None = None
) -> ValidationResult
```

**Parameters:**
- `output_dir`: Documentation directory
- `component_types`: Component types to validate
- `project_root`: Project root directory

**Returns:** ValidationResult with validation details

##### get_registry_stats()

Get registry statistics.

```python
async def get_registry_stats() -> dict[str, Any]
```

**Returns:** Dictionary with component statistics

### PlatingContext

Configuration context for plating operations.

```python
from plating import PlatingContext

context = PlatingContext(
    provider_name="my_provider",
    log_level="INFO",
    no_color=False,
    verbose=False,
    quiet=False
)
```

#### Constructor Parameters

- `provider_name`: Provider name (required)
- `log_level`: Logging level (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`)
- `no_color`: Disable colored output
- `verbose`: Enable verbose output
- `quiet`: Suppress non-error output

#### Methods

##### to_dict()

Convert context to dictionary.

```python
def to_dict() -> dict[str, Any]
```

##### save()

Save context to foundation configuration.

```python
def save() -> None
```

##### load()

Load context from foundation configuration.

```python
@classmethod
def load(cls) -> PlatingContext
```

### PlatingBundle

Represents a documentation bundle.

```python
from plating.bundles import PlatingBundle
from pathlib import Path

bundle = PlatingBundle(
    name="my_resource",
    plating_dir=Path("my_resource.plating"),
    component_type="resource"
)
```

#### Properties

- `name`: Component name
- `plating_dir`: Bundle directory path
- `component_type`: Component type identifier
- `docs_dir`: Documentation templates directory
- `examples_dir`: Example files directory
- `fixtures_dir`: Test fixtures directory

#### Methods

##### load_main_template()

Load the main documentation template.

```python
def load_main_template() -> str | None
```

**Returns:** Template content or None if not found

##### load_examples()

Load all example files.

```python
def load_examples() -> dict[str, str]
```

**Returns:** Dictionary mapping filenames to content

##### load_partials()

Load partial templates.

```python
def load_partials() -> dict[str, str]
```

**Returns:** Dictionary of partial templates

##### has_main_template()

Check if bundle has main template.

```python
def has_main_template() -> bool
```

##### has_examples()

Check if bundle has examples.

```python
def has_examples() -> bool
```

## Result Types

### AdornResult

Result from adorn operations.

```python
@define
class AdornResult:
    components_processed: int
    templates_generated: int
    examples_created: int
    errors: list[str]
    duration: float
```

### PlateResult

Result from plate operations.

```python
@define
class PlateResult:
    files_generated: int
    output_files: list[Path]
    success: bool
    errors: list[str]
    duration: float
```

### ValidationResult

Result from validation operations.

```python
@define
class ValidationResult:
    total: int
    passed: int
    failed: int
    failures: list[ValidationFailure]
    duration: float
```

### ValidationFailure

Details of validation failure.

```python
@define
class ValidationFailure:
    file: Path
    reason: str
    line: int | None
    column: int | None
```

## Component Types

Enumeration of component types.

```python
from plating.types import ComponentType

ComponentType.RESOURCE      # Terraform resources
ComponentType.DATA_SOURCE   # Data sources
ComponentType.FUNCTION      # Provider functions
ComponentType.PROVIDER      # Provider configuration
```

**Properties:**
- `display_name`: Formatted display name
- `output_subdir`: Output directory name

## Error Classes

### PlatingError

Base exception for all plating errors.

```python
class PlatingError(Exception):
    def to_user_message() -> str
    def to_dict() -> dict[str, Any]
```

### Specific Errors

```python
BundleError         # Bundle-related errors
PlatingRenderError  # Template rendering errors
SchemaError         # Schema extraction errors
AdorningError       # Component adorning errors
FileSystemError     # File system operations
TemplateError       # Template processing errors
ValidationError     # Documentation validation errors
```

## Template Functions

Functions available in Jinja2 templates.

### schema()

Render component schema as markdown table.

```jinja2
{{ schema() }}
```

**Output:** Markdown table with columns: Argument, Type, Required, Description

### example(name)

Include example file.

```jinja2
{{ example("basic") }}
```

**Parameters:**
- `name`: Filename without extension

**Output:** Example wrapped in code block

### include(filename)

Include static partial.

```jinja2
{{ include("_note.md") }}
```

**Parameters:**
- `filename`: Partial filename

**Output:** Raw partial content

### render(filename)

Render dynamic partial.

```jinja2
{{ render("_section.md") }}
```

**Parameters:**
- `filename`: Partial filename

**Output:** Processed partial with context

## Foundation Integration

Plating includes foundation patterns:

### Retry Policy

```python
RetryPolicy(
    max_attempts=3,
    backoff=BackoffStrategy.EXPONENTIAL,
    base_delay=0.5,
    max_delay=10.0,
    retryable_errors=(IOError, OSError, TimeoutError, ConnectionError)
)
```

### Metrics

Operations tracked:
- `adorn`: Adorning duration
- `plate`: Generation performance
- `validate`: Validation time
- `template_render`: Rendering metrics

### Logging

```python
from provide.foundation import logger, pout, perr

logger.info("Processing", component="my_resource")
pout("✅ Success")
perr("❌ Error")
```

## Async Operations

All operations are asynchronous:

```python
import asyncio

async def main():
    context = PlatingContext(provider_name="my_provider")
    api = Plating(context)

    # All methods must be awaited
    result = await api.adorn()
    result = await api.plate()
    result = await api.validate()
    stats = await api.get_registry_stats()

asyncio.run(main())
```

## Registry Access

Access the component registry:

```python
# Get components by type
resources = api.registry.get_components(ComponentType.RESOURCE)

# Get specific component
resource = api.registry.get_component(
    ComponentType.RESOURCE,
    "my_resource"
)

# Get documented components
documented = api.registry.get_components_with_templates(
    ComponentType.RESOURCE
)
```

## Complete Example

```python
#!/usr/bin/env python3
import asyncio
from pathlib import Path
from plating import Plating, PlatingContext
from plating.types import ComponentType

async def generate_documentation():
    # Configure
    context = PlatingContext(
        provider_name="my_provider",
        log_level="INFO"
    )

    # Initialize
    api = Plating(context, package_name="pyvider.my_provider")

    # Generate templates
    adorn_result = await api.adorn(
        component_types=[ComponentType.RESOURCE]
    )

    if adorn_result.templates_generated > 0:
        print(f"Created {adorn_result.templates_generated} templates")

    # Generate documentation
    plate_result = await api.plate(
        output_dir=Path("docs"),
        validate_markdown=True,
        force=True
    )

    if not plate_result.success:
        for error in plate_result.errors:
            print(f"Error: {error}")
        return False

    print(f"Generated {plate_result.files_generated} files")

    # Validate
    validate_result = await api.validate(
        output_dir=Path("docs")
    )

    print(f"Validation: {validate_result.passed}/{validate_result.total}")

    return validate_result.failed == 0

if __name__ == "__main__":
    success = asyncio.run(generate_documentation())
    exit(0 if success else 1)
```