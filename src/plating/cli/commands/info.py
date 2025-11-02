# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Info command implementation."""

import asyncio
from typing import Any

import click
from provide.foundation import pout
from provide.foundation.cli.decorators import flexible_options

from plating.cli.helpers.auto_detect import get_package_name, get_provider_name
from plating.plating import Plating
from plating.types import PlatingContext


@click.command("info")
@flexible_options
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
def info_command(provider_name: str | None, package_name: str | None, **kwargs: Any) -> None:
    """Show registry information and statistics."""

    async def run() -> None:
        actual_provider_name = get_provider_name(provider_name)
        actual_package_name = get_package_name(package_name)

        if actual_package_name:
            pout(f"🔍 Filtering to package: {actual_package_name}")
        else:
            pout("🔍 Discovering all packages")

        context = PlatingContext(provider_name=actual_provider_name)
        api = Plating(context, actual_package_name)

        stats = api.get_registry_stats()

        pout("📊 Registry Statistics:")
        pout(f"  • Total components: {stats.get('total_components', 0)}")
        pout(f"  • Component types: {', '.join(stats.get('component_types', []))}")

        for comp_type in stats.get("component_types", []):
            count = stats.get(comp_type, {}).get("total", 0)
            with_templates = stats.get(comp_type, {}).get("with_templates", 0)

            pout(f"  • {comp_type}: {count} total, {with_templates} with templates")

    asyncio.run(run())
