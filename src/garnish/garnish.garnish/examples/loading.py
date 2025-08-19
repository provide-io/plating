from pathlib import Path
from garnish.garnish import GarnishBundle

# Create and load bundle assets
bundle = GarnishBundle(
    name="database",
    garnish_dir=Path("./resources/database.garnish"),
    component_type="resource"
)

# Load the main template
template = bundle.load_main_template()
if template:
    print(f"Template loaded: {len(template)} characters")

# Load all examples
examples = bundle.load_examples()
for name, content in examples.items():
    print(f"Example '{name}': {len(content)} characters")

# Load partials for template inclusion
partials = bundle.load_partials()
print(f"Found {len(partials)} partials")

# Load test fixtures
fixtures = bundle.load_fixtures()
print(f"Found {len(fixtures)} fixtures")