import asyncio

from plating.dresser import PlatingDresser


async def dress_all_components():
    """Dress all components missing .plating directories."""
    dresser = PlatingDresser()

    # Find and dress all missing components
    results = await dresser.dress_missing()

    # Display results
    total = sum(results.values())
    print(f"Dressed {total} components:")
    for component_type, count in results.items():
        if count > 0:
            print(f"  - {count} {component_type}(s)")

    return results


# Run the async function
results = asyncio.run(dress_all_components())
