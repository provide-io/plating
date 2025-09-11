#
# plating/test_runner/adapters.py
#
"""Test adapters for integrating with external test runners."""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from provide.foundation import logger
from provide.foundation.process import ProcessError, run_command
from rich.console import Console

from plating.config import get_config
from plating.plating import PlatingBundle, PlatingDiscovery

from .core import _run_simple_tests
from .suite_builder import prepare_bundles_summary, prepare_test_suites_for_stir
from .utils import get_terraform_version

console = Console()


def run_tests_with_stir(test_dir: Path, parallel: int = 4) -> dict[str, Any]:
    """Run tests using tofusoup stir command.

    Args:
        test_dir: Directory containing test suites
        parallel: Number of parallel tests to run

    Returns:
        Dictionary with test results from stir
    """
    # Check if soup command is available
    soup_cmd = shutil.which("soup")
    if not soup_cmd:
        raise RuntimeError(
            "tofusoup is not installed or not in PATH. Please install tofusoup to use the test command."
        )

    # Build stir command - ensure absolute path
    test_dir_abs = test_dir.resolve()
    cmd = ["soup", "stir", str(test_dir_abs), "--json"]

    # Run stir with plugin cache to avoid re-downloading providers
    env = os.environ.copy()

    # Set up environment from config
    config = get_config()
    env = config.get_terraform_env()

    # Find a directory with pyproject.toml to run from
    # First, check current directory
    cwd = Path.cwd()
    run_dir = cwd

    # Look for pyproject.toml in current or parent directories
    if not (run_dir / "pyproject.toml").exists():
        # Try looking up the directory tree
        for parent in cwd.parents:
            if (parent / "pyproject.toml").exists():
                run_dir = parent
                break
        else:
            # If not found, check if tofusoup is in a known location
            tofusoup_dir = Path.home() / "code" / "gh" / "provide-io" / "tofusoup"
            if tofusoup_dir.exists() and (tofusoup_dir / "pyproject.toml").exists():
                run_dir = tofusoup_dir
            else:
                # Fallback: run from test directory (will likely fail but allows graceful fallback)
                run_dir = test_dir

    try:
        result = run_command(
            cmd,
            capture_output=True,
            env=env,
            cwd=str(run_dir),  # Run from directory with pyproject.toml
        )
    except FileNotFoundError as e:
        # Handle case where command is not found
        raise RuntimeError(
            f"TofuSoup not found or not installed. Please install tofusoup to use stir testing. Error: {e}"
        ) from e
    except ProcessError as e:
        # Check if this is the pyproject.toml error
        error_msg = str(e)
        if hasattr(e, "stderr") and e.stderr:
            error_msg += f" {e.stderr}"
        if hasattr(e, "stdout") and e.stdout:
            error_msg += f" {e.stdout}"
        if "pyproject.toml" in error_msg:
            # This is a known issue with soup tool install - raise RuntimeError to trigger fallback
            raise RuntimeError(
                "soup stir requires pyproject.toml context. Falling back to simple runner."
            ) from e

        # Check if this is a command not found error
        if any(phrase in error_msg.lower() for phrase in ["not found", "no such file", "command not found"]):
            raise RuntimeError(
                f"TofuSoup not found or not installed. Please install tofusoup to use stir testing. Error: {e}"
            ) from e

        # For other process errors, log and re-raise
        logger.error("TofuSoup stir execution failed", error=str(e))
        raise RuntimeError(f"Failed to run tofusoup stir: {e}") from e

    # Parse JSON output
    if result.stdout:
        return json.loads(result.stdout)
    else:
        return {"total": 0, "passed": 0, "failed": 0, "test_details": {}}


