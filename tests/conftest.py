#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Centralized test configuration and fixtures using provide-testkit."""

from pathlib import Path

from provide.testkit.mocking import ANY, AsyncMock, MagicMock, Mock, PropertyMock, call, patch
import pytest

# Import testkit utilities from specific modules
try:
    from provide.testkit import mock_logger, reset_foundation_setup_for_testing

    TESTKIT_AVAILABLE = True
except ImportError:
    TESTKIT_AVAILABLE = False

    # Fallback implementations
    def reset_foundation_setup_for_testing() -> None:
        pass

    def mock_logger():
        return Mock()


# Import file fixtures from testkit file module
try:
    from provide.testkit.file import (
        empty_directory,
        nested_directory_structure,
        temp_directory,
        temp_file,
        test_files_structure,
    )
except ImportError:
    # Fallback to pytest's tmp_path
    @pytest.fixture
    def temp_directory(tmp_path):
        return tmp_path

    @pytest.fixture
    def test_files_structure(tmp_path):
        return tmp_path, tmp_path

    nested_directory_structure = temp_directory
    empty_directory = temp_directory
    temp_file = temp_directory

# Import mocking fixtures
try:
    from provide.testkit.mocking import (
        async_mock_factory,
        auto_patch,
        magic_mock_factory,
        mock_factory,
        mock_open_fixture,
        patch_fixture,
        property_mock_factory,
    )
except ImportError:
    # Fallback implementations
    @pytest.fixture
    def mock_factory():
        def _create_mock(name=None, **kwargs):
            return Mock(name=name, **kwargs)

        return _create_mock

    @pytest.fixture
    def magic_mock_factory():
        def _create_magic_mock(name=None, **kwargs):
            return MagicMock(name=name, **kwargs)

        return _create_magic_mock

    @pytest.fixture
    def async_mock_factory():
        def _create_async_mock(name=None, **kwargs):
            return AsyncMock(name=name, **kwargs)

        return _create_async_mock

    @pytest.fixture
    def property_mock_factory():
        def _create_property_mock(**kwargs):
            return PropertyMock(**kwargs)

        return _create_property_mock

    @pytest.fixture
    def patch_fixture():
        patches = []

        def _patch(target, **kwargs):
            patcher = patch(target, **kwargs)
            mock = patcher.start()
            patches.append(patcher)
            return mock

        yield _patch
        for patcher in patches:
            patcher.stop()

    auto_patch = patch_fixture

    @pytest.fixture
    def mock_open_fixture():
        from unittest.mock import mock_open

        return lambda read_data=None: mock_open(read_data=read_data)


def pytest_configure(config) -> None:
    """Register custom marks."""
    config.addinivalue_line("markers", "tdd: marks tests as TDD (test-driven development)")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "requires_textual: marks tests that require Textual app context")
    config.addinivalue_line("markers", "skip_in_ci: marks tests to skip in CI environments")


@pytest.fixture(autouse=True)
def foundation_test_setup():
    """
    Reset foundation state before and after each test.

    This ensures proper test isolation for foundation components
    like logging, registries, and other global state.
    """
    reset_foundation_setup_for_testing()
    yield
    reset_foundation_setup_for_testing()


@pytest.fixture
def plating_bundle_structure(temp_directory):
    """
    Create standard .plating bundle structure for testing.

    Creates:
        test.plating/
        ├── docs/
        │   ├── main.md.j2
        │   └── partial.md.j2
        └── examples/
            ├── basic.tf
            └── fixtures/
                └── variables.tf

    Returns:
        Path to the plating bundle directory
    """
    plating_dir = temp_directory / "test.plating"

    # Create directory structure
    docs_dir = plating_dir / "docs"
    examples_dir = plating_dir / "examples"
    fixtures_dir = examples_dir / "fixtures"

    docs_dir.mkdir(parents=True)
    examples_dir.mkdir(parents=True)
    fixtures_dir.mkdir(parents=True)

    # Create template files
    (docs_dir / "main.md.j2").write_text("# {{ name }}\n\n{{ description }}")
    (docs_dir / "partial.md.j2").write_text("## {{ title }}\n{{ content }}")

    # Create example files
    (examples_dir / "basic.tf").write_text('resource "test" "example" {\n  name = "test"\n}')
    (fixtures_dir / "variables.tf").write_text('variable "name" {\n  type = string\n}')

    return plating_dir


@pytest.fixture
def mock_plating_bundle():
    """Create a mock PlatingBundle for testing."""
    bundle = Mock(name="PlatingBundle")
    bundle.name = "test_resource"
    bundle.component_type = "resource"
    bundle.plating_dir = "/tmp/test.plating"
    bundle.docs_dir = "/tmp/test.plating/docs"
    bundle.examples_dir = "/tmp/test.plating/examples"
    bundle.has_main_template.return_value = True
    bundle.has_examples.return_value = True
    bundle.load_examples.return_value = ["example content"]
    return bundle


@pytest.fixture
def mock_foundation_hub():
    """Create a mock foundation Hub for testing."""
    hub = Mock(name="Hub")
    hub.discover_components = Mock(return_value=None)
    hub.list_components = Mock(return_value=[])
    hub.get_component = Mock(return_value=None)
    return hub


@pytest.fixture
def mock_component_class():
    """Create a mock component class with documentation."""
    component = Mock(name="ComponentClass")
    component.__doc__ = "Test component documentation\nMore details here"
    component.__module__ = "test.module"
    component.__name__ = "TestComponent"
    return component


