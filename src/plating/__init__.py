#
# plating/__init__.py
#
"""Modern async documentation generation with full foundation integration.

A clean, type-safe API for generating high-quality documentation with
multi-domain support via foundation patterns.

Key Features:
- Type-safe async-first API
- Full foundation integration (retry, metrics, circuit breakers)
- Registry-based component discovery with multi-domain support
- Integrated markdown validation with configurable rules
- Context-aware template rendering with Jinja2
- Extensible beyond Terraform to any domain (Kubernetes, CloudFormation, API docs, etc.)

Example Usage:
    ```python
    import asyncio
    from pathlib import Path
    from plating import Plating, ComponentType, PlatingContext

    async def main():
        # Initialize with foundation context
        context = PlatingContext(
            provider_name="my_provider",
            log_level="INFO",
            no_color=False
        )

        api = Plating(context)

        # Create missing templates
        adorn_result = await api.adorn(component_types=[ComponentType.RESOURCE])
        print(f"Created {adorn_result.templates_generated} templates")

        # Generate docs with validation
        plate_result = await api.plate(
            Path("docs"),
            component_types=[ComponentType.RESOURCE],
            validate_markdown=True,
            force=True
        )

        if plate_result.success:
            print(f"Generated {len(plate_result.output_files)} files")

        # Validate existing documentation
        validation_result = await api.validate()
        print(f"Validation: {validation_result.passed}/{validation_result.total} passed")

    # Run the async main
    asyncio.run(main())
    ```

CLI Usage:
    ```bash
    # Create missing templates
    plating adorn --component-type resource --provider-name my_provider

    # Generate documentation
    plating plate --output-dir docs --validate

    # Validate existing docs
    plating validate --output-dir docs

    # Show registry info
    plating info --provider-name my_provider
    ```
"""

from plating._version import __version__

# Old PlatingAPI removed - use Plating class directly

# Template engine
from plating.templating.engine import AsyncTemplateEngine, template_engine

# New modular components
from plating.bundles import FunctionPlatingBundle, PlatingBundle as ModularPlatingBundle

# Foundation decorators and utilities
from plating.decorators import (
    plating_metrics,
    with_circuit_breaker,
    with_metrics,
    with_retry,
    with_timing,
)
from plating.discovery import PlatingDiscovery as ModularPlatingDiscovery
from plating.templating.metadata import TemplateMetadataExtractor
from plating.generation import DocumentationAdorner, DocumentationPlater, TemplateRenderer

# from plating.markdown_validator import MarkdownValidator, get_markdown_validator, reset_markdown_validator
# Core async API
from plating.plating import Plating, plating

# Registry and validation
from plating.registry import PlatingRegistry, get_plating_registry, reset_plating_registry

# Type-safe data structures
from plating.types import (
    AdornResult,
    ArgumentInfo,
    ComponentType,
    PlateResult,
    PlatingContext,
    SchemaInfo,
    ValidationResult,
)

__all__ = [
    "AdornResult",
    "ArgumentInfo",
    # Template engine
    "AsyncTemplateEngine",
    # Type-safe structures
    "ComponentType",
    "DocumentationAdorner",
    "DocumentationPlater",
    # New modular components
    "FunctionPlatingBundle",
    "MarkdownValidator",
    "ModularPlatingBundle",
    "ModularPlatingDiscovery",
    "PlateResult",
    # Core API
    "Plating",
    "PlatingContext",
    # Registry and validation
    "PlatingRegistry",
    "SchemaInfo",
    "TemplateMetadataExtractor",
    "TemplateRenderer",
    "ValidationResult",
    # Version
    "__version__",
    "get_markdown_validator",
    "get_plating_registry",
    "plating",
    "plating_metrics",
    "reset_markdown_validator",
    "reset_plating_registry",
    "template_engine",
    "with_circuit_breaker",
    "with_metrics",
    # Foundation decorators
    "with_retry",
    "with_timing",
]


# 🚀✨🎯🍽️
