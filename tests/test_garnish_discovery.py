"""
Unit tests for GarnishDiscovery class using TDD approach.
"""
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from garnish.garnish import GarnishDiscovery, GarnishBundle


class TestGarnishDiscovery:
    """Test suite for GarnishDiscovery functionality."""

    def test_discovery_initialization(self):
        """Test that GarnishDiscovery can be initialized with package name."""
        discovery = GarnishDiscovery()
        assert discovery.package_name == "pyvider.components"
        
        custom_discovery = GarnishDiscovery(package_name="custom.package")
        assert custom_discovery.package_name == "custom.package"

    @patch("garnish.garnish.importlib.util.find_spec")
    def test_discover_bundles_no_package(self, mock_find_spec):
        """Test discovery when package is not found."""
        mock_find_spec.return_value = None
        
        discovery = GarnishDiscovery()
        bundles = discovery.discover_bundles()
        
        assert bundles == []
        mock_find_spec.assert_called_once_with("pyvider.components")

    @patch("garnish.garnish.importlib.util.find_spec")
    def test_discover_bundles_no_origin(self, mock_find_spec):
        """Test discovery when package spec has no origin."""
        mock_spec = MagicMock()
        mock_spec.origin = None
        mock_find_spec.return_value = mock_spec
        
        discovery = GarnishDiscovery()
        bundles = discovery.discover_bundles()
        
        assert bundles == []

    @patch("garnish.garnish.importlib.util.find_spec")
    def test_discover_bundles_with_garnish_dirs(self, mock_find_spec, tmp_path):
        """Test discovery finds .garnish directories."""
        # Create test structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()
        
        # Create resources with garnish directories
        resources_dir = package_dir / "resources"
        resources_dir.mkdir()
        
        resource1_garnish = resources_dir / "resource1.garnish"
        resource1_garnish.mkdir()
        
        resource2_garnish = resources_dir / "resource2.garnish"
        resource2_garnish.mkdir()
        
        # Create data source with garnish
        data_sources_dir = package_dir / "data_sources"
        data_sources_dir.mkdir()
        
        data1_garnish = data_sources_dir / "data1.garnish"
        data1_garnish.mkdir()
        
        # Create a file that should be ignored
        fake_garnish_file = resources_dir / "fake.garnish"
        fake_garnish_file.write_text("not a directory")
        
        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec
        
        discovery = GarnishDiscovery()
        bundles = discovery.discover_bundles()
        
        assert len(bundles) == 3
        bundle_names = [b.name for b in bundles]
        assert "resource1" in bundle_names
        assert "resource2" in bundle_names
        assert "data1" in bundle_names

    @patch("garnish.garnish.importlib.util.find_spec")
    def test_discover_bundles_with_component_type_filter(self, mock_find_spec, tmp_path):
        """Test discovery filters by component type."""
        # Create test structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()
        
        # Create resources
        resources_dir = package_dir / "resources"
        resources_dir.mkdir()
        resource_garnish = resources_dir / "resource1.garnish"
        resource_garnish.mkdir()
        
        # Create data sources
        data_sources_dir = package_dir / "data_sources"
        data_sources_dir.mkdir()
        data_garnish = data_sources_dir / "data1.garnish"
        data_garnish.mkdir()
        
        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec
        
        discovery = GarnishDiscovery()
        
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
        discovery = GarnishDiscovery()
        
        # Test resource path
        resource_path = Path("/pkg/resources/test.garnish")
        assert discovery._determine_component_type(resource_path) == "resource"
        
        # Test data source path
        data_path = Path("/pkg/data_sources/test.garnish")
        assert discovery._determine_component_type(data_path) == "data_source"
        
        # Test function path
        func_path = Path("/pkg/functions/test.garnish")
        assert discovery._determine_component_type(func_path) == "function"
        
        # Test unknown path defaults to resource
        unknown_path = Path("/pkg/unknown/test.garnish")
        assert discovery._determine_component_type(unknown_path) == "resource"

    @patch("garnish.garnish.importlib.util.find_spec")
    def test_discover_multi_component_bundles(self, mock_find_spec, tmp_path):
        """Test discovery of multi-component bundles (subdirectories in .garnish)."""
        # Create test structure with multi-component bundle
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()
        
        # Create a multi-component garnish directory
        multi_garnish = package_dir / "multi.garnish"
        multi_garnish.mkdir()
        
        # Add subdirectories for different component types
        resource_dir = multi_garnish / "resource"
        resource_dir.mkdir()
        (resource_dir / "docs").mkdir()
        
        data_dir = multi_garnish / "data_source"
        data_dir.mkdir()
        (data_dir / "docs").mkdir()
        
        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec
        
        discovery = GarnishDiscovery()
        bundles = discovery.discover_bundles()
        
        # Should find 2 bundles (one for each subdirectory)
        assert len(bundles) == 2
        
        # Check that both component types are found
        component_types = {b.component_type for b in bundles}
        assert "resource" in component_types
        assert "data_source" in component_types

    @patch("garnish.garnish.importlib.util.find_spec")
    def test_discover_bundles_creates_correct_bundle_objects(self, mock_find_spec, tmp_path):
        """Test that discovered bundles have correct attributes."""
        # Create test structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()
        
        resources_dir = package_dir / "resources"
        resources_dir.mkdir()
        
        test_garnish = resources_dir / "test_resource.garnish"
        test_garnish.mkdir()
        
        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec
        
        discovery = GarnishDiscovery()
        bundles = discovery.discover_bundles()
        
        assert len(bundles) == 1
        bundle = bundles[0]
        
        assert isinstance(bundle, GarnishBundle)
        assert bundle.name == "test_resource"
        assert bundle.garnish_dir == test_garnish
        assert bundle.component_type == "resource"

    @patch("garnish.garnish.importlib.util.find_spec")
    def test_discover_bundles_recursive_search(self, mock_find_spec, tmp_path):
        """Test that discovery searches recursively for .garnish directories."""
        # Create nested structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()
        
        # Create deeply nested garnish directory
        deep_dir = package_dir / "providers" / "aws" / "resources"
        deep_dir.mkdir(parents=True)
        
        deep_garnish = deep_dir / "instance.garnish"
        deep_garnish.mkdir()
        
        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec
        
        discovery = GarnishDiscovery()
        bundles = discovery.discover_bundles()
        
        assert len(bundles) == 1
        assert bundles[0].name == "instance"

    @patch("garnish.garnish.importlib.util.find_spec")
    def test_discover_bundles_ignores_hidden_directories(self, mock_find_spec, tmp_path):
        """Test that discovery ignores hidden .garnish directories."""
        # Create test structure
        package_dir = tmp_path / "test_package"
        package_dir.mkdir()
        
        # Create regular garnish
        regular_garnish = package_dir / "regular.garnish"
        regular_garnish.mkdir()
        
        # Create hidden garnish (should be ignored)
        hidden_garnish = package_dir / ".hidden.garnish"
        hidden_garnish.mkdir()
        
        # Mock the spec
        mock_spec = MagicMock()
        mock_spec.origin = str(package_dir / "__init__.py")
        mock_find_spec.return_value = mock_spec
        
        discovery = GarnishDiscovery()
        bundles = discovery.discover_bundles()
        
        assert len(bundles) == 1
        assert bundles[0].name == "regular"

    def test_discovery_empty_result_is_list(self):
        """Test that discovery always returns a list, even when empty."""
        discovery = GarnishDiscovery(package_name="non.existent.package")
        bundles = discovery.discover_bundles()
        
        assert isinstance(bundles, list)
        assert len(bundles) == 0