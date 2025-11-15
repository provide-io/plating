#!/usr/bin/env python3
"""
Use garnish to document itself!
"""
from pathlib import Path
from garnish.garnish import GarnishBundle
from garnish.plater import GarnishPlater

def main():
    """Generate garnish documentation using garnish."""
    
    # Find all .garnish bundles in src/garnish
    src_dir = Path(__file__).parent / "src" / "garnish"
    garnish_dirs = list(src_dir.glob("*.garnish"))
    
    print("🍲 Garnish is documenting itself!")
    print(f"Found {len(garnish_dirs)} garnish bundles:")
    
    bundles = []
    for garnish_dir in garnish_dirs:
        # Extract component name from directory
        name = garnish_dir.stem  # Remove .garnish extension
        
        # Determine component type (treating them as "modules" for documentation)
        component_type = "resource"  # Use resource type for standard doc layout
        
        print(f"  - {name}")
        
        bundle = GarnishBundle(
            name=name,
            garnish_dir=garnish_dir,
            component_type=component_type
        )
        bundles.append(bundle)
    
    # Create output directory
    output_dir = Path(__file__).parent / "self_docs"
    output_dir.mkdir(exist_ok=True)
    
    # Plate the documentation
    print(f"\n🍽️ Plating documentation to {output_dir}")
    plater = GarnishPlater(bundles=bundles)
    plater.plate(output_dir, force=True)
    
    # Special handling for README
    readme_bundle = None
    for bundle in bundles:
        if bundle.name == "readme":
            readme_bundle = bundle
            break
    
    if readme_bundle:
        # Generate README.md at root
        readme_template = readme_bundle.load_main_template()
        if readme_template:
            # Simple template processing (no Jinja2 for README)
            readme_path = Path(__file__).parent / "README.md"
            readme_path.write_text(readme_template)
            print(f"\n📝 Generated README.md at {readme_path}")
    
    print("\n✨ Documentation complete!")
    print(f"View the generated docs in: {output_dir}")
    
    # List generated files
    generated_files = list(output_dir.rglob("*.md"))
    if generated_files:
        print(f"\nGenerated {len(generated_files)} documentation files:")
        for file in generated_files:
            print(f"  - {file.relative_to(output_dir)}")

if __name__ == "__main__":
    main()