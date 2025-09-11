#
# plating/__init__.py
#
"""Plating - Documentation generation for Terraform/OpenTofu providers.

This package implements a comprehensive documentation generation system for
Terraform/OpenTofu providers. It automatically discovers components via pyvider.hub,
processes Jinja2 templates and examples, and generates Terraform Registry-compliant
documentation with built-in validation.

Key Features:
- Unified Plating API for all operations
- Functional operations API for scripting
- Bundle-based documentation organization
- Async template rendering
- Example validation with Terraform/OpenTofu
- Rich CLI with pipeline support
"""

from plating._version import __version__
from plating.api import Plating
from plating.cli import main
from plating.generator import DocsGenerator
from plating.models import FunctionInfo, ProviderInfo, ResourceInfo
from plating.operations import (
    adorn_missing_components,
    clean_docs,
    full_pipeline,
    plate_documentation,
    validate_examples,
)
from plating.plating import PlatingBundle, PlatingDiscovery
from plating.results import AdornResult, CleanResult, PlateResult, ValidationResult
from plating.validator import PlatingValidator, run_validation

__all__ = [
    # Version
    "__version__",
    # Main API Classes
    "Plating",
    "PlatingBundle",
    "PlatingDiscovery",
    "PlatingValidator",
    # Functional Operations
    "adorn_missing_components",
    "clean_docs",
    "full_pipeline",
    "plate_documentation",
    "run_validation",
    "validate_examples",
    # Result Classes
    "AdornResult",
    "CleanResult",
    "PlateResult",
    "ValidationResult",
    # Legacy/Compatibility
    "DocsGenerator",
    "FunctionInfo",
    "ProviderInfo",
    "ResourceInfo",
    # CLI
    "main",
]


# 🥄📚🪄
