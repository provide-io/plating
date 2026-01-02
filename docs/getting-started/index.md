# Getting Started with Plating

!!! info "Release Status"

    **Plating is in its pre-release series.**
    Some documented or roadmap items are exploratory and may change or be removed.

    ✅ **Currently Working:**
    - PSPF documentation generation
    - Template-based doc system (Jinja2)
    - Component discovery via foundation.hub
    - CLI commands (adorn, plate, validate)
    - Async-first architecture

    ⚠️ **Known Limitations:**
    - Some advanced features are documented separately

    📋 **Roadmap:**
    - Enhanced template functions
    - Additional component types

    **Current Version:** v0.3.0

---

## What is Plating?

Plating is a modern, async-first documentation generation system for Terraform/OpenTofu providers. Just as a chef carefully plates a dish, Plating helps you present your provider documentation beautifully and professionally.

**Key Features:**

- **🎯 Automatic Generation** - Create comprehensive docs from provider code
- **✨ Smart Templates** - Automatically generate documentation templates
- **🍽️ Beautiful Output** - Terraform Registry-compliant markdown
- **🔍 Component Discovery** - Find resources, data sources, and functions automatically
- **⚡ Foundation Integration** - Built-in retry policies, metrics, circuit breakers
- **🚀 Async-First** - High-performance parallel processing

---

## Prerequisites

Before installing Plating, ensure you have:

- **Python 3.11+** - Required for modern async features
- **UV** - Required package manager
- **Git** - For source installation

### Install UV (Recommended)

UV is a fast Python package manager. Install it with:

=== "macOS/Linux"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "pipx"
    ```bash
    pipx install uv
    ```

