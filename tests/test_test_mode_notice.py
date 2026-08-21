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

import pytest

from plating.core.doc_generator import (
    TEST_MODE_NOTICE,
    _determine_subcategory,
    _inject_test_mode_notice,
)
from plating.types import SchemaInfo

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


class TestNoticeMatchesTheSubcategory:
    """Whatever earns `subcategory: "Test Mode"` must also earn the notice.

    The two are decided from the same facts, and they drifted once already:
    the notice took only `_extract_component_metadata`'s answer, which guesses a
    module path from the bundle's directory and so misses a component whose code
    lives in another type's module. `pyvider_nested_resource_test` and
    `pyvider_nested_data_processor` are declared in a data-source module, got the
    subcategory from the hub's schema and no notice at all.
    """

    @pytest.mark.parametrize(
        ("from_module", "from_schema"),
        [(True, False), (False, True), (True, True)],
    )
    def test_either_source_of_truth_is_enough(self, from_module: bool, from_schema: bool) -> None:
        schema_info = SchemaInfo(test_only=from_schema) if from_schema else None

        assert _determine_subcategory(schema_info, from_module) == "Test Mode"
        assert TEST_MODE_NOTICE in _inject_test_mode_notice(
            PAGE, from_module or bool(schema_info and schema_info.test_only)
        )

    def test_neither_means_no_notice_and_no_subcategory(self) -> None:
        assert _determine_subcategory(SchemaInfo(test_only=False), False) is None
        assert TEST_MODE_NOTICE not in _inject_test_mode_notice(PAGE, False)


# 🧪📄🔚
