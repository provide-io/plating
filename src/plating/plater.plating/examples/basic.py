from pathlib import Path

from plating.plating import PlatingBundle
from plating.plater import PlatingPlater

# Create a bundle
bundle = PlatingBundle(
    name="vpc", plating_dir=Path("./resources/vpc.plating"), component_type="resource"
)

# Create plater and render
plater = PlatingPlater(bundles=[bundle])
plater.plate(Path("./docs"))

# Check output
output_file = Path("./docs/resources/vpc.md")
if output_file.exists():
    print(f"Documentation generated: {output_file}")
