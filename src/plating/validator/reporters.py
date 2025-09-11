#
# plating/test_runner/reporters.py
#
"""Report generation for test results."""

import json
from pathlib import Path
from typing import Any


def generate_report(results: dict[str, Any], output_file: Path, format: str) -> None:
    """Generate a test report in the specified format."""
    if format == "json":
        _generate_json_report(results, output_file)
    elif format == "markdown":
        _generate_markdown_report(results, output_file)
    elif format == "html":
        _generate_html_report(results, output_file)


def _generate_json_report(results: dict[str, Any], output_file: Path) -> None:
    """Generate a JSON format test report."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)


def _generate_markdown_report(results: dict[str, Any], output_file: Path) -> None:
    """Generate a Markdown format test report."""
    with open(output_file, "w") as f:
        f.write("# Plating Test Report\n\n")
        f.write(f"Generated: {results['timestamp']}\n\n")
        f.write(f"**Terraform Version**: {results.get('terraform_version', 'Unknown')}\n\n")

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
                component_name = test_name.replace("data_source_", "").replace("_test", "")
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
                    test["details"].get("resources", 0) > 0 for test in tests_by_type[comp_type]
                )
                has_data_sources = any(
                    test["details"].get("data_sources", 0) > 0 for test in tests_by_type[comp_type]
                )
                has_functions = any(
                    test["details"].get("functions", 0) > 0 for test in tests_by_type[comp_type]
                )
                has_outputs = any(test["details"].get("outputs", 0) > 0 for test in tests_by_type[comp_type])

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
                    name = test["name"]

                    # Status icon
                    if details["success"]:
                        status = "✅ PASS"
                    elif details.get("skipped", False):
                        status = "⏭️ SKIP"
                    else:
                        status = "❌ FAIL"

                    # Build row data
                    row_data = [
                        name,
                        status,
                        f"{details.get('duration', 0):.1f}s",
                    ]

                    # Add optional columns if they have data
                    if has_resources:
                        row_data.append(str(details.get("resources", 0)))
                    if has_data_sources:
                        row_data.append(str(details.get("data_sources", 0)))
                    if has_functions:
                        row_data.append(str(details.get("functions", 0)))
                    if has_outputs:
                        row_data.append(str(details.get("outputs", 0)))

                    row_data.extend(
                        [
                            str(bundle_info.get("examples_count", 0)),
                            "✓" if bundle_info.get("has_fixtures", False) else "✗",
                        ]
                    )

                    f.write("| " + " | ".join(row_data) + " |\n")

                f.write("\n")

        # Failed test details
        failed_tests = [
            (name, details) for name, details in test_details.items() if not details.get("success", False)
        ]

        if failed_tests:
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


def _generate_html_report(results: dict[str, Any], output_file: Path) -> None:
    """Generate an HTML format test report."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Plating Test Report</title>
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
    <h1>Plating Test Report</h1>
    <p>Generated: {results["timestamp"]}</p>
    <p><strong>Terraform Version</strong>: {results.get("terraform_version", "Unknown")}</p>

    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li><strong>Total Tests</strong>: {results["total"]}</li>
            <li class="passed"><strong>Passed</strong>: {results["passed"]} ✅</li>
            <li class="failed"><strong>Failed</strong>: {results["failed"]} ❌</li>
            <li class="warning"><strong>Warnings</strong>: {results.get("warnings", 0)} ⚠️</li>
            <li><strong>Skipped</strong>: {results.get("skipped", 0)}</li>
        </ul>
    </div>

    <div class="test-details">
        <h2>Test Details</h2>
"""

    for test_name, details in results.get("test_details", {}).items():
        status_class = "success" if details["success"] else "failure" if not details.get("skipped") else "skipped"
        status_icon = "✅" if details["success"] else "❌" if not details.get("skipped") else "⏭️"

        html_content += f"""
        <div class="test-case {status_class}">
            <h3>{status_icon} {test_name}</h3>
            <table>
                <tr><td><strong>Duration</strong></td><td>{details.get("duration", 0):.2f}s</td></tr>
                <tr><td><strong>Resources</strong></td><td>{details.get("resources", 0)}</td></tr>
                <tr><td><strong>Data Sources</strong></td><td>{details.get("data_sources", 0)}</td></tr>
                <tr><td><strong>Functions</strong></td><td>{details.get("functions", 0)}</td></tr>
                <tr><td><strong>Outputs</strong></td><td>{details.get("outputs", 0)}</td></tr>
            </table>
"""

        if details.get("warnings"):
            html_content += f"""
            <div class="warning-list">
                <h4>Warnings ({len(details["warnings"])})</h4>
                <ul>
"""
            for warning in details["warnings"]:
                html_content += f"                    <li>{warning.get('message', str(warning))}</li>\n"
            html_content += """                </ul>
            </div>
"""

        if not details["success"] and not details.get("skipped"):
            html_content += f"""
            <div style="background-color: #ffeeee; padding: 10px; margin-top: 10px;">
                <h4>Error</h4>
                <pre>{details.get("last_log", "No error details available")}</pre>
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
        has_fixtures = "✓" if bundle_info.get("has_fixtures") else "✗"
        html_content += f"""
        <tr>
            <td>{bundle_name}</td>
            <td>{bundle_info.get("component_type", "unknown")}</td>
            <td>{bundle_info.get("examples_count", 0)}</td>
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


# 📊📈📄