#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""MkDocs navigation generation with capability-first organization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from provide.foundation import logger
import yaml  # type: ignore[import-untyped]

from plating.bundles import PlatingBundle
from plating.core.doc_generator import group_components_by_capability
from plating.types import ComponentType


class MkdocsNavGenerator:
    """Generate mkdocs.yml navigation structure with capability-first organization."""

    def __init__(self, base_path: Path) -> None:
        """Initialize the generator.

        Args:
            base_path: Base directory containing mkdocs.yml
        """
        self.base_path = base_path
        self.mkdocs_file = base_path / "mkdocs.yml"

    def generate_nav(
        self,
        components: list[tuple[PlatingBundle, ComponentType]],
        include_guides: bool = True,
    ) -> dict[str, Any]:
        """Generate navigation structure grouped by capability.

        Args:
            components: List of (component, component_type) tuples
            include_guides: Whether to include guides section

        Returns:
            Navigation dictionary suitable for mkdocs.yml
        """
        nav = []

        # Add Overview
        nav.append({"Overview": "index.md"})

        # Add Guides section if indicated
        if include_guides:
            guides_nav = self._generate_guides_nav()
            if guides_nav:
                nav.extend(guides_nav)

        # Group components by capability
        grouped = group_components_by_capability(components)

        # Generate navigation for each capability
        for capability, types_dict in grouped.items():
            capability_nav = self._generate_capability_section(capability, types_dict)
            if capability_nav:
                nav.append(capability_nav)

        return {"nav": nav}

    def _generate_guides_nav(self) -> list[dict[str, Any]]:  # noqa: C901
        """Generate guides navigation if guides directory exists."""
        guides_dir = self.base_path / "docs" / "guides"

        if not guides_dir.exists():
            return []

        guides_nav = []

        # Find all .md files in guides directory
        guide_files = list(guides_dir.glob("*.md"))

        if not guide_files:
            return []

        # Extract metadata from guides and sort by guide_order
        guides_with_order = []
        for guide_file in guide_files:
            guide_order = None
            page_title = None

            # Extract frontmatter if present
            try:
                content = guide_file.read_text(encoding="utf-8")
                if content.startswith("---"):
                    # Extract YAML frontmatter
                    lines = content.split("\n")
                    fm_end = -1
                    for i in range(1, len(lines)):
                        if lines[i].strip() == "---":
                            fm_end = i
                            break

                    if fm_end > 0:
                        fm_text = "\n".join(lines[1:fm_end])
                        fm = yaml.safe_load(fm_text) or {}
                        guide_order = fm.get("guide_order")
                        page_title = fm.get("page_title")
            except Exception as e:
                logger.debug(f"Could not extract frontmatter from {guide_file}: {e}")

            # Fallback to generated title if page_title not present
            if not page_title:
                page_title = guide_file.stem.replace("_", " ").replace("-", " ").title()

            # Default guide_order to 999 if not specified (sorts last)
            if guide_order is None:
                guide_order = 999

            guides_with_order.append((guide_order, page_title, guide_file.name))

        # Sort by guide_order, then by filename
        guides_with_order.sort(key=lambda x: (x[0], x[2]))

        guides_section = {}
        for _, title, filename in guides_with_order:
            rel_path = f"guides/{filename}"
            guides_section[title] = rel_path

        if guides_section:
            guides_nav.append({"Guides": guides_section})

        return guides_nav

    def _generate_capability_section(
        self,
        capability: str,
        types_dict: dict[str, list[tuple[PlatingBundle, ComponentType]]],
    ) -> dict[str, Any] | None:
        """Generate navigation section for a capability."""
        section = {}

        # Order: resources, data sources, functions
        type_order = [ComponentType.RESOURCE, ComponentType.DATA_SOURCE, ComponentType.FUNCTION]

        for comp_type in type_order:
            if comp_type.value not in types_dict:
                continue

            components = types_dict[comp_type.value]
            if not components:
                continue

            # Get display name for component type
            type_display = {
                ComponentType.RESOURCE: "Resources",
                ComponentType.DATA_SOURCE: "Data Sources",
                ComponentType.FUNCTION: "Functions",
            }.get(comp_type, str(comp_type))

            # Create component links
            component_links = {}
            for component, _ in sorted(components, key=lambda x: x[0].name):
                # Create display name (without provider prefix for resources/data sources)
                display_name = component.name
                if comp_type in [ComponentType.RESOURCE, ComponentType.DATA_SOURCE]:  # noqa: SIM102
                    # Strip provider prefix for cleaner display
                    if "_" in display_name:
                        parts = display_name.split("_", 1)
                        if len(parts) == 2:
                            display_name = parts[1]

                # Create file path
                file_path = f"{comp_type.output_subdir}/{component.name}.md"
                component_links[display_name] = file_path

            if component_links:
                section[type_display] = component_links

        if section:
            return {capability: section}

        return None

    def update_mkdocs_config(self, nav: dict[str, Any]) -> None:
        """Update mkdocs.yml with generated navigation.

        Args:
            nav: Navigation dictionary to write
        """
        # Read existing mkdocs.yml if it exists
        if self.mkdocs_file.exists():
            with self.mkdocs_file.open() as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}

        # Update nav section
        config["nav"] = nav.get("nav", [])

        # Write back to file
        with self.mkdocs_file.open("w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Updated mkdocs navigation: {self.mkdocs_file}")
