# 
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from plating.config import get_config
from plating.config.defaults import (
    MATH_FUNCTIONS,
    STRING_MANIPULATION_FUNCTIONS,
    STRING_TRANSFORM_FUNCTIONS,
)

#
# plating/templating/metadata.py
#
"""Template metadata extraction utilities."""


class TemplateMetadataExtractor:
    """Extracts metadata from function implementations for template rendering."""

    def __init__(self) -> None:
        self.config = get_config()

    def extract_function_metadata(self, function_name: str, component_type: str) -> dict[str, Any]:
        """Extract metadata for a function to populate templates.

        Args:
            function_name: Name of the function
            component_type: Type of component (function, resource, etc.)

        Returns:
            Dictionary containing metadata for template rendering
        """
        return self._generate_function_metadata(function_name)

    def _generate_function_metadata(self, function_name: str) -> dict[str, Any]:
        """Generate realistic metadata based on function name patterns.

        Args:
            function_name: Name of the function

        Returns:
            Dictionary containing function metadata
        """
        # Analyze function name to generate appropriate metadata
        if function_name in STRING_TRANSFORM_FUNCTIONS:
            return self._generate_string_transform_metadata(function_name)
        elif function_name in MATH_FUNCTIONS:
            return self._generate_math_function_metadata(function_name)
        elif function_name in STRING_MANIPULATION_FUNCTIONS:
            return self._generate_string_manipulation_metadata(function_name)
        else:
            return self._generate_generic_metadata(function_name)

    def _generate_string_transform_metadata(self, function_name: str) -> dict[str, Any]:
        """Generate metadata for string transformation functions."""
        transform_descriptions = {
            "upper": ("Converts a string to uppercase", "HELLO WORLD"),
            "lower": ("Converts a string to lowercase", "hello world"),
            "title": ("Converts a string to title case", "Hello World"),
        }

        description, example_output = transform_descriptions.get(
            function_name, ("Transforms a string", "output")
        )

        return {
            "signature_markdown": f"`{function_name}(str)`",
            "arguments_markdown": "- `str`: The input string to transform",
            "has_variadic": False,
            "variadic_argument_markdown": "",
            "description": description,
            "examples": {
                "example": f'{function_name}("Hello World") # Returns: "{example_output}"',
                "basic": f'{function_name}("Hello World") # Returns: "{example_output}"',
            },
        }

    def _generate_math_function_metadata(self, function_name: str) -> dict[str, Any]:
        """Generate metadata for mathematical functions."""
        math_descriptions = {
            "add": ("Adds two numbers together", "5"),
            "subtract": ("Subtracts the second number from the first", "1"),
            "multiply": ("Multiplies two numbers", "6"),
            "divide": ("Divides the first number by the second", "1.5"),
            "min": ("Finds the minimum value in a list of numbers", "1"),
            "max": ("Finds the maximum value in a list of numbers", "5"),
            "sum": ("Calculates the sum of a list of numbers", "15"),
            "round": ("Rounds a number to a specified precision", "3.14"),
        }

        description, example_output = math_descriptions.get(
            function_name, ("Performs a mathematical operation", "result")
        )

        # Handle functions with special signatures
        if function_name in ["min", "max", "sum"]:
            signature = f"`{function_name}(numbers)`"
            args = "- `numbers`: A list of numbers to process"
            example = f"{function_name}([1, 3, 5, 2, 4]) # Returns: {example_output}"
        elif function_name == "round":
            signature = f"`{function_name}(number, precision)`"
            args = "- `number`: The number to round\n- `precision`: Number of decimal places (optional, default: 0)"
            example = f"{function_name}(3.14159, 2) # Returns: {example_output}"
        else:
            # Default two-argument functions (add, subtract, multiply, divide)
            signature = f"`{function_name}(a, b)`"
            args = "- `a`: The first number\n- `b`: The second number"
            example = f"{function_name}(3, 2) # Returns: {example_output}"

        return {
            "signature_markdown": signature,
            "arguments_markdown": args,
            "has_variadic": False,
            "variadic_argument_markdown": "",
            "description": description,
            "examples": {
                "example": example,
                "basic": example,
            },
        }

    def _generate_string_manipulation_metadata(self, function_name: str) -> dict[str, Any]:
        """Generate metadata for string manipulation functions."""
        manip_descriptions = {
            "join": ("Joins a list of strings with a separator", '"hello,world"'),
            "split": ("Splits a string by a delimiter", '["hello", "world"]'),
            "replace": ("Replaces occurrences of a substring", '"hello world"'),
        }

        description, example_output = manip_descriptions.get(function_name, ("Manipulates strings", "output"))

        if function_name == "join":
            signature = f"`{function_name}(separator, list)`"
            args = "- `separator`: The string to join with\n- `list`: List of strings to join"
            example = f'{function_name}(",", ["hello", "world"]) # Returns: {example_output}'
        elif function_name == "split":
            signature = f"`{function_name}(str, delimiter)`"
            args = "- `str`: The string to split\n- `delimiter`: The delimiter to split on"
            example = f'{function_name}("hello,world", ",") # Returns: {example_output}'
        else:  # replace
            signature = f"`{function_name}(str, old, new)`"
            args = (
                "- `str`: The input string\n- `old`: The substring to replace\n- `new`: The replacement string"
            )
            example = f'{function_name}("hello test", "test", "world") # Returns: {example_output}'

        return {
            "signature_markdown": signature,
            "arguments_markdown": args,
            "has_variadic": False,
            "variadic_argument_markdown": "",
            "description": description,
            "examples": {"example": example, "basic": example},
        }

    def _generate_generic_metadata(self, function_name: str) -> dict[str, Any]:
        """Generate generic metadata for unknown functions."""
        return {
            "signature_markdown": self.config.fallback_signature_format.format(function_name=function_name),
            "arguments_markdown": self.config.fallback_arguments_markdown,
            "has_variadic": False,
            "variadic_argument_markdown": "",
            "description": f"Processes input using {function_name} logic",
            "examples": {
                "example": f'{function_name}("input") # Returns: processed output',
                "basic": f'{function_name}("input") # Returns: processed output',
            },
        }

    def discover_template_files(self, docs_dir: Path) -> list[Path]:
        """Discover all template files in a docs directory.

        Args:
            docs_dir: Directory containing template files

        Returns:
            List of template file paths
        """
        if not docs_dir.exists():
            return []

        template_files = []
        for template_file in docs_dir.glob("*.tmpl.md"):
            template_files.append(template_file)

        return template_files

# 🍽️📖🔚
