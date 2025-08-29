from pathlib import Path

from garnish.garnish import GarnishBundle
from garnish.plater import GarnishPlater

# Create a bundle
bundle = GarnishBundle(
    name="vpc",
    garnish_dir=Path("./resources/vpc.garnish"),
    component_type="resource"
)

# Create plater and render
plater = GarnishPlater(bundles=[bundle])
plater.plate(Path("./docs"))

# Check output
output_file = Path("./docs/resources/vpc.md")
if output_file.exists():
    print(f"Documentation generated: {output_file}")
