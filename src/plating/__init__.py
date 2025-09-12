#
# plating/__init__.py
#
"""Modern async documentation generation for Terraform/OpenTofu providers.

A clean, type-safe API with full foundation integration for generating
high-quality Terraform Registry-compliant documentation.

Key Features:
- Type-safe async-first API
- Full foundation integration (retry, metrics, circuit breakers)
- Registry-based component discovery
- Integrated markdown validation
- Context-aware template rendering

Example Usage:
    ```python
    from plating import Plating, ComponentType, PlatingContext
    
    # Initialize with context
    context = PlatingContext(provider_name="my_provider")
    plating = Plating(context)
    
    # Create missing templates
    result = await plating.adorn([ComponentType.RESOURCE])
    
    # Generate documentation with validation
    result = await plating.plate(Path("docs"), validate_markdown=True)
    
    # Validate existing documentation
    result = await plating.validate(Path("docs"))
    ```
"""

from plating._version import __version__

# Modern async API
from plating.api import Plating, plating

# Type-safe data structures
from plating.types import (
    ComponentType,
    PlatingContext,
    SchemaInfo,
    ArgumentInfo,
    AdornResult,
    PlateResult,
    ValidationResult,
)

# Template engine
from plating.async_template_engine import AsyncTemplateEngine, template_engine

# Foundation decorators and utilities
from plating.decorators import (
    with_retry,
    with_circuit_breaker,
    with_metrics,
    with_timing,
    plating_metrics,
)

# Registry and validation
from plating.registry import PlatingRegistry, get_plating_registry
from plating.markdown_validator import MarkdownValidator, get_markdown_validator

# Core bundle system (for advanced users)
from plating.plating import PlatingBundle, PlatingDiscovery

__all__ = [
    # Version
    "__version__",
    
    # Modern API
    "Plating",
    "plating",
    
    # Type-safe structures
    "ComponentType",
    "PlatingContext",
    "SchemaInfo", 
    "ArgumentInfo",
    "AdornResult",
    "PlateResult",
    "ValidationResult",
    
    # Template engine
    "AsyncTemplateEngine",
    "template_engine",
    
    # Foundation decorators
    "with_retry",
    "with_circuit_breaker", 
    "with_metrics",
    "with_timing",
    "plating_metrics",
    
    # Registry and validation
    "PlatingRegistry",
    "get_plating_registry",
    "MarkdownValidator", 
    "get_markdown_validator",
    
    # Core system (advanced)
    "PlatingBundle",
    "PlatingDiscovery",
]


def example_usage():
    """Example of modern API usage."""
    import asyncio
    from pathlib import Path
    
    async def main():
        # Initialize with foundation context
        context = PlatingContext(
            provider_name="my_provider",
            log_level="INFO",  # Foundation context feature
            no_color=False    # Foundation context feature
        )
        
        api = Plating(context)
        
        # Create missing templates with type safety
        adorn_result = await api.adorn([ComponentType.RESOURCE, ComponentType.DATA_SOURCE])
        print(f"Created {adorn_result.templates_generated} templates")
        
        # Generate docs with integrated validation
        plate_result = await api.plate(
            Path("docs"),
            component_types=[ComponentType.RESOURCE],
            validate_markdown=True,  # Built-in markdown linting
            force=True
        )
        
        if plate_result.success:
            print(f"Generated {len(plate_result.output_files)} files "
                  f"in {plate_result.duration_seconds:.2f}s")
        else:
            print(f"Errors: {plate_result.errors}")
        
        # Validate existing documentation
        validation_result = await api.validate()
        print(f"Validation: {validation_result.passed}/{validation_result.total} passed")
        if validation_result.lint_errors:
            print(f"Linting issues: {len(validation_result.lint_errors)}")
        
        # Get registry statistics
        stats = api.get_registry_stats()
        print(f"Registry contains {stats['total_components']} components")
    
    # Example would be: asyncio.run(main())
    return main


# 🍲🚀✨🎯