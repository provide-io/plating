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

    def _generate_provider_tf(self, group_dir: Path) -> None:
        """Generate provider.tf file.

        Args:
            group_dir: Directory for the example group
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
        provider_path = group_dir / "provider.tf"
        provider_path.write_text(provider_content, encoding="utf-8")

    def _generate_readme(self, group: ExampleGroup, group_dir: Path) -> None:
        """Generate README for example group.

        Args:
            group: Example group
            group_dir: Directory for the example group
        """
        # Format group name for display
        group_title = group.name.replace("_", " ").title()

        # List components
        component_items = []
        for component_name, component_type in [(name, "resource") for name in sorted(group.components.keys())]:
            component_items.append(f"- `{component_name}` ({component_type})")
        components_list = "\n".join(component_items)

        # List files
        file_items = ["- `provider.tf` - Provider configuration"]
        for component_name in sorted(group.components.keys()):
            file_items.append(f"- `{component_name}.tf` - Component configuration")
        if group.fixtures:
            file_items.append(f"- `fixtures/` - Supporting files ({len(group.fixtures)} files)")
        files_list = "\n".join(file_items)

        readme_content = f"""# {group_title} Example

This grouped example demonstrates multiple components working together.

## Components

{components_list}

## Files

{files_list}

## Usage

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

## Requirements

- Terraform >= 1.0
- {self.provider_name} provider >= {self.provider_version}

---
*Generated by [Plating](https://github.com/provide-io/plating) - Terraform Provider Documentation Generator*
"""
        readme_path = group_dir / "README.md"
        readme_path.write_text(readme_content, encoding="utf-8")


# 🍲🔗📦🏗️

# 🍽️📖🔚
