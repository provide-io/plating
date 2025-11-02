# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Example generation helpers for CLI commands."""

from pathlib import Path

from provide.foundation import perr, pout

from plating.plating import Plating
from plating.types import ComponentType


def generate_examples_if_requested(
    api: Plating,
    generate_examples: bool,
    provider_name: str | None,
    examples_dir: Path,
    types: list[ComponentType] | None,
    grouped_examples_dir: Path,
) -> None:
    """Generate executable examples if requested.

    Args:
        api: Plating API instance
        generate_examples: Whether to generate examples
        provider_name: Provider name for examples
        examples_dir: Directory for single-component examples
        types: Component types to process
        grouped_examples_dir: Directory for grouped examples
    """
    if not generate_examples:
        return

    from plating.example_compiler import ExampleCompiler

    # Get all bundles with examples
    bundles_with_examples = []
    for component_type_enum in types or list(ComponentType):
        bundles = api.registry.get_components_with_templates(component_type_enum)
        bundles_with_examples.extend([b for b in bundles if b.has_examples()])

    if not bundles_with_examples:
        pout("ℹ️  No components with examples found")
        return

    compiler = ExampleCompiler(
        provider_name=provider_name or "pyvider",
        provider_version="0.0.5",
    )

    compilation_result = compiler.compile_examples(
        bundles_with_examples, examples_dir, types, grouped_examples_dir
    )

    total_examples = compilation_result.examples_generated + compilation_result.grouped_examples_generated

    if total_examples > 0:
        pout(f"and {compilation_result.grouped_examples_generated} grouped examples (total: {total_examples})")
        pout("📂 Example files:")
        for example_file in compilation_result.output_files[:5]:  # Show first 5
            pout(f"  • {example_file}")
        if len(compilation_result.output_files) > 5:
            pout(f"  ... and {len(compilation_result.output_files) - 5} more")
    else:
        pout("ℹ️  No examples found to compile")

    if compilation_result.errors:
        perr("⚠️ Some example compilation errors:")
        for error in compilation_result.errors:
            perr(f"  • {error}")
