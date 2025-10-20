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

        component_dir = type_dir / bundle.name
        component_dir.mkdir(parents=True, exist_ok=True)

        # Load only flat examples (not grouped ones)
        flat_examples = self._load_flat_examples(bundle)
        if not flat_examples:
            return

        # Generate individual example directories
        for example_name, example_content in flat_examples.items():
            self._generate_individual_example(bundle, component_dir, example_name, example_content, result)

    def _load_flat_examples(self, bundle: PlatingBundle) -> dict[str, str]:
        """Load only flat .tf examples (not grouped subdirectories).

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
                flat_examples[example_file.stem] = example_file.read_text(encoding="utf-8")
            except Exception:
                continue

        return flat_examples

    def _generate_individual_example(
        self,
        bundle: PlatingBundle,
        component_dir: Path,
        example_name: str,
        example_content: str,
        result: SingleCompilationResult,
    ) -> None:
        """Generate a single executable example.

        Args:
            bundle: Plating bundle
            component_dir: Directory for this component
            example_name: Name of the example
            example_content: Content of the example
            result: Result object to update
        """
        example_dir = component_dir / example_name
        example_dir.mkdir(parents=True, exist_ok=True)

        # Generate main.tf with provider config + example
        main_tf_content = self._build_complete_example(example_content)
        main_tf_path = example_dir / "main.tf"
        main_tf_path.write_text(main_tf_content, encoding="utf-8")
        result.output_files.append(main_tf_path)

        # Generate README.md
        readme_content = self._generate_example_readme(bundle, example_name, example_content)
        readme_path = example_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        result.output_files.append(readme_path)

        result.examples_generated += 1

    def _build_complete_example(self, example_content: str) -> str:
        """Build a complete Terraform configuration with provider block.

        Args:
            example_content: Terraform resource/data source content

        Returns:
            Complete Terraform configuration
        """
        provider_config = self._generate_provider_config()

        # Add some spacing and comments
        complete_content = f"""{provider_config}

# Generated by Plating - Executable Example
{example_content}
"""
        return complete_content

    def _generate_provider_config(self) -> str:
        """Generate provider configuration block.

        Returns:
            Terraform provider configuration
        """
        return f'''terraform {{
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
}}'''

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
