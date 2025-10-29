#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Modern CLI interface using the async Plating API with error handling."""

import asyncio
from pathlib import Path
import sys

import click
from provide.foundation import logger, perr, pout

from plating.errors import PlatingError
from plating.plating import Plating
from plating.types import ComponentType, PlatingContext


def auto_detect_package_name() -> str | None:
    """Auto-detect package name from pyproject.toml in current directory.

    Returns:
        Package name if found, None otherwise
    """
    try:
        pyproject_path = Path.cwd() / "pyproject.toml"
        if not pyproject_path.exists():
            return None

        # Try tomllib (Python 3.11+) first, fall back to tomli
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[import-not-found,no-redef]
            except ImportError:
                logger.debug("Neither tomllib nor tomli available for parsing pyproject.toml")
                return None

        with pyproject_path.open("rb") as f:
            pyproject = tomllib.load(f)

        # Try to get package name from [project] section
        if "project" in pyproject and "name" in pyproject["project"]:
            return pyproject["project"]["name"]

        return None
    except Exception as e:
        logger.debug(f"Failed to auto-detect package name: {e}")
        return None


def _load_tomllib_module() -> type | None:
    """Load tomllib or tomli module.

    Returns:
        tomllib module or None if not available
    """
    try:
        import tomllib
        return tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[import-not-found,no-redef]
            return tomllib
        except ImportError:
            return None


def _get_provider_name_from_pyproject(pyproject_path: Path) -> str | None:
    """Get provider name from pyproject.toml if configured.

    Args:
        pyproject_path: Path to pyproject.toml file

    Returns:
        Provider name if found, None otherwise
    """
    if not pyproject_path.exists():
        return None

    tomllib = _load_tomllib_module()
    if tomllib is None:
        return None

    try:
        with pyproject_path.open("rb") as f:
            pyproject = tomllib.load(f)

        # Check for [tool.plating] provider_name
        if "tool" in pyproject and "plating" in pyproject["tool"]:
            if "provider_name" in pyproject["tool"]["plating"]:
                return pyproject["tool"]["plating"]["provider_name"]
    except Exception as e:
        logger.debug(f"Failed to read pyproject.toml: {e}")

    return None


def _extract_provider_from_package_name(package_name: str) -> str | None:
    """Extract provider name from package name patterns.

    Args:
        package_name: Package name to parse

    Returns:
        Provider name if pattern matches, None otherwise
    """
    # Handle terraform-provider-{name} pattern
    if package_name.startswith("terraform-provider-"):
        return package_name.replace("terraform-provider-", "")

    # Handle {name}-provider pattern
    if package_name.endswith("-provider"):
        return package_name.replace("-provider", "")

    return None


def auto_detect_provider_name() -> str | None:
    """Auto-detect provider name from package name or pyproject.toml.

    Returns:
        Provider name if found, None otherwise
    """
    try:
        # First, check if there's explicit config in pyproject.toml
        pyproject_path = Path.cwd() / "pyproject.toml"
        provider_name = _get_provider_name_from_pyproject(pyproject_path)
        if provider_name:
            return provider_name

        # Try to extract from package name pattern
        package_name = auto_detect_package_name()
        if package_name:
            return _extract_provider_from_package_name(package_name)

        return None
    except Exception as e:
        logger.debug(f"Failed to auto-detect provider name: {e}")
        return None


def get_provider_name(provided_name: str | None) -> str:
    """Get provider name from CLI arg or auto-detect.

    Args:
        provided_name: Provider name from CLI argument (may be None)

    Returns:
        Provider name to use

    Raises:
        click.UsageError: If no provider name provided and auto-detection fails
    """
    if provided_name:
        return provided_name

    detected = auto_detect_provider_name()
    if detected:
        pout(f"🏷️  Auto-detected provider: {detected}")
        return detected

    raise click.UsageError(
        "Could not auto-detect provider name. Please provide --provider-name or add [tool.plating] provider_name to pyproject.toml"
    )


