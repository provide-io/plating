# Complete Examples

Real-world examples of using Plating for documentation generation.

## Full Provider Documentation

Complete workflow for documenting an entire provider:

```python
#!/usr/bin/env python3
"""
generate_docs.py - Generate complete provider documentation
"""
import asyncio
import sys
from pathlib import Path
from plating import Plating, PlatingContext
from plating.types import ComponentType
from provide.foundation import logger, pout, perr

async def generate_provider_docs():
    """Generate documentation for entire provider."""

    # Configure context
    context = PlatingContext(
        provider_name="mycloud",
        log_level="INFO",
        no_color=False
    )

    # Initialize API
    api = Plating(context, package_name="pyvider.mycloud")

    pout("🚀 Starting documentation generation for mycloud provider")

    # Step 1: Create templates for undocumented components
    pout("\n📝 Creating documentation templates...")
    adorn_result = await api.adorn()

    if adorn_result.templates_generated > 0:
        pout(f"✅ Created {adorn_result.templates_generated} new templates")
        pout(f"   Components processed: {adorn_result.components_processed}")
    else:
        pout("ℹ️  All components already have templates")

    # Step 2: Generate documentation (validation runs automatically)
    pout("\n📄 Generating documentation...")
    plate_result = await api.plate(
        output_dir=Path("docs"),
        validate_markdown=True,  # Validates during generation
        force=True  # Overwrite existing files
    )

    if plate_result.success:
        pout(f"✅ Generated {plate_result.files_generated} documentation files")
        for file in plate_result.output_files[:5]:  # Show first 5
            pout(f"   • {file}")
        if len(plate_result.output_files) > 5:
            pout(f"   • ... and {len(plate_result.output_files) - 5} more")
    else:
        perr("❌ Documentation generation failed")
        for error in plate_result.errors:
            perr(f"   • {error}")
        return False

    # Note: validate_markdown=True already validated during generation
    # Optional: Run standalone validation if you need additional checks
    # validate_result = await api.validate(output_dir=Path("docs"))

    # Step 3: Generate statistics
    stats = api.get_registry_stats()  # Note: This is a sync method, not async
    pout(f"\n📈 Documentation Coverage:")
    pout(f"   • Resources: {stats['resource']['total']} total, {stats['resource']['with_templates']} with docs")
    pout(f"   • Data Sources: {stats['data_source']['total']} total, {stats['data_source']['with_templates']} with docs")
    pout(f"   • Functions: {stats['function']['total']} total, {stats['function']['with_templates']} with docs")

    pout(f"\n✨ Documentation generation complete!")
    return True

if __name__ == "__main__":
    success = asyncio.run(generate_provider_docs())
    sys.exit(0 if success else 1)
```

## Multi-Provider Batch Processing

Process multiple providers in parallel:

```python
#!/usr/bin/env python3
"""
batch_docs.py - Generate docs for multiple providers
"""
import asyncio
from pathlib import Path
from typing import List, Tuple
from plating import Plating, PlatingContext
from plating.types import PlateResult

async def process_provider(
    provider_name: str,
    package_name: str
) -> Tuple[str, PlateResult]:
    """Process a single provider."""

    context = PlatingContext(
        provider_name=provider_name,
        quiet=True  # Suppress output for parallel processing
    )

    api = Plating(context, package_name=package_name)

    # Generate docs
    output_dir = Path(f"docs/{provider_name}")
    result = await api.plate(output_dir=output_dir)

    return provider_name, result

async def batch_process():
    """Process multiple providers in parallel."""

    providers = [
        ("aws", "pyvider.aws"),
        ("azure", "pyvider.azure"),
        ("gcp", "pyvider.gcp"),
        ("kubernetes", "pyvider.kubernetes"),
    ]

    print(f"Processing {len(providers)} providers...")

    # Process all providers in parallel
    tasks = [
        process_provider(name, package)
        for name, package in providers
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Report results
    for provider_name, result in results:
        if isinstance(result, Exception):
            print(f"❌ {provider_name}: Failed - {result}")
        elif isinstance(result, PlateResult):
            if result.success:
                print(f"✅ {provider_name}: {result.files_generated} files")
            else:
                print(f"❌ {provider_name}: Failed with {len(result.errors)} errors")

if __name__ == "__main__":
    asyncio.run(batch_process())
```

