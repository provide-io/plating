from pathlib import Path
from garnish.garnish import GarnishDiscovery
from garnish.plater import GarnishPlater

# Discover all bundles in the provider
discovery = GarnishDiscovery(package_name="my_provider")
bundles = discovery.discover_bundles()

print(f"Found {len(bundles)} bundles to plate")

# Batch plate all bundles
plater = GarnishPlater(bundles=bundles)
output_dir = Path("./docs")

# Render all documentation
plater.plate(output_dir, force=True)

# Count generated files
resource_docs = list((output_dir / "resources").glob("*.md"))
data_docs = list((output_dir / "data-sources").glob("*.md"))
function_docs = list((output_dir / "functions").glob("*.md"))

print(f"Generated:")
print(f"  - {len(resource_docs)} resource docs")
print(f"  - {len(data_docs)} data source docs")
print(f"  - {len(function_docs)} function docs")