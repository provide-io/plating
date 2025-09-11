from pathlib import Path

from plating.plating import PlatingBundle

# Create a bundle for a resource component
bundle = PlatingBundle(
    name="s3_bucket",
    plating_dir=Path("./resources/s3_bucket.plating"),
    component_type="resource",
)

# Access bundle properties
print(f"Bundle name: {bundle.name}")
print(f"Docs directory: {bundle.docs_dir}")
print(f"Component type: {bundle.component_type}")