## CI/CD Integration

GitHub Actions workflow example:

```python
#!/usr/bin/env python3
"""
ci_docs.py - CI/CD documentation generation script
"""
import asyncio
import os
import sys
from pathlib import Path
from plating import Plating, PlatingContext

async def ci_generate_docs():
    """Generate docs for CI/CD pipeline."""

    # Get configuration from environment
    provider_name = os.environ.get("PROVIDER_NAME", "myprovider")
    package_name = os.environ.get("PACKAGE_NAME", "pyvider.myprovider")
    output_dir = Path(os.environ.get("DOCS_OUTPUT", "docs"))

    # CI-optimized context
    context = PlatingContext(
        provider_name=provider_name,
        no_color=True,  # No colors in CI logs
        verbose=True    # Detailed output for debugging
    )

    api = Plating(context, package_name=package_name)

    # Generate documentation
    result = await api.plate(
        output_dir=output_dir,
        validate_markdown=True,
        force=True
    )

    if not result.success:
        print(f"::error::Documentation generation failed")
        for error in result.errors:
            print(f"::error::{error}")
        return 1

    # Validate
    validate_result = await api.validate(output_dir=output_dir)

    if validate_result.failed > 0:
        print(f"::warning::{validate_result.failed} files failed validation")
        return 1

    print(f"::notice::Generated {result.files_generated} documentation files")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(ci_generate_docs())
    sys.exit(exit_code)
```

## Custom Template Functions

Add custom functions to templates:

```python
#!/usr/bin/env python3
"""
custom_functions.py - Custom template functions
"""
import asyncio
from datetime import datetime
from pathlib import Path
from plating import Plating, PlatingContext
from plating.templating.engine import template_engine

def format_date(date_str: str) -> str:
    """Format date for documentation."""
    dt = datetime.fromisoformat(date_str)
    return dt.strftime("%B %d, %Y")

def terraform_version(version: str) -> str:
    """Format Terraform version requirement."""
    return f"Terraform >= {version}"

async def generate_with_custom_functions():
    """Generate docs with custom template functions."""

    context = PlatingContext(provider_name="myprovider")
    api = Plating(context)

    # Add custom functions to the global template engine
    template_engine._jinja_env.globals.update({
        "format_date": format_date,
        "tf_version": terraform_version,
        "provider_version": lambda: "1.2.3",
        "copyright_year": lambda: datetime.now().year,
    })

    # Now templates can use:
    # {{ format_date("2024-01-01") }}
    # {{ tf_version("1.0") }}
    # {{ provider_version() }}
    # {{ copyright_year() }}

    result = await api.plate()
    return result

asyncio.run(generate_with_custom_functions())
```

## Selective Component Processing

Process specific components:

```python
#!/usr/bin/env python3
"""
selective_docs.py - Generate docs for specific components
"""
import asyncio
from plating import Plating, PlatingContext
from plating.types import ComponentType

async def selective_generation():
    """Generate docs for specific component types."""

    context = PlatingContext(provider_name="myprovider")
    api = Plating(context, package_name="pyvider.myprovider")

    # Only process resources
    print("Processing resources...")
    resource_result = await api.plate(
        component_types=[ComponentType.RESOURCE]
    )
    print(f"Generated {resource_result.files_generated} resource docs")

    # Only process data sources
    print("Processing data sources...")
    data_result = await api.plate(
        component_types=[ComponentType.DATA_SOURCE]
    )
    print(f"Generated {data_result.files_generated} data source docs")

    # Process specific components by filtering
    registry = api.registry
    vpc_resources = [
        r for r in registry.get_components(ComponentType.RESOURCE)
        if "vpc" in r.name.lower()
    ]
    print(f"Found {len(vpc_resources)} VPC-related resources")

asyncio.run(selective_generation())
```

## Error Handling

Comprehensive error handling:

