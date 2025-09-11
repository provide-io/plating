from pathlib import Path

from plating.plater import PlatingPlater
from plating.plating import PlatingBundle, PlatingDiscovery

# Discover all bundles in a provider
discovery = PlatingDiscovery(package_name="my_provider")
bundles = discovery.discover_bundles()

# Or create bundles manually
bundle = PlatingBundle(
    name="load_balancer",
    plating_dir=Path("./resources/load_balancer.plating"),
    component_type="resource",
)

# Plate the documentation
plater = PlatingPlater(bundles=[bundle])
output_dir = Path("./docs")
plater.plate(output_dir, force=True)

print(f"Documentation generated in {output_dir}")
