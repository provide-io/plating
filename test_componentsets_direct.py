#!/usr/bin/env python3
"""Direct test for ComponentSets functionality without full plating imports."""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import only what we need directly
from attrs import define, field, validators
from provide.foundation import logger

# Import component_sets directly without going through __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "component_sets", 
    os.path.join(os.path.dirname(__file__), "src", "plating", "component_sets.py")
)
component_sets = importlib.util.module_from_spec(spec)
sys.modules["component_sets"] = component_sets
spec.loader.exec_module(component_sets)

ComponentSet = component_sets.ComponentSet
ComponentReference = component_sets.ComponentReference

def test_component_reference():
    """Test ComponentReference basic functionality."""
    print("Testing ComponentReference...")
    
    ref = ComponentReference("s3_bucket", "resource")
    assert ref.name == "s3_bucket"
    assert ref.component_type == "resource"
    assert str(ref) == "resource/s3_bucket"
    
    # Test equality
    ref2 = ComponentReference("s3_bucket", "resource")
    assert ref == ref2
    
    # Test hash
    assert hash(ref) == hash(ref2)
    
    print("✅ ComponentReference test passed")

def test_component_set_creation():
    """Test ComponentSet creation and basic operations."""
    print("Testing ComponentSet creation...")
    
    # Create components
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("s3_bucket", "data_source")
    
    # Create set
    comp_set = ComponentSet(
        name="aws_storage",
        description="AWS storage components",
        components={"terraform": [ref1, ref2]},
        tags={"aws", "storage"}
    )
    
    assert comp_set.name == "aws_storage"
    assert comp_set.description == "AWS storage components"
    assert comp_set.total_component_count() == 2
    assert comp_set.has_domain("terraform")
    assert not comp_set.has_domain("kubernetes")
    assert comp_set.has_tag("aws")
    assert comp_set.has_tag("storage")
    assert comp_set.version == "1.0.0"  # default
    
    print("✅ ComponentSet creation test passed")

def test_component_set_operations():
    """Test ComponentSet domain and component operations."""
    print("Testing ComponentSet operations...")
    
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("ec2_instance", "resource")
    
    comp_set = ComponentSet(name="test_set")
    
    # Test adding components
    comp_set.add_component("terraform", ref1)
    comp_set.add_component("terraform", ref2)
    comp_set.add_component("kubernetes", ref1)
    
    assert comp_set.total_component_count() == 3
    assert len(comp_set.filter_by_domain("terraform")) == 2
    assert len(comp_set.filter_by_domain("kubernetes")) == 1
    
    # Test get_domains
    domains = comp_set.get_domains()
    assert "terraform" in domains
    assert "kubernetes" in domains
    
    # Test removing components
    removed = comp_set.remove_component("terraform", ref1)
    assert removed is True
    assert len(comp_set.filter_by_domain("terraform")) == 1
    
    print("✅ ComponentSet operations test passed")

def test_component_set_union():
    """Test ComponentSet union operation."""
    print("Testing ComponentSet union...")
    
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("ec2_instance", "resource")
    ref3 = ComponentReference("rds_instance", "resource")
    
    set1 = ComponentSet(
        name="set1",
        components={"terraform": [ref1, ref2]},
        tags={"aws", "compute"}
    )
    
    set2 = ComponentSet(
        name="set2", 
        components={
            "terraform": [ref2, ref3],
            "kubernetes": [ref1]
        },
        tags={"aws", "database"}
    )
    
    # Test union
    union_set = set1.union(set2)
    assert union_set.name == "set1_union_set2"
    assert union_set.total_component_count() == 4  # ref1, ref2, ref3 in terraform + ref1 in kubernetes
    assert len(union_set.filter_by_domain("terraform")) == 3  # ref1, ref2, ref3
    assert len(union_set.filter_by_domain("kubernetes")) == 1  # ref1
    assert union_set.has_tag("aws")
    assert union_set.has_tag("compute")
    assert union_set.has_tag("database")
    
    print("✅ ComponentSet union test passed")

def test_component_set_intersection():
    """Test ComponentSet intersection operation."""
    print("Testing ComponentSet intersection...")
    
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("ec2_instance", "resource")
    ref3 = ComponentReference("rds_instance", "resource")
    
    set1 = ComponentSet(
        name="set1",
        components={"terraform": [ref1, ref2]},
        tags={"aws", "compute", "common"}
    )
    
    set2 = ComponentSet(
        name="set2", 
        components={"terraform": [ref1, ref3]},
        tags={"aws", "storage", "common"}
    )
    
    # Test intersection
    intersection_set = set1.intersection(set2)
    assert intersection_set.name == "set1_intersection_set2"
    assert intersection_set.total_component_count() == 1  # only ref1 is common
    terraform_components = intersection_set.filter_by_domain("terraform")
    assert len(terraform_components) == 1
    assert terraform_components[0] == ref1
    assert intersection_set.has_tag("aws")
    assert intersection_set.has_tag("common")
    assert not intersection_set.has_tag("compute")  # not in both sets
    assert not intersection_set.has_tag("storage")  # not in both sets
    
    print("✅ ComponentSet intersection test passed")

def test_component_set_difference():
    """Test ComponentSet difference operation."""
    print("Testing ComponentSet difference...")
    
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("ec2_instance", "resource")
    ref3 = ComponentReference("rds_instance", "resource")
    
    set1 = ComponentSet(
        name="set1",
        components={"terraform": [ref1, ref2, ref3]},
        tags={"aws", "unique", "shared"}
    )
    
    set2 = ComponentSet(
        name="set2", 
        components={"terraform": [ref2]},  # Only ref2 is shared
        tags={"aws", "shared"}
    )
    
    # Test difference
    diff_set = set1.difference(set2)
    assert diff_set.name == "set1_difference_set2"
    assert diff_set.total_component_count() == 2  # ref1 and ref3 (not ref2)
    terraform_components = diff_set.filter_by_domain("terraform")
    assert len(terraform_components) == 2
    assert ref1 in terraform_components
    assert ref3 in terraform_components
    assert ref2 not in terraform_components
    assert diff_set.has_tag("unique")  # unique to set1
    assert not diff_set.has_tag("shared")  # common to both sets
    
    print("✅ ComponentSet difference test passed")

