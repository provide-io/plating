#
# plating/validator/__init__.py
#
"""Validator module for plating example validation."""

from plating.validator.adapters import PlatingValidator, parse_validation_results, run_validation_with_stir
from plating.validator.core import run_validation
from plating.validator.reporters import generate_report
from plating.validator.suite_builder import prepare_bundles_summary, prepare_validation_suites
from plating.validator.utils import get_terraform_version
from plating.results import ValidationResult

__all__ = [
    # Main classes
    "PlatingValidator",
    "ValidationResult",
    # Core functions
    "run_validation",
    "run_validation_with_stir",
    "parse_validation_results",
    # Suite preparation
    "prepare_validation_suites", 
    "prepare_bundles_summary",
    # Reporting
    "generate_report",
    # Utilities
    "get_terraform_version",
]

# 🔍✅📊