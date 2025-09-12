from pathlib import Path

from plating.plating import PlatingBundle
from plating.generator import DocsGenerator
from plating.plater import PlatingPlater
from plating.schema import SchemaProcessor

# Setup schema processor
generator = DocsGenerator(provider_dir=Path("."), provider_name="my_provider")
schema_processor = SchemaProcessor(generator)

# Create bundle
bundle = PlatingBundle(
    name="instance",
    plating_dir=Path("./resources/instance.plating"),
    component_type="resource",
)

# Plate with schema support
plater = PlatingPlater(bundles=[bundle], schema_processor=schema_processor)

# Render with schema information included
plater.plate(Path("./docs"), force=True)

print("Documentation with schema generated!")
