#
# tofusoup/garnish/test_runner.py
#
"""Test runner for garnish example files."""

import asyncio
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from garnish.garnish import GarnishBundle, GarnishDiscovery

console = Console()


def _get_terraform_version() -> tuple[str, str]:
    """Get the Terraform/OpenTofu binary and version being used.

    Returns:
        Tuple of (binary_name, version_string)
    """
    # Check which binary is available
    tf_binary = shutil.which("tofu") or shutil.which("terraform") or "terraform"
    binary_name = "OpenTofu" if "tofu" in tf_binary else "Terraform"

    try:
        result = subprocess.run(
            [tf_binary, "-version"], capture_output=True, text=True, timeout=5
        )
        version_lines = result.stdout.strip().split("\n")
        if version_lines:
            version_string = version_lines[0]
        else:
            version_string = "Unknown version"
    except Exception:
        version_string = "Unable to determine version"

    return binary_name, version_string


def run_garnish_tests(
    component_types: list[str] | None = None,
    parallel: int = 4,
    output_dir: Path | None = None,
    output_file: Path | None = None,
    output_format: str = "json",
) -> dict[str, any]:
    """Run all garnish example files as Terraform tests.

    Args:
        component_types: Optional list of component types to filter by
        parallel: Number of tests to run in parallel
        output_dir: Directory to create test suites in

    Returns:
        Dictionary with test results including:
        - total: Total number of tests
        - passed: Number of passed tests
        - failed: Number of failed tests
        - failures: Dict mapping test names to error messages
    """
    # Create temporary directory if not specified
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="garnish-tests-"))
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Show Terraform version info
        binary_name, version_string = _get_terraform_version()
        console.print(
            Panel(
                f"[bold cyan]{binary_name}[/bold cyan]\n{version_string}",
                title="🔧 Test Environment",
                border_style="blue",
            )
        )

        # Discover all garnish bundles
        console.print("\n[bold yellow]🔍 Discovering garnish bundles...[/bold yellow]")
        discovery = GarnishDiscovery()
        bundles = []

        if component_types:
            for ct in component_types:
                bundles.extend(discovery.discover_bundles(component_type=ct))
        else:
            bundles = discovery.discover_bundles()

        console.print(
            f"Found [bold green]{len(bundles)}[/bold green] components with garnish bundles"
        )

        # Create test suites for each bundle with examples
        console.print(
            f"\n[bold yellow]📦 Assembling test suites in:[/bold yellow] {output_dir}"
        )

        # Create a table to show test suite assembly
        table = Table(title="Test Suite Assembly", box=None)
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Examples", style="green", justify="center")
        table.add_column("Test Directory", style="yellow")

        test_suites = []
        total_examples = 0

        for bundle in bundles:
            examples = bundle.load_examples()
            if examples:
                suite_dir = _create_test_suite(bundle, examples, output_dir)
                if suite_dir:
                    test_suites.append(suite_dir)
                    total_examples += len(examples)

                    # Add to table
                    table.add_row(
                        bundle.name,
                        bundle.component_type,
                        str(len(examples)),
                        suite_dir.name,
                    )

        if table.row_count > 0:
            console.print(table)
            console.print(
                f"\n[bold]Total:[/bold] {len(test_suites)} test suites, {total_examples} examples"
            )

        if not test_suites:
            console.print(
                "[yellow]No test suites created (no components with examples found)[/yellow]"
            )
            return {"total": 0, "passed": 0, "failed": 0, "failures": {}}

        # Show what files were created for first test suite as example
        if test_suites:
            first_suite = test_suites[0]
            console.print(
                f"\n[bold yellow]📄 Example test suite contents:[/bold yellow] {first_suite.name}"
            )
            for tf_file in sorted(first_suite.glob("*.tf")):
                console.print(f"  - {tf_file.name}")

        # Run tests using simple runner
        console.print(
            f"\n[bold yellow]🚀 Running tests...[/bold yellow]\n"
        )
        results = _run_simple_tests(output_dir)

        # Enrich results with bundle information
        results["bundles"] = {}
        for bundle in bundles:
            # Count fixture files recursively
            fixture_count = 0
            if bundle.fixtures_dir.exists():
                fixture_count = sum(
                    1 for _ in bundle.fixtures_dir.rglob("*") if _.is_file()
                )

            results["bundles"][bundle.name] = {
                "component_type": bundle.component_type,
                "examples_count": len(bundle.load_examples()),
                "has_fixtures": bundle.fixtures_dir.exists(),
                "fixture_count": fixture_count,
            }
        results["terraform_version"] = version_string

        # Generate report if output file specified
        if output_file:
            _generate_report(results, output_file, output_format)
            console.print(
                f"\n[bold green]📝 Test report written to:[/bold green] {output_file}"
            )

        return results

    finally:
        # Clean up temporary directory if it was auto-created
        if output_dir and output_dir.name.startswith("garnish-tests-"):
            shutil.rmtree(output_dir, ignore_errors=True)


