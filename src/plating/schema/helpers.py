#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Schema extraction and processing helpers."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import inspect
from typing import Any

from provide.foundation import logger

from plating.bundles import PlatingBundle
from plating.types import ComponentType, SchemaInfo

#
# plating/schema/helpers.py
#


def _run_blocking(coro: Any) -> Any:
    """Run a coroutine to completion from sync code, loop or no loop.

    Component discovery is async but schema extraction is called from both
    sync CLI paths and from inside an already-running loop. asyncio.run() would
    raise in the latter, so fall back to a private loop on a worker thread.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def discover_components_by_dimension(package_name: str) -> dict[str, dict[str, Any]]:
    """Discover a provider's components, grouped by registry dimension.

    Prefers pyvider's own discovery, which walks the package and registers
    every component type -- including the tfprotov6.11 additions -- under its
    own dimension. Falls back to foundation's entry-point discovery for
    providers that are not pyvider-based.
    """
    try:
        from pyvider.hub.components import ComponentRegistry
        from pyvider.hub.discovery import ComponentDiscovery
    except ImportError:
        logger.debug("pyvider hub unavailable, falling back to entry-point discovery")
        return _discover_via_entry_points(package_name)

    registry = ComponentRegistry()
    try:
        _run_blocking(ComponentDiscovery(registry).discover_all(strict=False))
    except Exception as e:
        logger.warning(f"Component discovery failed: {e}")
        return _discover_via_entry_points(package_name)

    components = registry.list_components()
    if not components:
        return _discover_via_entry_points(package_name)
    return components


def _discover_via_entry_points(package_name: str) -> dict[str, dict[str, Any]]:
    """Discover components through foundation's entry-point hub."""
    from provide.foundation.hub import Hub

    hub = Hub()
    try:
        hub.discover_components(package_name)
    except Exception as e:
        logger.warning(f"Entry-point discovery failed: {e}")
        return {}

    discovered: dict[str, dict[str, Any]] = {}
    for component_type in ComponentType:
        dimension = component_type.value
        try:
            names = hub.list_components(dimension=dimension) or []
        except Exception:
            continue
        found = {name: hub.get_component(name, dimension=dimension) for name in names}
        if found:
            discovered[dimension] = found
    return discovered


def extract_provider_schema(package_name: str) -> dict[str, Any]:
    """Extract provider schema for every documentable component type.

    Keys are derived as f"{component_type.value}_schemas", which is the same
    form get_component_schema() looks up, so a new component type needs no
    change here beyond being listed in ComponentType.documentable().
    """
    logger.info("Extracting provider schema via component discovery...")

    discovered = discover_components_by_dimension(package_name)
    if not discovered:
        logger.warning("No components discovered; provider schema will be empty")
        return {}

    provider_schema: dict[str, Any] = {}
    for component_type in ComponentType.documentable():
        components = discovered.get(component_type.value, {})
        if component_type.is_schema_backed:
            provider_schema[f"{component_type.value}_schemas"] = extract_component_schemas(components)
        else:
            provider_schema[f"{component_type.value}_schemas"] = extract_function_schemas(components)

    # Functions are also published under their historical key, which templates
    # and the provider index still read.
    provider_schema["functions"] = provider_schema.get(
        f"{ComponentType.FUNCTION.value}_schemas",
        {},
    )

    counts = {key: len(value) for key, value in provider_schema.items() if value}
    logger.info("Provider schema extracted", **counts)
    return provider_schema


def extract_component_schemas(components: dict[str, Any]) -> dict[str, Any]:
    """Build schema dicts for already-discovered components.

    Works for every schema-backed component type: resources, data sources,
    ephemeral resources, list resources, state stores and actions all expose
    the same get_schema() contract.
    """
    schemas: dict[str, Any] = {}
    for name, component in components.items():
        if component is None:
            continue
        if not hasattr(component, "get_schema"):
            # Some components carry a pre-built schema instead of a factory.
            raw_schema = getattr(component, "__pyvider_schema__", None)
            if raw_schema is not None:
                schemas[name] = _annotate_schema(dict(raw_schema), component)
            continue
        try:
            schema_dict = convert_pvs_schema_to_dict(component.get_schema())
            schemas[name] = _annotate_schema(schema_dict, component)
        except Exception as e:
            logger.warning(f"Failed to get schema for {name}: {e}")
    return schemas


def _annotate_schema(schema_dict: dict[str, Any], component: Any) -> dict[str, Any]:
    """Attach the plating-specific metadata templates rely on."""
    schema_dict["test_only"] = getattr(component, "_is_test_only", False)
    schema_dict["component_of"] = getattr(component, "_parent_capability", None)
    return schema_dict


def get_component_schemas_from_hub(hub: Any, dimension: str) -> dict[str, Any]:
    """Get component schemas from a foundation hub by dimension."""
    try:
        names = hub.list_components(dimension=dimension) or []
        components = {name: hub.get_component(name, dimension=dimension) for name in names}
    except Exception as e:
        logger.warning(f"Failed to get {dimension} components: {e}")
        return {}
    return extract_component_schemas(components)


