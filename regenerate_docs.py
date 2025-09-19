#!/usr/bin/env python3
"""Regenerate pyvider-components documentation using new plating system."""

import sys
from pathlib import Path

# Add src to path for direct imports
sys.path.insert(0, "src")

from plating.api import PlatingAPI

def main():
    """Regenerate all documentation for pyvider-components."""
    print("🚀 Regenerating pyvider-components documentation...")

    # Set up paths
    docs_dir = Path("/Users/tim/code/gh/provide-io/pyvider-components/docs")
    docs_dir.mkdir(exist_ok=True)

    # Create subdirectories
    functions_dir = docs_dir / "functions"
    resources_dir = docs_dir / "resources"
    data_sources_dir = docs_dir / "data_sources"

    functions_dir.mkdir(exist_ok=True)
    resources_dir.mkdir(exist_ok=True)
    data_sources_dir.mkdir(exist_ok=True)

    api = PlatingAPI()

    try:
        print("\n📚 Generating function documentation...")
        function_files = api.generate_function_documentation(functions_dir)
        function_paths = api.write_generated_files(function_files)
        print(f"✅ Generated {len(function_paths)} function documentation files")

        print("\n📦 Generating resource documentation...")
        resource_files = api.generate_resource_documentation(resources_dir)
        resource_paths = api.write_generated_files(resource_files)
        print(f"✅ Generated {len(resource_paths)} resource documentation files")

        print("\n📊 Generating all documentation...")
        all_files = api.generate_all_documentation(docs_dir)
        print(f"✅ Generated {len(all_files)} total documentation files")

        # Show sample of what was generated
        print(f"\n📋 Sample of generated files:")
        all_files_on_disk = list(docs_dir.rglob("*.md"))
        for i, file_path in enumerate(sorted(all_files_on_disk)[:10]):
            rel_path = file_path.relative_to(docs_dir)
            print(f"  {i+1:2d}. {rel_path}")

        if len(all_files_on_disk) > 10:
            print(f"  ... and {len(all_files_on_disk) - 10} more files")

        print(f"\n🎉 Documentation regeneration complete!")
        print(f"📁 Total files generated: {len(all_files_on_disk)}")
        print(f"📍 Documentation location: {docs_dir}")

    except Exception as e:
        print(f"❌ Error during documentation generation: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())