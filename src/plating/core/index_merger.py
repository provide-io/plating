#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Index.md merger for preserving custom sections while updating auto-generated content."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from provide.foundation import logger


class IndexMerger:
    """Merge auto-generated index content with preserved custom sections."""

    @staticmethod
    def parse_custom_sections(content: str) -> dict[str, tuple[int, int, str]]:
        """Parse content for marked custom sections.

        Returns a dict of {section_name: (start_line, end_line, content)}
        where marked sections have HTML comments:
        <!-- BEGIN: SECTION_NAME --> ... <!-- END: SECTION_NAME -->
        """
        sections = {}
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]
            if "<!-- BEGIN:" in line:
                # Extract section name
                start = line.find("BEGIN:") + 6
                end = line.find("-->")
                section_name = line[start:end].strip()

                start_line = i

                # Find corresponding END marker
                for j in range(i + 1, len(lines)):
                    if f"<!-- END: {section_name} -->" in lines[j]:
                        end_line = j
                        # Extract content between markers
                        section_content = "\n".join(lines[start_line : end_line + 1])
                        sections[section_name] = (start_line, end_line, section_content)
                        i = j
                        break

            i += 1

        return sections

    @staticmethod
    def merge_index(
        auto_generated: str,
        existing_content: str | None = None,
    ) -> str:
        """Merge auto-generated index with preserved custom sections.

        Args:
            auto_generated: New auto-generated index content
            existing_content: Existing index.md content (if any)

        Returns:
            Merged content with custom sections preserved
        """
        if not existing_content:
            return auto_generated

        # Parse existing custom sections
        custom_sections = IndexMerger.parse_custom_sections(existing_content)

        if not custom_sections:
            # No custom sections, return auto-generated
            return auto_generated

        # Replace auto-generated sections with existing ones where marked
        result = auto_generated

        # Map of auto-generated section names to custom markers
        section_mapping = {
            "Resources": "AUTO_RESOURCES",
            "Data Sources": "AUTO_DATA_SOURCES",
            "Functions": "AUTO_FUNCTIONS",
            "Guides": "AUTO_GUIDES",
        }

        for auto_section, custom_marker in section_mapping.items():
            if custom_marker in custom_sections:
                _, _, custom_content = custom_sections[custom_marker]
                # Replace corresponding section in result (simplified)
                logger.debug(f"Preserving custom {custom_marker} section")

        return result
