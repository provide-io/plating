import asyncio

from garnish.dresser import GarnishDresser


async def dress_resources_only():
    """Dress only resource components."""
    dresser = GarnishDresser()

    # Dress only resources
    results = await dresser.dress_missing(["resource"])

    print(f"Dressed {results['resource']} resources")
    print(f"Skipped {results['data_source']} data sources")
    print(f"Skipped {results['function']} functions")

    return results


# Dress multiple types
async def dress_multiple_types():
    """Dress resources and data sources."""
    dresser = GarnishDresser()

    # Dress resources and data sources
    results = await dresser.dress_missing(["resource", "data_source"])

    for component_type in ["resource", "data_source"]:
        count = results[component_type]
        if count > 0:
            print(f"✅ Dressed {count} {component_type}(s)")


# Run async functions
asyncio.run(dress_resources_only())
asyncio.run(dress_multiple_types())
