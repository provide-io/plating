#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Component discovery logic for .plating bundles."""

from __future__ import annotations

import contextlib
import importlib.metadata
import importlib.util
from pathlib import Path

from plating.bundles import FunctionPlatingBundle, PlatingBundle

#
# plating/discovery/finder.py
#


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

    def _distribution_to_module_name(self, dist_name: str) -> str | None:
        """Convert a distribution name to a module name.

        Args:
            dist_name: Distribution name (e.g., "pyvider-components")

        Returns:
            Module name (e.g., "pyvider.components") or None if not found
        """
        try:
            # First, try to find an entry point that matches the distribution name
            eps = importlib.metadata.entry_points()
            for group in eps.groups:
                group_eps = eps.select(group=group)
                for ep in group_eps:
                    if ep.name == dist_name:
                        return ep.value

            # Fallback: construct module name from distribution name
            dist = importlib.metadata.distribution(dist_name)
            top_level_text = dist.read_text("top_level.txt")
            if top_level_text:
                top_levels = top_level_text.strip().split("\n")
                if top_levels:
                    top_level = top_levels[0]
                    # Convert dist name "pyvider-components" to "pyvider.components"
                    if dist_name.startswith(f"{top_level}-"):
                        suffix = dist_name[len(top_level) + 1 :].replace("-", ".")
                        return f"{top_level}.{suffix}"
                    return top_level
        except (importlib.metadata.PackageNotFoundError, FileNotFoundError, TypeError):
            pass

        return None

    def _discover_from_all_packages(self, component_type: str | None = None) -> list[PlatingBundle]:  # noqa: C901
        """Discover .plating bundles from all installed packages.

        Searches site-packages and other Python paths for .plating directories.
        Much simpler than trying to map distribution names to import names.
        """
        all_bundles: list[PlatingBundle] = []
        searched_paths: set[Path] = set()

        # Get all site-packages and source directories
        import sys

        search_roots = set()

        for path_str in sys.path:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                # Add site-packages, dist-packages, and src directories
                search_roots.add(path)

        # Search each root for .plating directories
        for root in search_roots:
            try:
                for plating_dir in root.rglob("*.plating"):
                    if not plating_dir.is_dir() or plating_dir.name.startswith("."):
                        continue

                    # Skip if we've seen this directory
                    if plating_dir in searched_paths:
                        continue
                    searched_paths.add(plating_dir)

                    # Determine component type and create bundles
                    bundle_component_type = self._determine_component_type(plating_dir)
                    if component_type and bundle_component_type != component_type:
                        continue

                    # Process the bundle (same logic as single-package discovery)
                    sub_component_bundles = self._discover_sub_components(plating_dir, bundle_component_type)
                    if sub_component_bundles:
                        all_bundles.extend(sub_component_bundles)
                    elif bundle_component_type == "function":
                        function_bundles = self._discover_component_templates(
                            plating_dir, bundle_component_type
                        )
                        if function_bundles:
                            all_bundles.extend(function_bundles)
                        else:
                            component_name = plating_dir.name.replace(".plating", "")
                            bundle = PlatingBundle(
                                name=component_name,
                                plating_dir=plating_dir,
                                component_type=bundle_component_type,
                            )
                            all_bundles.append(bundle)
                    else:
                        component_name = plating_dir.name.replace(".plating", "")
                        bundle = PlatingBundle(
                            name=component_name,
                            plating_dir=plating_dir,
                            component_type=bundle_component_type,
                        )
                        all_bundles.append(bundle)
            except Exception:
                # Skip directories that cause errors
                continue

        return all_bundles

    def _discover_from_package(
        self, package_name: str, component_type: str | None = None
    ) -> list[PlatingBundle]:
        """Discover .plating bundles from a specific package."""
        bundles: list[PlatingBundle] = []

        # Try to find the module spec
        # If package_name is a distribution name (e.g., "pyvider-components"),
        # convert it to a module name (e.g., "pyvider.components")
        spec = None
        with contextlib.suppress(ModuleNotFoundError, ValueError, AttributeError):
            spec = importlib.util.find_spec(package_name)

        # If direct lookup failed and package_name looks like a distribution name (has hyphens),
        # try resolving distribution name to module name
        if not spec and "-" in package_name and "." not in package_name:
            module_name = self._distribution_to_module_name(package_name)
            if module_name:
                with contextlib.suppress(ModuleNotFoundError, ValueError, AttributeError):
                    spec = importlib.util.find_spec(module_name)

        if not spec or not spec.origin:
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
                # Check for individual template files (multiple components in one module)
                template_bundles = self._discover_component_templates(plating_dir, bundle_component_type)
                if template_bundles:
                    bundles.extend(template_bundles)
                else:
                    # Fallback to single bundle
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

    def _discover_component_templates(self, plating_dir: Path, component_type: str) -> list[PlatingBundle]:
        """Discover individual component templates within a .plating bundle.

        Used when multiple components are defined in a single Python module.
        Each component gets its own template file (e.g., pyvider_component_name.tmpl.md).
        """
        template_bundles: list[PlatingBundle] = []
        docs_dir = plating_dir / "docs"

        if not docs_dir.exists():
            return template_bundles

        # Find all .tmpl.md files except main.md.j2
        for template_file in docs_dir.glob("*.tmpl.md"):
            component_name = template_file.stem.replace(".tmpl", "")

            # For functions, use specialized FunctionPlatingBundle
            if component_type == "function":
                func_bundle: PlatingBundle = FunctionPlatingBundle(
                    name=component_name,
                    plating_dir=plating_dir,
                    component_type=component_type,
                    template_file=template_file,
                )
                template_bundles.append(func_bundle)
            else:
                # For data sources and resources, use regular PlatingBundle
                # but override the name to match the component name from the template
                regular_bundle = PlatingBundle(
                    name=component_name,
                    plating_dir=plating_dir,
                    component_type=component_type,
                )
                template_bundles.append(regular_bundle)

        return template_bundles

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


# 🍽️📖🔚
