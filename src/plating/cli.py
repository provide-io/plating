#!/usr/bin/env python3
#
# plating/cli.py
#
"""Modern CLI interface using the async Plating API with error handling."""

import asyncio
import sys
from pathlib import Path

import click
from provide.foundation import logger, perr, pout

from plating.errors import PlatingError
from plating.plating import Plating
from plating.types import ComponentType, PlatingContext


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
    help="Provider name for context.",
)
@click.option(
    "--package-name",
    type=str,
    required=True,
    help="Package to search for components.",
)
def adorn_command(component_type: tuple[str, ...], provider_name: str | None, package_name: str) -> None:
    """Create missing documentation templates and examples."""

    async def run() -> int:
        try:
            if not provider_name:
                raise click.UsageError("--provider-name is required")
            context = PlatingContext(provider_name=provider_name)
            api = Plating(context, package_name)

            # Convert string types to ComponentType enums
            types = [ComponentType(t) for t in component_type] if component_type else list(ComponentType)

            pout(f"🎨 Adorning {len(types)} component types...")
            result = await api.adorn(component_types=types)

            if result.success:
                pout(f"✅ Generated {result.templates_generated} templates")
                pout(f"📦 Processed {result.components_processed} components")
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
    help="Provider name for context.",
)
@click.option(
    "--package-name",
    type=str,
    required=True,
    help="Package to search for components.",
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
    package_name: str,
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
            if not provider_name:
                raise click.UsageError("--provider-name is required")
            context = PlatingContext(provider_name=provider_name)
            api = Plating(context, package_name)

            # Convert string types to ComponentType enums
            types = [ComponentType(t) for t in component_type] if component_type else None

            # Handle output_dir default behavior - if not specified, let the API auto-detect
            final_output_dir = output_dir if output_dir != Path("docs") else None

            pout("🍽️ Plating documentation...")
            result = await api.plate(final_output_dir, types, force, validate, project_root)

            if result.success:
                pout(f"✅ Generated {result.files_generated} files in {result.duration_seconds:.2f}s")
                pout(f"📦 Processed {result.bundles_processed} bundles")
                if result.output_files:
                    pout("📄 Generated files:")
                    for file in result.output_files[:10]:  # Show first 10
                        pout(f"  • {file}")
                    if len(result.output_files) > 10:
                        pout(f"  ... and {len(result.output_files) - 10} more")

                # Generate executable examples if requested
                if generate_examples:
                    from plating.example_compiler import ExampleCompiler

                    pout("📁 Generating executable examples...")

                    # Get all bundles with examples
                    bundles_with_examples = []
                    for component_type_enum in types or list(ComponentType):
                        bundles = api.registry.get_components_with_templates(component_type_enum)
                        bundles_with_examples.extend([b for b in bundles if b.has_examples()])

                    if bundles_with_examples:
                        compiler = ExampleCompiler(
                            provider_name=provider_name or "pyvider",
                            provider_version="0.0.5",
                        )

                        compilation_result = compiler.compile_examples(
                            bundles_with_examples, examples_dir, types, grouped_examples_dir
                        )

                        total_examples = (
                            compilation_result.examples_generated
                            + compilation_result.grouped_examples_generated
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
                    else:
                        pout("ℹ️  No components with examples found")

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
    help="Provider name for context.",
)
@click.option(
    "--package-name",
    type=str,
    required=True,
    help="Package to search for components.",
)
def validate_command(
    output_dir: Path, component_type: tuple[str, ...], provider_name: str | None, package_name: str
) -> None:
    """Validate generated documentation."""

    async def run() -> None:
        if not provider_name:
            raise click.UsageError("--provider-name is required")
        context = PlatingContext(provider_name=provider_name)
        api = Plating(context, package_name)

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
    help="Provider name for context.",
)
@click.option(
    "--package-name",
    type=str,
    required=True,
    help="Package to search for components.",
)
def info_command(provider_name: str | None, package_name: str) -> None:
    """Show registry information and statistics."""

    async def run() -> None:
        if not provider_name:
            raise click.UsageError("--provider-name is required")
        context = PlatingContext(provider_name=provider_name)
        api = Plating(context, package_name)

        stats = api.get_registry_stats()

        pout("📊 Registry Statistics:")
        pout(f"  • Total components: {stats.get('total_components', 0)}")
        pout(f"  • Component types: {', '.join(stats.get('component_types', []))}")

        for comp_type in stats.get("component_types", []):
            count = stats.get(f"{comp_type}_count", 0)
            with_templates = stats.get(f"{comp_type}_with_templates", 0)
            with_examples = stats.get(f"{comp_type}_with_examples", 0)

            pout(
                f"  • {comp_type}: {count} total, {with_templates} with templates, "
                f"{with_examples} with examples"
            )

    asyncio.run(run())


@main.command("stats")
@click.option(
    "--package-name",
    type=str,
    required=True,
    help="Package to search for components.",
)
def stats_command(package_name: str) -> None:
    """Show registry statistics."""

    async def run() -> None:
        # Stats command doesn't need provider context
        context = PlatingContext(provider_name="")
        api = Plating(context, package_name)

        stats = api.get_registry_stats()

        pout("📊 Registry Statistics:")
        pout(f"   Total components: {stats.get('total_components', 0)}")

        component_types = stats.get("component_types", [])
        if component_types:
            pout("\n📦 Components by type:")
            for comp_type in sorted(component_types):
                count = stats.get(f"{comp_type}_count", 0)
                with_templates = stats.get(f"{comp_type}_with_templates", 0)
                with_examples = stats.get(f"{comp_type}_with_examples", 0)
                pout(
                    f"   {comp_type}: {count} total, {with_templates} with templates, "
                    f"{with_examples} with examples"
                )

    asyncio.run(run())


if __name__ == "__main__":
    main()


