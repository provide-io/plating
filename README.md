# 🍽️ Plating

> A sophisticated documentation generation system for Terraform/OpenTofu providers

Plating is a powerful documentation system that brings culinary elegance to technical documentation. Just as a chef carefully plates a dish, Plating helps you present your Terraform provider documentation beautifully.

## ✨ Features

- **🎯 Automatic Documentation Generation** - Generate comprehensive docs from your provider code
- **✨ Smart Component Adorning** - Automatically create documentation templates for undocumented components
- **🍽️ Beautiful Plating** - Render documentation with examples, schemas, and rich formatting
- **🔍 Component Discovery** - Automatically find and document resources, data sources, and functions
- **📝 Jinja2 Templates** - Flexible templating with custom functions and filters
- **🔄 Schema Integration** - Extract and format provider schemas automatically
- **🎯 Capability-First Organization** - Group documentation by feature (Math, Utilities, Lens) instead of just type
- **📍 Smart Navigation** - Auto-generated mkdocs.yml with capability-first structure
- **📚 Guide Support** - Built-in support for provider guides and tutorials

## 🚀 Getting Started

### Installation

**Note:** Plating is currently in pre-release. Install from source for now.

> **Version Info:** The version `0.0.1000-0` is a pre-release identifier indicating active development. Expect the API and features to evolve as the project matures.

```bash
# Clone the repository
git clone https://github.com/provide-io/plating.git
cd plating

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
uv sync
```

**Coming soon to PyPI:**
```bash
# PyPI installation (not yet available)
# uv add plating
```

### Quick Install from Git

```bash
# Install directly from GitHub
uv add git+https://github.com/provide-io/plating.git
```

## Documentation
- [Documentation index](docs/index.md)
- [Examples](examples/README.md)

## Development
- See [CLAUDE.md](CLAUDE.md) for local development notes.
- Run `uv sync --extra dev` to set up the dev environment.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

Apache 2.0

## 📦 Prerequisites

> **Important:** This project uses `uv` for Python environment and package management.

### Install UV

