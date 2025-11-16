#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test module for subcategory frontmatter injection and preservation."""


from plating.core.doc_generator import _inject_subcategory, _inject_test_mode_subcategory


class TestSubcategoryFrontmatter:
    """Test suite for subcategory injection and preservation."""

    def test_inject_subcategory_creates_frontmatter(self) -> None:
        """Add frontmatter if missing."""
        content = """# test_resource (Resource)

This is a resource without frontmatter.

## Example Usage

Some example here.
"""

        result = _inject_subcategory(content, "Lens")

        # Should add frontmatter
        assert result.startswith("---"), "Should add frontmatter start marker"
        assert 'subcategory: "Lens"' in result, "Should add subcategory field"
        assert "---\n\n#" in result, "Should have proper frontmatter end and content separation"
        assert "This is a resource without frontmatter" in result, "Should preserve original content"

    def test_inject_subcategory_adds_to_existing_frontmatter(self) -> None:
        """Inject into existing frontmatter."""
        content = """---
page_title: "Resource: test_resource"
description: |-
  Test resource description
---

# test_resource (Resource)

Content here.
"""

        result = _inject_subcategory(content, "Utilities")

        # Should inject subcategory into existing frontmatter
        assert result.startswith("---"), "Should preserve frontmatter start"
        assert 'page_title: "Resource: test_resource"' in result, "Should preserve page_title"
        assert "description: |-" in result, "Should preserve description"
        assert 'subcategory: "Utilities"' in result, "Should add subcategory"

        # Subcategory should be before closing ---
        lines = result.split("\n")
        subcategory_line = next(i for i, line in enumerate(lines) if "subcategory:" in line)
        closing_marker = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
        assert subcategory_line < closing_marker, "Subcategory should be before closing marker"

    def test_inject_subcategory_preserves_existing(self) -> None:
        """Don't override existing subcategory."""
        content = """---
page_title: "Resource: test_resource"
description: |-
  Test resource
subcategory: "Lens"
---

# test_resource (Resource)

Content here.
"""

        result = _inject_subcategory(content, "Test Mode")

        # Should NOT change existing subcategory
        assert 'subcategory: "Lens"' in result, "Should keep original subcategory"
        assert 'subcategory: "Test Mode"' not in result, "Should not add new subcategory"
        assert result.count("subcategory:") == 1, "Should have exactly one subcategory field"

    def test_inject_subcategory_malformed_frontmatter(self) -> None:
        """Handle malformed gracefully."""
        # Missing closing ---
        content = """---
page_title: "Resource: test_resource"
description: |-
  Test resource

# test_resource (Resource)

Content here.
"""

        result = _inject_subcategory(content, "Utilities")

        # Should return original content when frontmatter is malformed
        assert result == content, "Should return original content for malformed frontmatter"

    def test_inject_test_mode_subcategory(self) -> None:
        """Special handling for Test Mode."""
        content = """---
page_title: "Resource: test_resource"
description: |-
  Test resource
---

# test_resource (Resource)

Content here.
"""

        result = _inject_test_mode_subcategory(content)

        assert 'subcategory: "Test Mode"' in result, "Should inject Test Mode subcategory"

    def test_inject_subcategory_multiple_fields(self) -> None:
        """Preserve all frontmatter fields."""
        content = """---
page_title: "Data Source: test_data"
description: |-
  Multi-line description
  with multiple lines
sidebar_label: "Test Data"
custom_field: "custom_value"
another_field: 123
---

# test_data (Data Source)

Content here.
"""

        result = _inject_subcategory(content, "Lens")

        # Should preserve all fields
        assert 'page_title: "Data Source: test_data"' in result, "Should preserve page_title"
        assert "Multi-line description" in result, "Should preserve multi-line description"
        assert 'sidebar_label: "Test Data"' in result, "Should preserve sidebar_label"
        assert 'custom_field: "custom_value"' in result, "Should preserve custom_field"
        assert "another_field: 123" in result, "Should preserve another_field"
        assert 'subcategory: "Lens"' in result, "Should add subcategory"

    def test_inject_subcategory_empty_frontmatter(self) -> None:
        """Handle empty frontmatter block."""
        content = """---
---

# test_resource (Resource)

Content here.
"""

        result = _inject_subcategory(content, "Utilities")

        assert 'subcategory: "Utilities"' in result, "Should inject subcategory into empty frontmatter"
        assert "# test_resource (Resource)" in result, "Should preserve content"

    def test_inject_test_mode_preserves_existing_subcategory(self) -> None:
        """Test Mode injection should not override existing subcategory."""
        content = """---
page_title: "Resource: test_resource"
subcategory: "Lens"
---

# test_resource (Resource)

Content here.
"""

        result = _inject_test_mode_subcategory(content)

        # Should NOT override existing subcategory
        assert 'subcategory: "Lens"' in result, "Should preserve existing subcategory"
        assert 'subcategory: "Test Mode"' not in result, "Should not add Test Mode subcategory"

    def test_inject_subcategory_with_comments(self) -> None:
        """Preserve comments in frontmatter."""
        content = """---
# This is a comment
page_title: "Resource: test_resource"
# Another comment
description: |-
  Test resource
---

# test_resource (Resource)

Content here.
"""

        result = _inject_subcategory(content, "Utilities")

        assert "# This is a comment" in result, "Should preserve first comment"
        assert "# Another comment" in result, "Should preserve second comment"
        assert 'subcategory: "Utilities"' in result, "Should add subcategory"

    def test_inject_subcategory_with_none_skips_injection(self) -> None:
        """When subcategory is None, skip injection entirely."""
        content = """---
page_title: "Resource: test_resource"
description: |-
  Test resource
---

# test_resource (Resource)

Content here.
"""

        result = _inject_subcategory(content, None)

        # Should return content unchanged when subcategory is None
        assert result == content, "Should return unchanged content when subcategory is None"
        assert "subcategory:" not in result, "Should not add any subcategory field"

    def test_inject_subcategory_none_with_no_frontmatter(self) -> None:
        """When subcategory is None and no frontmatter, return unchanged."""
        content = """# test_resource (Resource)

Content here without frontmatter.
"""

        result = _inject_subcategory(content, None)

        assert result == content, "Should return unchanged content when subcategory is None"
        assert "---" not in result, "Should not add frontmatter when subcategory is None"

    def test_inject_subcategory_none_preserves_existing_frontmatter(self) -> None:
        """When subcategory is None, preserve existing frontmatter as-is."""
        content = """---
page_title: "Resource: test_resource"
subcategory: "Math"
description: |-
  Test resource
---

# test_resource (Resource)

Content here.
"""

        result = _inject_subcategory(content, None)

        # Should return unchanged, keeping the Math subcategory
        assert result == content, "Should return unchanged content when subcategory is None"
        assert 'subcategory: "Math"' in result, "Should preserve existing Math subcategory"


# 🍽️📖🔚
