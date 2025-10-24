from __future__ import annotations

from typing import Any

#
# plating/schema/formatters.py
#
"""Schema formatting and conversion utilities."""


def format_type_string(type_info: Any) -> str:
    """Convert a type object to a human-readable type string."""
    if not type_info:
        return "String"  # Default fallback

    # Handle CTY type objects
    try:
        # Import here to avoid circular imports
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

        if hasattr(type_info, "__class__"):
            type_class = type_info.__class__
            if type_class == CtyString:
                return "String"
            elif type_class == CtyNumber:
                return "Number"
            elif type_class == CtyBool:
                return "Boolean"
            elif type_class == CtyList:
                element_type = format_type_string(getattr(type_info, "element_type", None))
                return f"List of {element_type}"
            elif type_class == CtySet:
                element_type = format_type_string(getattr(type_info, "element_type", None))
                return f"Set of {element_type}"
            elif type_class == CtyMap:
                element_type = format_type_string(getattr(type_info, "element_type", None))
                return f"Map of {element_type}"
            elif type_class == CtyObject:
                return "Object"
            elif type_class == CtyDynamic:
                return "Dynamic"
    except (ImportError, AttributeError):
        pass

    # Handle string representations
    if isinstance(type_info, str):
        type_str = type_info.lower()
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

    # Handle dict representations (from schema extraction)
    if isinstance(type_info, dict):
        # Check if it's an empty dict (common case we saw)
        if not type_info:
            return "String"  # Default fallback

        # Try to infer from dict structure
        if "type" in type_info:
            return format_type_string(type_info["type"])

    # Final fallback
    return "String"


def parse_schema_to_markdown(schema: dict[str, Any]) -> str:
    """Parse a schema object into markdown documentation."""
    if not schema:
        return ""

    # Extract block information
    block = schema.get("block", {})
    if not block:
        return ""

    markdown_lines = []

    # Handle attributes
    attributes = block.get("attributes", {})
    if attributes:
        markdown_lines.append("## Arguments\n")
        for attr_name, attr_spec in attributes.items():
            description = attr_spec.get("description", "")
            attr_type_raw = attr_spec.get("type", {})
            attr_type = format_type_string(attr_type_raw)
            required = attr_spec.get("required", False)
            optional = attr_spec.get("optional", False)
            computed = attr_spec.get("computed", False)

            # Determine characteristics
            characteristics = []
            if required:
                characteristics.append("Required")
            elif optional:
                characteristics.append("Optional")
            elif computed:
                characteristics.append("Computed")

            # Format like tfplugindocs: (Type, Characteristics)
            type_text = f"({attr_type}, {', '.join(characteristics)})" if characteristics else f"({attr_type})"

            markdown_lines.append(f"- `{attr_name}` {type_text} {description}".strip())

        markdown_lines.append("")

    # Handle nested blocks
    nested_blocks = block.get("block_types", {})
    if nested_blocks and isinstance(nested_blocks, dict):
        markdown_lines.append("## Blocks\n")
        for block_name, block_spec in nested_blocks.items():
            description = block_spec.get("description", "")

            markdown_lines.append(f"### {block_name}")
            if description:
                markdown_lines.append(f"\n{description}\n")

            # Handle block attributes
            block_attrs = block_spec.get("block", {}).get("attributes", {})
            if block_attrs:
                for attr_name, attr_spec in block_attrs.items():
                    attr_description = attr_spec.get("description", "")
                    attr_type = attr_spec.get("type", "unknown")
                    required = attr_spec.get("required", False)
                    optional = attr_spec.get("optional", False)
                    computed = attr_spec.get("computed", False)

                    if required:
                        req_text = " (Required)"
                    elif optional:
                        req_text = " (Optional)"
                    elif computed:
                        req_text = " (Computed)"
                    else:
                        req_text = ""

                    markdown_lines.append(f"- `{attr_name}` ({attr_type}){req_text} - {attr_description}")

            markdown_lines.append("")

    return "\n".join(markdown_lines)


def parse_function_signature(func_schema: dict[str, Any]) -> str:
    """Parse function signature from schema."""
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

    # Handle return type
    return_type = signature.get("return_type", "any")

    param_str = ", ".join(params)
    return f"function({param_str}) -> {return_type}"


def parse_function_arguments(func_schema: dict[str, Any]) -> str:
    """Parse function arguments from schema."""
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
    """Parse variadic argument from schema."""
    if "signature" not in func_schema or "variadic_parameter" not in func_schema["signature"]:
        return ""

    variadic = func_schema["signature"]["variadic_parameter"]
    variadic_name = variadic.get("name", "args")
    variadic_type = variadic.get("type", "any")
    description = variadic.get("description", "")

    return f"- `{variadic_name}` ({variadic_type}) - {description}"
