#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test module for guide discovery and rendering."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from plating.mkdocs.nav_generator import MkdocsNavGenerator


class TestGuideDiscovery:
    """Test suite for guide discovery functionality."""

    def test_generate_guides_nav_no_guides_directory(self, temp_directory):
        """Return empty when no guides directory exists."""
        generator = MkdocsNavGenerator(temp_directory)

        # Guides directory doesn't exist
        guides_nav = generator._generate_guides_nav()

        assert guides_nav == [], "Should return empty list when guides directory doesn't exist"

    def test_generate_guides_nav_with_guides(self, temp_directory):
        """Find and list guide files."""
        # Create guides directory with files
        guides_dir = temp_directory / "docs" / "guides"
        guides_dir.mkdir(parents=True)

        (guides_dir / "getting_started.md").write_text("# Getting Started\n\nGuide content")
        (guides_dir / "advanced_usage.md").write_text("# Advanced Usage\n\nAdvanced content")
        (guides_dir / "troubleshooting.md").write_text("# Troubleshooting\n\nTroubleshooting content")

        generator = MkdocsNavGenerator(temp_directory)
        guides_nav = generator._generate_guides_nav()

        assert len(guides_nav) == 1, "Should return one Guides section"
        assert "Guides" in guides_nav[0], "Should have Guides key"

        guides_dict = guides_nav[0]["Guides"]
        assert len(guides_dict) == 3, "Should have 3 guide entries"

        # Check that guides are present
        guide_titles = list(guides_dict.keys())
        assert "Getting Started" in guide_titles, "Should have Getting Started guide"
        assert "Advanced Usage" in guide_titles, "Should have Advanced Usage guide"
        assert "Troubleshooting" in guide_titles, "Should have Troubleshooting guide"

    def test_generate_guides_nav_converts_filenames(self, temp_directory):
        """Convert snake_case and kebab-case to Title Case."""
        guides_dir = temp_directory / "docs" / "guides"
        guides_dir.mkdir(parents=True)

        (guides_dir / "getting_started.md").write_text("# Guide")
        (guides_dir / "api-reference.md").write_text("# Guide")
        (guides_dir / "common_patterns.md").write_text("# Guide")

        generator = MkdocsNavGenerator(temp_directory)
        guides_nav = generator._generate_guides_nav()

        guides_dict = guides_nav[0]["Guides"]
        guide_titles = list(guides_dict.keys())

        assert "Getting Started" in guide_titles, "Should convert getting_started to Getting Started"
        assert "Api Reference" in guide_titles, "Should convert api-reference to Api Reference"
        assert "Common Patterns" in guide_titles, "Should convert common_patterns to Common Patterns"

        # Check file paths are correct
        assert guides_dict["Getting Started"] == "guides/getting_started.md", "Should have correct file path"
        assert guides_dict["Api Reference"] == "guides/api-reference.md", "Should preserve original filename in path"

    def test_generate_guides_nav_ignores_non_markdown(self, temp_directory):
        """Only include .md files."""
        guides_dir = temp_directory / "docs" / "guides"
        guides_dir.mkdir(parents=True)

        # Create various file types
        (guides_dir / "valid_guide.md").write_text("# Guide")
        (guides_dir / "README.txt").write_text("Not markdown")
        (guides_dir / "image.png").write_text("Binary data")
        (guides_dir / "config.yaml").write_text("key: value")
        (guides_dir / "script.py").write_text("print('hello')")

        generator = MkdocsNavGenerator(temp_directory)
        guides_nav = generator._generate_guides_nav()

        assert len(guides_nav) == 1, "Should return one Guides section"
        guides_dict = guides_nav[0]["Guides"]

        assert len(guides_dict) == 1, "Should only include .md files"
        assert "Valid Guide" in guides_dict, "Should include the markdown file"

    def test_generate_guides_nav_alphabetical_order(self, temp_directory):
        """Sort guides alphabetically."""
        guides_dir = temp_directory / "docs" / "guides"
        guides_dir.mkdir(parents=True)

        # Create files in non-alphabetical order
        (guides_dir / "zebra.md").write_text("# Zebra")
        (guides_dir / "alpha.md").write_text("# Alpha")
        (guides_dir / "middle.md").write_text("# Middle")
        (guides_dir / "beta.md").write_text("# Beta")

        generator = MkdocsNavGenerator(temp_directory)
        guides_nav = generator._generate_guides_nav()

        guides_dict = guides_nav[0]["Guides"]
        guide_titles = list(guides_dict.keys())

        # Check that guides are sorted alphabetically
        expected_order = ["Alpha", "Beta", "Middle", "Zebra"]
        assert guide_titles == expected_order, f"Should sort alphabetically: expected {expected_order}, got {guide_titles}"

    def test_generate_guides_nav_empty_directory(self, temp_directory):
        """Return empty when guides directory exists but is empty."""
        guides_dir = temp_directory / "docs" / "guides"
        guides_dir.mkdir(parents=True)

        generator = MkdocsNavGenerator(temp_directory)
        guides_nav = generator._generate_guides_nav()

        assert guides_nav == [], "Should return empty list when guides directory is empty"

    def test_generate_guides_nav_subdirectories_ignored(self, temp_directory):
        """Only process files in guides root, not subdirectories."""
        guides_dir = temp_directory / "docs" / "guides"
        guides_dir.mkdir(parents=True)

        # Create file in root
        (guides_dir / "root_guide.md").write_text("# Root Guide")

        # Create subdirectory with file
        subdir = guides_dir / "advanced"
        subdir.mkdir()
        (subdir / "nested_guide.md").write_text("# Nested Guide")

        generator = MkdocsNavGenerator(temp_directory)
        guides_nav = generator._generate_guides_nav()

        guides_dict = guides_nav[0]["Guides"]

        assert len(guides_dict) == 1, "Should only include files in root directory"
        assert "Root Guide" in guides_dict, "Should include root guide"
        assert "Nested Guide" not in guides_dict, "Should not include nested guide"


# 🍽️📖🔚
