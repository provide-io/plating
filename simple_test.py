#!/usr/bin/env python3
"""Simple test script to verify function documentation generation without complex imports."""

from pathlib import Path

# Import just the components we need
from plating.discovery import PlatingDiscovery, TemplateMetadataExtractor
from plating.generation import DocumentationPlater

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

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()