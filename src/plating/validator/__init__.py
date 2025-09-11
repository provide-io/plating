#
# plating/test_runner/__init__.py
#
"""Test runner module for plating example files."""

from .adapters import PlatingTestAdapter, parse_stir_results, run_tests_with_stir
from .core import TestResult, run_tests
from .reporters import generate_report
from .suite_builder import prepare_bundles_summary, prepare_test_suites_for_stir
from .utils import get_terraform_version

__all__ = [
    # Main classes
    "PlatingTestAdapter",
    "TestResult",
    # Core functions
    "run_tests",
    "run_tests_with_stir",
    "parse_stir_results",
    # Suite preparation
    "prepare_test_suites_for_stir", 
    "prepare_bundles_summary",
    # Reporting
    "generate_report",
    # Utilities
    "get_terraform_version",
]

# 🧪📦🎯