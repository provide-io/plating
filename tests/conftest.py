#
# tests/conftest.py
#
"""Centralized test configuration and fixtures using provide-testkit."""

import pytest
from provide.testkit import (
    # Foundation test utilities
    reset_foundation_setup_for_testing,
    mock_logger,
    # File and directory fixtures
    temp_directory,
    test_files_structure,
    nested_directory_structure,
    empty_directory,
    temp_file,
    temp_file_with_content,
    temp_binary_file,
    temp_named_file,
    # Mocking utilities
    mock_factory,
    magic_mock_factory,
    async_mock_factory,
    property_mock_factory,
    patch_fixture,
    auto_patch,
    mock_open_fixture,
    # Common utilities
    ANY,
    AsyncMock,
    MagicMock,
    Mock,
    PropertyMock,
    call,
    patch,
)


def pytest_configure(config):
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
def mock_plating_bundle(mock_factory):
    """Create a mock PlatingBundle for testing."""
    bundle = mock_factory("PlatingBundle")
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
def mock_foundation_hub(mock_factory):
    """Create a mock foundation Hub for testing."""
    hub = mock_factory("Hub")
    hub.discover_components = Mock(return_value=None)
    hub.list_components = Mock(return_value=[])
    hub.get_component = Mock(return_value=None)
    return hub


@pytest.fixture 
def mock_component_class(mock_factory):
    """Create a mock component class with documentation."""
    component = mock_factory("ComponentClass")
    component.__doc__ = "Test component documentation\nMore details here"
    component.__module__ = "test.module"
    component.__name__ = "TestComponent"
    return component


@pytest.fixture
def mock_generator(mock_factory):
    """Create a mock DocsGenerator for schema testing."""
    generator = mock_factory("DocsGenerator")
    generator.provider_name = "test_provider"
    generator.provider_dir = "/test/provider"
    return generator


# Re-export all testkit utilities for easy access in tests
__all__ = [
    # Foundation utilities
    "foundation_test_setup",
    "mock_logger",
    # File fixtures
    "temp_directory", 
    "test_files_structure",
    "nested_directory_structure",
    "empty_directory",
    "temp_file",
    "temp_file_with_content",
    "temp_binary_file",
    "temp_named_file",
    # Plating-specific fixtures
    "plating_bundle_structure",
    "mock_plating_bundle",
    "mock_foundation_hub",
    "mock_component_class",
    "mock_generator",
    # Mocking utilities
    "mock_factory",
    "magic_mock_factory", 
    "async_mock_factory",
    "property_mock_factory",
    "patch_fixture",
    "auto_patch",
    "mock_open_fixture",
    # Mock objects
    "ANY",
    "AsyncMock",
    "MagicMock",
    "Mock",
    "PropertyMock",
    "call",
    "patch",
]


# 🧪🏗️✨🎯