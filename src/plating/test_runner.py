#
# plating/test_runner.py
#
"""Test runner for plating example files."""

from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from rich.console import Console
from rich.table import Table

from typing import Any

from provide.foundation import logger, pout, perr
from provide.foundation.process import run_command, ProcessError

from plating.config import get_config
from plating.plating import PlatingBundle, PlatingDiscovery

console = Console()

# Cache terraform version to avoid repeated subprocess calls
_terraform_version_cache = None


def _get_terraform_version() -> tuple[str, str]:
    """Get the Terraform/OpenTofu binary and version being used.

    Returns:
        Tuple of (binary_name, version_string)
    """
    global _terraform_version_cache

    # Return cached version if available
    if _terraform_version_cache is not None:
        return _terraform_version_cache

    # Get binary from config
    config = get_config()
    tf_binary = config.terraform_binary
    binary_name = "OpenTofu" if "tofu" in tf_binary else "Terraform"

    try:
        result = run_command(
            [tf_binary, "-version"], capture_output=True, timeout=5
        )
        version_lines = result.stdout.strip().split("\n")
        if version_lines:
            version_string = version_lines[0]
        else:
            version_string = "Unknown version"
    except ProcessError:
        version_string = "Unable to determine version"

    _terraform_version_cache = (binary_name, version_string)
    return _terraform_version_cache