def test_component_set_serialization():
    """Test ComponentSet serialization and deserialization."""
    print("Testing ComponentSet serialization...")
    
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("ec2_instance", "resource")
    
    original_set = ComponentSet(
        name="test_set",
        description="Test serialization",
        components={
            "terraform": [ref1],
            "kubernetes": [ref2]
        },
        tags={"test", "serialization"},
        version="1.5.0",
        metadata={"created_by": "test", "priority": "high"}
    )
    
    # Test to_dict
    dict_data = original_set.to_dict()
    assert dict_data["name"] == "test_set"
    assert dict_data["version"] == "1.5.0"
    assert set(dict_data["tags"]) == {"test", "serialization"}
    assert dict_data["metadata"]["created_by"] == "test"
    assert len(dict_data["components"]["terraform"]) == 1
    assert len(dict_data["components"]["kubernetes"]) == 1
    
    # Test from_dict
    loaded_set = ComponentSet.from_dict(dict_data)
    assert loaded_set.name == original_set.name
    assert loaded_set.version == original_set.version
    assert loaded_set.tags == original_set.tags
    assert loaded_set.metadata == original_set.metadata
    assert loaded_set.total_component_count() == 2
    
    # Test JSON round trip
    json_data = original_set.to_json()
    json_loaded_set = ComponentSet.from_json(json_data)
    assert json_loaded_set.name == original_set.name
    assert json_loaded_set.tags == original_set.tags
    
    print("✅ ComponentSet serialization test passed")

def test_component_set_validation():
    """Test ComponentSet validation logic."""
    print("Testing ComponentSet validation...")
    
    # Test empty name validation
    try:
        ComponentSet(name="")
        assert False, "Should have raised ValueError for empty name"
    except ValueError as e:
        assert "Length of 'name' must be >= 1" in str(e)
    
    # Test invalid version validation
    try:
        ComponentSet(name="test", version="invalid.version.format.too.many")
        assert False, "Should have raised ValueError for invalid version"
    except ValueError as e:
        assert "Invalid version format" in str(e)
    
    # Test duplicate component validation
    ref = ComponentReference("s3_bucket", "resource")
    try:
        ComponentSet(
            name="test",
            components={"terraform": [ref, ref]}  # Same component twice
        )
        assert False, "Should have raised ValueError for duplicate components"
    except ValueError as e:
        assert "Duplicate component" in str(e)
    
    print("✅ ComponentSet validation test passed")

def test_component_set_file_operations():
    """Test ComponentSet file save/load operations."""
    print("Testing ComponentSet file operations...")
    
    ref1 = ComponentReference("s3_bucket", "resource")
    
    original_set = ComponentSet(
        name="file_test_set",
        description="Test file operations",
        components={"terraform": [ref1]},
        tags={"test", "file"},
        version="2.0.0"
    )
    
    # Test save to file
    test_file = Path("/tmp/test_component_set.json")
    original_set.save_to_file(test_file)
    assert test_file.exists()
    
    # Test load from file
    loaded_set = ComponentSet.load_from_file(test_file)
    assert loaded_set.name == original_set.name
    assert loaded_set.version == original_set.version
    assert loaded_set.tags == original_set.tags
    assert loaded_set.total_component_count() == 1
    
    # Clean up
    test_file.unlink()
    
    print("✅ ComponentSet file operations test passed")

def test_component_set_advanced_queries():
    """Test ComponentSet advanced query methods."""
    print("Testing ComponentSet advanced queries...")
    
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("s3_bucket", "data_source")  # Same name, different type
    ref3 = ComponentReference("ec2_instance", "resource")
    
    comp_set = ComponentSet(
        name="query_test",
        components={
            "terraform": [ref1, ref2],
            "kubernetes": [ref3]
        },
        tags={"test", "query"}
    )
    
    # Test get_component_by_name
    s3_components = comp_set.get_component_by_name("s3_bucket")
    assert len(s3_components) == 2
    assert ref1 in s3_components
    assert ref2 in s3_components
    
    # Test get_component_by_name with domain filter
    terraform_s3 = comp_set.get_component_by_name("s3_bucket", "terraform")
    assert len(terraform_s3) == 2
    
    kubernetes_s3 = comp_set.get_component_by_name("s3_bucket", "kubernetes")
    assert len(kubernetes_s3) == 0
    
    # Test has_component
    assert comp_set.has_component(ref1)
    assert comp_set.has_component(ref1, "terraform")
    assert not comp_set.has_component(ref1, "kubernetes")
    
    # Test tag operations
    comp_set.add_tag("new_tag")
    assert comp_set.has_tag("new_tag")
    
    removed = comp_set.remove_tag("new_tag")
    assert removed is True
    assert not comp_set.has_tag("new_tag")
    
    print("✅ ComponentSet advanced queries test passed")

def run_all_tests():
    """Run all ComponentSets tests."""
    print("🧪 Running comprehensive ComponentSets tests...\n")
    
    try:
        test_component_reference()
        test_component_set_creation()
        test_component_set_operations()
        test_component_set_union()
        test_component_set_intersection()
        test_component_set_difference()
        test_component_set_serialization()
        test_component_set_validation()
        test_component_set_file_operations()
        test_component_set_advanced_queries()
        
        print("\n🎉 All ComponentSets tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)