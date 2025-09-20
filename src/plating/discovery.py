from __future__ import annotations

#
# plating/discovery.py
#
"""Component discovery logic for .plating bundles."""

import importlib.util
from pathlib import Path

from plating.bundles import FunctionPlatingBundle, PlatingBundle


class PlatingDiscovery:
    """Discovers .plating bundles from installed packages."""

    def __init__(self, package_name: str = "pyvider.components") -> None:
        self.package_name = package_name

    def discover_bundles(self, component_type: str | None = None) -> list[PlatingBundle]:
        """Discover all .plating bundles from the installed package."""
        bundles: list[PlatingBundle] = []

        try:
            spec = importlib.util.find_spec(self.package_name)
            if not spec or not spec.origin:
                return bundles
        except (ModuleNotFoundError, ValueError):
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
