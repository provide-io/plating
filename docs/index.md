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

For complete API documentation, see the [API Reference](api/).

## Template Types

- **Project Templates**: Complete project scaffolding
- **Documentation Templates**: README, API docs, and guides
- **Code Templates**: Classes, functions, and modules
- **Configuration Templates**: CI/CD, build, and deployment configs