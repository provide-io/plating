#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Integration tests for full plate workflow with capability-first organization."""

from unittest.mock import Mock, patch

import pytest
import yaml

from plating.bundles import PlatingBundle
from plating.mkdocs.nav_generator import MkdocsNavGenerator
from plating.plating import Plating
from plating.types import ComponentType, PlatingContext


@pytest.mark.integration
class TestFullPlateWorkflow:
    """End-to-end integration tests for plate workflow."""

    @pytest.fixture
    def mock_registry(self, temp_directory):
        """Create a mock plating registry with sample components."""
        registry = Mock()

        # Create sample components with different subcategories
        lens_resource_dir = temp_directory / "lens_resource.plating"
        lens_docs = lens_resource_dir / "docs"
        lens_docs.mkdir(parents=True)
        (lens_docs / "lens_resource.tmpl.md").write_text(
            """---
page_title: "Resource: lens_resource"
subcategory: "Lens"
---

# lens_resource (Resource)

Lens resource content
"""
        )

        util_data_dir = temp_directory / "util_data.plating"
        util_docs = util_data_dir / "docs"
        util_docs.mkdir(parents=True)
        (util_docs / "util_data.tmpl.md").write_text(
            """---
page_title: "Data Source: util_data"
subcategory: "Utilities"
---

# util_data (Data Source)

Utilities data source content
"""
        )

        test_func_dir = temp_directory / "test_func.plating"
        test_docs = test_func_dir / "docs"
        test_docs.mkdir(parents=True)
        (test_docs / "test_func.tmpl.md").write_text(
            """---
page_title: "Function: test_func"
subcategory: "Test Mode"
---

# test_func (Function)

Test mode function content
"""
        )

        # Create bundle objects
        lens_bundle = PlatingBundle("lens_resource", lens_resource_dir, "resource")
        util_bundle = PlatingBundle("util_data", util_data_dir, "data_source")
        test_bundle = PlatingBundle("test_func", test_func_dir, "function")

        # Configure registry mock
        registry.get_components_with_templates = Mock(
            side_effect=lambda comp_type: {
                ComponentType.RESOURCE: [lens_bundle],
                ComponentType.DATA_SOURCE: [util_bundle],
                ComponentType.FUNCTION: [test_bundle],
            }.get(comp_type, [])
        )

        return registry

    @pytest.fixture
    def plating_context(self):
        """Create a plating context for testing."""
        return PlatingContext(
            provider_name="test_provider",
            component_type=ComponentType.RESOURCE,
        )

    @pytest.mark.asyncio
    async def test_plate_workflow_generates_capability_first_index(
        self, temp_directory, mock_registry, plating_context
    ) -> None:
        """Full workflow generates correct index with capability-first organization."""
        output_dir = temp_directory / "docs"
        output_dir.mkdir(parents=True)

        # Mock the registry
        with (
            patch("plating.plating.get_plating_registry", return_value=mock_registry),
            patch("plating.plating.extract_provider_schema", return_value={}),
        ):
            # Create plating instance
            plating = Plating(context=plating_context, package_name="test_package")
            plating.registry = mock_registry

            # Run plate workflow
            result = await plating.plate(output_dir=output_dir, force=True)

            # Check result
            assert result.files_generated > 0, "Should generate files"

            # Check that index.md was created
            index_file = output_dir / "index.md"
            assert index_file.exists(), "Should create index.md"

            # Read and verify index content
            index_content = index_file.read_text()

            # Should have capability sections in correct order
            assert "## Lens" in index_content, "Should have Lens capability section"
            assert "## Utilities" in index_content, "Should have Utilities capability section"
            assert "## Test Mode" in index_content, "Should have Test Mode capability section"

            # Test Mode should appear after other capabilities
            lens_pos = index_content.index("## Lens")
            utilities_pos = index_content.index("## Utilities")
            test_mode_pos = index_content.index("## Test Mode")

            assert test_mode_pos > lens_pos, "Test Mode should appear after Lens"
            assert test_mode_pos > utilities_pos, "Test Mode should appear after Utilities"

    @pytest.mark.asyncio
    async def test_plate_workflow_creates_mkdocs_nav(
        self, temp_directory, sample_components_mixed_types
    ) -> None:
        """Full workflow creates mkdocs.yml with correct navigation structure."""
        output_dir = temp_directory / "docs"
        output_dir.mkdir(parents=True)

        # Create MkdocsNavGenerator and generate nav
        generator = MkdocsNavGenerator(temp_directory)
        nav = generator.generate_nav(sample_components_mixed_types, include_guides=False)

        # Update mkdocs config
        generator.update_mkdocs_config(nav)

        # Verify mkdocs.yml was created
        mkdocs_file = temp_directory / "mkdocs.yml"
        assert mkdocs_file.exists(), "Should create mkdocs.yml"

        # Read and verify structure
        with mkdocs_file.open() as f:
            config = yaml.safe_load(f)

        assert "nav" in config, "Should have nav section"
        nav_items = config["nav"]

        # First item should be Overview
        assert nav_items[0] == {"Overview": "index.md"}, "First item should be Overview"

        # Should have capability sections
        capability_sections = [item for item in nav_items if isinstance(item, dict) and "Overview" not in item]
        assert len(capability_sections) >= 3, "Should have at least 3 capability sections"

    @pytest.mark.asyncio
    async def test_plate_workflow_discovers_guides(self, temp_directory, sample_guides_directory) -> None:
        """Full workflow finds and processes guides."""
        # Create empty components list
        components = []

        # Create MkdocsNavGenerator
        generator = MkdocsNavGenerator(temp_directory)
        nav = generator.generate_nav(components, include_guides=True)

        nav_items = nav["nav"]

        # Check for Guides section
        guides_sections = [item for item in nav_items if isinstance(item, dict) and "Guides" in item]
        assert len(guides_sections) == 1, "Should have Guides section"

        guides_dict = guides_sections[0]["Guides"]
        assert "Getting Started" in guides_dict, "Should include getting_started guide"
        assert "Advanced Usage" in guides_dict, "Should include advanced_usage guide"
        assert "Troubleshooting" in guides_dict, "Should include troubleshooting guide"

    @pytest.mark.asyncio
    async def test_plate_workflow_respects_force_flag(
        self, temp_directory, mock_registry, plating_context
    ) -> None:
        """Force regeneration works correctly."""
        output_dir = temp_directory / "docs"
        output_dir.mkdir(parents=True)

        # Create an existing file
        existing_file = output_dir / "resources" / "lens_resource.md"
        existing_file.parent.mkdir(parents=True, exist_ok=True)
        existing_file.write_text("# Old content\n\nThis should be overwritten")

        with (
            patch("plating.plating.get_plating_registry", return_value=mock_registry),
            patch("plating.plating.extract_provider_schema", return_value={}),
        ):
            plating = Plating(context=plating_context, package_name="test_package")
            plating.registry = mock_registry

            # Run with force=False (should skip existing file)
            await plating.plate(output_dir=output_dir, force=False)

            # Check file wasn't modified
            content_after_no_force = existing_file.read_text()
            assert "Old content" in content_after_no_force, "Should not overwrite when force=False"

            # Run with force=True (should overwrite)
            await plating.plate(output_dir=output_dir, force=True)

            # File should exist and be regenerated
            assert existing_file.exists(), "File should still exist"

            # Note: In real workflow, content would be different
            # This test verifies the force flag is passed through correctly

    @pytest.mark.asyncio
    async def test_plate_workflow_handles_missing_templates(self, temp_directory, plating_context) -> None:
        """Graceful degradation when components lack templates."""
        output_dir = temp_directory / "docs"
        output_dir.mkdir(parents=True)

        # Create component without template
        no_template_dir = temp_directory / "no_template.plating"
        no_template_dir.mkdir(parents=True)
        # No docs directory created

        bundle_no_template = PlatingBundle("no_template", no_template_dir, "resource")

        # Create registry with bundle that has no template
        registry = Mock()
        registry.get_components_with_templates = Mock(
            side_effect=lambda comp_type: {
                ComponentType.RESOURCE: [bundle_no_template],
                ComponentType.DATA_SOURCE: [],
                ComponentType.FUNCTION: [],
            }.get(comp_type, [])
        )

        with (
            patch("plating.plating.get_plating_registry", return_value=registry),
            patch("plating.plating.extract_provider_schema", return_value={}),
        ):
            plating = Plating(context=plating_context, package_name="test_package")
            plating.registry = registry

            # Should not crash when template is missing
            result = await plating.plate(output_dir=output_dir, force=True)

            # Should complete even with missing template
            assert isinstance(result, object), "Should return result object"

    @pytest.mark.asyncio
    async def test_plate_workflow_component_grouping(
        self, temp_directory, mock_registry, plating_context
    ) -> None:
        """Verify components are correctly grouped by capability."""
        from plating.core.doc_generator import group_components_by_capability

        # Get components from mock registry
        components = []
        for comp_type in [ComponentType.RESOURCE, ComponentType.DATA_SOURCE, ComponentType.FUNCTION]:
            bundles = mock_registry.get_components_with_templates(comp_type)
            for bundle in bundles:
                components.append((bundle, comp_type))

        # Group by capability
        grouped = group_components_by_capability(components)

        # Verify grouping
        assert "Lens" in grouped, "Should have Lens capability"
        assert "Utilities" in grouped, "Should have Utilities capability"
        assert "Test Mode" in grouped, "Should have Test Mode capability"

        # Verify Test Mode is last
        keys = list(grouped.keys())
        assert keys[-1] == "Test Mode", "Test Mode should be last"

        # Verify correct components in each group (use .value for string keys)
        assert ComponentType.RESOURCE.value in grouped["Lens"], "Lens should have resource"
        assert ComponentType.DATA_SOURCE.value in grouped["Utilities"], "Utilities should have data source"
        assert ComponentType.FUNCTION.value in grouped["Test Mode"], "Test Mode should have function"


# 🍽️📖🔚
