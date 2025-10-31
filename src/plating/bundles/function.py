# 
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from pathlib import Path

from attrs import define, field

from plating.bundles.base import PlatingBundle

#
# plating/bundles/function.py
#
"""Specialized PlatingBundle for individual function templates."""


@define
class FunctionPlatingBundle(PlatingBundle):
    """Specialized PlatingBundle for individual function templates."""

    template_file: Path = field()

    def load_main_template(self) -> str | None:
        """Load the specific template file for this function."""
        try:
            return self.template_file.read_text(encoding="utf-8")
        except Exception:
            return None

# 🍽️📖🔚
