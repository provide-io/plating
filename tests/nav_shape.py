#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Read a generated mkdocs nav back for assertions.

mkdocs nav is a list of single-key mappings, so the order of entries lives in
the file rather than in a dict's insertion order. Tests care about which
entries exist and where they point, not the list mechanics, so they flatten it.
Anything asserting on *order* should index the list directly instead.
"""

from __future__ import annotations

from typing import Any


def as_mapping(nav: list[dict[str, Any]]) -> dict[str, Any]:
    """Flatten a nav list of single-key mappings into one mapping."""
    return {key: value for entry in nav for key, value in entry.items()}


# 🗺️📖🔚
