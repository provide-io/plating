#
# plating/test_runner/suite_builder.py
#
"""Test suite preparation and building functionality."""

from datetime import datetime
from pathlib import Path

from rich.console import Console

from plating.plating import PlatingBundle, PlatingDiscovery

console = Console()


def prepare_test_suites_for_stir(bundles: list[PlatingBundle], output_dir: Path) -> list[Path]:
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


def prepare_bundles_summary(bundles: list[PlatingBundle]) -> dict:
    """Prepare a summary of bundles for test results.

    Args:
        bundles: List of plating bundles

    Returns:
        Dictionary with bundle information for test results
    """
    results = {
        "bundles": {},
        "timestamp": datetime.now().isoformat(),
    }

    if bundles:
        for bundle in bundles:
            fixture_count = 0
            if hasattr(bundle.fixtures_dir, "exists") and bundle.fixtures_dir.exists():
                try:
                    fixture_count = sum(1 for _ in bundle.fixtures_dir.rglob("*") if _.is_file())
                except (AttributeError, TypeError):
                    # Handle mock objects in tests
                    fixture_count = 0

            try:
                examples = bundle.load_examples()
                examples_count = len(examples) if examples else 0
            except (AttributeError, TypeError):
                examples_count = 0

            try:
                has_fixtures = hasattr(bundle.fixtures_dir, "exists") and bundle.fixtures_dir.exists()
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


def _create_test_suite(bundle: PlatingBundle, examples: dict[str, str], output_dir: Path) -> Path | None:
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
        console.print(f"[red]⚠️  Failed to create test suite for {bundle.name}: {e}[/red]")
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


# 🏗️📦🔨