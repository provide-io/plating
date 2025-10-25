#
# plating/__init__.py
#
"""Modern async documentation generation with full foundation integration.

A clean, type-safe API for generating high-quality Terraform/OpenTofu
provider documentation with foundation patterns.

Key Features:
- Type-safe async-first API
- Full foundation integration (retry, metrics, circuit breakers)
- Registry-based component discovery
- Integrated markdown validation with configurable rules
- Context-aware template rendering with Jinja2
- Support for resources, data sources, functions, and provider docs

Example Usage:
    ```python
    import asyncio
    from pathlib import Path
    from plating import Plating, ComponentType, PlatingContext
    from provide.foundation import pout

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
        pout(f"✅ Created {adorn_result.templates_generated} templates")

        # Generate docs with validation
        plate_result = await api.plate(
            Path("docs"),
            component_types=[ComponentType.RESOURCE],
            validate_markdown=True,
            force=True
        )

        if plate_result.success:
            pout(f"✅ Generated {len(plate_result.output_files)} files")

        # Validate existing documentation
        validation_result = await api.validate()
        pout(f"📊 Validation: {validation_result.passed}/{validation_result.total} passed")

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
from plating.generation import DocumentationAdorner, DocumentationPlater
from plating.plating import Plating, plating

# Registry and validation
from plating.registry import PlatingRegistry, get_plating_registry, reset_plating_registry

# Template engine
from plating.templating.engine import AsyncTemplateEngine, template_engine
from plating.templating.metadata import TemplateMetadataExtractor

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
    "__version__",
    "AdornResult",
    "ArgumentInfo",
    "AsyncTemplateEngine",
    "ComponentType",
    "DocumentationAdorner",
    "DocumentationPlater",
    "FunctionPlatingBundle",
    "ModularPlatingBundle",
    "ModularPlatingDiscovery",
    "PlateResult",
    "Plating",
    "PlatingContext",
    "PlatingRegistry",
    "SchemaInfo",
    "TemplateMetadataExtractor",
    "ValidationResult",
    "get_plating_registry",
    "plating",
    "plating_metrics",
    "reset_plating_registry",
    "template_engine",
    "with_circuit_breaker",
    "with_metrics",
    "with_retry",
    "with_timing",
]
