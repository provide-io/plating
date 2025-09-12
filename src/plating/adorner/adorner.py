#
# plating/adorner/adorner.py
#
"""Core adorner implementation."""

import asyncio
from typing import Any

from provide.foundation import logger, perr, pout
from provide.foundation.hub import Hub, discover_components

from plating.adorner.finder import ComponentFinder
from plating.adorner.templates import TemplateGenerator
from plating.errors import AdorningError, handle_error
from plating.plating import PlatingDiscovery


class PlatingAdorner:
    """Adorns components with .plating directories."""

    def __init__(self):
        self.plating_discovery = PlatingDiscovery()
        self.template_generator = TemplateGenerator()
        self.component_finder = ComponentFinder()
        # Initialize foundation hub for component discovery
        self.hub = Hub()

    async def adorn_missing(self, component_types: list[str] = None) -> dict[str, int]:
        """
        Adorn components with missing .plating directories.

        Returns a dictionary with counts of adorned components by type.
        """
        # Discover all components via foundation hub
        try:
            discover_components("pyvider.components", hub=self.hub)
        except Exception as e:
            logger.error(f"Component discovery failed: {e}")
            return {"resource": 0, "data_source": 0, "function": 0}

        # Find existing plating bundles
        existing_bundles = await asyncio.to_thread(self.plating_discovery.discover_bundles)
        existing_names = {bundle.name for bundle in existing_bundles}

        # Track adorning results
        adorned = {"resource": 0, "data_source": 0, "function": 0}

        # Filter by component types if specified
        target_types = component_types or ["resource", "data_source", "function"]

        # Adorn missing components
        for component_type in target_types:
            components = self._get_components_by_dimension(component_type)
            for name, component_class in components.items():
                if name not in existing_names:
                    success = await self._adorn_component(name, component_type, component_class)
                    if success:
                        adorned[component_type] += 1

        return adorned

    def _get_components_by_dimension(self, dimension: str) -> dict[str, Any]:
        """Get components from foundation hub by dimension."""
        components = {}
        try:
            names = self.hub.registry.list_dimension(dimension)
            for name in names:
                entry = self.hub.registry.get_entry(name=name, dimension=dimension)
                if entry and entry.value:
                    components[name] = entry.value
        except Exception as e:
            logger.warning(f"Failed to get {dimension} components: {e}")
        return components

    async def _adorn_component(self, name: str, component_type: str, component_class) -> bool:
        """Adorn a single component with a .plating directory."""
        try:
            # Find the component's source file location
            logger.trace(f"Looking for source file for {name}")
            source_file = await self.component_finder.find_source(component_class)
            if not source_file:
                logger.warning(f"Could not find source file for {name}")
                pout(f"⚠️ Could not find source file for {name}")
                return False

            # Create .plating directory structure
            plating_dir = source_file.parent / f"{source_file.stem}.plating"
            docs_dir = plating_dir / "docs"
            examples_dir = plating_dir / "examples"

            logger.trace(f"Creating .plating directory at {plating_dir}")
            try:
                await asyncio.to_thread(docs_dir.mkdir, parents=True, exist_ok=True)
                await asyncio.to_thread(examples_dir.mkdir, parents=True, exist_ok=True)
            except OSError as e:
                raise AdorningError(name, component_type, f"Failed to create directories: {e}")

            # Generate and write template
            template_content = await self.template_generator.generate_template(
                name, component_type, component_class
            )
            template_file = docs_dir / f"{name}.tmpl.md"
            await asyncio.to_thread(template_file.write_text, template_content)

            # Generate and write example
            example_content = await self.template_generator.generate_example(name, component_type)
            example_file = examples_dir / "example.tf"
            await asyncio.to_thread(example_file.write_text, example_content)

            logger.info(f"Successfully adorned {component_type}: {name}")
            pout(f"✅ Adorned {component_type}: {name}")
            return True

        except AdorningError:
            raise  # Re-raise our custom errors
        except Exception as e:
            error = AdorningError(name, component_type, str(e))
            handle_error(error, logger)
            perr(f"❌ Failed to adorn {name}: {e}")
            return False


# 🍲🥄👗🪄
