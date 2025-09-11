from pathlib import Path

from plating.plating import PlatingDiscovery
from plating.plater import PlatingPlater

# Discover all bundles in the provider
discovery = PlatingDiscovery(package_name="my_provider")
bundles = discovery.discover_bundles()

print(f"Found {len(bundles)} bundles to plate")

# Batch plate all bundles
plater = PlatingPlater(bundles=bundles)
output_dir = Path("./docs")

# Render all documentation
plater.plate(output_dir, force=True)

# Count generated files
resource_docs = list((output_dir / "resources").glob("*.md"))
data_docs = list((output_dir / "data-sources").glob("*.md"))
function_docs = list((output_dir / "functions").glob("*.md"))

print("Generated:")
print(f"  - {len(resource_docs)} resource docs")
print(f"  - {len(data_docs)} data source docs")
print(f"  - {len(function_docs)} function docs")
