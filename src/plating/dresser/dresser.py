#
# plating/dresser/dresser.py
#
"""Core dresser implementation."""

import asyncio

from pyvider.hub import ComponentDiscovery, hub
from provide.foundation import logger, pout, perr

from plating.dresser.finder import ComponentFinder
from plating.dresser.templates import TemplateGenerator
from plating.errors import DressingError, handle_error
from plating.plating import PlatingDiscovery


class PlatingDresser:
    """Dresses components with .plating directories."""

    def __init__(self):
        self.plating_discovery = PlatingDiscovery()
        self.template_generator = TemplateGenerator()
        self.component_finder = ComponentFinder()

    async def dress_missing(self, component_types: list[str] = None) -> dict[str, int]:
        """
        Dress components with missing .plating directories.

        Returns a dictionary with counts of dressed components by type.
        """
        # Discover all components via hub
        discovery = ComponentDiscovery(hub)
        await discovery.discover_all()
        components = hub.list_components()

        # Find existing plating bundles
        existing_bundles = await asyncio.to_thread(
            self.plating_discovery.discover_bundles
        )
        existing_names = {bundle.name for bundle in existing_bundles}

        # Track dressing results
        dressed = {"resource": 0, "data_source": 0, "function": 0}

        # Filter by component types if specified
        target_types = component_types or ["resource", "data_source", "function"]

        # Dress missing components
        for component_type in target_types:
            if component_type in components:
                for name, component_class in components[component_type].items():
                    if name not in existing_names:
                        success = await self._dress_component(
                            name, component_type, component_class
                        )
                        if success:
                            dressed[component_type] += 1

        return dressed

    async def _dress_component(
        self, name: str, component_type: str, component_class
    ) -> bool:
        """Dress a single component with a .plating directory."""
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
                raise DressingError(
                    name, component_type, f"Failed to create directories: {e}"
                )

            # Generate and write template
            template_content = await self.template_generator.generate_template(
                name, component_type, component_class
            )
            template_file = docs_dir / f"{name}.tmpl.md"
            await asyncio.to_thread(template_file.write_text, template_content)

            # Generate and write example
            example_content = await self.template_generator.generate_example(
                name, component_type
            )
            example_file = examples_dir / "example.tf"
            await asyncio.to_thread(example_file.write_text, example_content)

            logger.info(f"Successfully dressed {component_type}: {name}")
            pout(f"✅ Dressed {component_type}: {name}")
            return True

        except DressingError:
            raise  # Re-raise our custom errors
        except Exception as e:
            error = DressingError(name, component_type, str(e))
            handle_error(error, logger)
            perr(f"❌ Failed to dress {name}: {e}")
            return False


# 🍲🥄👗🪄
