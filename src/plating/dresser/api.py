#
# plating/dresser/api.py
#
"""Public API for the dresser module."""

import asyncio

from plating.dresser.dresser import PlatingDresser


# Async entry point
async def dress_missing_components(component_types: list[str] = None) -> dict[str, int]:
    """Dress components with missing .plating directories."""
    dresser = PlatingDresser()
    return await dresser.dress_missing(component_types)


# Sync entry point
def dress_components(component_types: list[str] = None) -> dict[str, int]:
    """Sync entry point for dressing components."""
    return asyncio.run(dress_missing_components(component_types))


# 🍲🥄👗🎯🪄
