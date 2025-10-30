#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from pathlib import Path

from attrs import define, field
from provide.foundation import logger

from plating.bundles import PlatingBundle
from plating.compiler import GroupedExampleCompiler, SingleExampleCompiler
from plating.types import ComponentType

#
# plating/example_compiler.py
#
"""Executable example compilation for Terraform provider documentation."""


@define
class CompilationResult:
    """Result of example compilation process."""

    examples_generated: int = field(default=0)
    grouped_examples_generated: int = field(default=0)
    output_files: list[Path] = field(factory=list)
    errors: list[str] = field(factory=list)


class ExampleCompiler:
    """Orchestrates compilation of both single-component and grouped examples."""

    def __init__(
        self,
        provider_name: str,
        provider_version: str = "0.0.5",
    ) -> None:
        """Initialize the example compiler.

        Args:
            provider_name: Name of the Terraform provider
            provider_version: Version of the provider
        """
        self.provider_name = provider_name
        self.provider_version = provider_version

        # Initialize both compilers
        self.single_compiler = SingleExampleCompiler(provider_name, provider_version)
        self.grouped_compiler = GroupedExampleCompiler(provider_name, provider_version)

    def compile_examples(
        self,
        bundles: list[PlatingBundle],
        output_dir: Path,
        component_types: list[ComponentType] | None = None,
        grouped_output_dir: Path | None = None,
    ) -> CompilationResult:
        """Compile both single-component and grouped examples.

        Args:
            bundles: List of plating bundles to compile examples from
            output_dir: Base directory for single-component examples (e.g., "examples")
            component_types: Filter to specific component types
            grouped_output_dir: Directory for grouped examples (e.g., "examples/integration")
                               If None, uses output_dir / "integration"

        Returns:
            CompilationResult with generated files and statistics
        """
        result = CompilationResult()

        # Compile single-component examples
        try:
            single_result = self.single_compiler.compile_examples(bundles, output_dir, component_types)
            result.examples_generated = single_result.examples_generated
            result.output_files.extend(single_result.output_files)
            result.errors.extend(single_result.errors)
        except Exception as e:
            error_msg = f"Failed to compile single-component examples: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)

        # Compile grouped (cross-component) examples
        try:
            groups = self.grouped_compiler.discover_groups(bundles)
            if groups:
                # Use provided grouped_output_dir or default to output_dir/integration
                final_grouped_dir = grouped_output_dir if grouped_output_dir else output_dir / "integration"
                grouped_count = self.grouped_compiler.compile_groups(groups, final_grouped_dir)
                result.grouped_examples_generated = grouped_count
        except ValueError as e:
            # Collision errors should be surfaced to the user
            error_msg = str(e)
            result.errors.append(error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Failed to compile grouped examples: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)

        total_examples = result.examples_generated + result.grouped_examples_generated
        logger.info(
            f"Generated {result.examples_generated} single-component and "
            f"{result.grouped_examples_generated} grouped examples (total: {total_examples})"
        )

        return result


# 🍲⚡📁🏗️

# 🍽️📖🔚
