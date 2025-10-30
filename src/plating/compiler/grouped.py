#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Grouped (cross-component) example compilation."""

from __future__ import annotations

from pathlib import Path

from attrs import define, field
from provide.foundation import logger

from plating.bundles import PlatingBundle

#
# Type definitions
#


@define
class ExampleGroup:
    """Represents a grouped example spanning multiple components."""

    name: str
    components: dict[str, str] = field(factory=dict)  # {component_name: tf_content}
    fixtures: dict[str, Path] = field(factory=dict)  # {rel_path: source_path}
    component_types: set[str] = field(factory=set)


#
# Grouped example compiler
#


class GroupedExampleCompiler:
    """Compiles grouped (cross-component) examples from plating bundles."""

    def __init__(self, provider_name: str, provider_version: str = "0.0.5") -> None:
        """Initialize the grouped example compiler.

        Args:
            provider_name: Name of the Terraform provider
            provider_version: Version of the provider
        """
        self.provider_name = provider_name
        self.provider_version = provider_version

    def discover_groups(self, bundles: list[PlatingBundle]) -> dict[str, ExampleGroup]:
        """Discover all example groups across bundles.

        Args:
            bundles: List of plating bundles to discover groups from

        Returns:
            Dictionary mapping group name to ExampleGroup
        """
        groups: dict[str, ExampleGroup] = {}

        for bundle in bundles:
            for group_name in self._get_group_names(bundle):
                if group_name not in groups:
                    groups[group_name] = ExampleGroup(name=group_name)

                # Load TF content
                tf_content = self._load_group_tf(bundle, group_name)
                if tf_content:
                    # Check if component name already exists
                    if bundle.name in groups[group_name].components:
                        raise ValueError(
                            f"\nError: Filename collision in grouped example '{group_name}'\n\n"
                            f"  Multiple components with the name '{bundle.name}' detected.\n"
                            f"  This will result in '{bundle.name}.tf' being overwritten.\n\n"
                            f"  Please rename one of the components or use different example groups."
                        )

                    groups[group_name].components[bundle.name] = tf_content
                    groups[group_name].component_types.add(bundle.component_type)

                # Load fixtures
                fixtures = self._load_group_fixtures(bundle, group_name)

                # Check for fixture collisions
                for fixture_path in fixtures.keys():
                    if fixture_path in groups[group_name].fixtures:
                        # Collision detected
                        raise ValueError(
                            f"\nError: Fixture collision in grouped example '{group_name}'\n\n"
                            f"  The following fixture file appears in multiple components:\n"
                            f"    - fixtures/{fixture_path}\n\n"
                            f"  Components with this fixture:\n"
                            f"    - {bundle.name}\n"
                            f"    - (another component)\n\n"
                            f"  Please rename the fixture files to avoid conflicts."
                        )

                groups[group_name].fixtures.update(fixtures)

        return groups

    def compile_groups(self, groups: dict[str, ExampleGroup], output_dir: Path) -> int:
        """Compile all example groups to output directory.

        Args:
            groups: Dictionary of example groups to compile
            output_dir: Output directory for grouped examples (e.g., "examples/integration")

        Returns:
            Number of groups compiled
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for group in groups.values():
            group_dir = output_dir / group.name
            group_dir.mkdir(parents=True, exist_ok=True)

            # Generate provider.tf
            self._generate_provider_tf(group_dir)

            # Write each component's TF file
            for component_name, tf_content in group.components.items():
                tf_path = group_dir / f"{component_name}.tf"
                tf_path.write_text(tf_content, encoding="utf-8")

            # Copy fixtures
            if group.fixtures:
                fixtures_dir = group_dir / "fixtures"
                fixtures_dir.mkdir(exist_ok=True)
                for rel_path, source_path in group.fixtures.items():
                    dest = fixtures_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(source_path.read_bytes())

            # Generate README.md
            self._generate_readme(group_dir, group)

            logger.info(f"Compiled grouped example '{group.name}' with {len(group.components)} components")
            count += 1

        return count

    def _get_group_names(self, bundle: PlatingBundle) -> list[str]:
        """Get names of example groups in bundle (subdirectory names).

        Args:
            bundle: Plating bundle to inspect

        Returns:
            List of group names (subdirectory names with main.tf)
        """
        if not bundle.examples_dir.exists():
            return []

        group_names = []
        for item in bundle.examples_dir.iterdir():
            if item.is_dir() and (item / "main.tf").exists():
                group_names.append(item.name)

        return group_names

    def _load_group_tf(self, bundle: PlatingBundle, group_name: str) -> str:
        """Load main.tf from group directory.

        Args:
            bundle: Plating bundle
            group_name: Name of the example group

        Returns:
            Content of main.tf file, or empty string if not found
        """
        tf_file = bundle.examples_dir / group_name / "main.tf"
        if tf_file.exists():
            try:
                return tf_file.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to read {tf_file}: {e}")
                return ""
        return ""

    def _load_group_fixtures(self, bundle: PlatingBundle, group_name: str) -> dict[str, Path]:
        """Load fixtures from group/fixtures/ directory.

        Args:
            bundle: Plating bundle
            group_name: Name of the example group

        Returns:
            Dictionary mapping relative path to source path
        """
        fixtures_dir = bundle.examples_dir / group_name / "fixtures"
        if not fixtures_dir.exists():
            return {}

        fixtures = {}
        for file_path in fixtures_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(fixtures_dir)
                fixtures[str(rel_path)] = file_path

        return fixtures

    def _generate_provider_tf(self, output_dir: Path) -> None:
        """Generate provider.tf file for grouped example.

        Args:
            output_dir: Directory to write provider.tf to
        """
        provider_tf_content = f"""terraform {{
  required_version = ">= 0.12"

  required_providers {{
    {self.provider_name} = {{
      source = "hashicorp/{self.provider_name}"
      version = "{self.provider_version}"
    }}
  }}
}}

provider "{self.provider_name}" {{
  # Configure provider settings here
}}
"""
        provider_tf_path = output_dir / "provider.tf"
        provider_tf_path.write_text(provider_tf_content, encoding="utf-8")

    def _generate_readme(self, output_dir: Path, group: ExampleGroup) -> None:
        """Generate README.md for grouped example.

        Args:
            output_dir: Directory to write README to
            group: The example group being compiled
        """
        # Create a human-readable title from the group name
        title = group.name.replace("_", " ").title()

        readme_content = f"""# {title} Example

This is a grouped example demonstrating how to use multiple {self.provider_name} components together.

## Components Included

{chr(10).join(f"- {name}" for name in sorted(group.components.keys()))}

## Usage

To use this example:

```bash
# Initialize Terraform
terraform init

# Review the planned changes
terraform plan

# Apply the configuration
terraform apply
```

## Clean Up

To remove the resources created by this example:

```bash
terraform destroy
```

## Notes

- This example demonstrates best practices for using multiple components together
- Modify the configuration files as needed for your use case
- Ensure you have the required providers configured
"""
        readme_path = output_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")


# 🍽️📖🔚
