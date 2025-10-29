#
# plating/compiler/single.py
#
"""Single-component example compilation."""

from __future__ import annotations

from pathlib import Path

from attrs import define, field
from provide.foundation import logger

from plating.bundles import PlatingBundle
from plating.types import ComponentType


@define
class SingleCompilationResult:
    """Result of single-component example compilation."""

    examples_generated: int = field(default=0)
    output_files: list[Path] = field(factory=list)
    errors: list[str] = field(factory=list)


class SingleExampleCompiler:
    """Compiles single-component executable Terraform examples."""

    def __init__(self, provider_name: str, provider_version: str = "0.0.5") -> None:
        """Initialize the single example compiler.

        Args:
            provider_name: Name of the Terraform provider
            provider_version: Version of the provider
        """
        self.provider_name = provider_name
        self.provider_version = provider_version

    def compile_examples(
        self,
        bundles: list[PlatingBundle],
        output_dir: Path,
        component_types: list[ComponentType] | None = None,
    ) -> SingleCompilationResult:
        """Compile single-component executable examples from plating bundles.

        Args:
            bundles: List of plating bundles to compile examples from
            output_dir: Base directory for generated examples (e.g., "examples")
            component_types: Filter to specific component types

        Returns:
            SingleCompilationResult with generated files and statistics
        """
        result = SingleCompilationResult()

        # Group bundles by component type
        bundles_by_type: dict[ComponentType, list[PlatingBundle]] = {}
        for bundle in bundles:
            # Convert string component_type to ComponentType enum
            bundle_type = (
                ComponentType(bundle.component_type)
                if isinstance(bundle.component_type, str)
                else bundle.component_type
            )

            if component_types and bundle_type not in component_types:
                continue

            if bundle_type not in bundles_by_type:
                bundles_by_type[bundle_type] = []
            bundles_by_type[bundle_type].append(bundle)

        # Generate examples for each component type
        for component_type, type_bundles in bundles_by_type.items():
            type_dir = output_dir / component_type.value
            type_dir.mkdir(parents=True, exist_ok=True)

            # Process each bundle individually - don't deduplicate
            # Each component should get its own example directory based on its name
            for bundle in type_bundles:
                try:
                    self._compile_component_examples(bundle, type_dir, result)
                except Exception as e:
                    error_msg = f"Failed to compile examples for {bundle.name}: {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)

        logger.info(f"Generated {result.examples_generated} single-component executable examples")
        return result

    def _compile_component_examples(
        self, bundle: PlatingBundle, type_dir: Path, result: SingleCompilationResult
    ) -> None:
        """Compile examples for a specific component.

        Args:
            bundle: Plating bundle
            type_dir: Directory for this component type
            result: Result object to update
        """
        if not bundle.has_examples():
            return

        # Strip provider prefix from component name for directory naming
        component_name = bundle.name
        if self.provider_name and component_name.startswith(f"{self.provider_name}_"):
            component_name = component_name[len(self.provider_name) + 1:]

        component_dir = type_dir / component_name
        component_dir.mkdir(parents=True, exist_ok=True)

        # Load only flat examples (not grouped ones)
        flat_examples = self._load_flat_examples(bundle)
        if not flat_examples:
            return

        # Generate provider.tf once for this component directory
        is_test_only = self._is_test_only_component(bundle, component_type)
        self._generate_provider_tf(component_dir, is_test_only)

        # Generate flat .tf files in the component directory
        for example_name, example_content in flat_examples.items():
            # Strip any provider blocks from the example content
            cleaned_content = self._strip_provider_blocks(example_content)

            # Write as flat .tf file
            tf_path = component_dir / f"{example_name}.tf"
            tf_path.write_text(cleaned_content, encoding="utf-8")
            result.output_files.append(tf_path)
            result.examples_generated += 1

    def _load_flat_examples(self, bundle: PlatingBundle) -> dict[str, str]:
        """Load only flat .tf examples (not grouped subdirectories).

        For bundles that share a plating directory with multiple components,
        filter examples to only include those that reference this specific component.

        Args:
            bundle: Plating bundle

        Returns:
            Dictionary of flat example name to content
        """
        flat_examples: dict[str, str] = {}

        if not bundle.examples_dir.exists():
            return flat_examples

        # Only load flat .tf files
        for example_file in bundle.examples_dir.glob("*.tf"):
            try:
                content = example_file.read_text(encoding="utf-8")

                # Filter examples: only include if they reference this component
                # Check if the component name appears in the example
                if self._example_references_component(content, bundle.name):
                    flat_examples[example_file.stem] = content
            except Exception:
                continue

        return flat_examples

    def _example_references_component(self, content: str, component_name: str) -> bool:
        """Check if an example file references a specific component.

        Args:
            content: Example file content
            component_name: Component name to search for

        Returns:
            True if the example references this component
        """
        # Look for references to the component in resource/data source/function calls
        # This handles: resource "component_name", data "component_name", provider::component_name()
        import re

        # Match resource/data declarations: resource "name" or data "name"
        resource_pattern = rf'(resource|data)\s+"{re.escape(component_name)}"'
        if re.search(resource_pattern, content):
            return True

        # Match function calls: provider::function_name()
        function_pattern = rf'{re.escape(self.provider_name)}::{re.escape(component_name)}\s*\('
        if re.search(function_pattern, content):
            return True

        return False

    def _generate_provider_tf(self, component_dir: Path) -> None:
        """Generate provider.tf file for a component directory.

        Args:
            component_dir: Directory for the component
        """
        provider_content = f"""terraform {{
  required_providers {{
    {self.provider_name} = {{
      source  = "local/providers/{self.provider_name}"
      version = ">= {self.provider_version}"
    }}
  }}
}}

provider "{self.provider_name}" {{
  # Provider configuration
  # Add your configuration options here
}}
"""
        provider_path = component_dir / "provider.tf"
        provider_path.write_text(provider_content, encoding="utf-8")

    def _strip_provider_blocks(self, content: str) -> str:
        """Strip terraform and provider blocks from example content.

        Args:
            content: Example content that may contain provider blocks

        Returns:
            Content with provider blocks removed
        """
        import re

        # Remove terraform block with required_providers
        content = re.sub(
            r'terraform\s*\{[^}]*required_providers\s*\{[^}]*\}[^}]*\}\s*\n*',
            '',
            content,
            flags=re.DOTALL
        )

        # Remove provider block
        content = re.sub(
            r'provider\s+"[^"]*"\s*\{[^}]*\}\s*\n*',
            '',
            content,
            flags=re.DOTALL
        )

        # Remove "Generated by Plating" comment if present
        content = re.sub(
            r'#\s*Generated by Plating[^\n]*\n*',
            '',
            content
        )

        # Clean up multiple blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content.strip() + '\n'

    def _generate_example_readme(self, bundle: PlatingBundle, example_name: str, content: str) -> str:
        """Generate README for an individual example.

        Args:
            bundle: Plating bundle
            example_name: Name of the example
            content: Example content

        Returns:
            README markdown content
        """
        bundle_type = (
            ComponentType(bundle.component_type)
            if isinstance(bundle.component_type, str)
            else bundle.component_type
        )
        return f"""# {bundle_type.value.replace("_", " ").title()}: {bundle.name} - {example_name} Example

This directory contains a complete, executable Terraform example demonstrating the `{bundle.name}` {bundle_type.value.replace("_", " ")}.

## What This Example Does

{self._extract_description_from_content(content)}

## How to Run

1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Review the planned changes:
   ```bash
   terraform plan
   ```

3. Apply the configuration:
   ```bash
   terraform apply
   ```

4. When you're done, clean up:
   ```bash
   terraform destroy
   ```

## Files

- `main.tf` - Complete Terraform configuration
- `README.md` - This documentation

## Requirements

- Terraform >= 1.0
- {self.provider_name} provider >= {self.provider_version}

Generated by [Plating](https://github.com/provide-io/plating) - Terraform Provider Documentation Generator
"""

    def _extract_description_from_content(self, content: str) -> str:
        """Extract a description from the first comment in the content.

        Args:
            content: Terraform content

        Returns:
            Description string
        """
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#") and not line.startswith("##"):
                return line[1:].strip()
        return "Demonstrates the basic usage of this component."


# 🍲⚡📦🔨
