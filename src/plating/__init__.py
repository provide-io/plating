#
# plating/__init__.py
#
"""Plating - Modern documentation generation for Terraform/OpenTofu providers.

This package implements a comprehensive documentation generation system with:
- Type-safe async-first API
- Foundation integration for reliability and observability  
- Clean developer experience without backward compatibility baggage

Key Features:
- Unified Plating API for all operations
- Type-safe contexts and enums
- Async template rendering with rate limiting
- Foundation integration (retry, metrics, circuit breakers)
- Clean modern Python patterns

Example Usage:
    ```python
    from plating import Plating, ComponentType
    
    # Initialize API
    plating = Plating(provider_name="my_provider")
    
    # Adorn components
    result = await plating.adorn([ComponentType.RESOURCE])
    
    # Generate documentation
    result = await plating.plate(Path("docs"), force=True)
    
    # Validate examples
    result = await plating.validate()
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

# Foundation decorators
from plating.decorators import (
    with_retry,
    with_circuit_breaker,
    with_metrics,
    with_timing,
    plating_metrics,
)

# Core bundle system
from plating.plating import PlatingBundle, PlatingDiscovery

# Legacy CLI (still functional but uses old patterns)
from plating.cli import main

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
    
    # Core bundle system
    "PlatingBundle",
    "PlatingDiscovery",
    
    # CLI
    "main",
]


# Modern usage examples
def example_usage():
    """Example of modern API usage."""
    import asyncio
    from pathlib import Path
    
    async def main():
        # Initialize with type-safe API
        api = Plating(provider_name="my_provider")
        
        # Adorn with enum types
        adorn_result = await api.adorn([ComponentType.RESOURCE, ComponentType.DATA_SOURCE])
        print(f"Adorned {adorn_result.components_processed} components")
        
        # Generate docs with structured results
        plate_result = await api.plate(
            Path("docs"),
            component_types=[ComponentType.RESOURCE],
            force=True
        )
        
        if plate_result.success:
            print(f"Generated {len(plate_result.output_files)} files in {plate_result.duration_seconds:.2f}s")
        else:
            print(f"Errors: {plate_result.errors}")
        
        # Validate with detailed results
        validation_result = await api.validate()
        print(f"Validation: {validation_result.passed}/{validation_result.total} passed")
    
    # Example would be: asyncio.run(main())
    return main


# 🍲🚀✨🎯