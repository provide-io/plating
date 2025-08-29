from pathlib import Path

from garnish.garnish import GarnishBundle, GarnishDiscovery
from garnish.plater import GarnishPlater

# Discover all bundles in a provider
discovery = GarnishDiscovery(package_name="my_provider")
bundles = discovery.discover_bundles()

# Or create bundles manually
bundle = GarnishBundle(
    name="load_balancer",
    garnish_dir=Path("./resources/load_balancer.garnish"),
    component_type="resource",
)

# Plate the documentation
plater = GarnishPlater(bundles=[bundle])
output_dir = Path("./docs")
plater.plate(output_dir, force=True)

print(f"Documentation generated in {output_dir}")
