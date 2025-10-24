# Plating Documentation

Welcome to Plating - Documentation and code generation templates for consistent project scaffolding and documentation automation.

## Features

Plating provides:

- **Template Engine**: Powerful templating system for code and documentation generation
- **Project Scaffolding**: Automated project structure creation
- **Documentation Generation**: Consistent documentation patterns across projects
- **Code Templates**: Reusable code templates and patterns
- **Multi-Language Support**: Templates for Python, Go, TypeScript, and more
- **Integration Tools**: CI/CD and development workflow templates

## Quick Start

### Installation

<div class="termy">

```console
$ pip install plating
// Installing plating...
Successfully installed plating

$ plating --version
plating, version 0.1.0
```

</div>

### Scaffold a New Component

<div class="termy">

```console
$ plating scaffold --component-type resource --name example_resource
// Creating .plating directory structure...
✓ Created example_resource.plating/
✓ Created docs/ directory
✓ Created examples/ directory
// Resource scaffold complete!

$ ls example_resource.plating/
docs/  examples/  resource.md.j2
```

</div>

### Generate Documentation

<div class="termy">

```console
$ plating render --output-dir docs/
// Discovering plating bundles...
Found 3 components
// Rendering documentation...
---> 100%
✓ Generated docs/resources/example_resource.md
✓ Generated docs/data-sources/example_data.md
✓ Generated docs/functions/example_function.md

Documentation generated successfully!
```

</div>

### Python API Usage

```python
from plating import Template, Generator

# Load a template
template = Template.load("python-package")

# Generate project structure
generator = Generator(template)
generator.create_project("my-new-project", {
    "package_name": "my_package",
    "author": "Your Name"
})
```

## API Reference

For complete API documentation, see the [API Reference](api/index.md).

## Template Types

- **Project Templates**: Complete project scaffolding
- **Documentation Templates**: README, API docs, and guides
- **Code Templates**: Classes, functions, and modules
- **Configuration Templates**: CI/CD, build, and deployment configs