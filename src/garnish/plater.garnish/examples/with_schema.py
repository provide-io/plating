from pathlib import Path

from garnish.garnish import GarnishBundle
from garnish.generator import DocsGenerator
from garnish.plater import GarnishPlater
from garnish.schema import SchemaProcessor

# Setup schema processor
generator = DocsGenerator(
    provider_dir=Path("."),
    provider_name="my_provider"
)
schema_processor = SchemaProcessor(generator)

# Create bundle
bundle = GarnishBundle(
    name="instance",
    garnish_dir=Path("./resources/instance.garnish"),
    component_type="resource"
)

# Plate with schema support
plater = GarnishPlater(
    bundles=[bundle],
    schema_processor=schema_processor
)

# Render with schema information included
plater.plate(Path("./docs"), force=True)

print("Documentation with schema generated!")
