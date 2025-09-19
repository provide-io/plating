from __future__ import annotations

from pathlib import Path

from plating.generation import DocumentationPlater

#
# plating/api.py
#
"""Main API orchestrator for plating documentation generation."""


class PlatingAPI:
    """Main API class for orchestrating documentation generation."""

    def __init__(self) -> None:
        self.plater = DocumentationPlater()

    def generate_all_documentation(self, output_dir: Path | str) -> list[tuple[Path, str]]:
        """Generate documentation for all discovered components.

        Args:
            output_dir: Directory to write generated documentation

        Returns:
            List of (file_path, content) tuples for generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return self.plater.generate_documentation(output_path)

    def generate_function_documentation(self, output_dir: Path | str) -> list[tuple[Path, str]]:
        """Generate documentation for function components only.

        Args:
            output_dir: Directory to write generated documentation

        Returns:
            List of (file_path, content) tuples for generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return self.plater.generate_documentation(output_path, component_type="function")

    def generate_resource_documentation(self, output_dir: Path | str) -> list[tuple[Path, str]]:
        """Generate documentation for resource components only.

        Args:
            output_dir: Directory to write generated documentation

        Returns:
            List of (file_path, content) tuples for generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return self.plater.generate_documentation(output_path, component_type="resource")

    def write_generated_files(self, generated_files: list[tuple[Path, str]]) -> list[Path]:
        """Write generated documentation files to disk.

        Args:
            generated_files: List of (file_path, content) tuples

        Returns:
            List of written file paths
        """
        written_files = []
        for file_path, content in generated_files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            written_files.append(file_path)
        return written_files