def prepare_test_suites_for_stir(
    bundles: list[PlatingBundle], output_dir: Path
) -> list[Path]:
    """Prepare test suites from plating bundles for stir execution.

    Args:
        bundles: List of plating bundles to prepare
        output_dir: Directory to create test suites in

    Returns:
        List of paths to created test suite directories
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    test_suites = []

    for bundle in bundles:
        examples = bundle.load_examples()
        if not examples:
            continue

        suite_dir = _create_test_suite(bundle, examples, output_dir)
        if suite_dir:
            test_suites.append(suite_dir)

    return test_suites


def run_tests_with_stir(test_dir: Path, parallel: int = 4) -> dict[str, Any]:
    """Run tests using tofusoup stir command.

    Args:
        test_dir: Directory containing test suites
        parallel: Number of parallel tests to run

    Returns:
        Dictionary with test results from stir
    """
    import json
    import subprocess

    # Check if soup command is available
    soup_cmd = shutil.which("soup")
    if not soup_cmd:
        raise RuntimeError(
            "tofusoup is not installed or not in PATH. "
            "Please install tofusoup to use the test command."
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
    except ProcessError as e:
        # Check if this is the pyproject.toml error
        error_msg = getattr(e, 'stderr', '') or getattr(e, 'stdout', '') or str(e)
        if "pyproject.toml" in error_msg:
            # This is a known issue with soup tool install - raise RuntimeError to trigger fallback
            raise RuntimeError(
                "soup stir requires pyproject.toml context. "
                "Falling back to simple runner."
            ) from e
        
        # For other process errors, log and re-raise
        logger.error("TofuSoup stir execution failed", error=str(e))
        raise RuntimeError(f"Failed to run tofusoup stir: {e}") from e

    # Parse JSON output
    if result.stdout:
        return json.loads(result.stdout)
    else:
        return {"total": 0, "passed": 0, "failed": 0, "test_details": {}}


def parse_stir_results(
    stir_output: dict[str, any], bundles: list[PlatingBundle] = None
) -> dict[str, Any]:
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
        results["bundles"] = {}
        for bundle in bundles:
            fixture_count = 0
            if hasattr(bundle.fixtures_dir, "exists") and bundle.fixtures_dir.exists():
                try:
                    fixture_count = sum(
                        1 for _ in bundle.fixtures_dir.rglob("*") if _.is_file()
                    )
                except (AttributeError, TypeError):
                    # Handle mock objects in tests
                    fixture_count = 0

            try:
                examples = bundle.load_examples()
                examples_count = len(examples) if examples else 0
            except (AttributeError, TypeError):
                examples_count = 0

            try:
                has_fixtures = (
                    hasattr(bundle.fixtures_dir, "exists")
                    and bundle.fixtures_dir.exists()
                )
            except (AttributeError, TypeError):
                has_fixtures = False

            results["bundles"][bundle.name] = {
                "component_type": bundle.component_type,
                "examples_count": examples_count,
                "has_fixtures": has_fixtures,
                "fixture_count": fixture_count,
            }

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
                console.print(
                    "[yellow]No test suites created (no components with examples found)[/yellow]"
                )
                return {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "failures": {},
                }

            # Try to run with stir
            try:
                stir_results = run_tests_with_stir(self.output_dir, parallel)
                results = parse_stir_results(stir_results, bundles)

            except (RuntimeError, FileNotFoundError):
                if self.fallback_to_simple:
                    console.print(
                        "[yellow]tofusoup not available, falling back to simple runner[/yellow]"
                    )
                    results = _run_simple_tests(self.output_dir)
                    results = parse_stir_results(results, bundles)
                else:
                    raise

            # Generate report if requested
            if output_file:
                _generate_report(results, output_file, output_format)

            return results

        finally:
            # Cleanup temp directory
            if self._temp_dir and self._temp_dir.exists():
                shutil.rmtree(self._temp_dir, ignore_errors=True)

    def _discover_bundles(
        self, component_types: list[str] = None
    ) -> list[PlatingBundle]:
        """Discover plating bundles."""
        discovery = PlatingDiscovery()

        if component_types:
            # Collect all bundles for specified types without duplicates
            seen = set()
            bundles = []
            for ct in component_types:
                for bundle in discovery.discover_bundles(component_type=ct):
                    if bundle.name not in seen:
                        bundles.append(bundle)
                        seen.add(bundle.name)
        else:
            bundles = discovery.discover_bundles()

        console.print(
            f"Found [bold green]{len(bundles)}[/bold green] components with plating bundles"
        )
        return bundles

    def _prepare_test_suites(self, bundles: list[PlatingBundle]) -> list[Path]:
        """Prepare test suites for stir execution."""
        console.print(
            f"\n[bold yellow]📦 Assembling test suites in:[/bold yellow] {self.output_dir}"
        )

        test_suites = prepare_test_suites_for_stir(bundles, self.output_dir)

        # Show summary table
        if test_suites:
            table = Table(title="Test Suite Assembly", box=None)
            table.add_column("Component", style="cyan", no_wrap=True)
            table.add_column("Type", style="magenta")
            table.add_column("Test Directory", style="yellow")

            for suite_dir in test_suites:
                # Parse suite name to get component info
                parts = suite_dir.name.rsplit("_test", 1)[0].split("_", 1)
                comp_type = parts[0]
                comp_name = parts[1] if len(parts) > 1 else "unknown"

                table.add_row(comp_name, comp_type, suite_dir.name)

            console.print(table)

        return test_suites


def run_plating_tests(
    component_types: list[str] | None = None,
    parallel: int = 4,
    output_dir: Path | None = None,
    output_file: Path | None = None,
    output_format: str = "json",
) -> dict[str, Any]:
    """Run all plating example files as Terraform tests.

    This is a compatibility wrapper that uses PlatingTestAdapter.

    Args:
        component_types: Optional list of component types to filter by
        parallel: Number of tests to run in parallel
        output_dir: Directory to create test suites in
        output_file: Optional file to write report to
        output_format: Format for report (json, markdown, html)

    Returns:
        Dictionary with test results including:
        - total: Total number of tests
        - passed: Number of passed tests
        - failed: Number of failed tests
        - failures: Dict mapping test names to error messages
    """
    # Use the new adapter
    adapter = PlatingTestAdapter(output_dir=output_dir, fallback_to_simple=True)
    return adapter.run_tests(
        component_types=component_types,
        parallel=parallel,
        output_file=output_file,
        output_format=output_format,
    )


def _create_test_suite(
    bundle: PlatingBundle, examples: dict[str, str], output_dir: Path
) -> Path | None:
    """Create a test suite directory for a plating bundle.

    Args:
        bundle: The plating bundle
        examples: Dictionary of example files
        output_dir: Base output directory

    Returns:
        Path to the created test suite directory, or None if creation failed
    """
    # Create directory name based on component type and name
    suite_name = f"{bundle.component_type}_{bundle.name}_test"
    suite_dir = output_dir / suite_name

    try:
        suite_dir.mkdir(parents=True, exist_ok=True)

        # Track all files being created to detect collisions
        created_files = set()

        # Generate provider.tf
        provider_content = _generate_provider_tf()
        (suite_dir / "provider.tf").write_text(provider_content)
        created_files.add("provider.tf")

        # First, copy fixture files to ../fixtures directory
        fixtures = bundle.load_fixtures()
        if fixtures:
            # Create fixtures directory at parent level
            fixtures_dir = suite_dir.parent / "fixtures"
            fixtures_dir.mkdir(parents=True, exist_ok=True)

            for fixture_path, content in fixtures.items():
                fixture_file = fixtures_dir / fixture_path
                fixture_file.parent.mkdir(parents=True, exist_ok=True)
                fixture_file.write_text(content)

        # Copy and rename example files
        for example_name, content in examples.items():
            # Create test-specific filename
            if example_name == "example":
                test_filename = f"{bundle.name}.tf"
            else:
                test_filename = f"{bundle.name}_{example_name}.tf"

            if test_filename in created_files:
                console.print(
                    f"[red]❌ Collision detected: example file '{test_filename}' conflicts with fixture file in {bundle.name}[/red]"
                )
                raise Exception(f"File collision: {test_filename}")

            (suite_dir / test_filename).write_text(content)
            created_files.add(test_filename)

        return suite_dir

    except Exception as e:
        console.print(
            f"[red]⚠️  Failed to create test suite for {bundle.name}: {e}[/red]"
        )
        return None


def _generate_provider_tf() -> str:
    """Generate a standard provider.tf file for tests."""
    return """terraform {
  required_providers {
    pyvider = {
      source  = "registry.terraform.io/provide-io/pyvider"
      version = "0.0.3"
    }
  }
}