def parse_stir_results(stir_output: dict[str, Any], bundles: list[PlatingBundle] = None) -> dict[str, Any]:
    """Parse and enrich stir results with plating bundle information.

    Args:
        stir_output: Raw output from stir command
        bundles: Optional list of plating bundles for enrichment

    Returns:
        Dictionary with plating-formatted test results
    """
    # Start with stir results, ensuring required keys exist
    results = dict(stir_output)

    # Ensure essential keys exist with defaults
    results.setdefault("total", 0)
    results.setdefault("passed", 0)
    results.setdefault("failed", 0)
    results.setdefault("test_details", {})

    # Add bundle information if provided
    if bundles:
        bundle_summary = prepare_bundles_summary(bundles)
        results.update(bundle_summary)

    # Ensure timestamp is present
    if "timestamp" not in results:
        results["timestamp"] = datetime.now().isoformat()

    return results


class PlatingTestAdapter:
    """Adapter to run plating tests using tofusoup stir."""

    def __init__(self, output_dir: Path = None, fallback_to_simple: bool = False):
        """Initialize the test adapter.

        Args:
            output_dir: Directory for test suites (temp if not specified)
            fallback_to_simple: Whether to fall back to simple runner if stir unavailable
        """
        self.output_dir = output_dir
        self.fallback_to_simple = fallback_to_simple
        self._temp_dir = None

    def run_tests(
        self,
        component_types: list[str] = None,
        parallel: int = 4,
        output_file: Path = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """Run plating tests using stir.

        Args:
            component_types: Optional list of component types to filter
            parallel: Number of parallel tests
            output_file: Optional file to write report to
            output_format: Format for report (json, markdown, html)

        Returns:
            Dictionary with test results
        """
        try:
            # Setup output directory
            if self.output_dir is None:
                self._temp_dir = Path(tempfile.mkdtemp(prefix="plating-tests-"))
                self.output_dir = self._temp_dir
            else:
                self.output_dir.mkdir(parents=True, exist_ok=True)

            # Discover bundles
            bundles = self._discover_bundles(component_types)

            if not bundles:
                return {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "warnings": 0,
                    "skipped": 0,
                    "failures": {},
                    "test_details": {},
                    "timestamp": datetime.now().isoformat(),
                }

            # Prepare test suites
            test_suites = self._prepare_test_suites(bundles)

            if not test_suites:
                console.print("[yellow]No test suites created (no components with examples found)[/yellow]")
                return {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "failures": {},
                }

            # Try to run with stir first, fall back to simple if needed
            try:
                results = run_tests_with_stir(self.output_dir, parallel)
                results = parse_stir_results(results, bundles)
            except RuntimeError as e:
                if self.fallback_to_simple:
                    console.print(f"[yellow]Stir unavailable ({e}), falling back to simple runner[/yellow]")
                    results = _run_simple_tests(self.output_dir)
                    results = parse_stir_results(results, bundles)
                else:
                    raise

            # Add terraform version
            binary_name, version = get_terraform_version()
            results["terraform_version"] = f"{binary_name} {version}"

            # Generate report if requested
            if output_file:
                from .reporters import generate_report

                generate_report(results, output_file, output_format)

            return results

        finally:
            # Clean up temp directory if we created it
            if self._temp_dir and self._temp_dir.exists():
                shutil.rmtree(self._temp_dir, ignore_errors=True)

    def _discover_bundles(self, component_types: list[str] = None) -> list[PlatingBundle]:
        """Discover plating bundles for testing.

        Args:
            component_types: Optional filter for component types

        Returns:
            List of discovered bundles
        """
        discovery = PlatingDiscovery()
        all_bundles = []

        if component_types:
            for component_type in component_types:
                bundles = discovery.discover_bundles(component_type)
                all_bundles.extend(bundles)
        else:
            all_bundles = discovery.discover_bundles()

        return all_bundles

    def _prepare_test_suites(self, bundles: list[PlatingBundle]) -> list[Path]:
        """Prepare test suites from bundles.

        Args:
            bundles: List of bundles to prepare

        Returns:
            List of test suite directory paths
        """
        return prepare_test_suites_for_stir(bundles, self.output_dir)


# 🔌⚡🧪