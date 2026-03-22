#!/usr/bin/env python3
"""Memray stress test for template engine hot paths.

Exercises Jinja2 environment creation, frontmatter parsing, and the
global header/footer injection logic that runs for every rendered doc.
"""
from __future__ import annotations

import os

os.environ.setdefault("LOG_LEVEL", "ERROR")

from plating.templating.engine import AsyncTemplateEngine

WARMUP = 5
CYCLES = 500


def _make_frontmatter_content(skip_header: bool = False, skip_footer: bool = False) -> str:
    """Generate synthetic markdown with YAML frontmatter."""
    fm_lines = ['---', 'page_title: "Test Resource"', 'description: "A test resource"']
    if skip_header:
        fm_lines.append("skip_global_header: true")
    if skip_footer:
        fm_lines.append("skip_global_footer: true")
    fm_lines.append("---")
    fm_lines.append("")
    fm_lines.append("# Test Resource")
    fm_lines.append("")
    fm_lines.append("This is the description paragraph.")
    fm_lines.append("")
    fm_lines.append("## Example Usage")
    fm_lines.append("")
    fm_lines.append("```terraform")
    fm_lines.append('resource "test" "example" {')
    fm_lines.append('  name = "test"')
    fm_lines.append("}")
    fm_lines.append("```")
    fm_lines.append("")
    fm_lines.append("## Schema")
    fm_lines.append("")
    fm_lines.append("| Argument | Type | Required | Description |")
    fm_lines.append("|----------|------|----------|-------------|")
    for i in range(20):
        fm_lines.append(f"| `attr_{i}` | String | No | Attribute {i} |")
    return "\n".join(fm_lines)


def main() -> None:
    engine = AsyncTemplateEngine()

    content_normal = _make_frontmatter_content()
    content_skip_header = _make_frontmatter_content(skip_header=True)
    content_skip_footer = _make_frontmatter_content(skip_footer=True)
    content_no_fm = "# No Frontmatter\n\nJust content.\n"

    header_text = "> This is a global header notice.\n"

    # Warmup
    for _ in range(WARMUP):
        engine._parse_frontmatter(content_normal)
        engine._check_frontmatter_flag("---\nfoo: bar\n---", "foo")

    # Stress: frontmatter parsing + header injection
    for _ in range(CYCLES):
        # Parse frontmatter variants
        fm, body = engine._parse_frontmatter(content_normal)
        engine._should_skip_header(fm)
        engine._should_skip_footer(fm)

        fm2, body2 = engine._parse_frontmatter(content_skip_header)
        engine._should_skip_header(fm2)

        fm3, body3 = engine._parse_frontmatter(content_skip_footer)
        engine._should_skip_footer(fm3)

        engine._parse_frontmatter(content_no_fm)

        # Header injection
        engine._inject_header_into_body(body, header_text)
        engine._inject_header_into_body(body2, header_text)
        engine._inject_header_into_body("No heading content", header_text)

    # Stress: Jinja environment creation (heavier path)
    templates = {"main.tmpl": "Hello {{ name }}!", "partial.tmpl": "Partial content"}
    for _ in range(CYCLES // 5):
        env = engine._get_jinja_env(templates)
        tmpl = env.get_template("main.tmpl")

    print(f"Template engine stress complete: {CYCLES} cycles")


if __name__ == "__main__":
    main()
