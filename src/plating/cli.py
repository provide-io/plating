#!/usr/bin/env python3
#
# plating/cli.py
#
"""Modern CLI interface using the async Plating API."""

import asyncio
from pathlib import Path

import click
from provide.foundation import perr, pout

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
    default="pyvider.components",
    help="Package to search for components.",
)
def adorn_command(component_type: tuple[str, ...], provider_name: str | None, package_name: str) -> None:
    """Create missing documentation templates and examples."""

    async def run():
        context = PlatingContext(provider_name=provider_name or "default")
        api = Plating(context, package_name)

        # Convert string types to ComponentType enums
        types = [ComponentType(t) for t in component_type] if component_type else list(ComponentType)

        pout(f"🎨 Adorning {len(types)} component types...")
        result = await api.adorn(types)

        if result.success:
            pout(f"✅ Generated {result.templates_generated} templates")
            pout(f"📦 Processed {result.components_processed} components")
        else:
            perr("❌ Adorn operation failed:")
            for error in result.errors:
                perr(f"  • {error}")

    asyncio.run(run())


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
    default="pyvider.components",
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
def plate_command(
    output_dir: Path,
    component_type: tuple[str, ...],
    provider_name: str | None,
    package_name: str,
    force: bool,
    validate: bool,
) -> None:
    """Generate documentation from plating bundles."""

    async def run():
        context = PlatingContext(provider_name=provider_name or "default")
        api = Plating(context, package_name)

        # Convert string types to ComponentType enums
        types = [ComponentType(t) for t in component_type] if component_type else None

        pout(f"🍽️ Plating documentation to {output_dir}...")
        result = await api.plate(output_dir, types, force, validate)

        if result.success:
            pout(f"✅ Generated {result.files_generated} files in {result.duration_seconds:.2f}s")
            pout(f"📦 Processed {result.bundles_processed} bundles")
            if result.output_files:
                pout("📄 Generated files:")
                for file in result.output_files[:10]:  # Show first 10
                    pout(f"  • {file}")
                if len(result.output_files) > 10:
                    pout(f"  ... and {len(result.output_files) - 10} more")
        else:
            perr("❌ Plate operation failed:")
            for error in result.errors:
                perr(f"  • {error}")

    asyncio.run(run())


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
    default="pyvider.components",
    help="Package to search for components.",
)
def validate_command(
    output_dir: Path, component_type: tuple[str, ...], provider_name: str | None, package_name: str
) -> None:
    """Validate generated documentation."""

    async def run():
        context = PlatingContext(provider_name=provider_name or "default")
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
    default="pyvider.components",
    help="Package to search for components.",
)
def info_command(provider_name: str | None, package_name: str) -> None:
    """Show registry information and statistics."""

    async def run():
        context = PlatingContext(provider_name=provider_name or "default")
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
                f"  • {comp_type}: {count} total, {with_templates} with templates, {with_examples} with examples"
            )

    asyncio.run(run())


@main.command("stats")
@click.option(
    "--package-name",
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def stats_command(package_name: str) -> None:
    """Show registry statistics."""

    async def run():
        context = PlatingContext(provider_name="default")
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
                    f"   {comp_type}: {count} total, {with_templates} with templates, {with_examples} with examples"
                )

    asyncio.run(run())


if __name__ == "__main__":
    main()


# 🚀✨🎯🍽️
