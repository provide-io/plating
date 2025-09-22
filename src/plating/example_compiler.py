from __future__ import annotations

from pathlib import Path

from attrs import define, field
from provide.foundation import logger

from plating.bundles import PlatingBundle
from plating.types import ComponentType

#
# plating/example_compiler.py
#
"""Executable example compilation for Terraform provider documentation."""


@define(frozen=True)
class CompilationResult:
    """Result of example compilation process."""

    examples_generated: int = field(default=0)
    output_files: list[Path] = field(factory=list)
    errors: list[str] = field(factory=list)
    provider_config_path: Path | None = field(default=None)
    complete_example_path: Path | None = field(default=None)


class ExampleCompiler:
    """Compiles executable Terraform examples from plating bundles."""

    def __init__(self, provider_name: str, provider_version: str = "0.0.5") -> None:
        self.provider_name = provider_name
        self.provider_version = provider_version

    def compile_examples(
        self,
        bundles: list[PlatingBundle],
        output_dir: Path,
        component_types: list[ComponentType] | None = None,
    ) -> CompilationResult:
        """Compile executable examples from plating bundles.

        Args:
            bundles: List of plating bundles to compile examples from
            output_dir: Base directory for generated examples (docs/examples)
            component_types: Filter to specific component types

        Returns:
            CompilationResult with generated files and statistics
        """
        result = CompilationResult()
        examples_dir = output_dir / "examples"
        examples_dir.mkdir(parents=True, exist_ok=True)

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
            type_dir = examples_dir / component_type.value
            type_dir.mkdir(parents=True, exist_ok=True)

            for bundle in type_bundles:
                try:
                    self._compile_component_examples(bundle, type_dir, result)
                except Exception as e:
                    error_msg = f"Failed to compile examples for {bundle.name}: {e}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)

        # Generate complete showcase example
        try:
            complete_path = self._generate_complete_example(bundles, examples_dir, result)
            result = CompilationResult(
                examples_generated=result.examples_generated,
                output_files=result.output_files,
                errors=result.errors,
                provider_config_path=result.provider_config_path,
                complete_example_path=complete_path,
            )
        except Exception as e:
            result.errors.append(f"Failed to generate complete example: {e}")

        logger.info(f"Generated {result.examples_generated} executable examples")
        return result

    def _compile_component_examples(
        self, bundle: PlatingBundle, type_dir: Path, result: CompilationResult
    ) -> None:
        """Compile examples for a specific component."""
        if not bundle.has_examples():
            return

        component_dir = type_dir / bundle.name
        component_dir.mkdir(parents=True, exist_ok=True)

        examples = bundle.load_examples()
        if not examples:
            return

        # Generate individual example directories
        for example_name, example_content in examples.items():
            self._generate_individual_example(bundle, component_dir, example_name, example_content, result)

        # Generate combined example if multiple examples exist
        if len(examples) > 1:
            self._generate_combined_example(bundle, component_dir, examples, result)

    def _generate_individual_example(
        self,
        bundle: PlatingBundle,
        component_dir: Path,
        example_name: str,
        example_content: str,
        result: CompilationResult,
    ) -> None:
        """Generate a single executable example."""
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

        result = CompilationResult(
            examples_generated=result.examples_generated + 1,
            output_files=result.output_files,
            errors=result.errors,
            provider_config_path=result.provider_config_path,
            complete_example_path=result.complete_example_path,
        )

    def _generate_combined_example(
        self,
        bundle: PlatingBundle,
        component_dir: Path,
        examples: dict[str, str],
        result: CompilationResult,
    ) -> None:
        """Generate a combined example showing all component capabilities."""
        combined_dir = component_dir / "complete"
        combined_dir.mkdir(parents=True, exist_ok=True)

        # Combine all examples
        combined_content = self._combine_examples(examples)
        main_tf_content = self._build_complete_example(combined_content)

        main_tf_path = combined_dir / "main.tf"
        main_tf_path.write_text(main_tf_content, encoding="utf-8")
        result.output_files.append(main_tf_path)

        # Generate combined README
        readme_content = self._generate_combined_readme(bundle, examples)
        readme_path = combined_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        result.output_files.append(readme_path)

        result = CompilationResult(
            examples_generated=result.examples_generated + 1,
            output_files=result.output_files,
            errors=result.errors,
            provider_config_path=result.provider_config_path,
            complete_example_path=result.complete_example_path,
        )

    def _generate_complete_example(
        self, bundles: list[PlatingBundle], examples_dir: Path, result: CompilationResult
    ) -> Path:
        """Generate a complete showcase example using all components."""
        complete_dir = examples_dir / "complete_showcase"
        complete_dir.mkdir(parents=True, exist_ok=True)

        # Collect representative examples from each component
        showcase_content = self._build_showcase_content(bundles)
        main_tf_content = self._build_complete_example(showcase_content)

        main_tf_path = complete_dir / "main.tf"
        main_tf_path.write_text(main_tf_content, encoding="utf-8")
        result.output_files.append(main_tf_path)

        # Generate variables file
        variables_content = self._generate_variables_tf()
        variables_path = complete_dir / "variables.tf"
        variables_path.write_text(variables_content, encoding="utf-8")
        result.output_files.append(variables_path)

        # Generate outputs file
        outputs_content = self._generate_outputs_tf(bundles)
        outputs_path = complete_dir / "outputs.tf"
        outputs_path.write_text(outputs_content, encoding="utf-8")
        result.output_files.append(outputs_path)

        # Generate showcase README
        readme_content = self._generate_showcase_readme(bundles)
        readme_path = complete_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")
        result.output_files.append(readme_path)

        return complete_dir

    def _build_complete_example(self, example_content: str) -> str:
        """Build a complete Terraform configuration with provider block."""
        provider_config = self._generate_provider_config()

        # Add some spacing and comments
        complete_content = f"""{provider_config}

# Generated by Plating - Executable Example
{example_content}
"""
        return complete_content

    def _generate_provider_config(self) -> str:
        """Generate provider configuration block."""
        return f'''terraform {{
  required_providers {{
    {self.provider_name} = {{
      source  = "registry.terraform.io/provide-io/{self.provider_name}"
      version = ">= {self.provider_version}"
    }}
  }}
}}

provider "{self.provider_name}" {{
  # Provider configuration
  # Add your configuration options here
}}'''

    def _combine_examples(self, examples: dict[str, str]) -> str:
        """Combine multiple example files into cohesive example."""
        combined = []

        for example_name, content in examples.items():
            combined.append(f"# === {example_name.title()} Example ===")
            combined.append("")
            combined.append(content.strip())
            combined.append("")
            combined.append("")

        return "\n".join(combined)

    def _build_showcase_content(self, bundles: list[PlatingBundle]) -> str:
        """Build showcase content using examples from all components."""
        sections = []

        # Group by component type for organized showcase
        by_type: dict[ComponentType, list[PlatingBundle]] = {}
        for bundle in bundles:
            # Convert string component_type to ComponentType enum
            bundle_type = (
                ComponentType(bundle.component_type)
                if isinstance(bundle.component_type, str)
                else bundle.component_type
            )

            if bundle_type not in by_type:
                by_type[bundle_type] = []
            by_type[bundle_type].append(bundle)

        for component_type, type_bundles in by_type.items():
            sections.append(f"# === {component_type.value.replace('_', ' ').title()}s ===")
            sections.append("")

            for bundle in type_bundles:
                examples = bundle.load_examples()
                if examples:
                    # Use the first (typically "basic") example
                    first_example = next(iter(examples.values()))
                    sections.append(f"# {bundle.name}")
                    sections.append(first_example.strip())
                    sections.append("")

            sections.append("")

        return "\n".join(sections)

    def _generate_variables_tf(self) -> str:
        """Generate variables.tf for the showcase."""
        return """# Variables for the complete showcase example

variable "output_directory" {
  description = "Directory for generated files"
  type        = string
  default     = "/tmp"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "pyvider-showcase"
}
"""

    def _generate_outputs_tf(self, bundles: list[PlatingBundle]) -> str:
        """Generate outputs.tf showing key results."""
        outputs = []
        outputs.append("# Outputs from the complete showcase example")
        outputs.append("")
        outputs.append('output "showcase_summary" {')
        outputs.append('  description = "Summary of the complete showcase"')
        outputs.append("  value = {")
        outputs.append("    timestamp = timestamp()")
        outputs.append(f"    components_demonstrated = {len(bundles)}")
        outputs.append("    environment = var.environment")
        outputs.append("  }")
        outputs.append("}")

        return "\n".join(outputs)

    def _generate_example_readme(self, bundle: PlatingBundle, example_name: str, content: str) -> str:
        """Generate README for an individual example."""
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

    def _generate_combined_readme(self, bundle: PlatingBundle, examples: dict[str, str]) -> str:
        """Generate README for combined examples."""
        bundle_type = (
            ComponentType(bundle.component_type)
            if isinstance(bundle.component_type, str)
            else bundle.component_type
        )
        example_list = "\n".join(
            f"- **{name}**: {self._extract_first_line(content)}" for name, content in examples.items()
        )

        return f"""# {bundle_type.value.replace("_", " ").title()}: {bundle.name} - Complete Examples

This directory contains a comprehensive Terraform example demonstrating all capabilities of the `{bundle.name}` {bundle_type.value.replace("_", " ")}.

## Examples Included

{example_list}

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

- `main.tf` - Complete Terraform configuration with all examples
- `README.md` - This documentation

## Requirements

- Terraform >= 1.0
- {self.provider_name} provider >= {self.provider_version}

Generated by [Plating](https://github.com/provide-io/plating) - Terraform Provider Documentation Generator
"""

    def _generate_showcase_readme(self, bundles: list[PlatingBundle]) -> str:
        """Generate README for the complete showcase."""
        component_list = "\n".join(
            f"- {(ComponentType(bundle.component_type) if isinstance(bundle.component_type, str) else bundle.component_type).value.replace('_', ' ').title()}: `{bundle.name}`"
            for bundle in bundles
        )

        return f"""# {self.provider_name.title()} Provider - Complete Showcase

This directory contains a comprehensive Terraform example showcasing all components of the {self.provider_name} provider.

## Components Demonstrated

{component_list}

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

4. View outputs:
   ```bash
   terraform output
   ```

5. When you're done, clean up:
   ```bash
   terraform destroy
   ```

## Files

- `main.tf` - Complete Terraform configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `README.md` - This documentation

## Customization

You can customize this example by:

1. Modifying variables in `variables.tf`
2. Overriding defaults:
   ```bash
   terraform apply -var="app_name=my-app" -var="environment=production"
   ```

## Requirements

- Terraform >= 1.0
- {self.provider_name} provider >= {self.provider_version}

Generated by [Plating](https://github.com/provide-io/plating) - Terraform Provider Documentation Generator
"""

    def _extract_description_from_content(self, content: str) -> str:
        """Extract a description from the first comment in the content."""
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#") and not line.startswith("##"):
                return line[1:].strip()
        return "Demonstrates the basic usage of this component."

    def _extract_first_line(self, content: str) -> str:
        """Extract the first meaningful line from content."""
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                return line
            if line.startswith("#") and not line.startswith("##"):
                return line[1:].strip()
        return "Example usage"


# 🍲⚡📁🏗️
