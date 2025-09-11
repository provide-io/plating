#
# plating/validator/core.py
#
"""Core validation execution functionality."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from provide.foundation import logger, pout
from provide.foundation.process import ProcessError, run_command
from rich.console import Console

from plating.config import get_config
from plating.plating import PlatingDiscovery
from plating.results import ValidationResult

console = Console()


def run_validation(
    component_types: list[str] = None,
    parallel: int = 4,
    output_file: Path = None,
    output_format: str = "json",
) -> ValidationResult:
    """Run validation for plating bundles.

    Args:
        component_types: Optional list of component types to filter
        parallel: Number of parallel tests (not used in simple mode)
        output_file: Optional file to write report to
        output_format: Format for report (json, markdown, html)

    Returns:
        ValidationResult with validation execution results
    """
    # Dogfood foundation for user output
    pout("🔍 Running validation on plating examples...")
    
    # Dogfood our own adapters and reporters
    from plating.validator.adapters import PlatingValidator
    from plating.validator.reporters import generate_report

    adapter = PlatingValidator(fallback_to_simple=True)
    results_dict = adapter.run_validation(
        component_types=component_types,
        parallel=parallel,
        output_file=output_file,
        output_format=output_format,
    )

    # Convert dict to ValidationResult (dogfood our results)
    return ValidationResult(
        total=results_dict.get("total", 0),
        passed=results_dict.get("passed", 0),
        failed=results_dict.get("failed", 0),
        warnings=results_dict.get("warnings", 0),
        skipped=results_dict.get("skipped", 0),
        failures=results_dict.get("failures", {}),
        test_details=results_dict.get("test_details", {}),
        duration=results_dict.get("duration", 0.0),
        terraform_version=results_dict.get("terraform_version", ""),
        bundles=results_dict.get("bundles", {}),
    )


def _run_simple_validation(validation_dir: Path) -> dict[str, Any]:
    """Run simple terraform validation without stir.

    Note: This is a simplified version without parallel execution or rich UI.
    For advanced test running with rich UI, use tofusoup.

    Args:
        validation_dir: Directory containing validation suites

    Returns:
        Dictionary with validation results
    """
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

    # Dogfood foundation for user output
    pout("🔍 Running simple validation (no stir)...")
    
    # Find all validation directories
    validation_dirs = [d for d in validation_dir.iterdir() if d.is_dir()]
    results["total"] = len(validation_dirs)

    # Dogfood our config system
    config = get_config()
    logger.debug("Using terraform binary", binary=config.terraform_binary)
    tf_binary = config.terraform_binary

    for suite_dir in validation_dirs:
        validation_name = suite_dir.name
        pout(f"🔍 Validating: {validation_name}")
        logger.debug("Starting validation", suite=validation_name)

        validation_info = {
            "name": validation_name,
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
                run_command(
                    [tf_binary, "init"],
                    cwd=suite_dir,
                    capture_output=True,
                    timeout=60,
                )
            except ProcessError as e:
                error_msg = str(e)
                if hasattr(e, "stderr") and e.stderr:
                    error_msg += f" {e.stderr}"
                logger.error(f"Terraform init failed for {suite_dir.name}: {error_msg}")
                raise

            # Run terraform apply
            try:
                apply_result = run_command(
                    [tf_binary, "apply", "-auto-approve"],
                    cwd=suite_dir,
                    capture_output=True,
                    timeout=config.test_timeout,
                )
            except ProcessError as e:
                error_msg = str(e)
                if hasattr(e, "stderr") and e.stderr:
                    error_msg += f" {e.stderr}"
                logger.error(f"Terraform apply failed for {suite_dir.name}: {error_msg}")
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
                    import json

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


# 🧪⚡🔬