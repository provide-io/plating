#
# plating/component_sets.py
#
"""ComponentSets for grouping related components across domains."""

import json
import re
from pathlib import Path
from typing import Any

from attrs import define, field, validators
from provide.foundation import logger


@define(frozen=True, slots=True)
class ComponentReference:
    """Reference to a component by name and type."""
    name: str = field(validator=validators.instance_of(str))
    component_type: str = field(validator=validators.instance_of(str))
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.component_type}/{self.name}"
    
    def __hash__(self) -> int:
        """Make hashable for use in sets."""
        return hash((self.name, self.component_type))


@define
class ComponentSet:
    """Collection of related components across domains."""
    
    name: str = field(validator=[
        validators.instance_of(str),
        validators.min_len(1)
    ])
    description: str = field(default="", validator=validators.instance_of(str))
    components: dict[str, list[ComponentReference]] = field(factory=dict)
    metadata: dict[str, Any] = field(factory=dict)
    tags: set[str] = field(factory=set, converter=set)
    version: str = field(default="1.0.0", validator=validators.instance_of(str))
    dependencies: list[str] = field(factory=list)
    
    def __attrs_post_init__(self):
        """Post-initialization validation."""
        self._validate()
    
    def _validate(self):
        """Validate ComponentSet structure."""
        if not self.name:
            raise ValueError("Component set name cannot be empty")
        
        # Validate version format (simple semver check)
        version_pattern = r'^\d+\.\d+\.\d+$'
        if not re.match(version_pattern, self.version):
            raise ValueError(f"Invalid version format: {self.version}")
        
        # Validate components structure
        for domain, component_list in self.components.items():
            if not isinstance(component_list, list):
                raise TypeError(f"Components for domain '{domain}' must be a list")
            
            seen_components = set()
            for comp in component_list:
                if not isinstance(comp, ComponentReference):
                    raise TypeError("Components must be ComponentReference instances")
                
                comp_key = (comp.name, comp.component_type)
                if comp_key in seen_components:
                    raise ValueError(f"Duplicate component {comp} in domain '{domain}'")
                seen_components.add(comp_key)
    
    def add_component(self, domain: str, component: ComponentReference) -> None:
        """Add a component to the specified domain."""
        if domain not in self.components:
            self.components[domain] = []
        
        # Check for duplicates
        comp_key = (component.name, component.component_type)
        existing_keys = {(c.name, c.component_type) for c in self.components[domain]}
        if comp_key in existing_keys:
            logger.warning(f"Component {component} already exists in domain '{domain}'")
            return
        
        self.components[domain].append(component)
        logger.debug(f"Added component {component} to set '{self.name}' domain '{domain}'")
    
    def remove_component(self, domain: str, component: ComponentReference) -> bool:
        """Remove a component from the specified domain."""
        if domain not in self.components:
            return False
        
        try:
            self.components[domain].remove(component)
            logger.debug(f"Removed component {component} from set '{self.name}' domain '{domain}'")
            return True
        except ValueError:
            logger.warning(f"Component {component} not found in domain '{domain}'")
            return False
    
    def filter_by_domain(self, domain: str) -> list[ComponentReference]:
        """Get all components for a specific domain."""
        return self.components.get(domain, []).copy()
    
    def get_domains(self) -> set[str]:
        """Get all domains in this component set."""
        return set(self.components.keys())
    
    def has_domain(self, domain: str) -> bool:
        """Check if the set has components in the specified domain."""
        return domain in self.components and len(self.components[domain]) > 0
    
    def is_empty(self) -> bool:
        """Check if the component set has no components."""
        return all(len(components) == 0 for components in self.components.values())
    
    def total_component_count(self) -> int:
        """Get total number of components across all domains."""
        return sum(len(components) for components in self.components.values())
    
    def union(self, other: "ComponentSet") -> "ComponentSet":
        """Create a new ComponentSet that is the union of this and another set."""
        union_name = f"{self.name}_union_{other.name}"
        union_components = {}
        
        # Combine components from both sets
        all_domains = self.get_domains().union(other.get_domains())
        for domain in all_domains:
            self_components = set(self.filter_by_domain(domain))
            other_components = set(other.filter_by_domain(domain))
            union_components[domain] = list(self_components.union(other_components))
        
        return ComponentSet(
            name=union_name,
            description=f"Union of {self.name} and {other.name}",
            components=union_components,
            tags=self.tags.union(other.tags),
            metadata={**self.metadata, **other.metadata},
            version="1.0.0"  # New version for combined set
        )
    
    def intersection(self, other: "ComponentSet") -> "ComponentSet":
        """Create a new ComponentSet that is the intersection of this and another set."""
        intersection_name = f"{self.name}_intersection_{other.name}"
        intersection_components = {}
        
        # Find common domains and components
        common_domains = self.get_domains().intersection(other.get_domains())
        for domain in common_domains:
            self_components = set(self.filter_by_domain(domain))
            other_components = set(other.filter_by_domain(domain))
            common_components = self_components.intersection(other_components)
            if common_components:
                intersection_components[domain] = list(common_components)
        
        return ComponentSet(
            name=intersection_name,
            description=f"Intersection of {self.name} and {other.name}",
            components=intersection_components,
            tags=self.tags.intersection(other.tags),
            version="1.0.0"
        )
    
    def difference(self, other: "ComponentSet") -> "ComponentSet":
        """Create a new ComponentSet with components in this set but not in other."""
        difference_name = f"{self.name}_difference_{other.name}"
        difference_components = {}
        
        # Find components in self but not in other
        for domain in self.get_domains():
            self_components = set(self.filter_by_domain(domain))
            other_components = set(other.filter_by_domain(domain))
            diff_components = self_components.difference(other_components)
            if diff_components:
                difference_components[domain] = list(diff_components)
        
        # Tags that are unique to self
        unique_tags = self.tags.difference(other.tags)
        
        return ComponentSet(
            name=difference_name,
            description=f"Components in {self.name} but not in {other.name}",
            components=difference_components,
            tags=unique_tags,
            version="1.0.0"
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        components_dict = {}
        for domain, component_list in self.components.items():
            components_dict[domain] = [
                {"name": comp.name, "component_type": comp.component_type}
                for comp in component_list
            ]
        
        return {
            "name": self.name,
            "description": self.description,
            "components": components_dict,
            "metadata": self.metadata,
            "tags": sorted(list(self.tags)),  # Convert to list for JSON serialization
            "version": self.version,
            "dependencies": self.dependencies,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentSet":
        """Create ComponentSet from dictionary."""
        components = {}
        for domain, component_list in data.get("components", {}).items():
            components[domain] = [
                ComponentReference(comp["name"], comp["component_type"])
                for comp in component_list
            ]
        
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            components=components,
            metadata=data.get("metadata", {}),
            tags=set(data.get("tags", [])),
            version=data.get("version", "1.0.0"),
            dependencies=data.get("dependencies", [])
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> "ComponentSet":
        """Create ComponentSet from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, path: Path) -> None:
        """Save ComponentSet to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())
        logger.info(f"Saved ComponentSet '{self.name}' to {path}")
    
    @classmethod
    def load_from_file(cls, path: Path) -> "ComponentSet":
        """Load ComponentSet from file."""
        if not path.exists():
            raise FileNotFoundError(f"ComponentSet file not found: {path}")
        
        json_content = path.read_text()
        comp_set = cls.from_json(json_content)
        logger.info(f"Loaded ComponentSet '{comp_set.name}' from {path}")
        return comp_set
    
    def get_component_by_name(self, name: str, domain: str = None) -> list[ComponentReference]:
        """Find components by name, optionally filtered by domain."""
        matches = []
        
        domains_to_search = [domain] if domain else self.get_domains()
        
        for search_domain in domains_to_search:
            for component in self.filter_by_domain(search_domain):
                if component.name == name:
                    matches.append(component)
        
        return matches
    
    def has_component(self, component: ComponentReference, domain: str = None) -> bool:
        """Check if the set contains a specific component."""
        domains_to_check = [domain] if domain else self.get_domains()
        
        for check_domain in domains_to_check:
            if component in self.filter_by_domain(check_domain):
                return True
        
        return False
    
    def merge_metadata(self, other_metadata: dict[str, Any]) -> None:
        """Merge additional metadata into this set."""
        self.metadata.update(other_metadata)
        logger.debug(f"Merged metadata into ComponentSet '{self.name}'")
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the component set."""
        self.tags.add(tag)
        logger.debug(f"Added tag '{tag}' to ComponentSet '{self.name}'")
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the component set."""
        try:
            self.tags.remove(tag)
            logger.debug(f"Removed tag '{tag}' from ComponentSet '{self.name}'")
            return True
        except KeyError:
            logger.warning(f"Tag '{tag}' not found in ComponentSet '{self.name}'")
            return False
    
    def has_tag(self, tag: str) -> bool:
        """Check if the component set has a specific tag."""
        return tag in self.tags


# 📦🔗✨⚡