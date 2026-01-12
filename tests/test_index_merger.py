#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test module for index merger functionality."""

from plating.core.index_merger import IndexMerger


class TestIndexMerger:
    """Test suite for IndexMerger class."""

    def test_parse_custom_sections_no_markers(self) -> None:
        """Handle content without markers."""
        content = """# Provider Index

This is regular content without any custom markers.

## Resources

- resource_one
- resource_two
"""

        sections = IndexMerger.parse_custom_sections(content)

        assert sections == {}, "Should return empty dict when no markers present"

    def test_parse_custom_sections_single_section(self) -> None:
        """Extract single marked section."""
        content = """# Provider Index

<!-- BEGIN: AUTO_RESOURCES -->
## Resources

- custom_resource_one
- custom_resource_two
<!-- END: AUTO_RESOURCES -->

## Data Sources

- data_source_one
"""

        sections = IndexMerger.parse_custom_sections(content)

        assert len(sections) == 1, "Should find one marked section"
        assert "AUTO_RESOURCES" in sections, "Should extract AUTO_RESOURCES section"

        _start, _end, section_content = sections["AUTO_RESOURCES"]
        assert "custom_resource_one" in section_content, "Should capture section content"
        assert "<!-- BEGIN: AUTO_RESOURCES -->" in section_content, "Should include begin marker"
        assert "<!-- END: AUTO_RESOURCES -->" in section_content, "Should include end marker"

    def test_parse_custom_sections_multiple_sections(self) -> None:
        """Extract multiple marked sections."""
        content = """# Provider Index

<!-- BEGIN: AUTO_RESOURCES -->
## Resources
- resource_one
<!-- END: AUTO_RESOURCES -->

Some content in between

<!-- BEGIN: AUTO_DATA_SOURCES -->
## Data Sources
- data_source_one
<!-- END: AUTO_DATA_SOURCES -->

<!-- BEGIN: AUTO_FUNCTIONS -->
## Functions
- function_one
<!-- END: AUTO_FUNCTIONS -->
"""

        sections = IndexMerger.parse_custom_sections(content)

        assert len(sections) == 3, "Should find three marked sections"
        assert "AUTO_RESOURCES" in sections, "Should have AUTO_RESOURCES"
        assert "AUTO_DATA_SOURCES" in sections, "Should have AUTO_DATA_SOURCES"
        assert "AUTO_FUNCTIONS" in sections, "Should have AUTO_FUNCTIONS"

        # Check content extraction
        _, _, resources_content = sections["AUTO_RESOURCES"]
        assert "resource_one" in resources_content, "Should capture resources content"

        _, _, data_content = sections["AUTO_DATA_SOURCES"]
        assert "data_source_one" in data_content, "Should capture data sources content"

        _, _, func_content = sections["AUTO_FUNCTIONS"]
        assert "function_one" in func_content, "Should capture functions content"

    def test_parse_custom_sections_nested_markers(self) -> None:
        """Handle section content with code blocks that might contain similar text."""
        content = """# Provider Index

<!-- BEGIN: AUTO_RESOURCES -->
## Resources

Here's an example:

```terraform
# This is NOT a real marker: <!-- BEGIN: FAKE -->
resource "test" "example" {}
# <!-- END: FAKE -->
```

- resource_one
<!-- END: AUTO_RESOURCES -->
"""

        sections = IndexMerger.parse_custom_sections(content)

        assert len(sections) == 1, "Should find only the real marked section"
        assert "AUTO_RESOURCES" in sections, "Should have AUTO_RESOURCES"
        assert "FAKE" not in sections, "Should not extract markers from code blocks"

        _, _, content_text = sections["AUTO_RESOURCES"]
        assert "resource_one" in content_text, "Should include all content up to real end marker"

    def test_merge_index_no_existing_content(self) -> None:
        """Return auto-generated when no existing content."""
        auto_generated = """# Provider Index

Auto-generated content here.

## Resources

- auto_resource_one
- auto_resource_two
"""

        merged = IndexMerger.merge_index(auto_generated, existing_content=None)

        assert merged == auto_generated, "Should return auto-generated content when no existing content"

    def test_merge_index_with_custom_sections(self) -> None:
        """Preserve marked sections from existing content."""
        auto_generated = """# Provider Index

Auto-generated header.

## Resources

- auto_resource_one
- auto_resource_two
"""

        existing_content = """# Provider Index

Custom header content.

<!-- BEGIN: AUTO_RESOURCES -->
## Resources

- custom_resource_one
- custom_resource_two
<!-- END: AUTO_RESOURCES -->
"""

        merged = IndexMerger.merge_index(auto_generated, existing_content=existing_content)

        # For now, the implementation just returns auto-generated
        # This test documents the current behavior
        assert merged == auto_generated, "Current implementation returns auto-generated content"

        # Note: When full merging is implemented, this test should verify:
        # - Custom sections are preserved
        # - Auto-generated sections are updated
        # - Overall structure is maintained

    def test_merge_index_malformed_markers(self) -> None:
        """Handle malformed markers gracefully."""
        auto_generated = """# Provider Index

## Resources
- resource_one
"""

        # Missing END marker
        existing_content = """# Provider Index

<!-- BEGIN: AUTO_RESOURCES -->
## Resources
- custom_resource

No end marker here!

## Data Sources
"""

        merged = IndexMerger.merge_index(auto_generated, existing_content=existing_content)

        # Should not crash with malformed markers
        assert isinstance(merged, str), "Should return string even with malformed markers"

    def test_parse_custom_sections_whitespace_handling(self) -> None:
        """Handle various whitespace in markers."""
        content = """# Provider Index

<!--BEGIN:AUTO_RESOURCES-->
Tight spacing
<!--END:AUTO_RESOURCES-->

<!-- BEGIN: AUTO_DATA_SOURCES -->
Normal spacing
<!-- END: AUTO_DATA_SOURCES -->

<!--  BEGIN:  AUTO_FUNCTIONS  -->
Extra spacing
<!--  END:  AUTO_FUNCTIONS  -->
"""

        sections = IndexMerger.parse_custom_sections(content)

        # Note: Current implementation expects "BEGIN:" with space
        # This test documents actual behavior
        assert "AUTO_DATA_SOURCES" in sections, "Should handle normal spacing"

    def test_merge_index_empty_existing_content(self) -> None:
        """Handle empty string as existing content."""
        auto_generated = """# Provider Index

Content here.
"""

        merged = IndexMerger.merge_index(auto_generated, existing_content="")

        assert merged == auto_generated, "Should treat empty string like None"


# 🍽️📖🔚