def get_package_name(provided_name: str | None) -> str | None:
    """Get package name from CLI arg, or auto-detect.

    Args:
        provided_name: Package name from CLI argument (may be None)

    Returns:
        Package name to filter to, or None if auto-detection fails
    """
    if provided_name:
        return provided_name

    detected = auto_detect_package_name()
    if detected:
        pout(f"📦 Auto-detected package: {detected}")
        return detected

    return None


@click.group()
def main() -> None:
    """Plating - Modern async documentation generator with foundation integration."""
    pass


@main.command("adorn")
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function", "provider"]),
    multiple=True,
    help="Component types to adorn (can be used multiple times).",
)
@click.option(
    "--provider-name",
    type=str,
    help="Provider name (auto-detected from package name if not provided).",
)
@click.option(
    "--package-name",
    type=str,
    help="Filter to specific package (default: auto-detect from pyproject.toml).",
)
def adorn_command(
    component_type: tuple[str, ...], provider_name: str | None, package_name: str | None
) -> None:
    """Create missing documentation templates and examples."""

    async def run() -> int:
        try:
            actual_provider_name = get_provider_name(provider_name)
            actual_package_name = get_package_name(package_name)

            if not actual_package_name:
                raise click.UsageError(
                    "Could not auto-detect package name. Please provide --package-name or run from a directory with pyproject.toml"
                )

            context = PlatingContext(provider_name=actual_provider_name)
            api = Plating(context, actual_package_name)

            # Convert string types to ComponentType enums
            types = [ComponentType(t) for t in component_type] if component_type else list(ComponentType)

            pout(f"🎨 Adorning {len(types)} component types...")
            result = await api.adorn(component_types=types)

            if result.success:
                pout(f"✅ Generated {result.templates_generated} templates and examples")
                return 0
            else:
                perr("❌ Adorn operation failed:")
                for error in result.errors:
                    perr(f"  • {error}")
                return 1

        except PlatingError as e:
            # Structured logging for debugging
            logger.error("Adorn command failed", error_details=e.to_dict())
            # User-friendly error message
            perr(f"\n❌ Error: {e.to_user_message()}\n")
            return 1

        except Exception as e:
            # Unexpected errors
            logger.exception("Unexpected error in adorn command")
            perr(f"\n❌ Unexpected error: {type(e).__name__}: {e}\n")
            perr("This is likely a bug. Please report it with the full error message.")
            return 1

    exit_code = asyncio.run(run())
    if exit_code != 0:
        sys.exit(exit_code)


def _generate_examples_if_requested(
    api: "Plating",
    generate_examples: bool,
    provider_name: str | None,
    examples_dir: Path,
    types: list["ComponentType"] | None,
    grouped_examples_dir: Path,
) -> None:
    """Generate executable examples if requested.

    Args:
        api: Plating API instance
        generate_examples: Whether to generate examples
        provider_name: Provider name for examples
        examples_dir: Directory for single-component examples
        types: Component types to process
        grouped_examples_dir: Directory for grouped examples
    """
    if not generate_examples:
        return

    from plating.example_compiler import ExampleCompiler

    pout("📁 Generating executable examples...")

    # Get all bundles with examples
    bundles_with_examples = []
    for component_type_enum in types or list(ComponentType):
        bundles = api.registry.get_components_with_templates(component_type_enum)
        bundles_with_examples.extend([b for b in bundles if b.has_examples()])

    if not bundles_with_examples:
        pout("ℹ️  No components with examples found")
        return

    compiler = ExampleCompiler(
        provider_name=provider_name or "pyvider",
        provider_version="0.0.5",
    )

    compilation_result = compiler.compile_examples(
        bundles_with_examples, examples_dir, types, grouped_examples_dir
    )

    total_examples = (
        compilation_result.examples_generated + compilation_result.grouped_examples_generated
    )

    if total_examples > 0:
        pout(
            f"✅ Generated {compilation_result.examples_generated} single-component "
            f"and {compilation_result.grouped_examples_generated} grouped examples "
            f"(total: {total_examples})"
        )
        pout("📂 Example files:")
        for example_file in compilation_result.output_files[:5]:  # Show first 5
            pout(f"  • {example_file}")
        if len(compilation_result.output_files) > 5:
            pout(f"  ... and {len(compilation_result.output_files) - 5} more")
    else:
        pout("ℹ️  No examples found to compile")

    if compilation_result.errors:
        perr("⚠️ Some example compilation errors:")
        for error in compilation_result.errors:
            perr(f"  • {error}")


