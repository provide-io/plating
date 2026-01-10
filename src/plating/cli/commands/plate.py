# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Plate command implementation."""

import asyncio
from pathlib import Path
import sys
from typing import Any

import click
from provide.foundation import logger, perr, pout
from provide.foundation.cli.decorators import flexible_options

from plating.cli.helpers.auto_detect import get_package_name, get_provider_name
from plating.cli.helpers.examples import generate_examples_if_requested
from plating.cli.helpers.output import print_plate_success
from plating.errors import PlatingError
from plating.plating import Plating
from plating.types import ComponentType, PlatingContext


@click.command("plate")
@flexible_options
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
@click.option(
    "--guides-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Source directory for guide documentation (copied to output-dir/guides).",
)
@click.option(
    "--global-partials-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory containing global partials (_global_header.md, _global_footer.md).",
)
def plate_command(  # noqa: C901
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
    guides_dir: Path | None,
    global_partials_dir: Path | None,
    **kwargs: Any,
) -> None:
    """Generate documentation from plating bundles."""

    async def run() -> int:
        try:
            actual_provider_name = get_provider_name(provider_name)
            actual_package_name = get_package_name(package_name)

            if actual_package_name:
                pout(f"🔍 Filtering to package: {actual_package_name}")
            else:
                pout("🔍 Discovering all packages")

            context = PlatingContext(
                provider_name=actual_provider_name, global_partials_dir=global_partials_dir
            )
            api = Plating(context, actual_package_name)

            # Convert string types to ComponentType enums
            types = [ComponentType(t) for t in component_type] if component_type else None

            # Handle output_dir default behavior - if not specified, let the API auto-detect
            final_output_dir = output_dir if output_dir != Path("docs") else None

            # Copy guides from source directory if provided
            if guides_dir:
                import shutil

                guides_output_dir = output_dir / "guides"
                guides_output_dir.mkdir(parents=True, exist_ok=True)

                # Copy all .md files from guides_dir to output_dir/guides/
                guide_files = list(guides_dir.glob("*.md"))
                if guide_files:
                    pout(f"📚 Copying {len(guide_files)} guide(s) from {guides_dir} to {guides_output_dir}")
                    for guide_file in guide_files:
                        shutil.copy2(guide_file, guides_output_dir / guide_file.name)
                else:
                    pout(f"⚠️  No guide files (*.md) found in {guides_dir}")

            result = await api.plate(final_output_dir, types, force, validate, project_root)

            if result.success:
                print_plate_success(result)
                generate_examples_if_requested(
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
