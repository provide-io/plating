from pathlib import Path
from garnish.garnish import GarnishBundle

# Create a bundle for a resource component
bundle = GarnishBundle(
    name="s3_bucket",
    garnish_dir=Path("./resources/s3_bucket.garnish"),
    component_type="resource"
)

# Access bundle properties
print(f"Bundle name: {bundle.name}")
print(f"Docs directory: {bundle.docs_dir}")
print(f"Component type: {bundle.component_type}")