provider "pyvider" {
  # Provider configuration for tests
}
"""


def _run_simple_tests(test_dir: Path) -> dict[str, Any]:
    """Run simple terraform tests without stir.

    Note: This is a simplified version without parallel execution or rich UI.
    For advanced test running with rich UI, use tofusoup.

    Args:
        test_dir: Directory containing test suites

    Returns:
        Dictionary with test results
    """
    import subprocess

    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "skipped": 0,
        "failures": {},
        "test_details": {},
        "timestamp": datetime.now().isoformat(),
    }

    # Find all test directories
    test_dirs = [d for d in test_dir.iterdir() if d.is_dir()]
    results["total"] = len(test_dirs)

    # Get terraform binary from config
    config = get_config()
    tf_binary = config.terraform_binary

    for suite_dir in test_dirs:
        test_name = suite_dir.name
        console.print(f"Running test: {test_name}")

        test_info = {
            "name": test_name,
            "success": False,
            "skipped": False,
            "duration": 0,
            "resources": 0,
            "data_sources": 0,
            "functions": 0,
            "outputs": 0,
            "last_log": "",
            "warnings": [],
        }

        start_time = datetime.now()

        try:
            # Run terraform init
            try:
                init_result = run_command(
                    [tf_binary, "init"],
                    cwd=suite_dir,
                    capture_output=True,
                    timeout=60,
                    env=config.get_terraform_env(),
                )
            except ProcessError as e:
                logger.error("Terraform init failed", command=e.cmd, returncode=e.returncode,
                           stdout=e.stdout, stderr=e.stderr, suite=suite_dir.name)
                raise

            # Run terraform apply
            try:
                apply_result = run_command(
                    [tf_binary, "apply", "-auto-approve"],
                    cwd=suite_dir,
                    capture_output=True,
                    timeout=config.test_timeout,
                    env=config.get_terraform_env(),
                )
            except ProcessError as e:
                logger.error("Terraform apply failed", command=e.cmd, returncode=e.returncode,
                           stdout=e.stdout, stderr=e.stderr, suite=suite_dir.name)
                raise

            # Parse output for resource counts
            output = apply_result.stdout
            if "Apply complete!" in output:
                # Try to extract resource counts
                import re

                match = re.search(r"(\d+) added", output)
                if match:
                    test_info["resources"] = int(match.group(1))

            # Run terraform destroy
            destroy_result = subprocess.run(
                [tf_binary, "destroy", "-auto-approve"],
                cwd=suite_dir,
                capture_output=True,
                text=True,
                timeout=config.test_timeout,
                env=config.get_terraform_env(),
            )

            if destroy_result.returncode != 0:
                raise subprocess.CalledProcessError(
                    destroy_result.returncode,
                    destroy_result.args,
                    destroy_result.stdout,
                    destroy_result.stderr,
                )

            test_info["success"] = True
            results["passed"] += 1
            console.print(f"  ✅ {test_name}: PASS")

        except subprocess.CalledProcessError as e:
            test_info["success"] = False
            test_info["last_log"] = str(e.stderr if e.stderr else e.stdout)
            results["failed"] += 1
            results["failures"][test_name] = test_info["last_log"]
            console.print(f"  ❌ {test_name}: FAIL")

        except subprocess.TimeoutExpired:
            test_info["success"] = False
            test_info["last_log"] = "Test timed out"
            results["failed"] += 1
            results["failures"][test_name] = "Test timed out"
            console.print(f"  ⏱️ {test_name}: TIMEOUT")

        except Exception as e:
            test_info["success"] = False
            test_info["last_log"] = str(e)
            results["failed"] += 1
            results["failures"][test_name] = str(e)
            console.print(f"  ❌ {test_name}: ERROR")

        end_time = datetime.now()
        test_info["duration"] = (end_time - start_time).total_seconds()
        results["test_details"][test_name] = test_info

    return results


def _extract_warnings_from_log(log_file: Path) -> list[dict[str, str]]:
    """Extract warning messages from a Terraform log file."""
    warnings = []
    try:
        with open(log_file) as f:
            for line in f:
                try:
                    log_entry = json.loads(line)
                    if log_entry.get("@level") == "warn":
                        warnings.append(
                            {
                                "message": log_entry.get("@message", ""),
                                "timestamp": log_entry.get("@timestamp", ""),
                            }
                        )
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to parse log file: {e}[/yellow]")
    return warnings


def _generate_report(results: dict[str, any], output_file: Path, format: str) -> None:
    """Generate a test report in the specified format."""
    if format == "json":
        _generate_json_report(results, output_file)
    elif format == "markdown":
        _generate_markdown_report(results, output_file)
    elif format == "html":
        _generate_html_report(results, output_file)


def _generate_json_report(results: dict[str, any], output_file: Path) -> None:
    """Generate a JSON format test report."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)


