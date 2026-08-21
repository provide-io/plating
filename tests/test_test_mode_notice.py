#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""A test-only component's page has to say it is unreachable.

`subcategory: "Test Mode"` groups these pages in the navigation, which tells a
reader they are grouped -- not that a provider started normally will not publish
them at all. terraform-provider-pyvider shipped fourteen such components, every
action, ephemeral resource, list resource and state store it had, and nothing on
the page said `tofu providers schema` would show none of them.
"""

from __future__ import annotations

from plating.core.doc_generator import TEST_MODE_NOTICE, _inject_test_mode_notice

PAGE = """---
page_title: "Action: pyvider_echo"
subcategory: "Test Mode"
---

# pyvider_echo (Action)

Appends a timestamped message to a file.

## Example Usage

```terraform
action "pyvider_echo" "example" {}
```
"""


class TestTestModeNotice:
    def test_a_test_only_page_carries_the_notice(self) -> None:
        assert TEST_MODE_NOTICE in _inject_test_mode_notice(PAGE, is_test_only=True)

    def test_a_normal_page_is_untouched(self) -> None:
        assert _inject_test_mode_notice(PAGE, is_test_only=False) == PAGE

    def test_the_notice_lands_after_the_heading_and_before_the_example(self) -> None:
        """A reader must meet it before the example they would otherwise copy."""
        out = _inject_test_mode_notice(PAGE, is_test_only=True)

        heading = out.index("# pyvider_echo (Action)")
        notice = out.index(TEST_MODE_NOTICE)
        example = out.index("## Example Usage")

        assert heading < notice < example

    def test_the_frontmatter_survives(self) -> None:
        out = _inject_test_mode_notice(PAGE, is_test_only=True)

        assert out.startswith("---\n")
        assert 'page_title: "Action: pyvider_echo"' in out
        assert out.index("subcategory") < out.index(TEST_MODE_NOTICE)

    def test_injecting_twice_does_not_duplicate(self) -> None:
        once = _inject_test_mode_notice(PAGE, is_test_only=True)

        assert _inject_test_mode_notice(once, is_test_only=True) == once

    def test_a_page_without_a_heading_still_gets_it(self) -> None:
        """Better at the top than dropped."""
        out = _inject_test_mode_notice("Body with no heading.\n", is_test_only=True)

        assert out.startswith(TEST_MODE_NOTICE)

    def test_the_notice_is_plain_markdown(self) -> None:
        """The registry renders a restricted subset -- no mkdocs admonitions."""
        assert all(line.startswith(">") for line in TEST_MODE_NOTICE.splitlines())
        assert "!!!" not in TEST_MODE_NOTICE
        assert ":::" not in TEST_MODE_NOTICE


# 🧪📄🔚
