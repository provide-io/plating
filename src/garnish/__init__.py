#
# garnish/__init__.py
#
"""Garnish - Documentation generation for Terraform/OpenTofu providers.

This package implements a comprehensive documentation generation system modeled after
HashiCorp's tfplugindocs tool. It extracts provider schemas, processes templates and
examples, and generates Terraform Registry-compliant documentation.
"""

from garnish.cli import main
from garnish.generator import DocsGenerator
from garnish.models import FunctionInfo, ProviderInfo, ResourceInfo

__all__ = [
    "DocsGenerator",
    "FunctionInfo",
    "ProviderInfo",
    "ResourceInfo",
    "main",
]


# 🥄📚🪄