def _generate_markdown_report(results: dict[str, any], output_file: Path) -> None:
    """Generate a Markdown format test report."""
    with open(output_file, "w") as f:
        f.write("# Garnish Test Report\n\n")
        f.write(f"Generated: {results['timestamp']}\n\n")
        f.write(
            f"**Terraform Version**: {results.get('terraform_version', 'Unknown')}\n\n"
        )

        # Summary
        f.write("## Summary\n\n")
        f.write(f"- **Total Tests**: {results['total']}\n")
        f.write(f"- **Passed**: {results['passed']} ✅\n")
        f.write(f"- **Failed**: {results['failed']} ❌\n")
        f.write(f"- **Warnings**: {results.get('warnings', 0)} ⚠️\n")
        f.write(f"- **Skipped**: {results.get('skipped', 0)}\n\n")

        # Group tests by component type
        tests_by_type = {}
        bundles = results.get("bundles", {})
        test_details = results.get("test_details", {})

        for test_name, details in test_details.items():
            # Determine component type from test name prefix
            if test_name.startswith("function_"):
                component_type = "function"
                component_name = test_name.replace("function_", "").replace("_test", "")
            elif test_name.startswith("resource_"):
                component_type = "resource"
                component_name = test_name.replace("resource_", "").replace("_test", "")
            elif test_name.startswith("data_source_"):
                component_type = "data_source"
                component_name = test_name.replace("data_source_", "").replace(
                    "_test", ""
                )
            else:
                component_type = "unknown"
                component_name = test_name.replace("_test", "")

            if component_type not in tests_by_type:
                tests_by_type[component_type] = []

            tests_by_type[component_type].append(
                {
                    "name": component_name,
                    "test_name": test_name,
                    "details": details,
                    "bundle_info": bundles.get(component_name, {}),
                }
            )

        # Write test results by component type
        for comp_type in ["resource", "data_source", "function"]:
            if comp_type in tests_by_type:
                type_display = comp_type.replace("_", " ").title()
                f.write(f"## {type_display} Tests\n\n")

                # Determine which columns have data for this component type
                has_resources = any(
                    test["details"].get("resources", 0) > 0
                    for test in tests_by_type[comp_type]
                )
                has_data_sources = any(
                    test["details"].get("data_sources", 0) > 0
                    for test in tests_by_type[comp_type]
                )
                has_functions = any(
                    test["details"].get("functions", 0) > 0
                    for test in tests_by_type[comp_type]
                )
                has_outputs = any(
                    test["details"].get("outputs", 0) > 0
                    for test in tests_by_type[comp_type]
                )

                # Build dynamic headers
                headers = ["Component", "Status", "Duration"]
                if has_resources:
                    headers.append("Resources")
                if has_data_sources:
                    headers.append("Data Sources")
                if has_functions:
                    headers.append("Functions")
                if has_outputs:
                    headers.append("Outputs")
                headers.extend(["Examples", "Fixtures"])

                f.write("| " + " | ".join(headers) + " |\n")
                f.write("|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|\n")

                # Sort tests by name
                tests_by_type[comp_type].sort(key=lambda x: x["name"])

                for test in tests_by_type[comp_type]:
                    details = test["details"]
                    bundle_info = test["bundle_info"]

                    status_icon = (
                        "✅"
                        if details.get("success", False)
                        else "❌"
                        if not details.get("skipped", False)
                        else "⏭️"
                    )
                    duration = (
                        f"{details.get('duration', 0):.1f}s"
                        if details.get("duration", 0) > 0
                        else "-"
                    )

                    # Build row data
                    row = [test["name"], status_icon, duration]

                    if has_resources:
                        row.append(
                            str(details.get("resources", 0))
                            if details.get("resources", 0) > 0
                            else "-"
                        )
                    if has_data_sources:
                        row.append(
                            str(details.get("data_sources", 0))
                            if details.get("data_sources", 0) > 0
                            else "-"
                        )
                    if has_functions:
                        row.append(
                            str(details.get("functions", 0))
                            if details.get("functions", 0) > 0
                            else "-"
                        )
                    if has_outputs:
                        row.append(
                            str(details.get("outputs", 0))
                            if details.get("outputs", 0) > 0
                            else "-"
                        )

                    examples = bundle_info.get("examples_count", 1)
                    fixture_count = bundle_info.get("fixture_count", 0)
                    fixtures_display = str(fixture_count) if fixture_count > 0 else "-"

                    row.extend([str(examples), fixtures_display])

                    f.write("| " + " | ".join(row) + " |\n")

                f.write("\n")

        # Failed tests details
        if results["failed"] > 0:
            f.write("## Failed Test Details\n\n")
            for test_name, error in results.get("failures", {}).items():
                f.write(f"### ❌ {test_name}\n\n")
                f.write(f"**Error**: {error}\n\n")

                # Add more details if available
                if test_name in test_details:
                    details = test_details[test_name]
                    if details.get("warnings"):
                        f.write(f"**Warnings** ({len(details['warnings'])}):\n")
                        for warning in details["warnings"]:
                            f.write(f"- {warning['message']}\n")
                        f.write("\n")

                    if details.get("last_log"):
                        f.write("**Last Log Entry**:\n")
                        f.write(f"```\n{details['last_log']}\n```\n\n")

        # Tests with warnings
        tests_with_warnings = [
            (name, details)
            for name, details in test_details.items()
            if details.get("warnings") and len(details["warnings"]) > 0
        ]

        if tests_with_warnings:
            f.write("## Tests with Warnings\n\n")
            for test_name, details in tests_with_warnings:
                f.write(f"### ⚠️  {test_name}\n\n")
                for warning in details["warnings"]:
                    f.write(f"- {warning['message']}\n")
                f.write("\n")