For more information, visit [UV Documentation](https://github.com/astral-sh/uv).

---

## Installation

### Install from PyPI

```bash
uv tool install plating
```

### From Source

```bash
# Clone the repository
git clone https://github.com/provide-io/plating.git
cd plating

# Install with UV
uv sync

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Verify installation
plating --help
```

### From GitHub (Direct)

```bash
# Install directly from GitHub (using UV)
uv tool install git+https://github.com/provide-io/plating.git
```

---

## Quick Start

Plating follows a simple three-step workflow: **Adorn → Plate → Validate**

### Step 1: Adorn Components

Create documentation templates for components that don't have them:

```bash
# Adorn all missing components
plating adorn --provider-name my_provider

# Adorn only specific component types
plating adorn --component-type resource
```

**Output:**
```console
🎨 Adorning 5 component types...
📦 Processing 10 resource(s)...
✅ Generated 8 templates
📦 Processed 10 components
```

This creates `.plating` bundles with template files for each component.

### Step 2: Customize Templates (Optional)

Edit the generated templates in your `.plating/docs/` directories:

{% raw %}
```markdown
---
page_title: "Resource: my_resource"
---

# my_resource

{{ example('basic') }}

## Schema

{{ schema() }}

## Import

Resources can be imported using:
```bash
terraform import my_resource.example resource_id
```
```
{% endraw %}

### Step 3: Plate Documentation

Transform templates into Terraform Registry-compliant documentation:

```bash
# Generate documentation
plating plate --output-dir docs/

# Generate with validation
plating plate --output-dir docs/ --validate
```

**Output:**
```console
🍽️ Plating documentation...
✅ Generated 10 files in 0.52s
📦 Processed 10 bundles
📄 Generated files:
  • docs/resources/example_resource.md
  • docs/data-sources/example_data.md
  • docs/functions/example_function.md
  ... and 7 more
```

### Step 4: Validate (Optional)

Validate your generated documentation:

```bash
plating validate --output-dir docs/
```

**Output:**
```console
📊 Validation results:
  • Total files: 10
  • Passed: 10
  • Failed: 0
  • Duration: 0.23s
✅ All validations passed
```

---

## Your First Documentation

Let's walk through a complete example:

### 1. Set Up Your Provider Project

```bash
# Create a provider project (or use existing)
mkdir my-terraform-provider
cd my-terraform-provider
```

### 2. Generate Templates

```bash
# Adorn resources and data sources
plating adorn \
  --provider-name my_provider \
  --component-type resource \
  --component-type data_source
```

### 3. Add Examples

Edit a generated bundle, e.g., `my_resource.plating/examples/basic.tf`:

```hcl
resource "my_resource" "example" {
  name        = "example"
  description = "Example resource configuration"

  settings {
    enabled = true
    timeout = 30
  }

  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

### 4. Generate Documentation

```bash
plating plate --output-dir docs/
```

### 5. Review Output

Check the generated documentation in `docs/resources/my_resource.md`:

```markdown
# my_resource

Manages a my_resource resource.

## Example Usage

```hcl
resource "my_resource" "example" {
  name        = "example"
  description = "Example resource configuration"
  ...
}
```

## Schema

### Required
- `name` (String) Name of the resource

### Optional
- `description` (String) Description
- `settings` (Block) Configuration settings
- `tags` (Map of String) Resource tags
```

---

## Python API Usage

For programmatic usage, use the Python API:

```python
import asyncio
from pathlib import Path
from plating import Plating, PlatingContext
from plating.types import ComponentType

async def generate_provider_docs():
    """Generate documentation for a Terraform provider."""

    # Initialize context
    context = PlatingContext(
        provider_name="my_provider",
        log_level="INFO",
        no_color=False
    )

    # Create API instance
    api = Plating(context, package_name="pyvider.components")

    # Step 1: Adorn components (create templates)
    adorn_result = await api.adorn(
        component_types=[
            ComponentType.RESOURCE,
            ComponentType.DATA_SOURCE
        ]
    )
    print(f"✅ Generated {adorn_result.templates_generated} templates")

    # Step 2: Plate documentation (with validation)
    plate_result = await api.plate(
        output_dir=Path("docs"),
        validate_markdown=True  # Automatic validation
    )
    print(f"📄 Generated {plate_result.files_generated} files")

    return plate_result.success

# Run the async function
if __name__ == "__main__":
    success = asyncio.run(generate_provider_docs())
    exit(0 if success else 1)
```

---

## Bundle Structure

Each component gets a `.plating` bundle directory:

```
my_resource.plating/
├── docs/
│   ├── my_resource.tmpl.md    # Main documentation template
│   └── _partial.md             # Reusable partials (optional)
├── examples/
│   ├── basic.tf                # Basic usage example
│   ├── advanced.tf             # Advanced example (optional)
│   └── full_stack/             # Grouped examples (optional)
│       └── main.tf             # Entry point for grouped examples
└── fixtures/                   # Test fixtures (optional)
    └── data.json               # Test data files
```

**Notes:**
- `.tf` files for Terraform configurations
- `.py` files for Python API examples
- Subdirectories must contain `main.tf` as entry point

---

## Template Functions

Plating provides powerful Jinja2 template functions:

{% raw %}

| Function | Description | Example |
|----------|-------------|---------|
| `schema()` | Render component schema as markdown table | `{{ schema() }}` |
| `example('name')` | Include example file in code block | `{{ example('basic') }}` |
| `include('file')` | Include static partial file | `{{ include('_intro.md') }}` |
| `render('file')` | Render dynamic template with context | `{{ render('_advanced.md') }}` |

{% endraw %}

**Example Template:**

{% raw %}
```markdown
# my_resource

{{ include('_description.md') }}

## Example Usage

{{ example('basic') }}

{{ example('advanced') }}

## Schema

{{ schema() }}

## Additional Information

{{ render('_details.tmpl.md') }}
```
{% endraw %}

---

## Common Commands

```bash
# Adorn specific component types
plating adorn --component-type resource --component-type data_source

# Filter to specific package
plating adorn --package-name pyvider.aws

# Generate with validation and force overwrite
plating plate --validate --force

# Show registry statistics
plating stats

# Validate specific directory
plating validate --output-dir ./documentation
```

---

## Pre-Release Limitations

Current limitations:

### Not Available Yet

- **Windows Full Support** - Some features may be experimental on Windows
- **Plugin System** - Custom template functions (planned)
- **Multi-Provider Support** - Batch processing multiple providers (planned)

### Known Issues

- **Template Hot-Reload** - Requires re-running `plating plate` to see changes
- **Error Messages** - Some errors may lack detailed context
- **Performance** - Large providers (100+ resources) may take 5-10 seconds

### Workarounds

**Issue: Templates not updating**
```bash
# Force regeneration
plating plate --force
```

**Issue: Missing components**
```bash
# Re-run discovery with verbose logging
plating adorn --log-level DEBUG
```

**Issue: Validation failures**
```bash
# Check specific file
plating validate --output-dir docs/ --log-level INFO
```

---

## Troubleshooting

### Installation Issues

**Problem: UV not found**
```bash
# Install UV first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell
source ~/.bashrc  # or ~/.zshrc
```

**Problem: Python version too old**
```bash
# Check Python version
python --version  # Must be 3.11+

# Install Python 3.11+ if needed
```

### Runtime Issues

**Problem: No components found**

- Ensure your provider package is installed in the same environment
- Use `--package-name` to specify the package explicitly
- Check that components are registered with foundation.hub

**Problem: Templates not rendering**

- Verify `.plating` bundle structure
- Check template syntax (must be valid Jinja2)
- Use `--log-level DEBUG` for detailed error messages

For more troubleshooting, see **[Troubleshooting Guide](../troubleshooting.md)**.

---

## Next Steps

Now that you're set up, explore:

- **[Authoring Bundles](../authoring-bundles.md)** - Create custom documentation templates
- **[Examples](../examples.md)** - Complete working examples
- **[CLI Reference](../cli-reference.md)** - All command-line options
- **[API Reference](../api-reference.md)** - Python API documentation
- **[Registry Pattern](../registry-pattern.md)** - Component discovery system

---

## Part of the provide.io Ecosystem

Plating is part of a larger ecosystem of Python and Terraform tools.

**[View Ecosystem Overview →](https://docs.provide.io/provide-foundation/ecosystem/)**

Understand how plating integrates with:
- **provide-foundation** - Core reliability patterns
- **pyvider** - Terraform provider framework
- **flavorpack** - Application packaging
- **provide-testkit** - Testing utilities

---

## Getting Help

- **[Troubleshooting Guide](../troubleshooting.md)** - Common issues and solutions
- **[GitHub Issues](https://github.com/provide-io/plating/issues)** - Report bugs or request features
- **[Discussions](https://github.com/provide-io/plating/discussions)** - Community support

**Found a bug?** Please report it with:
- Plating version (`plating --version`)
- Python version (`python --version`)
- Operating system
- Complete error output

---

**Ready to start?** Jump to **[Authoring Bundles](../authoring-bundles.md)** to learn how to create custom documentation templates!