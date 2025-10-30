#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from typing import Any

from plating.config import get_config

#
# plating/generation/adorner.py
#
"""Documentation content enhancement and template variable population."""


class DocumentationAdorner:
    """Enhances documentation content with metadata and template variables."""

    def __init__(self) -> None:
        self.config = get_config()

    def adorn_function_template(
        self, template_content: str, function_name: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Create template context for function documentation.

        Args:
            template_content: Raw template content
            function_name: Name of the function
            metadata: Function metadata from extractor

        Returns:
            Dictionary containing all template variables
        """

        # Create example function that templates can call
        def example(example_name: str) -> str:
            examples = metadata.get("examples", {})
            result = examples.get(example_name, self.config.example_placeholder)
            return str(result)

        return {
            "function_name": function_name,
            "template_content": template_content,
            "example": example,
            **metadata,
        }

    def adorn_resource_template(
        self, template_content: str, resource_name: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Create template context for resource documentation.

        Args:
            template_content: Raw template content
            resource_name: Name of the resource
            metadata: Resource metadata

        Returns:
            Dictionary containing all template variables
        """

        # Create example function that templates can call
        def example(example_name: str) -> str:
            examples = metadata.get("examples", {})
            result = examples.get(example_name, self.config.example_placeholder)
            return str(result)

        # Create schema function that templates can call
        def schema() -> str:
            schema_info = metadata.get("schema", {})
            if not schema_info:
                return "No schema information available."
            # Convert schema to markdown format
            return str(schema_info)

        return {
            "resource_name": resource_name,
            "template_content": template_content,
            "example": example,
            "schema": schema,
            **metadata,
        }

    def enhance_template_context(
        self, context: dict[str, Any], additional_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Enhance template context with additional metadata.

        Args:
            context: Base template context
            additional_data: Additional data to merge

        Returns:
            Enhanced template context
        """
        enhanced = context.copy()
        enhanced.update(additional_data)
        return enhanced

# 🍽️📖🔚
