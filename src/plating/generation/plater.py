from __future__ import annotations

from pathlib import Path
from typing import Any

from plating.bundles import FunctionPlatingBundle, PlatingBundle
from plating.discovery import PlatingDiscovery
from plating.generation.adorner import DocumentationAdorner
from plating.templating.metadata import TemplateMetadataExtractor
from plating.generation.renderer import TemplateRenderer

#
# plating/generation/plater.py
#
"""Main documentation generation orchestrator."""


class DocumentationPlater:
    """Orchestrates the complete documentation generation process."""

    def __init__(self) -> None:
        self.discovery = PlatingDiscovery()
        self.extractor = TemplateMetadataExtractor()
        self.adorner = DocumentationAdorner()
        self.renderer = TemplateRenderer()

    def generate_documentation(
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
                files = self._generate_function_documentation(bundle, output_dir)
                generated_files.extend(files)
            else:
                files = self._generate_component_documentation(bundle, output_dir)
                generated_files.extend(files)

        return generated_files

    def _generate_function_documentation(
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
        context = self.adorner.adorn_function_template(template_content, bundle.name, metadata)
        rendered_content = self.renderer.render_template(template_content, context)

        output_file = output_dir / f"{bundle.name}.md"
        return [(output_file, rendered_content)]

    def _generate_component_documentation(
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
        context = self.adorner.adorn_resource_template(template_content, bundle.name, metadata)
        rendered_content = self.renderer.render_template(template_content, context)

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
