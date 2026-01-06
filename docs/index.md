# Plating Documentation

!!! warning "Pre-release"
    This documentation covers a pre-release. APIs and features may change during the pre-release series.


Welcome to Plating - An async-first documentation generation system for Terraform/OpenTofu providers.

## What is Plating?

Plating is a modern documentation generator that transforms your Terraform provider code into beautiful, Terraform Registry-compliant documentation. Built on foundation patterns for enterprise reliability, Plating makes documentation as delightful as a well-plated dish.

## Key Features

- **🚀 Async-First Architecture**: High-performance parallel processing
- **📝 Automatic Template Generation**: Create documentation templates automatically
- **🎨 Beautiful Documentation**: Generate Terraform Registry-compliant markdown
- **🔍 Smart Discovery**: Automatically find components via foundation.hub
- **⚡ Foundation Integration**: Built-in retry policies, metrics, and circuit breakers
- **📊 Registry Pattern**: Centralized component management and statistics
- **🛡️ Enterprise Ready**: Production-grade resilience and observability

---

## Part of the provide.io Ecosystem

This project is part of a larger ecosystem of tools for Python and Terraform development.

**[View Ecosystem Overview →](https://foundry.provide.io/provide-foundation/ecosystem/)**

Understand how provide-foundation, pyvider, flavorpack, and other projects work together.

---

## Quick Start

### Installation

!!! info "Release Status"
    plating is in its pre-release series.
    Some APIs may change during the pre-release series.

    - **Current version:** v0.3.0
    - **Status:** Pre-release
    - **Installation:** Install from source

**Installation:**

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

**Install from PyPI:** `uv tool install plating`

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
import asyncio
from plating import Plating, PlatingContext
from plating.types import ComponentType
from pathlib import Path

async def main():
    # Initialize plating API with foundation context
    context = PlatingContext(
        provider_name="my_provider",
        log_level="INFO",
        no_color=False
    )
    api = Plating(context, package_name="pyvider.components")

    # Adorn components with templates
    result = await api.adorn(component_types=[ComponentType.RESOURCE])
    print(f"Generated {result.templates_generated} templates")

    # Plate documentation (validation runs automatically if validate_markdown=True)
    result = await api.plate(output_dir=Path("docs"), validate_markdown=True)
    print(f"Generated {result.files_generated} files")

    # Note: validate_markdown=True runs validation during generation
    # No need to call validate() separately unless you want to run it standalone

# Run the async main function
asyncio.run(main())
```

## Documentation

### Getting Started
- **[Quick Start](quick-start.md)** - Get up and running in 5 minutes
- **[Authoring Bundles](authoring-bundles.md)** - Create custom documentation
- **[Examples](examples.md)** - Complete working examples

### Reference
- **[API Reference](api-reference.md)** - Complete Python API documentation
- **[CLI Reference](cli-reference.md)** - Command-line interface and options
- **[Registry Pattern](registry-pattern.md)** - Component discovery and management

### Advanced Topics
- **[Performance](performance.md)** - Optimization and best practices
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

### API Documentation
- **[Auto-generated API](api/index.md)** - Auto-generated API documentation from source code

## Component Types Supported

- **Resources**: Terraform resources (e.g., `aws_s3_bucket`)
- **Data Sources**: Terraform data sources (e.g., `aws_ami`)
- **Functions**: Provider functions (e.g., `timestamp()`)
- **Providers**: Provider configuration documentation

## Architecture Overview

Plating follows a clean, modular architecture:

```
Plating API (async-first)
    ├── Registry (component discovery)
    ├── Template Engine (Jinja2)
    ├── Schema Processor (extraction)
    └── Foundation Integration
        ├── Retry Policies
        ├── Circuit Breakers
        └── Metrics & Observability
```
