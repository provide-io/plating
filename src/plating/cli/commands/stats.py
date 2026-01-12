# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Stats command implementation."""

import asyncio
from typing import Any

import click
from provide.foundation import pout
from provide.foundation.cli.decorators import flexible_options

from plating.cli.helpers.auto_detect import get_package_name
from plating.plating import Plating
from plating.types import PlatingContext


@click.command("stats")
@flexible_options
@click.option(
    "--package-name",
    type=str,
    help="Filter to specific package (default: search all installed packages).",
)
def stats_command(package_name: str | None, **kwargs: Any) -> None:
    """Show registry statistics."""

    async def run() -> None:
        actual_package_name = get_package_name(package_name)

        if actual_package_name:
            pout(f"🔍 Filtering to package: {actual_package_name}")
        else:
            pout("🔍 Discovering all packages")

        # Stats command doesn't need provider context
        context = PlatingContext(provider_name="")
        api = Plating(context, actual_package_name)

        stats = api.get_registry_stats()

        pout("📊 Registry Statistics:")
        pout(f"   Total components: {stats.get('total_components', 0)}")

        component_types = stats.get("component_types", [])
        if component_types:
            for comp_type in sorted(component_types):
                count = stats.get(comp_type, {}).get("total", 0)
                with_templates = stats.get(comp_type, {}).get("with_templates", 0)
                pout(f"   {comp_type}: {count} total, {with_templates} with templates")

    asyncio.run(run())
