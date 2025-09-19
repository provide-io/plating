from __future__ import annotations

from pathlib import Path
from typing import Any

#
# plating/discovery/templates.py
#
"""Template discovery and metadata extraction utilities."""


class TemplateMetadataExtractor:
    """Extracts metadata from function implementations for template rendering."""

    def extract_function_metadata(self, function_name: str, component_type: str) -> dict[str, Any]:
        """Extract metadata for a function to populate templates.

        Args:
            function_name: Name of the function
            component_type: Type of component (function, resource, etc.)

        Returns:
            Dictionary containing metadata for template rendering
        """
        # TODO: Implement actual function introspection
        # For now, return placeholder metadata
        return {
            "signature_markdown": f"`{function_name}(input)`",
            "arguments_markdown": "- `input`: The input value to process",
            "has_variadic": False,
            "variadic_argument_markdown": "",
            "examples": {"example": f"# Example usage of {function_name}"},
        }

    def discover_template_files(self, docs_dir: Path) -> list[Path]:
        """Discover all template files in a docs directory.

        Args:
            docs_dir: Directory containing template files

        Returns:
            List of template file paths
        """
        if not docs_dir.exists():
            return []

        template_files = []
        for template_file in docs_dir.glob("*.tmpl.md"):
            template_files.append(template_file)

        return template_files
