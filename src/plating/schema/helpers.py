#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Schema extraction and processing helpers."""

from __future__ import annotations

import inspect
from typing import Any

from provide.foundation import logger

from plating.bundles import PlatingBundle
from plating.types import ComponentType, SchemaInfo

#
# plating/schema/helpers.py
#


def extract_provider_schema(package_name: str) -> dict[str, Any]:
    """Extract provider schema using foundation hub discovery."""
    logger.info("Extracting provider schema via component discovery...")

    # Import here to avoid circular dependencies
    from provide.foundation.hub import Hub

    hub = Hub()

    try:
        # Use foundation's discovery with pyvider components entry point
        hub.discover_components(package_name)
    except Exception as e:
        logger.warning(f"Component discovery failed: {e}")
        return {}

    # Get components by dimension from foundation registry
    provider_schema = {
        "resource_schemas": get_component_schemas_from_hub(hub, "resource"),
        "data_source_schemas": get_component_schemas_from_hub(hub, "data_source"),
        "functions": get_function_schemas_from_hub(hub, "function"),
    }

    return provider_schema


def get_component_schemas_from_hub(hub: Any, dimension: str) -> dict[str, Any]:
    """Get component schemas from foundation hub by dimension."""
    schemas = {}
    try:
        names = hub.list_components(dimension=dimension)
        for name in names:
            component = hub.get_component(name, dimension=dimension)
            if component and hasattr(component, "get_schema"):
                try:
                    schema = component.get_schema()
                    # Convert PvsSchema to dict format for templates
                    schema_dict = convert_pvs_schema_to_dict(schema)
                    # Extract test_only metadata from component class
                    test_only = getattr(component, "_is_test_only", False)
                    schema_dict["test_only"] = test_only
                    # Extract component_of metadata (parent capability)
                    component_of = getattr(component, "_parent_capability", None)
                    schema_dict["component_of"] = component_of
                    schemas[name] = schema_dict
                except Exception as e:
                    logger.warning(f"Failed to get schema for {dimension} {name}: {e}")
    except Exception as e:
        logger.warning(f"Failed to get {dimension} components: {e}")
    return schemas


def get_function_schemas_from_hub(hub: Any, dimension: str) -> dict[str, Any]:
    """Get function schemas from foundation hub."""
    schemas = {}
    try:
        names = hub.list_components(dimension=dimension)
        for name in names:
            func = hub.get_component(name, dimension=dimension)
            if func:
                # For functions, we'll extract signature info from the callable
                try:
                    sig = inspect.signature(func)
                    schema_dict = {
                        "signature": {
                            "parameters": [
                                {
                                    "name": param.name,
                                    "type": str(param.annotation)
                                    if param.annotation != param.empty
                                    else "any",
                                    "description": f"Parameter {param.name}",
                                }
                                for param in sig.parameters.values()
                            ],
                            "return_type": str(sig.return_annotation)
                            if sig.return_annotation != sig.empty
                            else "any",
                        },
                        "description": func.__doc__ or f"Function {name}",
                    }
                    # Extract test_only metadata from function
                    test_only = getattr(func, "_is_test_only", False)
                    schema_dict["test_only"] = test_only
                    # Extract component_of metadata (parent capability)
                    component_of = getattr(func, "_parent_capability", None)
                    schema_dict["component_of"] = component_of
                    schemas[name] = schema_dict
                except Exception as e:
                    logger.warning(f"Failed to get schema for function {name}: {e}")
    except Exception as e:
        logger.warning(f"Failed to get function components: {e}")
    return schemas


def convert_pvs_schema_to_dict(pvs_schema: Any) -> dict[str, Any]:
    """Convert PvsSchema object to dictionary format for templates."""
    try:
        # Import here to avoid circular dependencies
        import attrs

        if attrs.has(type(pvs_schema)):
            schema_dict = attrs.asdict(pvs_schema)
        else:
            # Fallback: try to access schema attributes directly
            schema_dict = {
                "block": {
                    "attributes": getattr(pvs_schema, "attributes", {}),
                    "block_types": getattr(pvs_schema, "block_types", {}),
                },
                "description": getattr(pvs_schema, "description", ""),
            }
    except Exception as e:
        logger.warning(f"Failed to convert PvsSchema to dict: {e}")
        schema_dict = {"block": {"attributes": {}}}

    return schema_dict


def get_component_schema(
    component: PlatingBundle, component_type: ComponentType, provider_schema: dict[str, Any]
) -> SchemaInfo | None:
    """Extract component schema and convert to SchemaInfo."""
    if not provider_schema:
        return None

    schemas = provider_schema.get(f"{component_type.value}_schemas", {})
    if not schemas:
        return None

    # Try to find schema by component name (with and without pyvider_ prefix)
    component_schema = None
    for name, schema in schemas.items():
        if name == component.name or name == f"pyvider_{component.name}":
            component_schema = schema
            break

    if not component_schema:
        return None

    # Convert to SchemaInfo for template rendering
    return SchemaInfo.from_dict(component_schema)


# 🍽️📖🔚
