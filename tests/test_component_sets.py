#
# tests/test_component_sets.py
#
"""Tests for ComponentSets functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from provide.foundation.testing import TempDir

from plating.component_sets import ComponentSet, ComponentReference
from plating.registry import PlatingRegistry
from plating.types import ComponentType
from plating.plating import PlatingBundle


@pytest.fixture
def temp_dir():
    """Temporary directory for tests."""
    return TempDir()


@pytest.fixture
def mock_bundle():
    """Mock PlatingBundle for testing."""
    bundle = Mock(spec=PlatingBundle)
    bundle.name = "s3_bucket"
    bundle.component_type = "resource"
    bundle.plating_dir = Path("/mock/s3_bucket.plating")
    bundle.has_main_template.return_value = True
    bundle.has_examples.return_value = True
    return bundle


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
        assert result["tags"] == ["test"]  # Converted to list for JSON
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


class TestRegistryComponentSetIntegration:
    """Test Registry integration with ComponentSets."""
    
    @pytest.fixture
    def registry(self):
        """Test registry."""
        return PlatingRegistry("test.package")
    
    def test_register_component_set(self, registry, sample_components):
        """Test registering a ComponentSet."""
        comp_set = ComponentSet(
            name="aws_storage",
            components={"terraform": sample_components}
        )
        
        registry.register_set(comp_set)
        
        retrieved_set = registry.get_set("aws_storage")
        assert retrieved_set is not None
        assert retrieved_set.name == "aws_storage"
    
    def test_list_component_sets(self, registry, sample_components):
        """Test listing registered ComponentSets."""
        set1 = ComponentSet(name="set1", tags={"aws"})
        set2 = ComponentSet(name="set2", tags={"kubernetes"})
        
        registry.register_set(set1)
        registry.register_set(set2)
        
        all_sets = registry.list_sets()
        assert len(all_sets) == 2
        assert {s.name for s in all_sets} == {"set1", "set2"}
    
    def test_list_sets_by_tag(self, registry):
        """Test filtering ComponentSets by tag."""
        set1 = ComponentSet(name="set1", tags={"aws", "storage"})
        set2 = ComponentSet(name="set2", tags={"kubernetes", "storage"})
        set3 = ComponentSet(name="set3", tags={"aws", "compute"})
        
        registry.register_set(set1)
        registry.register_set(set2)
        registry.register_set(set3)
        
        storage_sets = registry.list_sets(tag="storage")
        aws_sets = registry.list_sets(tag="aws")
        
        assert len(storage_sets) == 2
        assert len(aws_sets) == 2
        assert {s.name for s in storage_sets} == {"set1", "set2"}
        assert {s.name for s in aws_sets} == {"set1", "set3"}
    
    def test_find_sets_containing_component(self, registry, sample_components):
        """Test finding sets that contain a specific component."""
        comp_ref = sample_components[0]  # s3_bucket resource
        
        set1 = ComponentSet(
            name="storage_set",
            components={"terraform": [comp_ref]}
        )
        set2 = ComponentSet(
            name="aws_set", 
            components={"terraform": [comp_ref, sample_components[1]]}
        )
        set3 = ComponentSet(
            name="other_set",
            components={"terraform": [sample_components[2]]}
        )
        
        registry.register_set(set1)
        registry.register_set(set2)
        registry.register_set(set3)
        
        containing_sets = registry.find_sets_containing(
            "s3_bucket", "resource", "terraform"
        )
        
        assert len(containing_sets) == 2
        assert {s.name for s in containing_sets} == {"storage_set", "aws_set"}
    
    def test_remove_component_set(self, registry):
        """Test removing a ComponentSet from registry."""
        comp_set = ComponentSet(name="test_set")
        
        registry.register_set(comp_set)
        assert registry.get_set("test_set") is not None
        
        registry.remove_set("test_set")
        assert registry.get_set("test_set") is None
    
    def test_get_set_stats(self, registry, sample_components):
        """Test getting statistics about ComponentSets."""
        set1 = ComponentSet(
            name="set1",
            components={
                "terraform": sample_components[:2],
                "kubernetes": sample_components[2:]
            },
            tags={"aws"}
        )
        set2 = ComponentSet(
            name="set2",
            components={"terraform": sample_components[1:3]},
            tags={"storage"}
        )
        
        registry.register_set(set1)
        registry.register_set(set2)
        
        stats = registry.get_set_stats()
        
        assert stats["total_sets"] == 2
        assert stats["total_components_in_sets"] >= 4
        assert "terraform" in stats["domains"]
        assert "kubernetes" in stats["domains"]


class TestComponentSetValidation:
    """Test ComponentSet validation logic."""
    
    def test_validate_empty_name(self):
        """Test validation fails for empty name."""
        with pytest.raises(ValueError, match="Component set name cannot be empty"):
            ComponentSet(name="")
    
    def test_validate_duplicate_components_in_domain(self):
        """Test validation catches duplicate components in same domain."""
        duplicate_ref = ComponentReference("s3_bucket", "resource")
        
        with pytest.raises(ValueError, match="Duplicate component"):
            ComponentSet(
                name="test_set",
                components={"terraform": [duplicate_ref, duplicate_ref]}
            )
    
    def test_validate_component_reference_types(self):
        """Test validation of component reference types."""
        with pytest.raises(TypeError, match="Components must be ComponentReference"):
            ComponentSet(
                name="test_set",
                components={"terraform": ["invalid_type"]}
            )
    
    def test_validate_version_format(self):
        """Test version format validation."""
        with pytest.raises(ValueError, match="Invalid version format"):
            ComponentSet(name="test_set", version="invalid.version.format.too.many.parts")


class TestComponentSetSerialization:
    """Test ComponentSet serialization and deserialization."""
    
    def test_save_and_load_component_set(self, temp_dir, sample_components):
        """Test saving and loading ComponentSet to/from file."""
        original_set = ComponentSet(
            name="test_set",
            description="Test set for serialization",
            components={"terraform": sample_components[:2]},
            tags={"test", "serialization"},
            version="1.5.0",
            metadata={"created_by": "test"}
        )
        
        # Save to file
        set_file = temp_dir.path / "test_set.json"
        original_set.save_to_file(set_file)
        
        # Load from file
        loaded_set = ComponentSet.load_from_file(set_file)
        
        assert loaded_set.name == original_set.name
        assert loaded_set.description == original_set.description
        assert loaded_set.version == original_set.version
        assert loaded_set.tags == original_set.tags
        assert loaded_set.metadata == original_set.metadata
        assert len(loaded_set.components["terraform"]) == 2
    
    def test_json_serialization_round_trip(self, sample_components):
        """Test JSON serialization round trip."""
        original_set = ComponentSet(
            name="json_test",
            components={"terraform": sample_components},
            tags={"json", "test"}
        )
        
        # Serialize to JSON
        json_data = original_set.to_json()
        
        # Deserialize from JSON
        loaded_set = ComponentSet.from_json(json_data)
        
        assert loaded_set.name == original_set.name
        assert loaded_set.tags == original_set.tags
        assert len(loaded_set.components["terraform"]) == len(sample_components)