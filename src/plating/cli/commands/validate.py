# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Validate command implementation."""

import asyncio
from pathlib import Path
from typing import Any

import click
from provide.foundation import perr, pout
from provide.foundation.cli.decorators import flexible_options

from plating.cli.helpers.auto_detect import get_package_name, get_provider_name
from plating.plating import Plating
from plating.types import ComponentType, PlatingContext

COMPONENT_TYPE_CHOICES = [member.value for member in ComponentType]


@click.command("validate")
@flexible_options
@click.option(
    "--output-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("docs"),
    help="Directory containing documentation to validate.",
)
@click.option(
    "--component-type",
    type=click.Choice(COMPONENT_TYPE_CHOICES),
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
    output_dir: Path,
    component_type: tuple[str, ...],
    provider_name: str | None,
    package_name: str | None,
    **kwargs: Any,
) -> None:
    """Validate generated documentation."""

    async def run() -> None:
        actual_provider_name = get_provider_name(provider_name)
        actual_package_name = get_package_name(package_name)

        if actual_package_name is None:
            pout("🔍 Discovering all packages")

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
