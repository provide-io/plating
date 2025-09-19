#!/usr/bin/env python3
"""Direct test script without importing from plating package to avoid decorator issues."""

import sys
from pathlib import Path

# Add src to path for direct imports
sys.path.insert(0, "src")

# Direct imports to avoid __init__.py decorator issues
from plating.discovery.finder import PlatingDiscovery
from plating.discovery.templates import TemplateMetadataExtractor
from plating.generation.plater import DocumentationPlater

def main():
    """Test individual function documentation generation."""
    print("Testing individual function documentation generation...")

    # Test metadata generation
    extractor = TemplateMetadataExtractor()

    # Test different function types
    test_functions = ["upper", "lower", "add", "multiply", "join", "unknown_function"]

    print("\n=== Testing Metadata Generation ===")
    for func_name in test_functions:
        metadata = extractor.extract_function_metadata(func_name, "function")
        print(f"\nFunction: {func_name}")
        print(f"  Signature: {metadata['signature_markdown']}")
        print(f"  Description: {metadata.get('description', 'No description')}")
        print(f"  Example: {metadata['examples']['basic']}")

    # Test discovery
    print("\n=== Testing Discovery ===")
    discovery = PlatingDiscovery()
    bundles = discovery.discover_bundles(component_type="function")

    if bundles:
        print(f"Found {len(bundles)} function bundles:")
        for bundle in bundles:
            print(f"  - {bundle.name} ({type(bundle).__name__})")
            if hasattr(bundle, 'template_file'):
                print(f"    Template: {bundle.template_file}")
    else:
        print("No function bundles found.")
        print("This is expected if no pyvider.components package is installed.")

    # Test documentation generation
    print("\n=== Testing Documentation Generation ===")
    try:
        plater = DocumentationPlater()

        # Create test output directory
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)

        generated_files = plater.generate_documentation(output_dir, component_type="function")

        if generated_files:
            print(f"Generated {len(generated_files)} documentation files:")
            for file_path, content in generated_files:
                print(f"  - {file_path}")
                lines = content.split('\n')[:3]
                for line in lines:
                    print(f"    {line}")
                print("    ...")
        else:
            print("No documentation files generated (no bundles found).")

    except Exception as e:
        print(f"Error during generation: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()