def get_function_schemas_from_hub(hub: Any, dimension: str) -> dict[str, Any]:
    """Get function schemas from a foundation hub."""
    try:
        names = hub.list_components(dimension=dimension) or []
        functions = {name: hub.get_component(name, dimension=dimension) for name in names}
    except Exception as e:
        logger.warning(f"Failed to get function components: {e}")
        return {}
    return extract_function_schemas(functions)


def extract_function_schemas(functions: dict[str, Any]) -> dict[str, Any]:
    """Build signature-based schema dicts for already-discovered functions."""
    schemas: dict[str, Any] = {}
    for name, func in functions.items():
        if not func:
            continue
        try:
            sig = inspect.signature(func)
        except Exception as e:
            logger.warning(f"Failed to get schema for function {name}: {e}")
            continue

        schema_dict: dict[str, Any] = {
            "signature": {
                "parameters": [
                    {
                        "name": param.name,
                        "type": str(param.annotation) if param.annotation != param.empty else "any",
                        "description": f"Parameter {param.name}",
                    }
                    for param in sig.parameters.values()
                ],
                "return_type": str(sig.return_annotation) if sig.return_annotation != sig.empty else "any",
            },
            "description": func.__doc__ or f"Function {name}",
        }
        schemas[name] = _annotate_schema(schema_dict, func)
    return schemas


def _encode_attribute_type(cty_type: Any) -> Any:
    """Encode a cty type into its Terraform JSON form.

    attrs.asdict() flattens a cty type to {} -- the primitive types carry no
    attrs fields -- which is why every attribute used to render as "String".
    The wire encoder produces the same shape Terraform publishes ("string",
    ["list", "string"], ["object", {...}]), which SchemaInfo._format_type
    already knows how to read.
    """
    if cty_type is None:
        return None
    try:
        from pyvider.cty.conversion.type_encoder import encode_cty_type_to_wire_json

        return encode_cty_type_to_wire_json(cty_type)
    except Exception as e:
        logger.debug(f"Could not encode cty type {cty_type!r}: {e}")
        return getattr(cty_type, "ctype", None) or str(cty_type)


def _convert_attribute(attribute: Any) -> dict[str, Any]:
    """Convert a PvsAttribute into the Terraform JSON attribute shape."""
    return {
        "type": _encode_attribute_type(getattr(attribute, "type", None)),
        "description": getattr(attribute, "description", "") or "",
        "description_kind": getattr(attribute, "description_kind", None),
        "required": bool(getattr(attribute, "required", False)),
        "optional": bool(getattr(attribute, "optional", False)),
        "computed": bool(getattr(attribute, "computed", False)),
        "sensitive": bool(getattr(attribute, "sensitive", False)),
        "write_only": bool(getattr(attribute, "write_only", False)),
        "deprecated": bool(getattr(attribute, "deprecated", False)),
    }


def _convert_block(block: Any) -> dict[str, Any]:
    """Convert a PvsObjectType block into the Terraform JSON block shape."""
    attributes = getattr(block, "attributes", None) or {}
    if not isinstance(attributes, dict):
        attributes = {getattr(a, "name", str(i)): a for i, a in enumerate(attributes)}

    nested = getattr(block, "block_types", None) or {}
    if not isinstance(nested, dict):
        nested = {getattr(b, "type_name", str(i)): b for i, b in enumerate(nested)}

    return {
        "attributes": {name: _convert_attribute(attr) for name, attr in attributes.items()},
        "block_types": {name: _convert_nested_block(b) for name, b in nested.items()},
        "description": getattr(block, "description", "") or "",
        "deprecated": bool(getattr(block, "deprecated", False)),
    }


def _convert_nested_block(nested_block: Any) -> dict[str, Any]:
    """Convert a PvsNestedBlock, recursing into its own block."""
    inner = getattr(nested_block, "block", None)
    nesting = getattr(nested_block, "nesting", None)
    return {
        "nesting_mode": getattr(nesting, "name", nesting),
        "min_items": getattr(nested_block, "min_items", 0),
        "max_items": getattr(nested_block, "max_items", 0),
        "description": getattr(nested_block, "description", "") or "",
        "block": _convert_block(inner) if inner is not None else {"attributes": {}, "block_types": {}},
    }


def convert_pvs_schema_to_dict(pvs_schema: Any) -> dict[str, Any]:
    """Convert a PvsSchema object to the Terraform JSON schema shape."""
    try:
        block = getattr(pvs_schema, "block", None)
        if block is not None:
            return {
                "version": getattr(pvs_schema, "version", 0),
                "block": _convert_block(block),
                "description": getattr(block, "description", "") or "",
            }

        # Schema-shaped object with no block wrapper (functions, plain dicts).
        if isinstance(pvs_schema, dict):
            return dict(pvs_schema)

        return {
            "block": _convert_block(pvs_schema),
            "description": getattr(pvs_schema, "description", "") or "",
        }
    except Exception as e:
        logger.warning(f"Failed to convert PvsSchema to dict: {e}")
        return {"block": {"attributes": {}, "block_types": {}}}


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
