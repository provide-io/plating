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
