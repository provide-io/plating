# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
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
from plating.resolution.source import resolve_provider_source
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
    "--generate-examples/--no-generate-examples",
    default=True,
    help="Generate executable example files alongside documentation (default: enabled).",
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
@click.option(
    "--local",
    "provider_source_local",
    is_flag=True,
    help="Use local provider source (overrides auto-detection).",
)
@click.option(
    "--remote",
    "provider_source_remote",
    is_flag=True,
    help="Use remote provider source (overrides auto-detection).",
)
@click.option(
    "--registry-url",
    type=str,
    help="Provider registry URL (e.g., registry.terraform.io).",
)
@click.option(
    "--namespace",
    type=str,
    help="Provider namespace (e.g., 'local', 'hashicorp').",
)
@click.option(
    "--flat-nav",
    is_flag=True,
    help="Generate flat registry-style navigation for link testing (default: grouped by capability).",
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
    guides_dir: Path | None,
    global_partials_dir: Path | None,
    provider_source_local: bool,
    provider_source_remote: bool,
    registry_url: str | None,
    namespace: str | None,
    flat_nav: bool,
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

            # Validate mutually exclusive flags
            if provider_source_local and provider_source_remote:
                perr("❌ Error: --local and --remote are mutually exclusive")
                return 1

            # Determine CLI source from flags
            cli_source = None
            if provider_source_local:
                cli_source = "local"
            elif provider_source_remote:
                cli_source = "remote"

            # Resolve provider source with precedence
            resolution = resolve_provider_source(
                provider_name=actual_provider_name,
                package_name=actual_package_name,
                cli_source=cli_source,
                cli_registry_url=registry_url,
                cli_namespace=namespace,
            )

            # Show resolution info
            pout(f"📦 Provider source: {resolution.source}")
            if resolution.source == "local":
                pout(
                    f"   Registry: {resolution.registry_url}/{resolution.namespace}/providers/{actual_provider_name}"
                )
            else:
                pout(f"   Registry: {resolution.registry_url}/{resolution.namespace}/{actual_provider_name}")
            logger.debug(f"Resolution path: {' → '.join(resolution.resolution_path)}")

            # Auto-detect global partials directory if not provided
            actual_global_partials_dir = global_partials_dir
            if actual_global_partials_dir is None:
                # Try new plating/partials structure first
                plating_partials_dir = Path("plating/partials")
                if plating_partials_dir.exists() and plating_partials_dir.is_dir():
                    actual_global_partials_dir = plating_partials_dir
                    pout(f"📝 Auto-detected partials directory: {actual_global_partials_dir}")

            context = PlatingContext(
                provider_name=actual_provider_name,
                global_partials_dir=actual_global_partials_dir,
                provider_source=resolution.source,
                provider_registry_url=resolution.registry_url,
                provider_namespace=resolution.namespace,
            )
            api = Plating(context, actual_package_name)

            # Convert string types to ComponentType enums
            types = [ComponentType(t) for t in component_type] if component_type else None

            # Handle output_dir default behavior - if not specified, let the API auto-detect
            final_output_dir = output_dir if output_dir != Path("docs") else None

            # Auto-detect guides directory if not provided
            actual_guides_dir = guides_dir
            if actual_guides_dir is None:
                # Try new plating/guides structure first, fall back to legacy guides/
                plating_guides_dir = Path("plating/guides")
                legacy_guides_dir = Path("guides")

                if plating_guides_dir.exists() and plating_guides_dir.is_dir():
                    actual_guides_dir = plating_guides_dir
                    pout(f"📚 Auto-detected guides directory: {actual_guides_dir}")
                elif legacy_guides_dir.exists() and legacy_guides_dir.is_dir():
                    actual_guides_dir = legacy_guides_dir
                    pout(f"📚 Auto-detected guides directory: {actual_guides_dir}")

            # Process guides and templates from source directory if provided or auto-detected
            if actual_guides_dir:
                import shutil

                from plating.core.guide_processor import GuideProcessingError, parse_template_file, process_template_file

                guides_output_dir = output_dir / "guides"
                guides_output_dir.mkdir(parents=True, exist_ok=True)

                # Find all markdown files in guides directory
                md_files = list(actual_guides_dir.glob("*.md"))
                tmpl_files_from_guides = list(actual_guides_dir.glob("*.tmpl.md"))
                regular_guides = [f for f in md_files if not f.name.endswith(".tmpl.md")]

                # Also check plating/templates/ directory if it exists
                templates_dir = Path("plating/templates")
                tmpl_files_from_templates = []
                if templates_dir.exists() and templates_dir.is_dir():
                    tmpl_files_from_templates = list(templates_dir.glob("*.tmpl.md"))

                # Combine template files from both locations
                tmpl_files = tmpl_files_from_guides + tmpl_files_from_templates

                if md_files or tmpl_files:
                    # Process template files first
                    if tmpl_files:
                        template_sources = []
                        if tmpl_files_from_guides:
                            template_sources.append(f"{actual_guides_dir}")
                        if tmpl_files_from_templates:
                            template_sources.append("plating/templates")
                        sources_str = " and ".join(template_sources)
                        pout(f"📝 Processing {len(tmpl_files)} template file(s) from {sources_str}")
                        for tmpl_file in tmpl_files:
                            try:
                                template = parse_template_file(tmpl_file)
                                output_path = process_template_file(template, output_dir)
                                pout(f"   ✓ {tmpl_file.name} → {output_path.relative_to(output_dir)}")
                            except GuideProcessingError as e:
                                perr(f"   ✗ {tmpl_file.name}: {e.to_user_message()}")
                                return 1

                    # Copy regular guide files
                    if regular_guides:
                        pout(f"📚 Copying {len(regular_guides)} guide(s) from {actual_guides_dir} to {guides_output_dir}")
                        for guide_file in regular_guides:
                            shutil.copy2(guide_file, guides_output_dir / guide_file.name)
                else:
                    pout(f"⚠️  No guide or template files found in {actual_guides_dir}")

            result = await api.plate(final_output_dir, types, force, validate, project_root, flat_nav)

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