Visit [UV Documentation](https://github.com/astral-sh/uv) for more information.

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pipx (if you prefer)
pipx install uv

# Update UV to latest version
uv self update
```

## 📚 Usage Examples

### 1. Adorn Your Components

First, create `.plating` bundles for your undocumented components:

```bash
# Adorn all missing components
plating adorn

# Adorn only resources
plating adorn --component-type resource
```

### 2. Customize Templates

Edit the generated templates in `.plating/docs/`:

```markdown
---
page_title: "Resource: my_resource"
---

# my_resource

{{ "{{ example('basic') }}" }}

## Schema

{{ "{{ schema() }}" }}
```

### 3. Generate Documentation

Render your documentation:

```bash
# Generate docs in ./docs directory
plating plate

# Custom output directory
plating plate --output-dir ./documentation
```

## 📂 Bundle Structure

Each component has a `.plating` bundle:

```
my_resource.plating/
├── docs/
│   ├── my_resource.tmpl.md    # Main template
│   └── _partial.md             # Reusable partials (optional)
├── examples/
│   ├── basic.tf                # Example configurations
│   ├── advanced.tf             # (optional)
│   └── full_stack/             # Grouped examples (optional)
│       └── main.tf             # Required entry point
└── fixtures/                   # Test fixtures (optional)
    └── data.json               # Test data files
```

**Note:** The `examples/` directory can contain:
- `.tf` files for resources/data sources (flat examples)
- `.py` files for Python API examples
- Subdirectories with `main.tf` for grouped examples that combine multiple components

## 🎨 Template Functions

Plating provides powerful template functions:

- `{{ "{{ schema() }}" }}` - Render component schema as markdown table
- `{{ "{{ example('name') }}" }}` - Include an example file in a terraform code block
- `{{ "{{ include('filename') }}" }}` - Include a static partial file
- `{{ "{{ render('filename') }}" }}` - Render a dynamic template partial with current context

## 🎯 Capability-First Organization

Plating now supports organizing documentation by **capability** (subcategory) instead of just by component type. This makes it easier to find related functionality across resource types.

### How It Works

1. **Add Subcategory to Templates**

   Add a `subcategory` field to your component template frontmatter:

   ```markdown
   ---
   page_title: "sqrt Function"
   subcategory: "Math"
   description: |-
     Calculate square root of a number
   ---
   ```

2. **Automatic Organization**

   Components are automatically grouped by capability in generated documentation:

   ```

   ## Math
   ### Functions
   - add
   - subtract
   - multiply

   ## String Utilities
   ### Functions
   - format
   - join
   - split

   ## Utilities
   ### Resources
   - pyvider_file_content
   ### Data Sources
   - pyvider_env_variables
   ```

3. **MkDocs Navigation**

   The `mkdocs.yml` navigation is automatically generated with capability-first structure:

   ```yaml
   nav:
     - Overview: index.md
     - Math:
         Functions:
           add: functions/add.md
           subtract: functions/subtract.md
     - String Utilities:
         Functions:
           format: functions/format.md
           join: functions/join.md
     - Utilities:
         Resources:
           file_content: resources/file_content.md
   ```

### Standard Subcategories

- **Math** - Numeric operations (add, subtract, multiply, etc.)
- **String Utilities** - String manipulation (format, join, split, etc.)
- **Collections** - List/map operations (contains, length, lookup)
- **Type Conversion** - Type casting functions
- **Lens** - Data transformation components (JQ integration)
- **Utilities** - General-purpose resources and data sources
- **Test Mode** - Components for testing (always appears last)

### Custom Subcategories

You can use any custom subcategory name. Just add it to your template frontmatter:

```markdown
---
page_title: "Custom Component"
subcategory: "My Custom Category"
---
```

### Guide Support

Add provider-level guides in `.plating/guides/`:

```
.plating/
├── guides/
│   ├── getting-started.tmpl.md
│   ├── authentication.tmpl.md
│   └── troubleshooting.tmpl.md
└── docs/
    └── components.tmpl.md
```

Guides are automatically discovered and added to the documentation structure and navigation.

## 🔍 Validation

Validate your generated documentation:

```bash
# Validate all documentation
plating validate

# Validate in custom directory
plating validate --output-dir ./documentation
```

## 🛡️ Foundation Integration

Plating is built on provide.foundation patterns for enterprise-grade reliability:

- **🔄 Automatic Retries**: Built-in retry policies with exponential backoff for I/O operations
- **📊 Metrics & Observability**: Integrated performance tracking and operation metrics
- **⚡ Circuit Breakers**: Prevents cascading failures in distributed systems
- **📝 Structured Logging**: Foundation logger integration with contextual information
- **🚀 Async-First Design**: High-performance async operations throughout

## 🔧 Advanced Usage

### Filter to Specific Package

By default, Plating searches all installed packages for components. You can filter to a specific package:

```bash
plating adorn --package-name pyvider.components
plating plate --package-name pyvider.components
```

### Generate Executable Examples

Generate standalone executable Terraform examples alongside documentation:

```bash
plating plate --generate-examples
```

Customize example output directories:

```bash
plating plate --generate-examples \
  --examples-dir examples/ \
  --grouped-examples-dir examples/integration/
```

## 🔧 Configuration

Configure Plating in your `pyproject.toml`:

```toml
[tool.plating]
# Provider name (auto-detected if not specified)
provider_name = "my_provider"
```

**Note:** Currently only `provider_name` can be configured in `pyproject.toml`. Other options like `output_dir` and `component_types` must be passed as CLI flags:

```bash
plating plate --output-dir docs --component-type resource
```

## 🏗️ Architecture

Plating follows a modular architecture:

- **PlatingBundle** - Represents documentation bundles
- **PlatingPlater** - Renders documentation
- **PlatingAdorner** - Creates documentation templates
- **PlatingDiscovery** - Finds components and bundles
- **SchemaProcessor** - Extracts provider schemas

## 🙏 Acknowledgments

Built with ❤️ using:
- [attrs](https://www.attrs.org/) - Python classes without boilerplate
- [Jinja2](https://jinja.palletsprojects.com/) - Powerful templating
- [pyvider](https://github.com/provide-io/pyvider) - Terraform provider framework
- [click](https://click.palletsprojects.com/) - Command line interface
- [rich](https://rich.readthedocs.io/) - Beautiful terminal output

---

*Plating - Making documentation as delightful as a well-plated dish* 🍽️
