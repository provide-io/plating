from __future__ import annotations

import importlib.metadata
import importlib.util
from pathlib import Path

from plating.bundles import FunctionPlatingBundle, PlatingBundle

#
# plating/discovery/finder.py
#
"""Component discovery logic for .plating bundles."""


class PlatingDiscovery:
    """Discovers .plating bundles from installed packages."""

    def __init__(self, package_name: str | None = None) -> None:
        """Initialize discovery.

        Args:
            package_name: Specific package to search, or None to search all packages
        """
        self.package_name = package_name

    def discover_bundles(self, component_type: str | None = None) -> list[PlatingBundle]:
        """Discover all .plating bundles from installed package(s).

        Args:
            component_type: Optional filter for specific component type

        Returns:
            List of discovered PlatingBundle objects
        """
        if self.package_name:
            # Single package discovery
            return self._discover_from_package(self.package_name, component_type)
        else:
            # Global discovery from all installed packages
            return self._discover_from_all_packages(component_type)

    def _discover_from_all_packages(self, component_type: str | None = None) -> list[PlatingBundle]:
        """Discover .plating bundles from all installed packages.

        This searches all installed packages by iterating through distributions and
        discovering their top-level modules and common submodules.
        """
        all_bundles: list[PlatingBundle] = []
        searched_paths: set[Path] = set()  # Avoid searching same path multiple times

        try:
            for dist in importlib.metadata.distributions():
                try:
                    top_level = dist.read_text('top_level.txt')
                    if top_level:
                        # Process each top-level module
                        for module_name in top_level.strip().split('\n'):
                            if module_name:
                                module_name = module_name.strip()

                                # Search the top-level module
                                bundles = self._discover_from_package_with_dedup(
                                    module_name, component_type, searched_paths
                                )
                                all_bundles.extend(bundles)

                                # Also search common submodules (e.g., pyvider.components, pyvider.resources)
                                for submodule in ['components', 'resources', 'data_sources', 'functions']:
                                    full_name = f"{module_name}.{submodule}"
                                    bundles = self._discover_from_package_with_dedup(
                                        full_name, component_type, searched_paths
                                    )
                                    all_bundles.extend(bundles)
                except Exception:
                    # Fallback: try the distribution name directly
                    bundles = self._discover_from_package_with_dedup(
                        dist.name, component_type, searched_paths
                    )
                    all_bundles.extend(bundles)
        except Exception:
            pass

        return all_bundles

    def _discover_from_package_with_dedup(
        self,
        package_name: str,
        component_type: str | None,
        searched_paths: set[Path]
    ) -> list[PlatingBundle]:
        """Discover from a package, avoiding duplicate path searches."""
        try:
            spec = importlib.util.find_spec(package_name)
            if not spec or not spec.origin:
                return []

            package_path = Path(spec.origin).parent

            # Skip if we've already searched this path
            if package_path in searched_paths:
                return []

            searched_paths.add(package_path)

            # Now do the actual discovery
            return self._discover_from_package(package_name, component_type)
        except (ModuleNotFoundError, ValueError, AttributeError):
            return []

    def _discover_from_package(
        self, package_name: str, component_type: str | None = None
    ) -> list[PlatingBundle]:
        """Discover .plating bundles from a specific package."""
        bundles: list[PlatingBundle] = []

        try:
            spec = importlib.util.find_spec(package_name)
            if not spec or not spec.origin:
                return bundles
        except (ModuleNotFoundError, ValueError, AttributeError):
            return bundles

        package_path = Path(spec.origin).parent

        for plating_dir in package_path.rglob("*.plating"):
            if not plating_dir.is_dir() or plating_dir.name.startswith("."):
                continue

            bundle_component_type = self._determine_component_type(plating_dir)
            if component_type and bundle_component_type != component_type:
                continue

            # First try to discover sub-components (subdirectories with docs/)
            sub_component_bundles = self._discover_sub_components(plating_dir, bundle_component_type)
            if sub_component_bundles:
                bundles.extend(sub_component_bundles)
            else:
                # For function bundles, check for individual template files
                if bundle_component_type == "function":
                    function_bundles = self._discover_function_templates(plating_dir)
                    if function_bundles:
                        bundles.extend(function_bundles)
                    else:
                        # Fallback to single bundle
                        component_name = plating_dir.name.replace(".plating", "")
                        bundle = PlatingBundle(
                            name=component_name, plating_dir=plating_dir, component_type=bundle_component_type
                        )
                        bundles.append(bundle)
                else:
                    # Non-function components use single bundle approach
                    component_name = plating_dir.name.replace(".plating", "")
                    bundle = PlatingBundle(
                        name=component_name, plating_dir=plating_dir, component_type=bundle_component_type
                    )
                    bundles.append(bundle)

        return bundles

    def _discover_sub_components(self, plating_dir: Path, component_type: str) -> list[PlatingBundle]:
        """Discover individual components within a multi-component .plating bundle."""
        sub_bundles = []

        for item in plating_dir.iterdir():
            if not item.is_dir():
                continue

            docs_dir = item / "docs"
            if docs_dir.exists() and docs_dir.is_dir():
                sub_component_type = item.name
                if sub_component_type not in ["resource", "data_source", "function"]:
                    sub_component_type = component_type

                bundle = PlatingBundle(name=item.name, plating_dir=item, component_type=sub_component_type)
                sub_bundles.append(bundle)

        return sub_bundles

    def _discover_function_templates(self, plating_dir: Path) -> list[PlatingBundle]:
        """Discover individual function templates within a function .plating bundle."""
        function_bundles: list[PlatingBundle] = []
        docs_dir = plating_dir / "docs"

        if not docs_dir.exists():
            return function_bundles

        # Find all .tmpl.md files except main.md.j2
        for template_file in docs_dir.glob("*.tmpl.md"):
            function_name = template_file.stem.replace(".tmpl", "")

            # Create a specialized bundle for individual function templates
            bundle = FunctionPlatingBundle(
                name=function_name,
                plating_dir=plating_dir,
                component_type="function",
                template_file=template_file,
            )
            function_bundles.append(bundle)

        return function_bundles

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
            return "resource"
