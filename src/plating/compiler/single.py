#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Single-component example compilation."""

from __future__ import annotations

from pathlib import Path
import re

from attrs import define, field
from provide.foundation import logger

from plating.bundles import PlatingBundle
from plating.bundles.base import EXAMPLE_METADATA_SUFFIX
from plating.core.doc_generator import _bundle_component_names, _extract_component_metadata
from plating.types import ComponentType


@define
class SingleCompilationResult:
    """Result of single-component example compilation."""

    examples_generated: int = field(default=0)
    output_files: list[Path] = field(factory=list)
    errors: list[str] = field(factory=list)


class SingleExampleCompiler:
    """Compiles single-component executable Terraform examples."""

    def __init__(
        self,
        provider_name: str,
        provider_version: str = "0.0.5",
        provider_attributes: set[str] | None = None,
    ) -> None:
        """Initialize the single example compiler.

        Args:
            provider_name: Name of the Terraform provider
            provider_version: Version of the provider
            provider_attributes: Names the provider's configuration block
                accepts, when the caller knows them. An argument is written
                into `provider.tf` only if it appears here, because Terraform
                refuses the whole configuration over one it does not recognise.
                None means "not known", and nothing beyond the required
                boilerplate is emitted.
        """
        self.provider_name = provider_name
        self.provider_version = provider_version
        self.provider_attributes = provider_attributes

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
            component_name = component_name[len(self.provider_name) + 1 :]

        component_dir = type_dir / component_name
        component_dir.mkdir(parents=True, exist_ok=True)

        # Load only flat examples (not grouped ones)
        flat_examples = self._load_flat_examples(bundle)
        if not flat_examples:
            return

        # Generate provider.tf once for this component directory
        component_type = (
            ComponentType(bundle.component_type)
            if isinstance(bundle.component_type, str)
            else bundle.component_type
        )
        is_test_only = self._is_test_only_component(bundle, component_type)
        self._generate_provider_tf(component_dir, is_test_only)

        # Generate flat files in the component directory
        for example_name, example_content in flat_examples.items():
            # Strip any provider blocks from the example content
            cleaned_content = self._strip_provider_blocks(example_content)

            # A list resource's query blocks are only valid in a .tfquery.hcl
            # file; writing them as .tf makes the directory fail to parse.
            suffix = ".tfquery.hcl" if re.search(r'\blist\s+"', cleaned_content) else ".tf"
            tf_path = component_dir / f"{example_name}{suffix}"
            tf_path.write_text(cleaned_content, encoding="utf-8")
            result.output_files.append(tf_path)
            result.examples_generated += 1

            # Carry the requirements sidecar next to the example it describes.
            # Whatever runs these directories -- `soup stir`, CI -- sees only this
            # generated tree, never the .plating bundle, so metadata left behind
            # here would be metadata nothing can act on.
            sidecar = bundle.examples_dir / f"{example_name}{EXAMPLE_METADATA_SUFFIX}"
            if sidecar.exists():
                meta_path = component_dir / f"{example_name}{EXAMPLE_METADATA_SUFFIX}"
                # Copied verbatim rather than re-serialised: these sidecars carry
                # comments explaining *why* a requirement exists, and a parse/dump
                # round-trip would silently drop every one of them.
                meta_path.write_bytes(sidecar.read_bytes())
                result.output_files.append(meta_path)

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

        # A list resource's example is a query file, not a configuration, so
        # globbing "*.tf" alone found nothing for those bundles at all.
        candidates = sorted(bundle.examples_dir.glob("*.tf")) + sorted(
            bundle.examples_dir.glob("*.tfquery.hcl")
        )

        # The bundle is named after its directory, which is frequently not the
        # component's name -- `filesystem_store.plating` documents `pyvider_fs`.
        # Match against every name the bundle could be documenting.
        names = _bundle_component_names(bundle, self.provider_name)

        for example_file in candidates:
            try:
                content = example_file.read_text(encoding="utf-8")
            except Exception:
                continue

            if any(self._example_references_component(content, name) for name in names):
                # ".tfquery.hcl" is two suffixes, so `.stem` leaves ".tfquery".
                stem = example_file.name.removesuffix(".tfquery.hcl").removesuffix(".tf")
                flat_examples[stem] = content

        return flat_examples

    def _example_references_component(self, content: str, component_name: str) -> bool:
        """Check if an example file references a specific component.

        Args:
            content: Example file content
            component_name: Component name to search for

        Returns:
            True if the example references this component
        """
        import re

        # Every block keyword that introduces a component by type name. The
        # first two are all this used to know, so an action, an ephemeral
        # resource, a list resource and a state store each looked like an
        # example referencing nothing -- their directories were created and
        # left empty, and `soup stir` counted them as passing because there was
        # nothing in them to apply.
        keywords = "resource|data|action|ephemeral|list|state_store"
        block_pattern = rf'\b({keywords})\s+"{re.escape(component_name)}"'
        if re.search(block_pattern, content):
            return True

        # Match function calls: provider::function_name()
        function_pattern = rf"{re.escape(self.provider_name)}::{re.escape(component_name)}\s*\("
        return bool(re.search(function_pattern, content))

    def _is_test_only_component(self, bundle: PlatingBundle, component_type: ComponentType) -> bool:
        """Check if a component is marked as test_only.

        Args:
            bundle: Plating bundle
            component_type: Component type

        Returns:
            True if component is test_only, False otherwise
        """
        try:
            is_test_only = _extract_component_metadata(bundle, component_type, self.provider_name)
            return is_test_only
        except Exception:
            return False

    def _generate_provider_tf(self, component_dir: Path, is_test_only: bool = False) -> None:
        """Generate provider.tf file for a component directory.

        Args:
            component_dir: Directory for the component
            is_test_only: Whether this component requires test mode
        """
        # A test-only component needs the provider to publish it, and the
        # provider decides that from its environment before any configuration
        # is read -- `PYVIDER_TESTMODE=true` in the process environment, which
        # is how the conformance suite does it. Saying so in a comment is the
        # whole of what this file can usefully do about it.
        #
        # It used to write `provider_testmode = true` into the block instead.
        # No provider published an attribute by that name, so Terraform refused
        # the configuration outright -- "Unsupported argument" -- and the five
        # examples that got it had never once run. An argument is emitted now
        # only when the caller has told us the provider accepts it.
        provider_config = ""
        if is_test_only:
            attribute = f"{self.provider_name}_testmode"
            if self.provider_attributes is not None and attribute in self.provider_attributes:
                provider_config = f"  {attribute} = true\n"
            else:
                provider_config = (
                    "  # This component is registered `test_only`. Start the\n"
                    "  # provider with PYVIDER_TESTMODE=true in its environment,\n"
                    "  # or it will not publish the component at all.\n"
                )

        provider_content = f"""terraform {{
  required_providers {{
    {self.provider_name} = {{
      source  = "local/providers/{self.provider_name}"
      version = ">= {self.provider_version}"
    }}
  }}
}}

provider "{self.provider_name}" {{
{provider_config}  # Add your configuration options here
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

        # A state store is configured inside `terraform { state_store "..." {} }`,
        # so a rule that removes terraform blocks would remove the example
        # itself. The generated provider.tf carries the required_providers
        # block; anything else in a terraform block here is the example.
        if not re.search(r'\bstate_store\s+"', content):
            content = re.sub(
                r"terraform\s*\{[^}]*required_providers\s*\{[^}]*\}[^}]*\}\s*\n*",
                "",
                content,
                flags=re.DOTALL,
            )

            # Remove provider block. Skipped for a state store for the same
            # reason: its `provider "pyvider" {}` sits inside the state_store
            # block and names which provider serves it.
            content = re.sub(r'provider\s+"[^"]*"\s*\{[^}]*\}\s*\n*', "", content, flags=re.DOTALL)

        # Remove "Generated by Plating" comment if present
        content = re.sub(r"#\s*Generated by Plating[^\n]*\n*", "", content)

        # Clean up multiple blank lines
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip() + "\n"

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


# 🍽️📖🔚
