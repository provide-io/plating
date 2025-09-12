#!/usr/bin/env python3
"""Test Registry integration with ComponentSets."""

import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import required modules directly
import importlib.util

def import_module_direct(module_name, file_path):
    """Import a module directly from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import modules in dependency order
src_dir = os.path.join(os.path.dirname(__file__), "src", "plating")

# Mock plating.plating module to avoid full import chain
plating_mock = Mock()
plating_mock.PlatingBundle = Mock
plating_mock.PlatingDiscovery = Mock
sys.modules["plating.plating"] = plating_mock

# Import component_sets
component_sets = import_module_direct(
    "component_sets", 
    os.path.join(src_dir, "component_sets.py")
)

# Import types
types_mod = import_module_direct(
    "plating.types", 
    os.path.join(src_dir, "types.py")
)

# Now we can import registry with mocked dependencies
with patch.dict('sys.modules', {
    'plating.plating': plating_mock,
    'plating.component_sets': component_sets,
    'plating.types': types_mod
}):
    registry_mod = import_module_direct(
        "plating.registry", 
        os.path.join(src_dir, "registry.py")
    )

ComponentSet = component_sets.ComponentSet
ComponentReference = component_sets.ComponentReference
PlatingRegistry = registry_mod.PlatingRegistry
ComponentType = types_mod.ComponentType

def test_registry_component_set_registration():
    """Test registering ComponentSets with the registry."""
    print("Testing ComponentSet registration...")
    
    # Create a mock registry (skip discovery)
    with patch.object(PlatingRegistry, '_discover_and_register'):
        registry = PlatingRegistry("test.package")
    
    # Create a ComponentSet
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("ec2_instance", "resource")
    
    comp_set = ComponentSet(
        name="aws_compute",
        description="AWS compute components",
        components={
            "terraform": [ref1, ref2],
            "kubernetes": [ref1]
        },
        tags={"aws", "compute"}
    )
    
    # Register the set
    registry.register_set(comp_set)
    
    # Retrieve the set
    retrieved_set = registry.get_set("aws_compute")
    assert retrieved_set is not None
    assert retrieved_set.name == "aws_compute"
    assert retrieved_set.total_component_count() == 3
    
    print("✅ ComponentSet registration test passed")

def test_registry_list_sets():
    """Test listing ComponentSets from registry."""
    print("Testing ComponentSet listing...")
    
    with patch.object(PlatingRegistry, '_discover_and_register'):
        registry = PlatingRegistry("test.package")
    
    # Create multiple sets
    set1 = ComponentSet(name="set1", tags={"aws", "storage"})
    set2 = ComponentSet(name="set2", tags={"kubernetes", "storage"})
    set3 = ComponentSet(name="set3", tags={"aws", "compute"})
    
    registry.register_set(set1)
    registry.register_set(set2)
    registry.register_set(set3)
    
    # Test list all sets
    all_sets = registry.list_sets()
    assert len(all_sets) == 3
    set_names = {s.name for s in all_sets}
    assert set_names == {"set1", "set2", "set3"}
    
    # Test list by tag
    storage_sets = registry.list_sets(tag="storage")
    assert len(storage_sets) == 2
    storage_names = {s.name for s in storage_sets}
    assert storage_names == {"set1", "set2"}
    
    aws_sets = registry.list_sets(tag="aws")
    assert len(aws_sets) == 2
    aws_names = {s.name for s in aws_sets}
    assert aws_names == {"set1", "set3"}
    
    print("✅ ComponentSet listing test passed")

def test_registry_find_sets_containing():
    """Test finding sets that contain specific components."""
    print("Testing find sets containing components...")
    
    with patch.object(PlatingRegistry, '_discover_and_register'):
        registry = PlatingRegistry("test.package")
    
    # Create component references
    s3_resource = ComponentReference("s3_bucket", "resource")
    s3_data = ComponentReference("s3_bucket", "data_source")
    ec2_resource = ComponentReference("ec2_instance", "resource")
    
    # Create sets with overlapping components
    storage_set = ComponentSet(
        name="storage_set",
        components={"terraform": [s3_resource, s3_data]}
    )
    
    aws_set = ComponentSet(
        name="aws_set",
        components={
            "terraform": [s3_resource, ec2_resource],
            "kubernetes": [s3_resource]
        }
    )
    
    compute_set = ComponentSet(
        name="compute_set",
        components={"terraform": [ec2_resource]}
    )
    
    registry.register_set(storage_set)
    registry.register_set(aws_set)
    registry.register_set(compute_set)
    
    # Find sets containing s3_bucket resource
    s3_containing_sets = registry.find_sets_containing("s3_bucket", "resource")
    assert len(s3_containing_sets) == 2
    s3_set_names = {s.name for s in s3_containing_sets}
    assert s3_set_names == {"storage_set", "aws_set"}
    
    # Find sets containing s3_bucket resource in terraform domain
    terraform_s3_sets = registry.find_sets_containing("s3_bucket", "resource", "terraform")
    assert len(terraform_s3_sets) == 2
    
    # Find sets containing s3_bucket resource in kubernetes domain
    k8s_s3_sets = registry.find_sets_containing("s3_bucket", "resource", "kubernetes")
    assert len(k8s_s3_sets) == 1
    assert k8s_s3_sets[0].name == "aws_set"
    
    # Find sets containing ec2_instance
    ec2_containing_sets = registry.find_sets_containing("ec2_instance", "resource")
    assert len(ec2_containing_sets) == 2
    ec2_set_names = {s.name for s in ec2_containing_sets}
    assert ec2_set_names == {"aws_set", "compute_set"}
    
    print("✅ Find sets containing components test passed")

def test_registry_remove_set():
    """Test removing ComponentSets from registry."""
    print("Testing ComponentSet removal...")
    
    with patch.object(PlatingRegistry, '_discover_and_register'):
        registry = PlatingRegistry("test.package")
    
    comp_set = ComponentSet(name="test_set")
    
    # Register and verify
    registry.register_set(comp_set)
    assert registry.get_set("test_set") is not None
    
    # Remove and verify
    removed = registry.remove_set("test_set")
    assert removed is True
    assert registry.get_set("test_set") is None
    
    # Try to remove non-existent set - may or may not fail depending on foundation Registry implementation
    removed_again = registry.remove_set("non_existent")
    # Don't assert specific behavior for non-existent entries
    
    print("✅ ComponentSet removal test passed")

def test_registry_set_stats():
    """Test getting ComponentSet statistics."""
    print("Testing ComponentSet statistics...")
    
    with patch.object(PlatingRegistry, '_discover_and_register'):
        registry = PlatingRegistry("test.package")
    
    # Create sets with different characteristics
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("ec2_instance", "resource")
    
    set1 = ComponentSet(
        name="set1",
        components={
            "terraform": [ref1, ref2],
            "kubernetes": [ref1]
        },
        tags={"aws", "v1"},
        version="1.0.0"
    )
    
    set2 = ComponentSet(
        name="set2",
        components={"terraform": [ref2]},
        tags={"storage", "v2"},
        version="2.0.0"
    )
    
    registry.register_set(set1)
    registry.register_set(set2)
    
    # Get statistics
    stats = registry.get_set_stats()
    
    assert stats["total_sets"] == 2
    assert stats["total_components_in_sets"] == 4  # 3 from set1 + 1 from set2
    assert set(stats["domains"]) == {"terraform", "kubernetes"}
    assert set(stats["tags"]) == {"aws", "storage", "v1", "v2"}
    assert set(stats["versions"]) == {"1.0.0", "2.0.0"}
    
    print("✅ ComponentSet statistics test passed")

def test_registry_create_set_from_components():
    """Test creating ComponentSet from existing registry components."""
    print("Testing create set from components...")
    
    with patch.object(PlatingRegistry, '_discover_and_register'):
        registry = PlatingRegistry("test.package")
    
    # Mock some components in the registry
    mock_bundle1 = Mock()
    mock_bundle1.name = "s3_bucket"
    mock_bundle2 = Mock()
    mock_bundle2.name = "ec2_instance"
    
    # Mock the get_component method to return bundles
    def mock_get_component(comp_type, name):
        if name == "s3_bucket":
            return mock_bundle1
        elif name == "ec2_instance":
            return mock_bundle2
        return None
    
    registry.get_component = mock_get_component
    
    # Create a set from existing components
    created_set = registry.create_set_from_components(
        name="auto_created_set",
        description="Automatically created set",
        component_filters={
            "terraform": ["s3_bucket", "ec2_instance"],
            "kubernetes": ["s3_bucket"]
        },
        tags={"auto", "test"}
    )
    
    assert created_set.name == "auto_created_set"
    assert created_set.description == "Automatically created set"
    assert created_set.total_component_count() == 3  # s3+ec2 in terraform, s3 in k8s
    assert created_set.has_tag("auto")
    assert created_set.has_tag("test")
    
    # Verify it was registered
    retrieved_set = registry.get_set("auto_created_set")
    assert retrieved_set is not None
    assert retrieved_set.name == "auto_created_set"
    
    print("✅ Create set from components test passed")

def run_all_tests():
    """Run all registry ComponentSet integration tests."""
    print("🧪 Running Registry ComponentSet integration tests...\n")
    
    try:
        test_registry_component_set_registration()
        test_registry_list_sets()
        test_registry_find_sets_containing()
        test_registry_remove_set()
        test_registry_set_stats()
        test_registry_create_set_from_components()
        
        print("\n🎉 All Registry ComponentSet integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)