def _print_plate_success(result: "PlateResult") -> None:
    """Print success message for plate operation.

    Args:
        result: Plate operation result
    """
    pout(f"✅ Generated {result.files_generated} files in {result.duration_seconds:.2f}s")
    pout(f"📦 Processed {result.bundles_processed} bundles")
    if result.output_files:
        pout("📄 Generated files:")
        for file in result.output_files[:10]:  # Show first 10
            pout(f"  • {file}")
        if len(result.output_files) > 10:
            pout(f"  ... and {len(result.output_files) - 10} more")


@main.command("plate")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("docs"),
    help="Output directory for documentation.",
)
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function", "provider"]),
    multiple=True,
    help="Component types to plate (can be used multiple times).",
)
@click.option(
    "--provider-name",
    type=str,
    help="Provider name (auto-detected from package name if not provided).",
)
@click.option(
    "--package-name",
    type=str,
    help="Filter to specific package (default: search all installed packages).",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite existing files.",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Enable/disable markdown validation.",
)
@click.option(
    "--project-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Project root directory (auto-detected if not provided).",
)
@click.option(
    "--generate-examples",
    is_flag=True,
    help="Generate executable example files alongside documentation.",
)
@click.option(
    "--examples-dir",
    type=click.Path(path_type=Path),
    default=Path("examples"),
    help="Output directory for compiled examples (default: examples).",
)
@click.option(
    "--grouped-examples-dir",
    type=click.Path(path_type=Path),
    default=Path("examples/integration"),
    help="Directory for grouped/cross-component examples (default: examples/integration).",
)
def plate_command(
    output_dir: Path,
    component_type: tuple[str, ...],
    provider_name: str | None,
    package_name: str | None,
    force: bool,
    project_root: Path | None,
    validate: bool,
    generate_examples: bool,
    examples_dir: Path,
    grouped_examples_dir: Path,
) -> None:
    """Generate documentation from plating bundles."""

    async def run() -> int:
        try:
            actual_provider_name = get_provider_name(provider_name)
            actual_package_name = get_package_name(package_name)

            if actual_package_name:
                pout(f"🔍 Filtering to package: {actual_package_name}")
            else:
                pout("🌍 Discovering from ALL installed packages")

            context = PlatingContext(provider_name=actual_provider_name)
            api = Plating(context, actual_package_name)

            # Convert string types to ComponentType enums
            types = [ComponentType(t) for t in component_type] if component_type else None

            # Handle output_dir default behavior - if not specified, let the API auto-detect
            final_output_dir = output_dir if output_dir != Path("docs") else None

            pout("🍽️ Plating documentation...")
            result = await api.plate(final_output_dir, types, force, validate, project_root)

            if result.success:
                _print_plate_success(result)
                _generate_examples_if_requested(
                    api, generate_examples, provider_name, examples_dir, types, grouped_examples_dir
                )
                return 0

            else:
                perr("❌ Plate operation failed:")
                for error in result.errors:
                    perr(f"  • {error}")
                return 1

        except PlatingError as e:
            # Structured logging for debugging
            logger.error("Plate command failed", error_details=e.to_dict())
            # User-friendly error message
            perr(f"\n❌ Error: {e.to_user_message()}\n")
            return 1

        except Exception as e:
            # Unexpected errors
            logger.exception("Unexpected error in plate command")
            perr(f"\n❌ Unexpected error: {type(e).__name__}: {e}\n")
            perr("This is likely a bug. Please report it with the full error message.")
            return 1

    exit_code = asyncio.run(run())
    if exit_code != 0:
        sys.exit(exit_code)


