#!/usr/bin/env python3
"""Memray stress test for doc_generator helper functions.

Exercises _inject_subcategory, _inject_test_mode_subcategory, and
group_components_by_capability which are called for every component.
"""

from __future__ import annotations

import os

os.environ.setdefault("LOG_LEVEL", "ERROR")

from plating.core.doc_generator import (
    _determine_subcategory,
    _inject_subcategory,
    _inject_test_mode_subcategory,
)

WARMUP = 10
CYCLES = 2000


def _make_content_with_frontmatter(subcategory: str | None = None) -> str:
    """Generate markdown with optional subcategory in frontmatter."""
    lines = ["---", 'page_title: "Test"', 'description: "Test component"']
    if subcategory:
        lines.append(f'subcategory: "{subcategory}"')
    lines.append("---")
    lines.append("")
    lines.append("# Test Component")
    lines.append("")
    lines.append("Content here.")
    return "\n".join(lines)


def _make_content_no_frontmatter() -> str:
    return "# Test Component\n\nContent here.\n"


def main() -> None:
    content_with_sub = _make_content_with_frontmatter("Networking")
    content_without_sub = _make_content_with_frontmatter()
    content_no_fm = _make_content_no_frontmatter()

    # Warmup
    for _ in range(WARMUP):
        _inject_subcategory(content_without_sub, "Test Mode")
        _inject_test_mode_subcategory(content_without_sub)
        _determine_subcategory(None, False)

    # Stress: subcategory injection
    for _ in range(CYCLES):
        # inject_subcategory with various inputs
        _inject_subcategory(content_without_sub, "Test Mode")
        _inject_subcategory(content_without_sub, "Networking")
        _inject_subcategory(content_without_sub, None)  # no-op path
        _inject_subcategory(content_with_sub, "Test Mode")  # already has subcategory
        _inject_subcategory(content_no_fm, "Test Mode")  # no frontmatter
        _inject_subcategory("malformed --- content", "Test Mode")  # malformed

        # inject_test_mode_subcategory
        _inject_test_mode_subcategory(content_without_sub)
        _inject_test_mode_subcategory(content_with_sub)
        _inject_test_mode_subcategory(content_no_fm)

        # determine_subcategory
        _determine_subcategory(None, False)
        _determine_subcategory(None, True)

    print(f"Doc generator stress complete: {CYCLES} cycles")


if __name__ == "__main__":
    main()
