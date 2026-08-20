#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

import asyncio
from typing import Any

from provide.foundation import logger, perr, pout
from provide.foundation.hub import Hub
from pyvider.hub.components import ComponentRegistry
from pyvider.hub.discovery import ComponentDiscovery

from plating.adorner.finder import ComponentFinder
from plating.discovery import PlatingDiscovery
from plating.errors import AdorningError, handle_error
from plating.templating.generator import TemplateGenerator
from plating.types import ComponentType

"""Core adorner implementation."""

# Component types that get a .plating bundle of their own. The provider itself
# renders to a single index page and is adorned separately.
_ADORNABLE_TYPES: tuple[str, ...] = tuple(member.value for member in ComponentType.documentable())


def _is_adorned(component_name: str, existing_names: set[str]) -> bool:
    """Whether a component already has a .plating bundle.

    A bundle is named after the module it sits beside ("secret_note.plating"),
    while a component is registered under its Terraform type name
    ("pyvider_secret_note"). Comparing the two verbatim reports every adorned
    component as missing, and adorning rewrites the bundle's templates -- so
    the provider prefix has to be discounted on the way in.
    """
    if component_name in existing_names:
        return True
    _, _, unprefixed = component_name.partition("_")
    return bool(unprefixed) and unprefixed in existing_names


class PlatingAdorner:
    """Adorns components with .plating directories."""

    def __init__(self, package_name: str, hub: Hub | None = None) -> None:
        """Initialize adorner with package name.

        Args:
            package_name: Python package to search for components
            hub: Optional Hub instance for component discovery
        """
        self.package_name = package_name
        self.plating_discovery = PlatingDiscovery(package_name)
        self.template_generator = TemplateGenerator()
        self.component_finder = ComponentFinder()
        # Allow hub to be injected for testing, otherwise create a default one
        if hub:
            self.hub = hub
        else:
            # Use provide.foundation Hub for consistent interface
            self.hub = Hub()
        # Initialize pyvider component registry and discovery
        self.registry = ComponentRegistry()
        self.discovery = ComponentDiscovery(self.registry)

    async def adorn_missing(self, component_types: list[str] | None = None) -> dict[str, int]:
        """
        Adorn components with missing .plating directories.

        Returns a dictionary with counts of adorned components by type.
        """
        pout(f"🔍 Discovering components in package: {self.package_name}")

        # Try to discover using hub first (can be mocked in tests)
        if hasattr(self.hub, "discover_components"):
            try:
                await asyncio.to_thread(self.hub.discover_components, self.package_name)
            except Exception as e:
                logger.warning(f"Hub component discovery failed: {e}")

        # Discover all components using pyvider's component discovery
        try:
            await self.discovery.discover_all(strict=False)
        except Exception as e:
            logger.error(f"Component discovery failed: {e}")
            perr(f"❌ Component discovery failed: {e}")
            return dict.fromkeys(_ADORNABLE_TYPES, 0)

        # Find existing plating bundles
        existing_bundles = await asyncio.to_thread(self.plating_discovery.discover_bundles)
        existing_names = {bundle.name for bundle in existing_bundles}
        pout(f"   Found {len(existing_bundles)} existing bundles")

        # Track adorning results
        adorned = dict.fromkeys(_ADORNABLE_TYPES, 0)

        # Filter by component types if specified
        target_types = component_types or list(_ADORNABLE_TYPES)
        pout(f"🎨 Adorning component types: {', '.join(target_types)}")

        # Adorn missing components
        for component_type in target_types:
            components = self._get_components_by_dimension(component_type)
            missing = [name for name in components if not _is_adorned(name, existing_names)]

            if missing:
                pout(f"✨ Processing {len(missing)} missing {component_type}(s)...")
                for name in missing:
                    # Get component class from components dict or from hub if available
                    component_class = components[name]
                    if component_class is None and hasattr(self.hub, "get_component"):
                        from contextlib import suppress

                        with suppress(Exception):
                            # Fall back to None, _adorn_component will handle it
                            component_class = await asyncio.to_thread(self.hub.get_component, name)
                    success = await self._adorn_component(name, component_type, component_class)
                    if success:
                        adorned[component_type] = adorned.get(component_type, 0) + 1
            else:
                pout(f"ℹ️  All {component_type}s already have .plating bundles")  # noqa: RUF001

        total_adorned = sum(adorned.values())
        if total_adorned > 0:
            pout(f"\n✅ Successfully adorned {total_adorned} component(s)")
        else:
            pout("\nℹ️  No components needed adorning")  # noqa: RUF001

        return adorned

    def _get_components_by_dimension(self, dimension: str) -> dict[str, Any]:
        """Get components from hub by dimension."""
        components: dict[str, Any] = {}
        try:
            # Try to use hub first (can be mocked in tests)
            if hasattr(self.hub, "list_components"):
                hub_components = self.hub.list_components(dimension=dimension)
                if isinstance(hub_components, dict) and hub_components:
                    return hub_components
                if isinstance(hub_components, list) and hub_components:
                    # Convert list of component names to dict format
                    return dict.fromkeys(hub_components)
            # Fall back to pyvider's registry. An empty answer from the hub is
            # not proof of absence: foundation discovers through entry points,
            # which never see the component types registered by decorator.
            all_components = self.registry.list_components()
            if dimension in all_components:
                components = all_components[dimension]
        except Exception as e:
            logger.warning(f"Failed to get {dimension} components: {e}")
        return components

    async def _adorn_component(self, name: str, component_type: str, component_class: type) -> bool:
        """Adorn a single component with a .plating directory."""
        try:
            # Find the component's source file location
            if logger.is_trace_enabled():
                logger.trace(f"Looking for source file for {name}")
            source_file = await self.component_finder.find_source(component_class)
            if not source_file:
                logger.warning(f"Could not find source file for {name}")
                pout(f"   ⚠️  Skipped {name} (source file not found)")
                return False

            # Create .plating directory structure
            plating_dir = source_file.parent / f"{source_file.stem}.plating"
            docs_dir = plating_dir / "docs"
            examples_dir = plating_dir / "examples"

            if logger.is_trace_enabled():
                logger.trace(f"Creating .plating directory at {plating_dir}")
            try:
                await asyncio.to_thread(docs_dir.mkdir, parents=True, exist_ok=True)
                await asyncio.to_thread(examples_dir.mkdir, parents=True, exist_ok=True)
            except OSError as e:
                raise AdorningError(name, component_type, f"Failed to create directories: {e}") from e

            # Generate and write template. Adorning scaffolds what is missing;
            # an existing template is hand-written content and is left alone.
            template_file = docs_dir / f"{name}.tmpl.md"
            if not template_file.exists():
                template_content = await self.template_generator.generate_template(
                    name, component_type, component_class
                )
                await asyncio.to_thread(template_file.write_text, template_content)

            # Generate and write example, named by the convention for this type:
            # a list resource's example is a query file, not configuration.
            try:
                suffix = ComponentType.from_value(component_type).example_suffix
            except ValueError:
                suffix = ".tf"
            example_file = examples_dir / f"example{suffix}"
            if not example_file.exists() and not any(examples_dir.iterdir()):
                example_content = await self.template_generator.generate_example(name, component_type)
                await asyncio.to_thread(example_file.write_text, example_content)

            logger.info(f"Successfully adorned {component_type}: {name}")
            return True

        except AdorningError:
            raise
        except Exception as e:
            error = AdorningError(name, component_type, str(e))
            handle_error(error, logger)
            perr(f"   ❌ {name}: {e}")
            return False


# 🍽️📖🔚
