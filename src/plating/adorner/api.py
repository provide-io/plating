#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Public API for the adorner module."""

import asyncio

from plating.adorner.adorner import PlatingAdorner


# Async entry point
async def adorn_missing_components(
    package_name: str = "pyvider.components", component_types: list[str] | None = None
) -> dict[str, int]:
    """Adorn components with missing .plating directories."""
    adorner = PlatingAdorner(package_name)
    return await adorner.adorn_missing(component_types)


# Sync entry point
def adorn_components(
    package_name: str = "pyvider.components", component_types: list[str] | None = None
) -> dict[str, int]:
    """Sync entry point for adorning components."""
    return asyncio.run(adorn_missing_components(package_name, component_types))


# 🍽️📖🔚
