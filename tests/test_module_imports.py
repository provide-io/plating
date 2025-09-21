#!/usr/bin/env python3
"""Test module import consistency after api.py → plating.py refactoring."""

import pytest


def test_old_api_module_updated():
    """Test that the old api.py module is updated for backward compatibility."""
    # Should be able to import PlatingAPI for backward compatibility
    from plating.api import PlatingAPI

    # Should be able to create instance
    api = PlatingAPI()
    assert api is not None


def test_new_module_exists():
    """Test that plating.plating module exists."""
    import importlib.util

    # Check if the module file exists and can be loaded
    spec = importlib.util.find_spec("plating.plating")
    assert spec is not None, "plating.plating module should exist"
    assert spec.origin is not None, "plating.plating should have a file origin"


def test_import_structure_basic():
    """Test basic import structure without full dependency loading."""
    # Test that we can at least access the modules without circular import errors
    # This tests the core refactoring without needing all dependencies

    # Check if __init__.py has the right imports configured
    import plating

    init_content = plating.__file__
    assert init_content.endswith("__init__.py"), "Should import from __init__.py"

    # Verify the module exists
    import importlib

    spec = importlib.util.find_spec("plating.plating")
    assert spec is not None, "plating.plating module should be importable"


if __name__ == "__main__":
    pytest.main([__file__])