@main.command("validate")
@click.option(
    "--output-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("docs"),
    help="Directory containing documentation to validate.",
)
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function", "provider"]),
    multiple=True,
    help="Component types to validate (can be used multiple times).",
)
@click.option(
    "--provider-name",
    type=str,
    help="Provider name (auto-detected from package name if not provided).",
)
@click.option(
    "--package-name",
    type=str,
    help="Filter to specific package (default: search all installed packages).",
)
def validate_command(
    output_dir: Path, component_type: tuple[str, ...], provider_name: str | None, package_name: str | None
) -> None:
    """Validate generated documentation."""

    async def run() -> None:
        actual_provider_name = get_provider_name(provider_name)
        actual_package_name = get_package_name(package_name)

        if actual_package_name is None:
            pout("🌍 Discovering components from ALL installed packages")

        context = PlatingContext(provider_name=actual_provider_name)
        api = Plating(context, actual_package_name)

        # Convert string types to ComponentType enums
        types = [ComponentType(t) for t in component_type] if component_type else None

        pout(f"🔍 Validating documentation in {output_dir}...")
        result = await api.validate(output_dir, types)

        pout("📊 Validation results:")
        pout(f"  • Total files: {result.total}")
        pout(f"  • Passed: {result.passed}")
        pout(f"  • Failed: {result.failed}")
        pout(f"  • Duration: {result.duration_seconds:.2f}s")

        if result.success:
            pout("✅ All validations passed")
        else:
            perr("❌ Validation failed:")
            if result.lint_errors:
                perr("  Markdown linting errors:")
                for error in result.lint_errors[:5]:  # Show first 5
                    perr(f"    • {error}")
                if len(result.lint_errors) > 5:
                    perr(f"    ... and {len(result.lint_errors) - 5} more")

            if result.errors:
                perr("  General errors:")
                for error in result.errors:
                    perr(f"    • {error}")

    asyncio.run(run())


@main.command("info")
@click.option(
    "--provider-name",
    type=str,
    help="Provider name (auto-detected from package name if not provided).",
)
@click.option(
    "--package-name",
    type=str,
    help="Filter to specific package (default: search all installed packages).",
)
def info_command(provider_name: str | None, package_name: str | None) -> None:
    """Show registry information and statistics."""

    async def run() -> None:
        actual_provider_name = get_provider_name(provider_name)
        actual_package_name = get_package_name(package_name)

        if actual_package_name:
            pout(f"🔍 Filtering to package: {actual_package_name}")
        else:
            pout("🌍 Discovering components from ALL installed packages")

        context = PlatingContext(provider_name=actual_provider_name)
        api = Plating(context, actual_package_name)

        stats = api.get_registry_stats()

        pout("📊 Registry Statistics:")
        pout(f"  • Total components: {stats.get('total_components', 0)}")
        pout(f"  • Component types: {', '.join(stats.get('component_types', []))}")

        for comp_type in stats.get("component_types", []):
            count = stats.get(comp_type, {}).get('total', 0)
            with_templates = stats.get(comp_type, {}).get('with_templates', 0)

            pout(
                f"  • {comp_type}: {count} total, {with_templates} with templates"
            )

    asyncio.run(run())


@main.command("stats")
@click.option(
    "--package-name",
    type=str,
    help="Filter to specific package (default: search all installed packages).",
)
def stats_command(package_name: str | None) -> None:
    """Show registry statistics."""

    async def run() -> None:
        actual_package_name = get_package_name(package_name)

        if actual_package_name:
            pout(f"🔍 Filtering to package: {actual_package_name}")
        else:
            pout("🌍 Discovering components from ALL installed packages")

        # Stats command doesn't need provider context
        context = PlatingContext(provider_name="")
        api = Plating(context, actual_package_name)

        stats = api.get_registry_stats()

        pout("📊 Registry Statistics:")
        pout(f"   Total components: {stats.get('total_components', 0)}")

        component_types = stats.get("component_types", [])
        if component_types:
            pout("\n📦 Components by type:")
            for comp_type in sorted(component_types):
                count = stats.get(comp_type, {}).get('total', 0)
                with_templates = stats.get(comp_type, {}).get('with_templates', 0)
                pout(
                    f"   {comp_type}: {count} total, {with_templates} with templates"
                )

    asyncio.run(run())


if __name__ == "__main__":
    main()

# 🍽️📖🔚
