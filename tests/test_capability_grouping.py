#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test module for capability grouping functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from plating.bundles import PlatingBundle
from plating.core.doc_generator import (
    group_components_by_capability,
    _extract_subcategory_from_template,
    _determine_subcategory,
)
from plating.types import ComponentType, SchemaInfo


class TestCapabilityGrouping:
    """Test suite for capability grouping functionality."""

    def test_group_components_by_capability_basic(self, sample_components_mixed_types):
        """Test basic grouping by subcategory."""
        components = sample_components_mixed_types

        grouped = group_components_by_capability(components)

        # Should have 3 capabilities: Lens, Utilities, Test Mode
        assert len(grouped) == 3, "Should group into 3 capabilities"
        assert "Lens" in grouped, "Should have Lens capability"
        assert "Utilities" in grouped, "Should have Utilities capability"
        assert "Test Mode" in grouped, "Should have Test Mode capability"

        # Check Lens has resource
        assert ComponentType.RESOURCE in grouped["Lens"]
        assert len(grouped["Lens"][ComponentType.RESOURCE]) == 1

        # Check Test Mode has data source
        assert ComponentType.DATA_SOURCE in grouped["Test Mode"]
        assert len(grouped["Test Mode"][ComponentType.DATA_SOURCE]) == 1

        # Check Utilities has function
        assert ComponentType.FUNCTION in grouped["Utilities"]
        assert len(grouped["Utilities"][ComponentType.FUNCTION]) == 1

    def test_group_components_by_capability_test_mode_last(self, temp_directory):
        """Verify Test Mode always appears last in ordering."""
        from plating.bundles import PlatingBundle
        from plating.types import ComponentType

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

    def test_group_components_by_capability_mixed_types(self, temp_directory):
        """Test with resources, data sources, and functions."""
        from plating.bundles import PlatingBundle
        from plating.types import ComponentType

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

    def test_extract_subcategory_from_template_with_subcategory(self, sample_component_with_subcategory):
        """Extract existing subcategory from template."""
        component = sample_component_with_subcategory

        subcategory = _extract_subcategory_from_template(component)

        assert subcategory == "Lens", "Should extract 'Lens' subcategory from template"

    def test_extract_subcategory_from_template_missing_subcategory(self, sample_component_no_subcategory):
        """Return None when subcategory is not present."""
        component = sample_component_no_subcategory

        subcategory = _extract_subcategory_from_template(component)

        assert subcategory is None, "Should return None when subcategory not present"

    def test_extract_subcategory_from_template_malformed_frontmatter(self, temp_directory):
        """Handle malformed templates gracefully."""
        from plating.bundles import PlatingBundle

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

    def test_determine_subcategory_test_only_components(self):
        """Test Mode detection for test_only components."""
        # Test with is_test_only=True
        subcategory = _determine_subcategory(schema_info=None, is_test_only=True)
        assert subcategory == "Test Mode", "Should return 'Test Mode' for test_only components"

        # Test with schema_info.test_only=True
        schema_info = SchemaInfo(test_only=True)
        subcategory = _determine_subcategory(schema_info=schema_info, is_test_only=False)
        assert subcategory == "Test Mode", "Should return 'Test Mode' from schema_info"

    def test_determine_subcategory_lens_components(self):
        """Lens subcategory detection."""
        # Test with component_of parameter
        subcategory = _determine_subcategory(schema_info=None, is_test_only=False, component_of="lens")
        assert subcategory == "Lens", "Should return 'Lens' for component_of='lens'"

        # Test with schema_info.component_of
        schema_info = SchemaInfo(component_of="lens")
        subcategory = _determine_subcategory(schema_info=schema_info, is_test_only=False)
        assert subcategory == "Lens", "Should return 'Lens' from schema_info.component_of"

        # Test that component_of parameter takes precedence
        schema_info = SchemaInfo(component_of="other")
        subcategory = _determine_subcategory(schema_info=schema_info, is_test_only=False, component_of="lens")
        assert subcategory == "Lens", "component_of parameter should take precedence over schema_info"

    def test_determine_subcategory_default_utilities(self):
        """Default to Utilities when no special metadata present."""
        subcategory = _determine_subcategory(schema_info=None, is_test_only=False)
        assert subcategory == "Utilities", "Should default to 'Utilities'"

        # Test with schema_info but no special fields
        schema_info = SchemaInfo(description="Regular component")
        subcategory = _determine_subcategory(schema_info=schema_info, is_test_only=False)
        assert subcategory == "Utilities", "Should default to 'Utilities' with regular schema_info"


# 🍽️📖🔚