```python
#!/usr/bin/env python3
"""
robust_docs.py - Robust documentation generation with error handling
"""
import asyncio
import logging
from pathlib import Path
from plating import Plating, PlatingContext
from plating.errors import (
    PlatingError,
    TemplateError,
    FileSystemError,
    ValidationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def robust_generation():
    """Generate docs with comprehensive error handling."""

    try:
        context = PlatingContext(
            provider_name="myprovider",
            log_level="DEBUG"
        )
        api = Plating(context, package_name="pyvider.myprovider")

        # Attempt documentation generation
        result = await api.plate(output_dir=Path("docs"))

        if result.success:
            logger.info(f"Success! Generated {result.files_generated} files")
        else:
            logger.error(f"Failed with {len(result.errors)} errors")
            for error in result.errors:
                logger.error(f"  - {error}")

    except TemplateError as e:
        logger.error(f"Template error in {e.template_path}:{e.line_number}")
        logger.error(f"  Reason: {e.reason}")
        if e.template_context:
            logger.error(f"  Context: {e.template_context}")
        return False

    except FileSystemError as e:
        logger.error(f"File system error with {e.path}")
        logger.error(f"  Operation: {e.operation}")
        logger.error(f"  Reason: {e.reason}")
        if e.caused_by:
            logger.error(f"  Caused by: {e.caused_by}")
        return False

    except ValidationError as e:
        logger.error(f"Validation error: {e.validation_name}")
        logger.error(f"  Reason: {e.reason}")
        if e.file_path:
            logger.error(f"  File: {e.file_path}")
        for failure in e.failures:
            logger.error(f"  - {failure}")
        return False

    except PlatingError as e:
        logger.error(f"Plating error: {e}")
        return False

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(robust_generation())
    exit(0 if success else 1)
```

## Testing Documentation

Test harness for documentation:

```python
#!/usr/bin/env python3
"""
test_docs.py - Test documentation generation
"""
import asyncio
import tempfile
from pathlib import Path
from plating import Plating, PlatingContext

async def test_documentation():
    """Test documentation generation in temp directory."""

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "docs"

        context = PlatingContext(
            provider_name="testprovider",
            quiet=True
        )
        api = Plating(context, package_name="pyvider.testprovider")

        # Test adorning
        adorn_result = await api.adorn()
        assert adorn_result.errors == []

        # Test plating
        plate_result = await api.plate(output_dir=output_dir)
        assert plate_result.success
        assert plate_result.files_generated > 0

        # Verify files exist
        for file in plate_result.output_files:
            assert file.exists(), f"Missing: {file}"

        # Test validation
        validate_result = await api.validate(output_dir=output_dir)
        assert validate_result.failed == 0

        print("✅ All tests passed!")

asyncio.run(test_documentation())
```

## Custom Bundle Creation

Programmatically create bundles:

```python
#!/usr/bin/env python3
"""
create_bundle.py - Create custom documentation bundles
"""
import asyncio
from pathlib import Path
from plating.bundles import PlatingBundle

async def create_custom_bundle():
    """Create a custom plating bundle."""

    # Create bundle directory structure
    bundle_dir = Path("my_resource.plating")
    bundle_dir.mkdir(exist_ok=True)
    (bundle_dir / "docs").mkdir(exist_ok=True)
    (bundle_dir / "examples").mkdir(exist_ok=True)
    (bundle_dir / "fixtures").mkdir(exist_ok=True)

    # Create main template
    template = """---
page_title: "Resource: myprovider_my_resource"
description: "Manages a my_resource in MyProvider"
---

# myprovider_my_resource

Manages a my_resource in the MyProvider infrastructure.

## Example Usage

{{ example("basic") }}

## Schema

{{ schema() }}

## Import

```bash
terraform import myprovider_my_resource.example <id>
```
"""

    (bundle_dir / "docs" / "my_resource.tmpl.md").write_text(template)

    # Create example
    example = '''resource "myprovider_my_resource" "example" {
  name        = "example-resource"
  description = "Created by Plating"

  configuration {
    setting = "value"
  }
}'''

    (bundle_dir / "examples" / "basic.tf").write_text(example)

    # Create bundle instance
    bundle = PlatingBundle(
        name="my_resource",
        plating_dir=bundle_dir,
        component_type="resource"
    )

    print(f"Created bundle: {bundle.name}")
    print(f"  Docs: {bundle.docs_dir}")
    print(f"  Examples: {bundle.examples_dir}")
    print(f"  Has template: {bundle.has_main_template()}")

asyncio.run(create_custom_bundle())
```