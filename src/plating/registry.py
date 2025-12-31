#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from typing import Any

from provide.foundation import Registry, RegistryEntry, logger
from provide.foundation.resilience import BackoffStrategy, RetryExecutor, RetryPolicy

from plating.bundles import PlatingBundle
from plating.discovery import PlatingDiscovery
from plating.types import ComponentType

#
# plating/registry.py
#
"""Component registry using foundation patterns."""


class PlatingRegistryEntry(RegistryEntry):
    """Registry entry for plating bundles."""

    def __init__(self, bundle: PlatingBundle, dimension: str) -> None:
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
            },
        )

    @property
    def bundle(self) -> PlatingBundle:
        """Get the PlatingBundle from this entry."""
        bundle: PlatingBundle = self.value
        return bundle


class PlatingRegistry(Registry):
    """Component registry using foundation Registry pattern with ComponentSet support."""

    def __init__(self, package_name: str | None = None) -> None:
        """Initialize registry with package discovery.

        Args:
            package_name: Package to search for plating bundles, or None to search all packages
        """
        super().__init__()
        self.package_name = package_name

        # Foundation resilience for discovery
        self._retry_policy = RetryPolicy(
            max_attempts=3,
            backoff=BackoffStrategy.EXPONENTIAL,
            base_delay=0.5,
            max_delay=5.0,
            retryable_errors=(OSError, ImportError, AttributeError),
        )
        self._retry_executor = RetryExecutor(self._retry_policy)

        # Initialize discovery with error handling
        try:
            self._discovery = PlatingDiscovery(package_name)
            # Auto-discover on initialization
            self._discover_and_register()
        except Exception as e:
            scope = package_name if package_name else "all packages"
            logger.error(f"Failed to initialize discovery for {scope}: {e}")
            # Set discovery to None so we can still create the registry
            self._discovery = None  # type: ignore[assignment]

    def _discover_and_register(self) -> None:
        """Discover and register all components using foundation patterns."""
        if not self._discovery:
            logger.warning("Discovery not initialized, skipping component registration")
            return

        try:
            bundles = self._retry_executor.execute_sync(self._discovery.discover_bundles)

            # Track seen components to avoid duplicate registration during global discovery
            seen_components: set[tuple[str, str]] = set()  # (name, dimension)

            logger.info(f"Discovered {len(bundles)} plating bundles")

            for bundle in bundles:
                component_key = (bundle.name, bundle.component_type)

                # Skip if we've already seen this component (deduplication for global discovery)
                if component_key in seen_components:
                    logger.debug(f"Skipping duplicate {bundle.component_type}/{bundle.name}")
                    continue

                seen_components.add(component_key)

                entry = PlatingRegistryEntry(bundle, dimension=bundle.component_type)
                self.register(
                    name=bundle.name,
                    dimension=bundle.component_type,  # "resource", "data_source", etc.
                    value=entry,
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
        stats["component_types_list"] = list(all_names.keys())

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
                1 for entry in entries if entry.value.metadata.get("has_template", False)
            )
            bundles_with_examples = sum(
                1 for entry in entries if entry.value.metadata.get("has_examples", False)
            )

            stats[f"{comp_type}_with_templates"] = bundles_with_templates
            stats[f"{comp_type}_with_examples"] = bundles_with_examples

        return stats


# Global registry instance for convenience
_global_registry = None


def get_plating_registry(package_name: str | None = None) -> PlatingRegistry:
    """Get or create the global plating registry.

    Args:
        package_name: Package to search for components, or None to search all packages

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

# 🍽️📖🔚
