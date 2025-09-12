#
# tests/test_component_sets_core.py
#
"""Core tests for ComponentSets functionality."""

from pathlib import Path

import pytest

from plating.component_sets import ComponentSet, ComponentReference


@pytest.fixture
def sample_components():
    """Sample component references for testing."""
    return [
        ComponentReference("s3_bucket", "resource"),
        ComponentReference("s3_bucket", "data_source"),
        ComponentReference("s3_bucket_policy", "resource"),
        ComponentReference("s3_access_point", "resource")
    ]


class TestComponentReference:
    """Test ComponentReference class."""
    
    def test_component_reference_creation(self):
        """Test creating a ComponentReference."""
        ref = ComponentReference("s3_bucket", "resource")
        assert ref.name == "s3_bucket"
        assert ref.component_type == "resource"
    
    def test_component_reference_equality(self):
        """Test ComponentReference equality."""
        ref1 = ComponentReference("s3_bucket", "resource")
        ref2 = ComponentReference("s3_bucket", "resource")
        ref3 = ComponentReference("s3_bucket", "data_source")
        
        assert ref1 == ref2
        assert ref1 != ref3
    
    def test_component_reference_hash(self):
        """Test ComponentReference is hashable."""
        ref = ComponentReference("s3_bucket", "resource")
        assert hash(ref) == hash((ref.name, ref.component_type))
    
    def test_component_reference_str(self):
        """Test ComponentReference string representation."""
        ref = ComponentReference("s3_bucket", "resource")
        assert str(ref) == "resource/s3_bucket"


