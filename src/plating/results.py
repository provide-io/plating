#
# plating/results.py
#
"""Result dataclasses for plating operations."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CleanResult:
    """Result from clean operation."""

    removed: list[Path]
    dirs_removed: list[Path]
    bytes_freed: int
    dry_run: bool = False

    @property
    def total_items(self) -> int:
        """Total number of items (files + directories) removed."""
        return len(self.removed) + len(self.dirs_removed)


@dataclass
class AdornResult:
    """Result from adorn operation."""

    adorned: dict[str, int]  # component_type -> count
    skipped: list[str]  # Already adorned component names
    errors: list[str]  # Any errors encountered
    duration: float = 0.0

    @property
    def total_adorned(self) -> int:
        """Total number of components adorned."""
        return sum(self.adorned.values())

    @property
    def success(self) -> bool:
        """Whether the operation succeeded without errors."""
        return len(self.errors) == 0


@dataclass
class PlateResult:
    """Result from plate operation."""

    plated: list[str]  # Files generated
    bundles_processed: int
    errors: list[str]
    duration: float = 0.0
    cleaned_first: bool = False

    @property
    def success(self) -> bool:
        """Whether the operation succeeded without errors."""
        return len(self.errors) == 0


@dataclass
class TestResult:
    """Result from test execution."""

    total: int
    passed: int
    failed: int
    warnings: int = 0
    skipped: int = 0
    failures: dict[str, str] = None  # test_name -> error_message
    test_details: dict[str, dict[str, Any]] = None  # Detailed test info
    duration: float = 0.0
    terraform_version: str = ""
    bundles: dict[str, dict[str, Any]] = None  # Bundle information

    def __post_init__(self):
        if self.failures is None:
            self.failures = {}
        if self.test_details is None:
            self.test_details = {}
        if self.bundles is None:
            self.bundles = {}

    @property
    def success(self) -> bool:
        """Whether all tests passed."""
        return self.failed == 0

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total == 0:
            return 100.0
        return (self.passed / self.total) * 100.0


@dataclass
class ValidationResult:
    """Result from validation operations."""

    valid: bool
    errors: list[str]
    warnings: list[str]

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

    @property
    def has_issues(self) -> bool:
        """Whether there are any errors or warnings."""
        return len(self.errors) > 0 or len(self.warnings) > 0


# 📊📈✅