@pytest.fixture
def mock_generator():
    """Create a mock DocsGenerator for schema testing."""
    generator = Mock(name="DocsGenerator")
    generator.provider_name = "test_provider"
    generator.provider_dir = Path("/test/provider")  # Use Path object, not string
    # Add dictionary-like attributes that SchemaProcessor expects to assign to
    generator.resources = {}
    generator.data_sources = {}
    generator.functions = {}
    generator.provider_info = None
    return generator


@pytest.fixture
def sample_component_with_subcategory(temp_directory):
    """Create a sample PlatingBundle with subcategory in frontmatter."""
    from plating.bundles import PlatingBundle

    plating_dir = temp_directory / "test_resource.plating"
    docs_dir = plating_dir / "docs"
    docs_dir.mkdir(parents=True)

    # Create template with subcategory
    template_content = """---
page_title: "Resource: test_resource"
description: |-
  Test resource
subcategory: "Lens"
---

# test_resource (Resource)

Test resource content
"""
    (docs_dir / "test_resource.tmpl.md").write_text(template_content)

    return PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")


@pytest.fixture
def sample_component_no_subcategory(temp_directory):
    """Create a sample PlatingBundle without subcategory."""
    from plating.bundles import PlatingBundle

    plating_dir = temp_directory / "test_data.plating"
    docs_dir = plating_dir / "docs"
    docs_dir.mkdir(parents=True)

    # Create template without subcategory
    template_content = """---
page_title: "Data Source: test_data"
description: |-
  Test data source
---

# test_data (Data Source)

Test data source content
"""
    (docs_dir / "test_data.tmpl.md").write_text(template_content)

    return PlatingBundle(name="test_data", plating_dir=plating_dir, component_type="data_source")


@pytest.fixture
def sample_components_mixed_types(temp_directory):
    """Create multiple PlatingBundles with different types and subcategories."""
    from plating.bundles import PlatingBundle
    from plating.types import ComponentType

    components = []

    # Resource with Lens subcategory
    resource_dir = temp_directory / "lens_resource.plating"
    resource_docs = resource_dir / "docs"
    resource_docs.mkdir(parents=True)
    (resource_docs / "lens_resource.tmpl.md").write_text(
        """---
subcategory: "Lens"
---
# Lens Resource
"""
    )
    components.append((PlatingBundle("lens_resource", resource_dir, "resource"), ComponentType.RESOURCE))

    # Data source with Test Mode subcategory
    data_dir = temp_directory / "test_data.plating"
    data_docs = data_dir / "docs"
    data_docs.mkdir(parents=True)
    (data_docs / "test_data.tmpl.md").write_text(
        """---
subcategory: "Test Mode"
---
# Test Data Source
"""
    )
    components.append((PlatingBundle("test_data", data_dir, "data_source"), ComponentType.DATA_SOURCE))

    # Function with Utilities (default)
    func_dir = temp_directory / "util_func.plating"
    func_docs = func_dir / "docs"
    func_docs.mkdir(parents=True)
    (func_docs / "util_func.tmpl.md").write_text(
        """---
subcategory: "Utilities"
---
# Utility Function
"""
    )
    components.append((PlatingBundle("util_func", func_dir, "function"), ComponentType.FUNCTION))

    return components


@pytest.fixture
def mock_mkdocs_config(temp_directory):
    """Create a temporary mkdocs.yml file."""
    import yaml

    mkdocs_file = temp_directory / "mkdocs.yml"
    config = {
        "site_name": "Test Provider",
        "theme": {"name": "material"},
        "nav": [{"Home": "index.md"}],
    }
    with open(mkdocs_file, "w") as f:
        yaml.dump(config, f)

    return mkdocs_file


@pytest.fixture
def sample_guides_directory(temp_directory):
    """Create a sample guides directory with markdown files."""
    guides_dir = temp_directory / "docs" / "guides"
    guides_dir.mkdir(parents=True)

    # Create guide files
    (guides_dir / "getting_started.md").write_text("# Getting Started\n\nGuide content")
    (guides_dir / "advanced_usage.md").write_text("# Advanced Usage\n\nAdvanced guide")
    (guides_dir / "troubleshooting.md").write_text("# Troubleshooting\n\nTroubleshooting guide")
    (guides_dir / "README.txt").write_text("Not a markdown file")

    return guides_dir


@pytest.fixture
def sample_template_with_frontmatter():
    """Sample template content with YAML frontmatter."""
    return """---
page_title: "Resource: test_resource"
description: |-
  Test resource description
---

# test_resource (Resource)

Content here
"""


@pytest.fixture
def sample_template_without_frontmatter():
    """Sample template content without YAML frontmatter."""
    return """# test_resource (Resource)

Content without frontmatter
"""


# Re-export all testkit utilities for easy access in tests
__all__ = [
    # Mock objects
    "ANY",
    "AsyncMock",
    "MagicMock",
    "Mock",
    "PropertyMock",
    "async_mock_factory",
    "auto_patch",
    "call",
    "empty_directory",
    # Foundation utilities
    "foundation_test_setup",
    "magic_mock_factory",
    "mock_component_class",
    # Mocking utilities
    "mock_factory",
    "mock_foundation_hub",
    "mock_generator",
    "mock_logger",
    "mock_open_fixture",
    "mock_plating_bundle",
    "nested_directory_structure",
    "patch",
    "patch_fixture",
    # Plating-specific fixtures
    "plating_bundle_structure",
    "property_mock_factory",
    # File fixtures
    "temp_directory",
    "temp_file",
    "test_files_structure",
]

# 🍽️📖🔚
