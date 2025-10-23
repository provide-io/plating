from __future__ import annotations

from pathlib import Path
from typing import Any

from plating.bundles import FunctionPlatingBundle, PlatingBundle
from plating.discovery import PlatingDiscovery
from plating.generation.adorner import DocumentationAdorner
from plating.templating.engine import AsyncTemplateEngine
from plating.templating.metadata import TemplateMetadataExtractor
from plating.types import PlatingContext

#
# plating/generation/plater.py
#
"""Main documentation generation orchestrator."""


class DocumentationPlater:
    """Orchestrates the complete documentation generation process using async rendering."""

    def __init__(self, package_name: str) -> None:
        self.package_name = package_name
        self.discovery = PlatingDiscovery(package_name)
        self.extractor = TemplateMetadataExtractor()
        self.adorner = DocumentationAdorner()
        self.renderer = AsyncTemplateEngine()

    async def generate_documentation(
        self, output_dir: Path, component_type: str | None = None
    ) -> list[tuple[Path, str]]:
        """Generate documentation for all discovered components.

        Args:
            output_dir: Directory to write generated documentation
            component_type: Optional filter for component type

        Returns:
            List of (file_path, content) tuples for generated files
        """
        bundles = self.discovery.discover_bundles(component_type)
        generated_files: list[tuple[Path, str]] = []

        for bundle in bundles:
            if isinstance(bundle, FunctionPlatingBundle):
                files = await self._generate_function_documentation(bundle, output_dir)
                generated_files.extend(files)
            else:
                files = await self._generate_component_documentation(bundle, output_dir)
                generated_files.extend(files)

        return generated_files

    async def _generate_function_documentation(
        self, bundle: FunctionPlatingBundle, output_dir: Path
    ) -> list[tuple[Path, str]]:
        """Generate documentation for individual function template.

        Args:
            bundle: Function bundle containing template file
            output_dir: Output directory

        Returns:
            List of generated file paths and content
        """
        template_content = bundle.load_main_template()
        if not template_content:
            return []

        metadata = self.extractor.extract_function_metadata(bundle.name, bundle.component_type)
        context_dict = self.adorner.adorn_function_template(template_content, bundle.name, metadata)

        # Create PlatingContext for async rendering
        context = PlatingContext(
            provider_name=context_dict.get("provider_name", "unknown"),
            **context_dict
        )
        rendered_content = await self.renderer.render(bundle, context)

        output_file = output_dir / f"{bundle.name}.md"
        return [(output_file, rendered_content)]

    async def _generate_component_documentation(
        self, bundle: PlatingBundle, output_dir: Path
    ) -> list[tuple[Path, str]]:
        """Generate documentation for non-function components.

        Args:
            bundle: Component bundle
            output_dir: Output directory

        Returns:
            List of generated file paths and content
        """
        template_content = bundle.load_main_template()
        if not template_content:
            return []

        metadata = self._extract_component_metadata(bundle)
        context_dict = self.adorner.adorn_resource_template(template_content, bundle.name, metadata)

        # Create PlatingContext for async rendering
        context = PlatingContext(
            provider_name=context_dict.get("provider_name", "unknown"),
            **context_dict
        )
        rendered_content = await self.renderer.render(bundle, context)

        output_file = output_dir / f"{bundle.name}.md"
        return [(output_file, rendered_content)]

    def _extract_component_metadata(self, bundle: PlatingBundle) -> dict[str, Any]:
        """Extract metadata for non-function components.

        Args:
            bundle: Component bundle

        Returns:
            Component metadata dictionary
        """
        # Component-specific metadata extraction delegated to TemplateMetadataExtractor
        return {
            "component_name": bundle.name,
            "component_type": bundle.component_type,
            "description": f"Documentation for {bundle.name} {bundle.component_type}",
        }
