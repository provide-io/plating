#
# plating/registry.py
#
"""Component registry using foundation patterns."""

from pathlib import Path
from typing import Any

from provide.foundation import Registry, RegistryEntry, logger
from provide.foundation.resilience import RetryPolicy, BackoffStrategy, RetryExecutor

from .plating import PlatingBundle, PlatingDiscovery
from .types import ComponentType


class PlatingRegistryEntry(RegistryEntry):
    """Registry entry for plating bundles."""
    
    def __init__(self, bundle: PlatingBundle, dimension: str):
        """Initialize entry from bundle."""
        super().__init__(
            name=bundle.name,
            dimension=dimension,
            value=bundle,
            metadata={
                "path": str(bundle.plating_dir),
                "component_type": bundle.component_type,
                "has_template": bundle.has_main_template(),
                "has_examples": bundle.has_examples(),
            }
        )
    
    @property
    def bundle(self) -> PlatingBundle:
        """Get the PlatingBundle from this entry."""
        return self.value



class PlatingRegistry(Registry):
    """Component registry using foundation Registry pattern with ComponentSet support."""
    
    def __init__(self, package_name: str = "pyvider.components"):
        """Initialize registry with package discovery.
        
        Args:
            package_name: Package to search for plating bundles
        """
        super().__init__()
        self.package_name = package_name
        
        # Foundation resilience for discovery
        self._retry_policy = RetryPolicy(
            max_attempts=3,
            backoff=BackoffStrategy.EXPONENTIAL,
            base_delay=0.5,
            max_delay=5.0,
            retryable_errors=(OSError, ImportError, AttributeError)
        )
        self._retry_executor = RetryExecutor(self._retry_policy)
        
        # Initialize discovery with error handling
        try:
            self._discovery = PlatingDiscovery(package_name)
            # Auto-discover on initialization
            self._discover_and_register()
        except Exception as e:
            logger.error(f"Failed to initialize discovery for {package_name}: {e}")
            # Set discovery to None so we can still create the registry
            self._discovery = None
    
    def _discover_and_register(self) -> None:
        """Discover and register all components using foundation patterns."""
        if not self._discovery:
            logger.warning("Discovery not initialized, skipping component registration")
            return
            
        try:
            bundles = self._retry_executor.execute_sync(
                self._discovery.discover_bundles
            )
            
            logger.info(f"Discovered {len(bundles)} plating bundles")
            
            for bundle in bundles:
                entry = PlatingRegistryEntry(bundle, dimension=bundle.component_type)
                self.register(
                    name=bundle.name,
                    dimension=bundle.component_type,  # "resource", "data_source", etc.
                    value=entry
                )
                logger.debug(f"Registered {bundle.component_type}/{bundle.name}")
                
        except Exception as e:
            logger.error(f"Failed to discover bundles: {e}")
            raise
    
    def get_components(self, component_type: ComponentType) -> list[PlatingBundle]:
        """Get all components of a specific type.
        
        Args:
            component_type: The component type to filter by
            
        Returns:
            List of PlatingBundle objects
        """
        names = self.list_dimension(component_type.value)
        entries = []
        for name in names:
            entry = self.get_entry(name=name, dimension=component_type.value)
            if entry:
                entries.append(entry)
        return [entry.value.bundle for entry in entries]
    
    def get_component(self, component_type: ComponentType, name: str) -> PlatingBundle | None:
        """Get a specific component by type and name.
        
        Args:
            component_type: The component type
            name: The component name
            
        Returns:
            PlatingBundle if found, None otherwise
        """
        entry = self.get_entry(name=name, dimension=component_type.value)
        return entry.value.bundle if entry else None
    
    def get_components_with_templates(self, component_type: ComponentType) -> list[PlatingBundle]:
        """Get components of a type that have templates.
        
        Args:
            component_type: The component type to filter by
            
        Returns:
            List of PlatingBundle objects with templates
        """
        components = self.get_components(component_type)
        return [bundle for bundle in components if bundle.has_main_template()]
    
    def get_components_with_examples(self, component_type: ComponentType) -> list[PlatingBundle]:
        """Get components of a type that have examples.
        
        Args:
            component_type: The component type to filter by
            
        Returns:
            List of PlatingBundle objects with examples
        """
        components = self.get_components(component_type)
        return [bundle for bundle in components if bundle.has_examples()]
    
    def get_all_component_types(self) -> list[ComponentType]:
        """Get all registered component types.
        
        Returns:
            List of ComponentType enums found in registry
        """
        dimensions = self.list_all().keys()
        component_types = []
        
        for dimension in dimensions:
            try:
                comp_type = ComponentType(dimension)
                component_types.append(comp_type)
            except ValueError:
                # Skip unknown component types
                pass
                
        return component_types
    
    def refresh(self) -> None:
        """Refresh the registry by re-discovering components."""
        logger.info("Refreshing plating registry")
        self.clear()
        self._discover_and_register()
    
    def get_registry_stats(self) -> dict[str, Any]:
        """Get statistics about the registry contents.
        
        Returns:
            Dictionary with registry statistics
        """
        stats = {}
        all_names = self.list_all()
        
        stats["total_components"] = sum(len(names) for names in all_names.values())
        stats["component_types"] = list(all_names.keys())
        
        for comp_type, names in all_names.items():
            stats[f"{comp_type}_count"] = len(names)
            
            # Get actual entries to access metadata
            entries = []
            for name in names:
                entry = self.get_entry(name=name, dimension=comp_type)
                if entry:
                    entries.append(entry)
            
            # Count bundles with templates/examples
            bundles_with_templates = sum(
                1 for entry in entries 
                if entry.value.metadata.get("has_template", False)
            )
            bundles_with_examples = sum(
                1 for entry in entries
                if entry.value.metadata.get("has_examples", False)
            )
            
            stats[f"{comp_type}_with_templates"] = bundles_with_templates
            stats[f"{comp_type}_with_examples"] = bundles_with_examples
            
        return stats
    
    def register_set(self, component_set: ComponentSet) -> None:
        """Register a ComponentSet in the registry.
        
        Args:
            component_set: The ComponentSet to register
        """
        entry = ComponentSetRegistryEntry(component_set)
        self.register(
            name=component_set.name,
            dimension="component_sets",
            value=entry
        )
        logger.info(f"Registered ComponentSet '{component_set.name}' with {component_set.total_component_count()} components")
    
    def get_set(self, name: str) -> ComponentSet | None:
        """Get a ComponentSet by name.
        
        Args:
            name: Name of the ComponentSet
            
        Returns:
            ComponentSet if found, None otherwise
        """
        entry = self.get_entry(name=name, dimension="component_sets")
        return entry.value.component_set if entry else None
    
    def list_sets(self, tag: str | None = None) -> list[ComponentSet]:
        """List all registered ComponentSets, optionally filtered by tag.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            List of ComponentSet objects
        """
        set_names = self.list_dimension("component_sets")
        component_sets = []
        
        for name in set_names:
            entry = self.get_entry(name=name, dimension="component_sets")
            if entry:
                comp_set = entry.value.component_set
                if tag is None or comp_set.has_tag(tag):
                    component_sets.append(comp_set)
        
        return component_sets
    
    def find_sets_containing(
        self,
        component_name: str,
        component_type: str,
        domain: str | None = None
    ) -> list[ComponentSet]:
        """Find ComponentSets that contain a specific component.
        
        Args:
            component_name: Name of the component to search for
            component_type: Type of the component
            domain: Optional domain to filter by
            
        Returns:
            List of ComponentSet objects containing the component
        """
        target_component = ComponentReference(component_name, component_type)
        matching_sets = []
        
        for comp_set in self.list_sets():
            if domain:
                # Check specific domain only
                if comp_set.has_component(target_component, domain):
                    matching_sets.append(comp_set)
            else:
                # Check all domains
                if comp_set.has_component(target_component):
                    matching_sets.append(comp_set)
        
        return matching_sets
    
    def remove_set(self, name: str) -> bool:
        """Remove a ComponentSet from the registry.
        
        Args:
            name: Name of the ComponentSet to remove
            
        Returns:
            True if removed, False if not found
        """
        try:
            self.remove(name=name, dimension="component_sets")
            logger.info(f"Removed ComponentSet '{name}' from registry")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove ComponentSet '{name}': {e}")
            return False
    
    def get_set_stats(self) -> dict[str, Any]:
        """Get statistics about ComponentSets in the registry.
        
        Returns:
            Dictionary with ComponentSet statistics
        """
        component_sets = self.list_sets()
        stats = {
            "total_sets": len(component_sets),
            "total_components_in_sets": 0,
            "domains": set(),
            "tags": set(),
            "versions": set(),
        }
        
        for comp_set in component_sets:
            stats["total_components_in_sets"] += comp_set.total_component_count()
            stats["domains"].update(comp_set.get_domains())
            stats["tags"].update(comp_set.tags)
            stats["versions"].add(comp_set.version)
        
        # Convert sets to lists for JSON serialization
        stats["domains"] = sorted(list(stats["domains"]))
        stats["tags"] = sorted(list(stats["tags"]))
        stats["versions"] = sorted(list(stats["versions"]))
        
        return stats
    
    def create_set_from_components(
        self,
        name: str,
        description: str,
        component_filters: dict[str, list[str]],
        tags: set[str] | None = None
    ) -> ComponentSet:
        """Create a ComponentSet from existing registered components.
        
        Args:
            name: Name for the new ComponentSet
            description: Description of the ComponentSet
            component_filters: Dict of domain -> list of component names
            tags: Optional tags for the set
            
        Returns:
            Created ComponentSet
        """
        component_set = ComponentSet(
            name=name,
            description=description,
            tags=tags or set()
        )
        
        for domain, component_names in component_filters.items():
            for comp_name in component_names:
                # Try to find the component in registry
                found_component = None
                for comp_type in ComponentType:
                    bundle = self.get_component(comp_type, comp_name)
                    if bundle:
                        found_component = ComponentReference(comp_name, comp_type.value)
                        break
                
                if found_component:
                    component_set.add_component(domain, found_component)
                else:
                    logger.warning(f"Component '{comp_name}' not found in registry")
        
        # Register the created set
        self.register_set(component_set)
        
        logger.info(f"Created ComponentSet '{name}' with {component_set.total_component_count()} components")
        return component_set


# Global registry instance for convenience
_global_registry = None

def get_plating_registry(package_name: str = "pyvider.components") -> PlatingRegistry:
    """Get or create the global plating registry.
    
    Args:
        package_name: Package to search for components
        
    Returns:
        PlatingRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = PlatingRegistry(package_name)
    return _global_registry


def reset_plating_registry() -> None:
    """Reset the global registry (primarily for testing)."""
    global _global_registry
    _global_registry = None


# 🗃️🔍⚡✨