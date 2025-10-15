from __future__ import annotations

import asyncio
from pathlib import Path

from plating.plating import Plating
from plating.types import ComponentType

#
# plating/api.py
#
"""Backward compatibility API wrapper for the modern async Plating API."""


class PlatingAPI:
    """Backward compatibility API wrapper around the modern async Plating class."""

    def __init__(self, provider_name: str, package_name: str) -> None:
        """Initialize plating instance with provider context.

        Args:
            provider_name: Name of the provider (required)
            package_name: Python package containing components (required)
        """
        from plating.types import PlatingContext

        context = PlatingContext(provider_name=provider_name)
        self._plating = Plating(context, package_name)

    def generate_all_documentation(self, output_dir: Path | str) -> list[tuple[Path, str]]:
        """Generate documentation for all discovered components.

        Args:
            output_dir: Directory to write generated documentation

        Returns:
            List of (file_path, content) tuples for generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Run the async plate operation
        result = asyncio.run(self._plating.plate(output_path))

        # Convert to old format (file_path, content) tuples
        files = []
        for file_path in result.output_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                files.append((file_path, content))
            except Exception:
                # If we can't read the file, skip it
                continue

        return files

    def generate_function_documentation(self, output_dir: Path | str) -> list[tuple[Path, str]]:
        """Generate documentation for function components only.

        Args:
            output_dir: Directory to write generated documentation

        Returns:
            List of (file_path, content) tuples for generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Run the async plate operation for functions only
        result = asyncio.run(self._plating.plate(output_path, component_types=[ComponentType.FUNCTION]))

        # Convert to old format
        files = []
        for file_path in result.output_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                files.append((file_path, content))
            except Exception:
                continue

        return files

    def generate_resource_documentation(self, output_dir: Path | str) -> list[tuple[Path, str]]:
        """Generate documentation for resource components only.

        Args:
            output_dir: Directory to write generated documentation

        Returns:
            List of (file_path, content) tuples for generated files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Run the async plate operation for resources only
        result = asyncio.run(self._plating.plate(output_path, component_types=[ComponentType.RESOURCE]))

        # Convert to old format
        files = []
        for file_path in result.output_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                files.append((file_path, content))
            except Exception:
                continue

        return files

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