class TestComponentSet:
    """Test ComponentSet class."""
    
    def test_component_set_creation(self, sample_components):
        """Test creating a ComponentSet."""
        comp_set = ComponentSet(
            name="aws_storage",
            description="AWS storage components",
            components={"terraform": sample_components[:2]},
            tags={"aws", "storage"}
        )
        
        assert comp_set.name == "aws_storage"
        assert comp_set.description == "AWS storage components"
        assert len(comp_set.components["terraform"]) == 2
        assert comp_set.tags == {"aws", "storage"}
        assert comp_set.version == "1.0.0"  # default
    
    def test_component_set_add_component(self):
        """Test adding components to a set."""
        comp_set = ComponentSet(name="test_set")
        ref = ComponentReference("s3_bucket", "resource")
        
        comp_set.add_component("terraform", ref)
        
        assert "terraform" in comp_set.components
        assert ref in comp_set.components["terraform"]
    
    def test_component_set_remove_component(self):
        """Test removing components from a set."""
        ref = ComponentReference("s3_bucket", "resource")
        comp_set = ComponentSet(
            name="test_set",
            components={"terraform": [ref]}
        )
        
        comp_set.remove_component("terraform", ref)
        
        assert len(comp_set.components["terraform"]) == 0
    
    def test_component_set_filter_by_domain(self, sample_components):
        """Test filtering components by domain."""
        comp_set = ComponentSet(
            name="test_set",
            components={
                "terraform": sample_components[:2],
                "kubernetes": sample_components[2:]
            }
        )
        
        terraform_components = comp_set.filter_by_domain("terraform")
        kubernetes_components = comp_set.filter_by_domain("kubernetes")
        
        assert len(terraform_components) == 2
        assert len(kubernetes_components) == 2
        assert terraform_components != kubernetes_components
    
    def test_component_set_get_domains(self, sample_components):
        """Test getting all domains in a set."""
        comp_set = ComponentSet(
            name="test_set",
            components={
                "terraform": sample_components[:2],
                "kubernetes": sample_components[2:],
                "cloudformation": []
            }
        )
        
        domains = comp_set.get_domains()
        
        assert domains == {"terraform", "kubernetes", "cloudformation"}
    
    def test_component_set_has_domain(self, sample_components):
        """Test checking if set has a domain."""
        comp_set = ComponentSet(
            name="test_set",
            components={"terraform": sample_components}
        )
        
        assert comp_set.has_domain("terraform")
        assert not comp_set.has_domain("kubernetes")
    
    def test_component_set_union(self, sample_components):
        """Test union of two component sets."""
        set1 = ComponentSet(
            name="set1",
            components={"terraform": sample_components[:2]},
            tags={"aws"}
        )
        set2 = ComponentSet(
            name="set2", 
            components={
                "terraform": sample_components[2:],
                "kubernetes": sample_components[:1]
            },
            tags={"storage"}
        )
        
        union_set = set1.union(set2)
        
        assert union_set.name == "set1_union_set2"
        assert len(union_set.components["terraform"]) == 4
        assert len(union_set.components["kubernetes"]) == 1
        assert union_set.tags == {"aws", "storage"}
    
    def test_component_set_intersection(self, sample_components):
        """Test intersection of two component sets."""
        shared_component = sample_components[0]
        
        set1 = ComponentSet(
            name="set1",
            components={"terraform": [shared_component, sample_components[1]]},
            tags={"aws", "common"}
        )
        set2 = ComponentSet(
            name="set2",
            components={"terraform": [shared_component, sample_components[2]]},
            tags={"storage", "common"}
        )
        
        intersection_set = set1.intersection(set2)
        
        assert intersection_set.name == "set1_intersection_set2"
        assert len(intersection_set.components["terraform"]) == 1
        assert shared_component in intersection_set.components["terraform"]
        assert intersection_set.tags == {"common"}
    
    def test_component_set_difference(self, sample_components):
        """Test difference of two component sets."""
        set1 = ComponentSet(
            name="set1",
            components={"terraform": sample_components[:3]},
            tags={"aws", "unique"}
        )
        set2 = ComponentSet(
            name="set2", 
            components={"terraform": sample_components[1:2]},
            tags={"aws", "shared"}
        )
        
        difference_set = set1.difference(set2)
        
        assert difference_set.name == "set1_difference_set2"
        assert len(difference_set.components["terraform"]) == 2
        assert sample_components[1] not in difference_set.components["terraform"]
        assert difference_set.tags == {"unique"}
    
    def test_component_set_is_empty(self):
        """Test checking if component set is empty."""
        empty_set = ComponentSet(name="empty")
        non_empty_set = ComponentSet(
            name="non_empty",
            components={"terraform": [ComponentReference("test", "resource")]}
        )
        
        assert empty_set.is_empty()
        assert not non_empty_set.is_empty()
    
    def test_component_set_total_component_count(self, sample_components):
        """Test getting total component count across domains."""
        comp_set = ComponentSet(
            name="test_set",
            components={
                "terraform": sample_components[:2],
                "kubernetes": sample_components[2:]
            }
        )
        
        assert comp_set.total_component_count() == 4
    
    def test_component_set_to_dict(self, sample_components):
        """Test converting ComponentSet to dictionary."""
        comp_set = ComponentSet(
            name="test_set",
            description="Test set",
            components={"terraform": sample_components[:1]},
            tags={"test"},
            version="2.0.0"
        )
        
        result = comp_set.to_dict()
        
        assert result["name"] == "test_set"
        assert result["description"] == "Test set"
        assert result["version"] == "2.0.0"
        assert set(result["tags"]) == {"test"}  # Converted to list for JSON
        assert "terraform" in result["components"]
    
    def test_component_set_from_dict(self):
        """Test creating ComponentSet from dictionary."""
        data = {
            "name": "test_set",
            "description": "Test description",
            "components": {
                "terraform": [
                    {"name": "s3_bucket", "component_type": "resource"}
                ]
            },
            "tags": ["test", "aws"],
            "version": "2.0.0",
            "metadata": {"env": "prod"}
        }
        
        comp_set = ComponentSet.from_dict(data)
        
        assert comp_set.name == "test_set"
        assert comp_set.description == "Test description"
        assert comp_set.version == "2.0.0"
        assert comp_set.tags == {"test", "aws"}
        assert comp_set.metadata["env"] == "prod"
        assert len(comp_set.components["terraform"]) == 1
    
    def test_component_set_serialization(self, sample_components):
        """Test ComponentSet JSON serialization."""
        original_set = ComponentSet(
            name="test_set",
            description="Test serialization",
            components={
                "terraform": sample_components[:1],
                "kubernetes": sample_components[1:2]
            },
            tags={"test", "serialization"},
            version="1.5.0",
            metadata={"created_by": "test"}
        )
        
        # Test to_json/from_json
        json_data = original_set.to_json()
        loaded_set = ComponentSet.from_json(json_data)
        
        assert loaded_set.name == original_set.name
        assert loaded_set.version == original_set.version
        assert loaded_set.tags == original_set.tags
        assert loaded_set.metadata == original_set.metadata
        assert loaded_set.total_component_count() == 2
    
    def test_component_set_file_operations(self, tmp_path):
        """Test ComponentSet file save/load operations."""
        ref1 = ComponentReference("s3_bucket", "resource")
        
        original_set = ComponentSet(
            name="file_test_set",
            description="Test file operations",
            components={"terraform": [ref1]},
            tags={"test", "file"},
            version="2.0.0"
        )
        
        # Test save to file
        test_file = tmp_path / "test_component_set.json"
        original_set.save_to_file(test_file)
        assert test_file.exists()
        
        # Test load from file
        loaded_set = ComponentSet.load_from_file(test_file)
        assert loaded_set.name == original_set.name
        assert loaded_set.version == original_set.version
        assert loaded_set.tags == original_set.tags
        assert loaded_set.total_component_count() == 1
    
    def test_component_set_advanced_queries(self, sample_components):
        """Test ComponentSet advanced query methods."""
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


class TestComponentSetValidation:
    """Test ComponentSet validation logic."""
    
    def test_validate_empty_name(self):
        """Test validation fails for empty name."""
        with pytest.raises(ValueError, match="Length of 'name' must be >= 1"):
            ComponentSet(name="")
    
    def test_validate_version_format(self):
        """Test version format validation."""
        with pytest.raises(ValueError, match="Invalid version format"):
            ComponentSet(name="test_set", version="invalid.version.format.too.many.parts")
    
    def test_validate_duplicate_components_in_domain(self):
        """Test validation catches duplicate components in same domain."""
        duplicate_ref = ComponentReference("s3_bucket", "resource")
        
        with pytest.raises(ValueError, match="Duplicate component"):
            ComponentSet(
                name="test_set",
                components={"terraform": [duplicate_ref, duplicate_ref]}
            )