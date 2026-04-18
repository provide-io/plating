#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Memray stress test for schema formatting hot paths.

Exercises parse_schema_to_markdown, format_type_string, and the
attribute table generation that runs for every resource/data-source.
"""
from __future__ import annotations

import os

os.environ.setdefault("LOG_LEVEL", "ERROR")

from plating.schema.formatters import (
    format_type_string,
    parse_function_arguments,
    parse_function_signature,
    parse_schema_to_markdown,
)

WARMUP = 10
CYCLES = 1000


def _make_schema(num_attrs: int) -> dict:
    """Create a synthetic provider schema with nested blocks."""
    attributes = {}
    for i in range(num_attrs):
        attributes[f"attr_{i:03d}"] = {
            "type": ["string", "number", "bool", "list"][i % 4],
            "description": f"Attribute {i} description text for testing",
            "required": i % 3 == 0,
            "optional": i % 3 == 1,
            "computed": i % 3 == 2,
        }
    return {
        "block": {
            "attributes": attributes,
            "block_types": {
                "nested_block": {
                    "block": {
                        "attributes": {
                            f"nested_{j}": {
                                "type": "string",
                                "description": f"Nested attr {j}",
                                "optional": True,
                            }
                            for j in range(5)
                        }
                    }
                }
            },
        }
    }


def _make_function_schema() -> dict:
    """Create a synthetic function schema."""
    return {
        "description": "A test function for stress testing",
        "summary": "Test function",
        "signature": {
            "parameters": [
                {"name": f"param_{i}", "type": "string", "description": f"Parameter {i}"}
                for i in range(5)
            ],
            "variadic_parameter": {
                "name": "extra_args",
                "type": "any",
                "description": "Additional arguments",
            },
            "return_type": "string",
        },
    }


def main() -> None:
    schema_small = _make_schema(10)
    schema_large = _make_schema(50)
    func_schema = _make_function_schema()

    type_inputs = ["string", "number", "bool", "list", "set", "map", "object", ""]
    type_dicts = [{"type": t} for t in type_inputs]

    # Warmup
    for _ in range(WARMUP):
        parse_schema_to_markdown(schema_small)
        for t in type_inputs:
            format_type_string(t)

    # Stress: schema formatting
    for _ in range(CYCLES):
        parse_schema_to_markdown(schema_small)
        parse_schema_to_markdown(schema_large)
        parse_function_signature(func_schema)
        parse_function_arguments(func_schema)
        for t in type_inputs:
            format_type_string(t)
        for td in type_dicts:
            format_type_string(td)

    print(f"Schema formatting stress complete: {CYCLES} cycles")


if __name__ == "__main__":
    main()
