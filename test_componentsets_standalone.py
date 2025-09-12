#!/usr/bin/env python3
"""Standalone test for ComponentSets functionality."""

import sys
sys.path.insert(0, "src")

from plating.component_sets import ComponentSet, ComponentReference

def test_component_reference():
    """Test ComponentReference basic functionality."""
    ref = ComponentReference("s3_bucket", "resource")
    assert ref.name == "s3_bucket"
    assert ref.component_type == "resource"
    assert str(ref) == "resource/s3_bucket"
    print("✅ ComponentReference test passed")

def test_component_set():
    """Test ComponentSet basic functionality."""
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
    assert comp_set.total_component_count() == 2
    assert comp_set.has_domain("terraform")
    assert not comp_set.has_domain("kubernetes")
    assert comp_set.has_tag("aws")
    
    # Test filtering
    terraform_components = comp_set.filter_by_domain("terraform")
    assert len(terraform_components) == 2
    
    print("✅ ComponentSet basic test passed")

def test_component_set_operations():
    """Test ComponentSet set operations."""
    # Create two sets
    ref1 = ComponentReference("s3_bucket", "resource")
    ref2 = ComponentReference("ec2_instance", "resource")
    ref3 = ComponentReference("rds_instance", "resource")
    
    set1 = ComponentSet(
        name="set1",
        components={"terraform": [ref1, ref2]},
        tags={"aws"}
    )
    
    set2 = ComponentSet(
        name="set2", 
        components={"terraform": [ref2, ref3]},
        tags={"aws", "database"}
    )
    
    # Test union
    union_set = set1.union(set2)
    assert union_set.total_component_count() == 3  # ref1, ref2, ref3
    assert union_set.has_tag("aws")
    assert union_set.has_tag("database")
    
    # Test intersection
    intersection_set = set1.intersection(set2)
    assert intersection_set.total_component_count() == 1  # ref2
    assert intersection_set.has_tag("aws")
    
    # Test difference
    diff_set = set1.difference(set2)
    assert diff_set.total_component_count() == 1  # ref1
    
    print("✅ ComponentSet operations test passed")

def test_component_set_serialization():
    """Test ComponentSet serialization."""
    ref1 = ComponentReference("s3_bucket", "resource")
    
    original_set = ComponentSet(
        name="test_set",
        description="Test serialization",
        components={"terraform": [ref1]},
        tags={"test"},
        version="1.5.0"
    )
    
    # Test JSON serialization
    json_data = original_set.to_json()
    loaded_set = ComponentSet.from_json(json_data)
    
    assert loaded_set.name == original_set.name
    assert loaded_set.version == original_set.version
    assert loaded_set.tags == original_set.tags
    assert loaded_set.total_component_count() == 1
    
    print("✅ ComponentSet serialization test passed")

if __name__ == "__main__":
    print("🧪 Running ComponentSets standalone tests...")
    
    test_component_reference()
    test_component_set()
    test_component_set_operations()
    test_component_set_serialization()
    
    print("\n🎉 All ComponentSets tests passed!")