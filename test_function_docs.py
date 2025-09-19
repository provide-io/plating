#!/usr/bin/env python3
"""Quick test script to verify individual function documentation generation."""

from pathlib import Path
from plating.api import PlatingAPI

def main():
    """Test individual function documentation generation."""
    print("Testing individual function documentation generation...")

    api = PlatingAPI()

    # Create a test output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    try:
        # Generate function documentation
        generated_files = api.generate_function_documentation(output_dir)

        if generated_files:
            print(f"\nGenerated {len(generated_files)} function documentation files:")
            for file_path, content in generated_files:
                print(f"  - {file_path}")
                # Show first few lines of content
                lines = content.split('\n')[:5]
                for line in lines:
                    print(f"    {line}")
                print("    ...")
        else:
            print("No function documentation files were generated.")
            print("This might mean no .plating bundles were found or no function templates exist.")

        # Write the files to disk
        if generated_files:
            written_files = api.write_generated_files(generated_files)
            print(f"\nWrote {len(written_files)} files to disk:")
            for file_path in written_files:
                print(f"  - {file_path}")

    except Exception as e:
        print(f"Error during generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()