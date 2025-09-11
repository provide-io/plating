#
# plating/__init__.py
#
"""Garnish - Documentation generation for Terraform/OpenTofu providers.

This package implements a comprehensive documentation generation system modeled after
HashiCorp's tfplugindocs tool. It extracts provider schemas, processes templates and
examples, and generates Terraform Registry-compliant documentation.
"""

from plating._version import __version__

from plating.cli import main
from plating.generator import DocsGenerator
from plating.models import FunctionInfo, ProviderInfo, ResourceInfo

__all__ = [
    "__version__",
    "DocsGenerator",
    "FunctionInfo",
    "ProviderInfo",
    "ResourceInfo",
    "main",
]


# 🥄📚🪄
