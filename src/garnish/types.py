#
# garnish/types.py
#
"""Type definitions for garnish."""

from typing import TypedDict, Any, Optional


class TestResult(TypedDict):
    """Result from a single test execution."""
    name: str
    status: str  # "passed", "failed", "skipped"
    duration: float
    error: Optional[str]
    output: Optional[str]


class TestSuiteResult(TypedDict):
    """Result from a test suite execution."""
    suite_name: str
    test_dir: str
    results: list[TestResult]
    total_duration: float
    passed: int
    failed: int
    skipped: int


class StirResult(TypedDict):
    """Result from soup stir execution."""
    success: bool
    test_suites: list[TestSuiteResult]
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    errors: list[str]


class DressResult(TypedDict):
    """Result from dressing components."""
    resources: int
    data_sources: int
    functions: int
    total: int
    errors: list[str]


class ValidationResult(TypedDict):
    """Result from validation operations."""
    valid: bool
    errors: list[str]
    warnings: list[str]


class SchemaInfo(TypedDict):
    """Schema information for a component."""
    name: str
    type: str
    description: str
    schema: dict[str, Any]
    schema_markdown: str


class ProviderInfo(TypedDict):
    """Provider information."""
    short_name: str
    rendered_name: str
    description: str
    version: str