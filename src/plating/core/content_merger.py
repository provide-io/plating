"""Content merging system for plating.

Discovers and merges content (guides, examples, assets) from component
packages into provider documentation.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil

from attrs import define, field
from provide.foundation import logger

from plating.config.runtime import PlatingConfig
from plating.errors import PlatingContentCollisionError


@define
class ContentSource:
    """Represents a source package providing mergeable content."""

    package_name: str = field()
    plating_path: Path = field()
    provides_content: bool = field(default=False)


@define
class ContentFile:
    """Represents a single content file to merge."""

    relative_path: Path = field()
    source_package: str = field()
    absolute_path: Path = field()
    subdir: str = field()  # guides, examples, assets, etc.


class ContentMerger:
    """Discovers and merges content from component packages.

    Implements convention-based merging with optional exclusions:
    - plating/guides/ → docs/guides/
    - plating/examples/ → docs/examples/
    - plating/assets/ → docs/assets/
    """

    def __init__(self, config: PlatingConfig) -> None:
        """Initialize content merger with configuration.

        Args:
            config: Plating configuration with merge settings
        """
        self.config = config
        self._discovered_sources: list[ContentSource] = []
        self._content_files: dict[Path, list[ContentFile]] = {}

    async def discover_content_sources(self) -> list[ContentSource]:
        """Discover plating/ directories from packages.

        Returns:
            List of discovered content sources
        """
        sources: list[ContentSource] = []

        for package_name in self.config.merge_content_from:
            try:
                # Find package location
                spec = importlib.util.find_spec(package_name)
                if spec is None or spec.origin is None:
                    logger.warning(f"Package '{package_name}' not found")
                    continue

                package_path = Path(spec.origin).parent

                # Search up from package to find project root (where pyproject.toml is)
                project_root = package_path
                while project_root.parent != project_root:  # Stop at filesystem root
                    if (project_root / "pyproject.toml").exists():
                        break
                    project_root = project_root.parent

                plating_path = project_root / "plating"

                if not plating_path.exists():
                    logger.debug(f"No plating/ in '{package_name}' project root at {project_root}")
                    continue

                # Check if package provides content
                provides_content = await self._check_provides_content(package_name)

                if provides_content:
                    sources.append(
                        ContentSource(
                            package_name=package_name,
                            plating_path=plating_path,
                            provides_content=True,
                        )
                    )
                    logger.info(f"Discovered content source: {package_name}")

            except Exception as e:
                logger.warning(f"Error discovering '{package_name}': {e}")

        self._discovered_sources = sources
        return sources

    async def _check_provides_content(self, package_name: str) -> bool:
        """Check if package has provides_content = true in config.

        Args:
            package_name: Package to check

        Returns:
            True if package provides content
        """
        # TODO: Read package's pyproject.toml [tool.plating] section
        # For now, assume true if plating/ exists
        return True

    async def collect_content_files(self) -> dict[Path, list[ContentFile]]:
        """Collect all content files from discovered sources.

        Returns:
            Dictionary mapping relative paths to list of ContentFile objects
        """
        collected: dict[Path, list[ContentFile]] = {}

        for source in self._discovered_sources:
            plating_dir = source.plating_path

            for subdir in plating_dir.iterdir():
                if not subdir.is_dir():
                    continue

                # Skip excluded directories
                if subdir.name in self.config.exclude_from_merge:
                    logger.debug(f"Excluding {subdir.name}/ from merge")
                    continue

                # Collect files in subdir
                for file_path in subdir.rglob("*.md"):
                    relative = file_path.relative_to(plating_dir)

                    content_file = ContentFile(
                        relative_path=relative,
                        source_package=source.package_name,
                        absolute_path=file_path,
                        subdir=subdir.name,
                    )

                    if relative not in collected:
                        collected[relative] = []
                    collected[relative].append(content_file)

        self._content_files = collected
        return collected

    def detect_collisions(self) -> list[tuple[Path, list[ContentFile]]]:
        """Detect filename collisions across packages.

        Returns:
            List of (path, conflicting_files) tuples
        """
        collisions: list[tuple[Path, list[ContentFile]]] = []

        for relative_path, files in self._content_files.items():
            if len(files) > 1:
                collisions.append((relative_path, files))

        return collisions

    async def merge_content(self, output_dir: Path) -> None:
        """Merge content from all sources to output directory.

        Args:
            output_dir: Output directory (usually docs/)

        Raises:
            PlatingContentCollisionError: If file collisions detected
        """
        # Check for collisions
        collisions = self.detect_collisions()
        if collisions:
            for rel_path, files in collisions:
                sources = [f.source_package for f in files]
                raise PlatingContentCollisionError(rel_path, sources)

        # Copy files
        for relative_path, files in self._content_files.items():
            # Only one file per path (no collisions)
            content_file = files[0]

            output_path = output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(content_file.absolute_path, output_path)

            logger.debug(f"Merged: {content_file.source_package}:{relative_path} → {output_path}")

        logger.info(f"Merged {len(self._content_files)} content files")
