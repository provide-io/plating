#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test module for capability grouping functionality."""


from plating.bundles import PlatingBundle
from plating.core.doc_generator import (
    _determine_subcategory,
    _extract_subcategory_from_template,
    group_components_by_capability,
)
from plating.types import ComponentType, SchemaInfo


class TestCapabilityGrouping:
    """Test suite for capability grouping functionality."""

    def test_group_components_by_capability_basic(self, sample_components_mixed_types) -> None:
        """Test basic grouping by subcategory."""
        components = sample_components_mixed_types

        grouped = group_components_by_capability(components)

        # Should have 3 entries: None (uncategorized), Lens, Test Mode
        # Based on the sample data, we have:
        # - A component with Lens subcategory
        # - A component with Test Mode (auto-detected)
        # - A component without subcategory (None)
        assert "Test Mode" in grouped, "Should have Test Mode capability"
        assert "Lens" in grouped, "Should have Lens capability"

        # Check that Test Mode is the last key (special ordering)
        keys = list(grouped.keys())
        assert keys[-1] == "Test Mode", "Test Mode should be last"

    def test_group_components_by_capability_test_mode_last(self, temp_directory) -> None:
        """Verify Test Mode always appears last in ordering."""

        components = []

        # Create components with different subcategories
        for name, subcategory in [
            ("test_comp", "Test Mode"),
            ("lens_comp", "Lens"),
            ("util_comp", "Utilities"),
            ("zebra_comp", "Zebra Category"),
        ]:
            comp_dir = temp_directory / f"{name}.plating"
            docs_dir = comp_dir / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / f"{name}.tmpl.md").write_text(
                f"""---
subcategory: "{subcategory}"
---
# {name}
"""
            )
            components.append((PlatingBundle(name, comp_dir, "resource"), ComponentType.RESOURCE))

        grouped = group_components_by_capability(components)

        # Get keys as list to check order
        keys = list(grouped.keys())

        # Test Mode should be last
        assert keys[-1] == "Test Mode", "Test Mode should always be last"

        # Other categories should be sorted alphabetically
        other_keys = keys[:-1]
        assert other_keys == sorted(other_keys), "Non-Test Mode categories should be alphabetically sorted"

    def test_group_components_by_capability_mixed_types(self, temp_directory) -> None:
        """Test with resources, data sources, and functions."""

        components = []

        # Create Lens category with all types
        for comp_type_str, comp_type_enum in [
            ("resource", ComponentType.RESOURCE),
            ("data_source", ComponentType.DATA_SOURCE),
            ("function", ComponentType.FUNCTION),
        ]:
            comp_dir = temp_directory / f"lens_{comp_type_str}.plating"
            docs_dir = comp_dir / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / f"lens_{comp_type_str}.tmpl.md").write_text(
                """---
subcategory: "Lens"
---
# Lens Component
"""
            )
            components.append((PlatingBundle(f"lens_{comp_type_str}", comp_dir, comp_type_str), comp_type_enum))

        grouped = group_components_by_capability(components)

        # Should have only Lens capability
        assert len(grouped) == 1, "Should have only one capability"
        assert "Lens" in grouped, "Should have Lens capability"

        # Lens should contain all three component types
        assert ComponentType.RESOURCE in grouped["Lens"], "Lens should have resources"
        assert ComponentType.DATA_SOURCE in grouped["Lens"], "Lens should have data sources"
        assert ComponentType.FUNCTION in grouped["Lens"], "Lens should have functions"

    def test_extract_subcategory_from_template_with_subcategory(self, sample_component_with_subcategory) -> None:
        """Extract existing subcategory from template."""
        component = sample_component_with_subcategory

        subcategory = _extract_subcategory_from_template(component)

        assert subcategory == "Lens", "Should extract 'Lens' subcategory from template"

    def test_extract_subcategory_from_template_missing_subcategory(self, sample_component_no_subcategory) -> None:
        """Return None when subcategory is not present."""
        component = sample_component_no_subcategory

        subcategory = _extract_subcategory_from_template(component)

        assert subcategory is None, "Should return None when subcategory not present"

    def test_extract_subcategory_from_template_malformed_frontmatter(self, temp_directory) -> None:
        """Handle malformed templates gracefully."""

        plating_dir = temp_directory / "malformed.plating"
        docs_dir = plating_dir / "docs"
        docs_dir.mkdir(parents=True)

        # Create template with malformed frontmatter (no closing ---)
        template_content = """---
page_title: "Resource: malformed"
description: |-
  Malformed template

# Missing closing ---

# malformed (Resource)

Content here
"""
        (docs_dir / "malformed.tmpl.md").write_text(template_content)

        component = PlatingBundle(name="malformed", plating_dir=plating_dir, component_type="resource")

        subcategory = _extract_subcategory_from_template(component)

        assert subcategory is None, "Should return None for malformed frontmatter"

    def test_determine_subcategory_test_only_components(self) -> None:
        """Test Mode detection for test_only components."""
        # Test with is_test_only=True
        subcategory = _determine_subcategory(schema_info=None, is_test_only=True)
        assert subcategory == "Test Mode", "Should return 'Test Mode' for test_only components"

        # Test with schema_info.test_only=True
        schema_info = SchemaInfo(test_only=True)
        subcategory = _determine_subcategory(schema_info=schema_info, is_test_only=False)
        assert subcategory == "Test Mode", "Should return 'Test Mode' from schema_info"

    def test_determine_subcategory_lens_components(self) -> None:
        """Lens subcategory is no longer auto-determined - comes from template frontmatter."""
        # Lens category now comes from template frontmatter, not from component_of decorator
        # _determine_subcategory() only handles Test Mode auto-detection
        subcategory = _determine_subcategory(schema_info=None, is_test_only=False)
        assert subcategory is None, "Should return None for regular components (non-test)"

        # Even with schema_info, regular components return None
        schema_info = SchemaInfo(description="Lens component")
        subcategory = _determine_subcategory(schema_info=schema_info, is_test_only=False)
        assert subcategory is None, "Should return None for regular components"

    def test_determine_subcategory_default_none(self) -> None:
        """Regular components return None - subcategory comes from template frontmatter."""
        # Without special metadata (like test_only), return None
        # This allows components without subcategory to render first per Terraform Registry standards
        subcategory = _determine_subcategory(schema_info=None, is_test_only=False)
        assert subcategory is None, "Should return None for regular components"

        # Test with schema_info but no special fields
        schema_info = SchemaInfo(description="Regular component")
        subcategory = _determine_subcategory(schema_info=schema_info, is_test_only=False)
        assert subcategory is None, "Should return None for regular components with schema_info"

    def test_group_components_uncategorized_first(self, temp_directory) -> None:
        """Uncategorized components (None subcategory) render first."""

        components = []

        # Create one component with no subcategory
        uncategorized_dir = temp_directory / "uncategorized.plating"
        uncategorized_docs = uncategorized_dir / "docs"
        uncategorized_docs.mkdir(parents=True)
        (uncategorized_docs / "uncategorized.tmpl.md").write_text(
            """---
page_title: "Resource: uncategorized"
---
# uncategorized
"""
        )
        components.append((PlatingBundle("uncategorized", uncategorized_dir, "resource"), ComponentType.RESOURCE))

        # Create one component with Math subcategory
        math_dir = temp_directory / "math.plating"
        math_docs = math_dir / "docs"
        math_docs.mkdir(parents=True)
        (math_docs / "math.tmpl.md").write_text(
            """---
page_title: "Function: math"
subcategory: "Math"
---
# math
"""
        )
        components.append((PlatingBundle("math", math_dir, "function"), ComponentType.FUNCTION))

        grouped = group_components_by_capability(components)
        keys = list(grouped.keys())

        # None should be first (uncategorized)
        assert keys[0] is None, "Uncategorized (None) components should be first"
        # Math should be after
        assert keys[1] == "Math", "Math category should be after uncategorized"


# 🍽️📖🔚
