#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for PlatingDiscovery class using TDD approach."""

from pathlib import Path

from provide.testkit.mocking import MagicMock, patch

from plating.bundles import PlatingBundle
from plating.discovery import PlatingDiscovery


class TestPlatingDiscovery:
    """Test suite for PlatingDiscovery functionality."""

    def test_discovery_initialization(self):
        """Test that PlatingDiscovery requires package name."""
        discovery = PlatingDiscovery("pyvider.components")
        assert discovery.package_name == "pyvider.components"

        custom_discovery = PlatingDiscovery("custom.package")
        assert custom_discovery.package_name == "custom.package"

    @patch("plating.discovery.finder.importlib.util.find_spec")
    def test_discover_bundles_no_package(self, mock_find_spec):
        """Test discovery when package is not found."""
        mock_find_spec.return_value = None

        discovery = PlatingDiscovery("pyvider.components")
        bundles = discovery.discover_bundles()

        assert bundles == []
        mock_find_spec.assert_called_once_with("pyvider.components")

    @patch("plating.discovery.finder.importlib.util.find_spec")
    def test_discover_bundles_no_origin(self, mock_find_spec):
        """Test discovery when package spec has no origin."""
        mock_spec = MagicMock()
        mock_spec.origin = None
        mock_find_spec.return_value = mock_spec

        discovery = PlatingDiscovery("pyvider.components")
        bundles = discovery.discover_bundles()

        assert bundles == []

    @patch("plating.discovery.finder.importlib.util.find_spec")
    def test_discover_bundles_with_plating_dirs(self, mock_find_spec, tmp_path):
        """Test discovery finds .plating directories."""
        # Create test structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()

        # Create resources with plating directories
        resources_dir = package_dir / "resources"
        resources_dir.mkdir()

        resource1_plating = resources_dir / "resource1.plating"
        resource1_plating.mkdir()

        resource2_plating = resources_dir / "resource2.plating"
        resource2_plating.mkdir()

        # Create data source with plating
        data_sources_dir = package_dir / "data_sources"
        data_sources_dir.mkdir()

        data1_plating = data_sources_dir / "data1.plating"
        data1_plating.mkdir()

        # Create a file that should be ignored
        fake_plating_file = resources_dir / "fake.plating"
        fake_plating_file.write_text("not a directory")

        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec

        discovery = PlatingDiscovery("pyvider.components")
        bundles = discovery.discover_bundles()

        assert len(bundles) == 3
        bundle_names = [b.name for b in bundles]
        assert "resource1" in bundle_names
        assert "resource2" in bundle_names
        assert "data1" in bundle_names

    @patch("plating.discovery.finder.importlib.util.find_spec")
    def test_discover_bundles_with_component_type_filter(self, mock_find_spec, tmp_path):
        """Test discovery filters by component type."""
        # Create test structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()

        # Create resources
        resources_dir = package_dir / "resources"
        resources_dir.mkdir()
        resource_plating = resources_dir / "resource1.plating"
        resource_plating.mkdir()

        # Create data sources
        data_sources_dir = package_dir / "data_sources"
        data_sources_dir.mkdir()
        data_plating = data_sources_dir / "data1.plating"
        data_plating.mkdir()

        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec

        discovery = PlatingDiscovery("pyvider.components")

        # Test filtering for resources only
        resource_bundles = discovery.discover_bundles(component_type="resource")
        assert len(resource_bundles) == 1
        assert resource_bundles[0].component_type == "resource"

        # Test filtering for data sources only
        data_bundles = discovery.discover_bundles(component_type="data_source")
        assert len(data_bundles) == 1
        assert data_bundles[0].component_type == "data_source"

    def test_determine_component_type_from_path(self):
        """Test component type determination from path."""
        discovery = PlatingDiscovery("pyvider.components")

        # Test resource path
        resource_path = Path("/pkg/resources/test.plating")
        assert discovery._determine_component_type(resource_path) == "resource"

        # Test data source path
        data_path = Path("/pkg/data_sources/test.plating")
        assert discovery._determine_component_type(data_path) == "data_source"

        # Test function path
        func_path = Path("/pkg/functions/test.plating")
        assert discovery._determine_component_type(func_path) == "function"

        # Test unknown path defaults to resource
        unknown_path = Path("/pkg/unknown/test.plating")
        assert discovery._determine_component_type(unknown_path) == "resource"

    @patch("plating.discovery.finder.importlib.util.find_spec")
    def test_discover_multi_component_bundles(self, mock_find_spec, tmp_path):
        """Test discovery of multi-component bundles (subdirectories in .plating)."""
        # Create test structure with multi-component bundle
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()

        # Create a multi-component plating directory
        multi_plating = package_dir / "multi.plating"
        multi_plating.mkdir()

        # Add subdirectories for different component types
        resource_dir = multi_plating / "resource"
        resource_dir.mkdir()
        (resource_dir / "docs").mkdir()

        data_dir = multi_plating / "data_source"
        data_dir.mkdir()
        (data_dir / "docs").mkdir()

        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec

        discovery = PlatingDiscovery("pyvider.components")
        bundles = discovery.discover_bundles()

        # Should find 2 bundles (one for each subdirectory)
        assert len(bundles) == 2

        # Check that both component types are found
        component_types = {b.component_type for b in bundles}
        assert "resource" in component_types
        assert "data_source" in component_types

    @patch("plating.discovery.finder.importlib.util.find_spec")
    def test_discover_bundles_creates_correct_bundle_objects(self, mock_find_spec, tmp_path):
        """Test that discovered bundles have correct attributes."""
        # Create test structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()

        resources_dir = package_dir / "resources"
        resources_dir.mkdir()

        test_plating = resources_dir / "test_resource.plating"
        test_plating.mkdir()

        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec

        discovery = PlatingDiscovery("pyvider.components")
        bundles = discovery.discover_bundles()

        assert len(bundles) == 1
        bundle = bundles[0]

        assert isinstance(bundle, PlatingBundle)
        assert bundle.name == "test_resource"
        assert bundle.plating_dir == test_plating
        assert bundle.component_type == "resource"

    @patch("plating.discovery.finder.importlib.util.find_spec")
    def test_discover_bundles_recursive_search(self, mock_find_spec, tmp_path):
        """Test that discovery searches recursively for .plating directories."""
        # Create nested structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()

        # Create deeply nested plating directory
        deep_dir = package_dir / "providers" / "aws" / "resources"
        deep_dir.mkdir(parents=True)

        deep_plating = deep_dir / "instance.plating"
        deep_plating.mkdir()

        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec

        discovery = PlatingDiscovery("pyvider.components")
        bundles = discovery.discover_bundles()

        assert len(bundles) == 1
        assert bundles[0].name == "instance"

    @patch("plating.discovery.finder.importlib.util.find_spec")
    def test_discover_bundles_ignores_hidden_directories(self, mock_find_spec, tmp_path):
        """Test that discovery ignores hidden .plating directories."""
        # Create test structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()

        # Create regular plating
        regular_plating = package_dir / "regular.plating"
        regular_plating.mkdir()

        # Create hidden plating (should be ignored)
        hidden_plating = package_dir / ".hidden.plating"
        hidden_plating.mkdir()

        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec

        discovery = PlatingDiscovery("pyvider.components")
        bundles = discovery.discover_bundles()

        assert len(bundles) == 1
        assert bundles[0].name == "regular"

    def test_discovery_empty_result_is_list(self):
        """Test that discovery always returns a list, even when empty."""
        discovery = PlatingDiscovery(package_name="non.existent.package")
        bundles = discovery.discover_bundles()

        assert isinstance(bundles, list)
        assert len(bundles) == 0

# 🍽️📖🔚
