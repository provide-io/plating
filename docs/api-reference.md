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
    project_root: Path | None = None,
    generate_examples: bool = False,
    examples_dir: Path | None = None,
    grouped_examples_dir: Path | None = None
) -> PlateResult
```

**Parameters:**
- `output_dir`: Output directory (default: auto-detected)
- `component_types`: Component types to process
- `force`: Overwrite existing files
- `validate_markdown`: Run validation after generation
- `project_root`: Project root directory
- `generate_examples`: Generate standalone executable examples
- `examples_dir`: Output directory for flat examples
- `grouped_examples_dir`: Output directory for grouped examples

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
def get_registry_stats() -> dict[str, Any]
```

**Returns:** Dictionary with component statistics

**Note:** This is a synchronous method, not async.

### PlatingContext

Configuration context for plating operations. This is an alias for `PlatingCLIContext` which extends foundation's `CLIContext`.

```python
from plating import PlatingContext

# Common usage with basic parameters
context = PlatingContext(
    provider_name="my_provider",
    log_level="INFO",
    no_color=False
)
```

#### Constructor Parameters

**Commonly Used Parameters:**
- `provider_name`: Provider name (required for most operations)
- `log_level`: Logging level (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`)
- `no_color`: Disable colored output
- `debug`: Enable debug mode
- `json_output`: Output in JSON format

**Additional Parameters (from PlatingCLIContext):**
- `name`: Component name
- `component_type`: ComponentType enum value
- `description`: Component description
- `schema`: SchemaInfo object
- `examples`: Dictionary of example files
- `signature`: Function signature string
- `arguments`: List of ArgumentInfo objects

**Plus all parameters from foundation's CLIContext** (config_file, log_file, profile, etc.)

#### Methods

##### to_dict()

Convert context to dictionary for template rendering.

```python
def to_dict(include_sensitive: bool = False) -> dict[str, Any]
```

**Parameters:**
- `include_sensitive`: Whether to include sensitive values

**Returns:** Dictionary with context values

##### save_context()

Save context to file.

```python
def save_context(path: Path) -> None
```

**Parameters:**
- `path`: Path to save context file

##### load_context()

Load context from file.

```python
@classmethod
def load_context(cls, path: Path) -> PlatingContext
```

**Parameters:**
- `path`: Path to context file

**Returns:** PlatingContext instance

**Note:** The methods are `save_context()` and `load_context()`, not `save()` and `load()`.

### PlatingBundle

Represents a documentation bundle.

```python
# Recommended: Import from main package (exported as ModularPlatingBundle)
from plating import ModularPlatingBundle as PlatingBundle
from pathlib import Path

# Or import directly from bundles module
from plating.bundles import PlatingBundle
from pathlib import Path

bundle = PlatingBundle(
    name="my_resource",
    plating_dir=Path("my_resource.plating"),
    component_type="resource"
)
```

**Note:** The main package exports this as `ModularPlatingBundle`, but you can import it directly from `plating.bundles` as `PlatingBundle`.

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
    components_processed: int = 0
    templates_generated: int = 0
    examples_created: int = 0
    errors: list[str] = field(factory=list)

    @property
    def success(self) -> bool:
        """Whether the operation succeeded."""
        return len(self.errors) == 0
```

**Note:** AdornResult does not have a duration field.

### PlateResult

Result from plate operations.

```python
@define
class PlateResult:
    bundles_processed: int = 0
    files_generated: int = 0
    duration_seconds: float = 0.0
    errors: list[str] = field(factory=list)
    output_files: list[Path] = field(factory=list)

    @property
    def success(self) -> bool:
        """Whether the operation succeeded."""
        return len(self.errors) == 0
```

### ValidationResult

Result from validation operations with markdown linting support.

```python
@define
class ValidationResult:
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    failures: dict[str, str] = field(factory=dict)  # Maps file paths to error messages
    errors: list[str] = field(factory=list)  # General errors
    lint_errors: list[str] = field(factory=list)  # Markdown linting errors
    terraform_version: str = ""

    @property
    def success(self) -> bool:
        """Whether all validations passed."""
        return self.failed == 0 and len(self.lint_errors) == 0 and len(self.errors) == 0
```

**Note:** `failures` is a dictionary mapping file paths to error messages, not a list of objects.

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

    # Async methods must be awaited
    result = await api.adorn()
    result = await api.plate()
    result = await api.validate()

    # get_registry_stats is synchronous
    stats = api.get_registry_stats()

asyncio.run(main())
```

## Registry Access

Access the component registry:

```python
# Get components by type (returns list[PlatingBundle])
resources = api.registry.get_components(ComponentType.RESOURCE)

# Get specific component (returns PlatingBundle | None)
resource = api.registry.get_component(
    ComponentType.RESOURCE,
    "my_resource"
)

# Get documented components (returns list[PlatingBundle])
documented = api.registry.get_components_with_templates(
    ComponentType.RESOURCE
)
```

**Registry Methods:**
- `get_components(component_type: ComponentType) -> list[PlatingBundle]`
- `get_component(component_type: ComponentType, name: str) -> PlatingBundle | None`
- `get_components_with_templates(component_type: ComponentType) -> list[PlatingBundle]`

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

    # Generate documentation (validation runs automatically with validate_markdown=True)
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

    # Optional: Run standalone validation if you need additional checks
    # validate_result = await api.validate(output_dir=Path("docs"))
    # print(f"Validation: {validate_result.passed}/{validate_result.total}")

    return plate_result.success

if __name__ == "__main__":
    success = asyncio.run(generate_documentation())
    exit(0 if success else 1)
```