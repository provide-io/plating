#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from typing import Any

#
# plating/schema/formatters.py
#
"""Schema formatting and conversion utilities."""


def _format_cty_type(type_info: Any) -> str | None:
    """Format CTY type objects to human-readable strings.

    Args:
        type_info: CTY type object

    Returns:
        Formatted type string or None if not a CTY type
    """
    try:
        from pyvider.cty import (
            CtyBool,
            CtyDynamic,
            CtyList,
            CtyMap,
            CtyNumber,
            CtyObject,
            CtySet,
            CtyString,
        )

        if not hasattr(type_info, "__class__"):
            return None

        type_class = type_info.__class__

        # Simple types
        type_map = {
            CtyString: "String",
            CtyNumber: "Number",
            CtyBool: "Boolean",
            CtyObject: "Object",
            CtyDynamic: "Dynamic",
        }

        if type_class in type_map:
            return type_map[type_class]

        # Container types with element types
        if type_class == CtyList:
            element_type = format_type_string(getattr(type_info, "element_type", None))
            return f"List of {element_type}"
        elif type_class == CtySet:
            element_type = format_type_string(getattr(type_info, "element_type", None))
            return f"Set of {element_type}"
        elif type_class == CtyMap:
            element_type = format_type_string(getattr(type_info, "element_type", None))
            return f"Map of {element_type}"

        return None

    except (ImportError, AttributeError):
        return None


def _format_string_type(type_str: str) -> str:
    """Format string type representations.

    Args:
        type_str: String representation of type

    Returns:
        Formatted type string
    """
    type_str = type_str.lower()

    # Check for specific type keywords
    if "string" in type_str:
        return "String"
    elif "number" in type_str or "int" in type_str or "float" in type_str:
        return "Number"
    elif "bool" in type_str:
        return "Boolean"
    elif "list" in type_str:
        return "List of String"
    elif "set" in type_str:
        return "Set of String"
    elif "map" in type_str:
        return "Map of String"
    elif "object" in type_str:
        return "Object"

    return "String"  # Default fallback


def format_type_string(type_info: Any) -> str:
    """Convert a type object to a human-readable type string.

    Args:
        type_info: Type information (CTY object, string, or dict)

    Returns:
        Human-readable type string
    """
    if not type_info:
        return "String"  # Default fallback

    # Try CTY type objects first
    cty_result = _format_cty_type(type_info)
    if cty_result:
        return cty_result

    # Handle string representations
    if isinstance(type_info, str):
        return _format_string_type(type_info)

    # Handle dict representations (from schema extraction)
    if isinstance(type_info, dict):
        if not type_info:
            return "String"  # Empty dict fallback

        if "type" in type_info:
            return format_type_string(type_info["type"])

    # Fallback for unknown types
    return "String"


def parse_schema_to_markdown(schema_dict: dict[str, Any]) -> str:
    """Convert a schema dictionary to markdown table format.

    Args:
        schema_dict: Schema dictionary with attributes and blocks

    Returns:
        Formatted markdown table
    """
    if not schema_dict:
        return "No arguments available."

    parts = []
    block = schema_dict.get("block", {})

    # Process attributes
    attributes = block.get("attributes", {})
    if attributes:
        parts.append(_format_attributes_table(attributes))

    # Process nested blocks
    block_types = block.get("block_types", {})
    if block_types:
        for block_name, block_schema in block_types.items():
            parts.append(f"\n### {block_name} Block\n")
            block_attrs = block_schema.get("block", {}).get("attributes", {})
            if block_attrs:
                parts.append(_format_attributes_table(block_attrs))

    return "\n".join(parts) if parts else "No arguments available."


def _format_attributes_table(attributes: dict[str, Any]) -> str:
    """Format attributes as a markdown table.

    Args:
        attributes: Dictionary of attribute definitions

    Returns:
        Markdown table string
    """
    if not attributes:
        return "No arguments available."

    lines = [
        "| Argument | Type | Required | Description |",
        "|----------|------|----------|-------------|",
    ]

    for attr_name, attr_def in attributes.items():
        type_str = _format_attribute_type(attr_def)
        required = _format_required_status(attr_def)
        description = attr_def.get("description", "No description available")
        lines.append(f"| `{attr_name}` | {type_str} | {required} | {description} |")

    return "\n".join(lines)


def _format_attribute_type(attr_def: dict[str, Any]) -> str:
    """Format attribute type from definition.

    Args:
        attr_def: Attribute definition dict

    Returns:
        Formatted type string
    """
    type_info = attr_def.get("type")
    return format_type_string(type_info)


def _format_required_status(attr_def: dict[str, Any]) -> str:
    """Format required status for an attribute.

    Args:
        attr_def: Attribute definition dict

    Returns:
        Required status string
    """
    if attr_def.get("required"):
        return "**Yes**"
    elif attr_def.get("computed"):
        return "No (Computed)"
    elif attr_def.get("optional"):
        return "No"

    return "No"


def parse_function_signature(func_schema: dict[str, Any]) -> str:
    """Parse function signature from schema.

    Args:
        func_schema: Function schema dictionary

    Returns:
        Formatted function signature string
    """
    if "signature" not in func_schema:
        return ""

    signature = func_schema["signature"]
    params = []

    # Handle parameters
    if "parameters" in signature:
        for param in signature["parameters"]:
            param_name = param.get("name", "arg")
            param_type = param.get("type", "any")
            params.append(f"{param_name}: {param_type}")

    # Handle variadic parameter
    if "variadic_parameter" in signature:
        variadic = signature["variadic_parameter"]
        variadic_name = variadic.get("name", "args")
        variadic_type = variadic.get("type", "any")
        params.append(f"...{variadic_name}: {variadic_type}")

    return_type = signature.get("return_type", "any")
    param_str = ", ".join(params)
    return f"function({param_str}) -> {return_type}"


def parse_function_arguments(func_schema: dict[str, Any]) -> str:
    """Parse function arguments from schema.

    Args:
        func_schema: Function schema dictionary

    Returns:
        Formatted arguments list
    """
    if "signature" not in func_schema:
        return ""

    signature = func_schema["signature"]
    lines = []

    # Handle parameters
    if "parameters" in signature:
        for param in signature["parameters"]:
            param_name = param.get("name", "arg")
            param_type = param.get("type", "any")
            description = param.get("description", "")
            lines.append(f"- `{param_name}` ({param_type}) - {description}")

    return "\n".join(lines)


def parse_variadic_argument(func_schema: dict[str, Any]) -> str:
    """Parse variadic argument from schema.

    Args:
        func_schema: Function schema dictionary

    Returns:
        Formatted variadic argument description
    """
    if "signature" not in func_schema:
        return ""

    signature = func_schema["signature"]
    if "variadic_parameter" not in signature:
        return ""

    variadic = signature["variadic_parameter"]
    variadic_name = variadic.get("name", "args")
    variadic_type = variadic.get("type", "any")
    description = variadic.get("description", "")

    return f"- `{variadic_name}` ({variadic_type}) - {description}"

# 🍽️📖🔚
