#!/usr/bin/env python3
"""Test module import consistency after api.py → plating.py refactoring."""

import pytest


def test_backward_compatibility_via_init():
    """Test that old imports still work via __init__.py re-exports."""
    # These should work exactly as before
    from plating import Plating, plating

    # Verify they're accessible
    assert Plating is not None
    assert callable(plating)


def test_direct_module_imports():
    """Test that new module names work directly."""
    # New direct imports should work
    from plating.plating import Plating, plating

    # Verify they're accessible
    assert Plating is not None
    assert callable(plating)


def test_import_consistency():
    """Test that both import paths give the same objects."""
    from plating import Plating as old_class, plating as old_func
    from plating.plating import Plating as new_class, plating as new_func

    # Should be the exact same objects
    assert old_class is new_class
    assert old_func is new_func


def test_no_circular_imports():
    """Test that there are no circular import issues."""
    import plating
    import plating.plating

    # Should be able to access without issues
    assert hasattr(plating, 'Plating')
    assert hasattr(plating.plating, 'Plating')


def test_all_exports_accessible():
    """Test that __all__ includes expected exports."""
    import plating

    # Main package should have core exports
    expected_exports = [
        'Plating',
        'plating',
        'ComponentType',
        'PlatingContext',
        '__version__'
    ]

    for export in expected_exports:
        assert hasattr(plating, export), f"plating missing {export}"


def test_plating_class_functionality():
    """Test that the Plating class is properly accessible."""
    from plating import Plating
    from plating.types import PlatingContext

    # Should be able to create context and class
    context = PlatingContext(provider_name="test", log_level="INFO")
    plating_instance = Plating(context)

    # Should have expected methods
    assert hasattr(plating_instance, 'adorn')
    assert hasattr(plating_instance, 'plate')
    assert hasattr(plating_instance, 'validate')


def test_old_api_module_removed():
    """Test that the old api.py module is gone."""
    with pytest.raises(ModuleNotFoundError):
        import plating.api


if __name__ == "__main__":
    pytest.main([__file__])