def _generate_html_report(results: dict[str, any], output_file: Path) -> None:
    """Generate an HTML format test report."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Garnish Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .warning {{ color: orange; }}
        .test-details {{ margin-top: 20px; }}
        .test-case {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; }}
        .test-case.success {{ border-left: 5px solid green; }}
        .test-case.failure {{ border-left: 5px solid red; }}
        .test-case.skipped {{ border-left: 5px solid gray; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .warning-list {{ background-color: #fff8dc; padding: 10px; margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>Garnish Test Report</h1>
    <p>Generated: {results["timestamp"]}</p>
    <p><strong>Terraform Version</strong>: {results.get("terraform_version", "Unknown")}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li><strong>Total Tests</strong>: {results["total"]}</li>
            <li class="passed"><strong>Passed</strong>: {results["passed"]} ✅</li>
            <li class="failed"><strong>Failed</strong>: {results["failed"]} ❌</li>
            <li class="warning"><strong>Warnings</strong>: {results["warnings"]} ⚠️</li>
            <li><strong>Skipped</strong>: {results["skipped"]}</li>
        </ul>
    </div>
    
    <div class="test-details">
        <h2>Test Details</h2>
"""

    for test_name, details in results.get("test_details", {}).items():
        status_class = (
            "success"
            if details["success"]
            else "failure"
            if not details["skipped"]
            else "skipped"
        )
        status_icon = (
            "✅" if details["success"] else "❌" if not details["skipped"] else "⏭️"
        )

        html_content += f"""
        <div class="test-case {status_class}">
            <h3>{status_icon} {test_name}</h3>
            <table>
                <tr><td><strong>Duration</strong></td><td>{details["duration"]:.2f}s</td></tr>
                <tr><td><strong>Resources</strong></td><td>{details["resources"]}</td></tr>
                <tr><td><strong>Data Sources</strong></td><td>{details["data_sources"]}</td></tr>
                <tr><td><strong>Functions</strong></td><td>{details["functions"]}</td></tr>
                <tr><td><strong>Outputs</strong></td><td>{details["outputs"]}</td></tr>
            </table>
"""

        if details["warnings"]:
            html_content += f"""
            <div class="warning-list">
                <h4>Warnings ({len(details["warnings"])})</h4>
                <ul>
"""
            for warning in details["warnings"]:
                html_content += f"                    <li>{warning['message']}</li>\n"
            html_content += """                </ul>
            </div>
"""

        if not details["success"] and not details["skipped"]:
            html_content += f"""
            <div style="background-color: #ffeeee; padding: 10px; margin-top: 10px;">
                <h4>Error</h4>
                <pre>{details["last_log"]}</pre>
            </div>
"""

        html_content += "        </div>\n"

    # Bundle information table
    html_content += """
    <h2>Bundle Information</h2>
    <table>
        <tr>
            <th>Component</th>
            <th>Type</th>
            <th>Examples</th>
            <th>Has Fixtures</th>
        </tr>
"""

    for bundle_name, bundle_info in results.get("bundles", {}).items():
        has_fixtures = "✓" if bundle_info["has_fixtures"] else "✗"
        html_content += f"""
        <tr>
            <td>{bundle_name}</td>
            <td>{bundle_info["component_type"]}</td>
            <td>{bundle_info["examples_count"]}</td>
            <td>{has_fixtures}</td>
        </tr>
"""

    html_content += """
    </table>
</body>
</html>
"""

    with open(output_file, "w") as f:
        f.write(html_content)


# 🧪📦🎯


# 🍲🥄🧪🪄
