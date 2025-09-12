#
# plating/garnish.py
#
"""Garnish bundle discovery and management."""

import importlib.util
from pathlib import Path

import attrs


@attrs.define
class PlatingBundle:
    """Represents a single .plating bundle with its assets."""

    name: str
    plating_dir: Path
    component_type: str  # "resource", "data_source", "function"

    @property
    def docs_dir(self) -> Path:
        """Directory containing documentation templates and partials."""
        return self.plating_dir / "docs"

    @property
    def examples_dir(self) -> Path:
        """Directory containing example Terraform files."""
        return self.plating_dir / "examples"

    @property
    def fixtures_dir(self) -> Path:
        """Directory containing fixture files for tests (inside examples dir)."""
        return self.examples_dir / "fixtures"

    def load_main_template(self) -> str | None:
        """Load the main template file for this component."""
        # Main template is typically <component_name>.tmpl.md
        template_file = self.docs_dir / f"{self.name}.tmpl.md"

        if not template_file.exists():
            return None

        try:
            return template_file.read_text(encoding="utf-8")
        except Exception:
            return None

    def load_examples(self) -> dict[str, str]:
        """Load all example files as a dictionary."""
        examples: dict[str, str] = {}

        if not self.examples_dir.exists():
            return examples

        for example_file in self.examples_dir.glob("*.tf"):
            try:
                examples[example_file.stem] = example_file.read_text(encoding="utf-8")
            except Exception:
                continue

        return examples

    def load_partials(self) -> dict[str, str]:
        """Load all partial files from docs directory.

        Partials are files starting with underscore (_) in the docs directory.
        """
        partials: dict[str, str] = {}

        if not self.docs_dir.exists():
            return partials

        # Load only files starting with underscore (partial convention)
        for partial_file in self.docs_dir.glob("_*"):
            if partial_file.is_file():
                try:
                    partials[partial_file.name] = partial_file.read_text(encoding="utf-8")
                except Exception:
                    continue

        return partials

    def load_fixtures(self) -> dict[str, str]:
        """Load all fixture files from fixtures directory."""
        fixtures: dict[str, str] = {}

        if not self.fixtures_dir.exists():
            return fixtures

        for fixture_file in self.fixtures_dir.rglob("*"):
            if fixture_file.is_file():
                try:
                    # Use relative path from fixtures dir as key
                    rel_path = fixture_file.relative_to(self.fixtures_dir)
                    fixtures[str(rel_path)] = fixture_file.read_text(encoding="utf-8")
                except Exception:
                    continue

        return fixtures


class PlatingDiscovery:
    """Discovers .plating bundles from installed packages."""

    def __init__(self, package_name: str = "pyvider.components"):
        self.package_name = package_name

    def discover_bundles(self, component_type: str | None = None) -> list[PlatingBundle]:
        """Discover all .plating bundles from the installed package."""
        bundles: list[PlatingBundle] = []

        # Find the package location
        try:
            spec = importlib.util.find_spec(self.package_name)
            if not spec or not spec.origin:
                return bundles
        except (ModuleNotFoundError, ValueError):
            # Package doesn't exist or invalid package name
            return bundles

        package_path = Path(spec.origin).parent

        # Search for .plating directories
        for plating_dir in package_path.rglob("*.plating"):
            if not plating_dir.is_dir():
                continue

            # Skip hidden directories
            if plating_dir.name.startswith("."):
                continue

            # Determine component type from path
            bundle_component_type = self._determine_component_type(plating_dir)
            if component_type and bundle_component_type != component_type:
                continue

            # Check if this is a multi-component bundle
            sub_component_bundles = self._discover_sub_components(plating_dir, bundle_component_type)
            if sub_component_bundles:
                # Multi-component bundle - use individual components
                bundles.extend(sub_component_bundles)
            else:
                # Single component bundle
                component_name = plating_dir.name.replace(".plating", "")

                bundle = PlatingBundle(
                    name=component_name,
                    plating_dir=plating_dir,
                    component_type=bundle_component_type,
                )

                bundles.append(bundle)

        return bundles

    def _discover_sub_components(self, plating_dir: Path, component_type: str) -> list[PlatingBundle]:
        """Discover individual components within a multi-component .plating bundle."""
        sub_bundles = []

        # Look for subdirectories that contain docs/ and examples/ folders
        for item in plating_dir.iterdir():
            if not item.is_dir():
                continue

            # Check if this looks like a component directory
            docs_dir = item / "docs"
            if docs_dir.exists() and docs_dir.is_dir():
                # Determine component type from subdirectory name
                sub_component_type = item.name
                if sub_component_type not in ["resource", "data_source", "function"]:
                    # Fall back to parent component type if not a recognized type
                    sub_component_type = component_type

                # This appears to be an individual component
                bundle = PlatingBundle(
                    name=item.name,  # Use the directory name as component name
                    plating_dir=item,  # Point to the individual component directory
                    component_type=sub_component_type,
                )
                sub_bundles.append(bundle)

        return sub_bundles

    def _determine_component_type(self, plating_dir: Path) -> str:
        """Determine component type from the .plating directory path."""
        path_parts = plating_dir.parts

        if "resources" in path_parts:
            return "resource"
        elif "data_sources" in path_parts:
            return "data_source"
        elif "functions" in path_parts:
            return "function"
        else:
            # Default to resource if unclear
            return "resource"


# 🍲🥄📄🪄
