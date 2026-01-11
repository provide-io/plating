#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

import asyncio

from plating.adorner import PlatingAdorner

"""Dress only resource components."""


async def dress_resources_only() -> None:
    adorner = PlatingAdorner()

    # Dress only resources
    results = await adorner.adorn_missing(["resource"])

    print(f"Dressed {results['resource']} resources")
    print(f"Skipped {results['data_source']} data sources")
    print(f"Skipped {results['function']} functions")

    return results


# Dress multiple types
async def dress_multiple_types() -> None:
    """Dress resources and data sources."""
    adorner = PlatingAdorner()

    # Dress resources and data sources
    results = await adorner.adorn_missing(["resource", "data_source"])

    for component_type in ["resource", "data_source"]:
        count = results[component_type]
        if count > 0:
            print(f"✅ Dressed {count} {component_type}(s)")


# Run async functions
asyncio.run(dress_resources_only())
asyncio.run(dress_multiple_types())

# 🍽️📖🔚