def _create_test_suite(
    bundle: GarnishBundle, examples: dict[str, str], output_dir: Path
) -> Path | None:
    """Create a test suite directory for a garnish bundle.

    Args:
        bundle: The garnish bundle
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
      source = "local/providers/pyvider"
      version = "0.1.0"
    }
  }
}

provider "pyvider" {
  # Provider configuration for tests
}
"""


def _run_simple_tests(test_dir: Path) -> dict[str, any]:
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
    
    # Get terraform binary
    tf_binary = shutil.which("tofu") or shutil.which("terraform") or "terraform"
    
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
            init_result = subprocess.run(
                [tf_binary, "init"],
                cwd=suite_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if init_result.returncode != 0:
                raise subprocess.CalledProcessError(
                    init_result.returncode, 
                    init_result.args,
                    init_result.stdout,
                    init_result.stderr
                )
            
            # Run terraform apply
            apply_result = subprocess.run(
                [tf_binary, "apply", "-auto-approve"],
                cwd=suite_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if apply_result.returncode != 0:
                raise subprocess.CalledProcessError(
                    apply_result.returncode,
                    apply_result.args,
                    apply_result.stdout,
                    apply_result.stderr
                )
            
            # Parse output for resource counts
            output = apply_result.stdout
            if "Apply complete!" in output:
                # Try to extract resource counts
                import re
                match = re.search(r'(\d+) added', output)
                if match:
                    test_info["resources"] = int(match.group(1))
            
            # Run terraform destroy
            destroy_result = subprocess.run(
                [tf_binary, "destroy", "-auto-approve"],
                cwd=suite_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if destroy_result.returncode != 0:
                raise subprocess.CalledProcessError(
                    destroy_result.returncode,
                    destroy_result.args,
                    destroy_result.stdout,
                    destroy_result.stderr
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
    except Exception:
        pass
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
        f.write(f"- **Warnings**: {results['warnings']} ⚠️\n")
        f.write(f"- **Skipped**: {results['skipped']}\n\n")

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
                    test["details"]["resources"] > 0
                    for test in tests_by_type[comp_type]
                )
                has_data_sources = any(
                    test["details"]["data_sources"] > 0
                    for test in tests_by_type[comp_type]
                )
                has_functions = any(
                    test["details"]["functions"] > 0
                    for test in tests_by_type[comp_type]
                )
                has_outputs = any(
                    test["details"]["outputs"] > 0 for test in tests_by_type[comp_type]
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
                        if details["success"]
                        else "❌"
                        if not details["skipped"]
                        else "⏭️"
                    )
                    duration = (
                        f"{details['duration']:.1f}s"
                        if details["duration"] > 0
                        else "-"
                    )

                    # Build row data
                    row = [test["name"], status_icon, duration]

                    if has_resources:
                        row.append(
                            str(details["resources"])
                            if details["resources"] > 0
                            else "-"
                        )
                    if has_data_sources:
                        row.append(
                            str(details["data_sources"])
                            if details["data_sources"] > 0
                            else "-"
                        )
                    if has_functions:
                        row.append(
                            str(details["functions"])
                            if details["functions"] > 0
                            else "-"
                        )
                    if has_outputs:
                        row.append(
                            str(details["outputs"]) if details["outputs"] > 0 else "-"
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
