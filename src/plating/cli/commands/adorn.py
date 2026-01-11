# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Adorn command implementation."""

import asyncio
import sys
from typing import Any

import click
from provide.foundation import logger, perr, pout
from provide.foundation.cli.decorators import flexible_options

from plating.cli.helpers.auto_detect import get_package_name, get_provider_name
from plating.errors import PlatingError
from plating.plating import Plating
from plating.types import ComponentType, PlatingContext


@click.command("adorn")
@flexible_options
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
    component_type: tuple[str, ...], provider_name: str | None, package_name: str | None, **kwargs: Any
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
                # Print success message with count
                pout(f"✅ Generated {result.templates_generated} template(s)")
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
