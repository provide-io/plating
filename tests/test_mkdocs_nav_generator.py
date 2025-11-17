#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Test module for MkDocs navigation generator."""

import yaml

from plating.bundles import PlatingBundle
from plating.mkdocs.nav_generator import MkdocsNavGenerator
from plating.types import ComponentType


class TestMkdocsNavGenerator:
    """Test suite for MkdocsNavGenerator class."""

    def test_mkdocs_nav_generator_initialization(self, temp_directory) -> None:
        """Test constructor initializes correctly."""
        generator = MkdocsNavGenerator(temp_directory)

        assert generator.base_path == temp_directory, "Should set base_path"
        assert generator.mkdocs_file == temp_directory / "mkdocs.yml", "Should set mkdocs_file path"

    def test_generate_nav_with_capabilities(self, temp_directory, sample_components_mixed_types) -> None:
        """Generate nav with multiple capabilities."""
        generator = MkdocsNavGenerator(temp_directory)
        components = sample_components_mixed_types

        nav = generator.generate_nav(components, include_guides=False)

        assert "nav" in nav, "Should have nav key"
        nav_items = nav["nav"]

        # First item should be Overview
        assert nav_items[0] == {"Overview": "index.md"}, "First item should be Overview"

        # Should have capability sections
        capability_sections = [item for item in nav_items if isinstance(item, dict) and "Overview" not in item]
        assert len(capability_sections) >= 3, "Should have at least 3 capability sections"

        # Check for expected capabilities
        capability_names = []
        for section in capability_sections:
            capability_names.extend(section.keys())

        assert "Lens" in capability_names, "Should have Lens capability"
        assert "Utilities" in capability_names, "Should have Utilities capability"
        assert "Test Mode" in capability_names, "Should have Test Mode capability"

    def test_generate_nav_guides_detection(self, temp_directory, sample_components_mixed_types) -> None:
        """Auto-detect and include guides."""
        # Create guides directory
        guides_dir = temp_directory / "docs" / "guides"
        guides_dir.mkdir(parents=True)
        (guides_dir / "getting_started.md").write_text("# Getting Started")

        generator = MkdocsNavGenerator(temp_directory)
        components = sample_components_mixed_types

        nav = generator.generate_nav(components, include_guides=True)

        nav_items = nav["nav"]

        # Check for Guides section
        guides_sections = [item for item in nav_items if isinstance(item, dict) and "Guides" in item]
        assert len(guides_sections) == 1, "Should have exactly one Guides section"

        guides_section = guides_sections[0]["Guides"]
        assert "Getting Started" in guides_section, "Should include getting started guide"

    def test_generate_capability_section_resources(self, temp_directory) -> None:
        """Generate resource sections."""

        # Create resource component
        resource_dir = temp_directory / "test_resource.plating"
        docs_dir = resource_dir / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "test_resource.tmpl.md").write_text("# Test Resource")

        component = PlatingBundle("test_resource", resource_dir, "resource")
        types_dict = {ComponentType.RESOURCE: [(component, ComponentType.RESOURCE)]}

        generator = MkdocsNavGenerator(temp_directory)
        section = generator._generate_capability_section("Utilities", types_dict)

        assert section is not None, "Should generate section"
        assert "Utilities" in section, "Should have capability name"
        assert "Resources" in section["Utilities"], "Should have Resources subsection"
        # Note: component name gets split on underscore, so "test_resource" becomes "resource"
        assert "resource" in section["Utilities"]["Resources"], "Should include component"

    def test_generate_capability_section_data_sources(self, temp_directory) -> None:
        """Generate data source sections."""

        # Create data source component
        data_dir = temp_directory / "test_data.plating"
        docs_dir = data_dir / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "test_data.tmpl.md").write_text("# Test Data Source")

        component = PlatingBundle("test_data", data_dir, "data_source")
        types_dict = {ComponentType.DATA_SOURCE: [(component, ComponentType.DATA_SOURCE)]}

        generator = MkdocsNavGenerator(temp_directory)
        section = generator._generate_capability_section("Utilities", types_dict)

        assert section is not None, "Should generate section"
        assert "Utilities" in section, "Should have capability name"
        assert "Data Sources" in section["Utilities"], "Should have Data Sources subsection"
        # Note: component name gets split on underscore, so "test_data" becomes "data"
        assert "data" in section["Utilities"]["Data Sources"], "Should include component"

    def test_generate_capability_section_functions(self, temp_directory) -> None:
        """Generate function sections."""

        # Create function component
        func_dir = temp_directory / "test_func.plating"
        docs_dir = func_dir / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "test_func.tmpl.md").write_text("# Test Function")

        component = PlatingBundle("test_func", func_dir, "function")
        types_dict = {ComponentType.FUNCTION: [(component, ComponentType.FUNCTION)]}

        generator = MkdocsNavGenerator(temp_directory)
        section = generator._generate_capability_section("Utilities", types_dict)

        assert section is not None, "Should generate section"
        assert "Utilities" in section, "Should have capability name"
        assert "Functions" in section["Utilities"], "Should have Functions subsection"
        assert "test_func" in section["Utilities"]["Functions"], "Should include component"

    def test_update_mkdocs_config_creates_file(self, temp_directory) -> None:
        """Create mkdocs.yml if doesn't exist."""
        generator = MkdocsNavGenerator(temp_directory)
        mkdocs_file = temp_directory / "mkdocs.yml"

        # Ensure file doesn't exist
        assert not mkdocs_file.exists(), "mkdocs.yml should not exist initially"

        nav_dict = {"nav": [{"Overview": "index.md"}]}
        generator.update_mkdocs_config(nav_dict)

        # Check file was created
        assert mkdocs_file.exists(), "mkdocs.yml should be created"

        # Verify content
        with mkdocs_file.open() as f:
            config = yaml.safe_load(f)

        assert "nav" in config, "Config should have nav key"
        assert config["nav"] == [{"Overview": "index.md"}], "Should write correct nav structure"

    def test_update_mkdocs_config_preserves_other_settings(self, temp_directory) -> None:
        """Don't overwrite other config sections."""
        generator = MkdocsNavGenerator(temp_directory)
        mkdocs_file = temp_directory / "mkdocs.yml"

        # Create initial config with other settings
        initial_config = {
            "site_name": "Test Provider Docs",
            "theme": {"name": "material", "palette": {"primary": "blue"}},
            "plugins": ["search", "minify"],
            "nav": [{"Old": "old.md"}],
        }
        with mkdocs_file.open("w") as f:
            yaml.dump(initial_config, f)

        # Update with new nav
        new_nav = {
            "nav": [{"Overview": "index.md"}, {"Guides": {"Getting Started": "guides/getting_started.md"}}]
        }
        generator.update_mkdocs_config(new_nav)

        # Verify other settings preserved
        with mkdocs_file.open() as f:
            updated_config = yaml.safe_load(f)

        assert updated_config["site_name"] == "Test Provider Docs", "Should preserve site_name"
        assert updated_config["theme"]["name"] == "material", "Should preserve theme"
        assert updated_config["theme"]["palette"]["primary"] == "blue", "Should preserve theme details"
        assert updated_config["plugins"] == ["search", "minify"], "Should preserve plugins"

        # But nav should be updated
        assert len(updated_config["nav"]) == 2, "Should have new nav structure"
        assert updated_config["nav"][0] == {"Overview": "index.md"}, "Should have new nav items"

    def test_generate_guides_nav_no_guides_directory(self, temp_directory) -> None:
        """Return empty when no guides directory exists."""
        generator = MkdocsNavGenerator(temp_directory)

        guides_nav = generator._generate_guides_nav()

        assert guides_nav == [], "Should return empty list when guides directory doesn't exist"

    def test_generate_guides_nav_empty_guides_directory(self, temp_directory) -> None:
        """Return empty when guides directory has no markdown files."""
        guides_dir = temp_directory / "docs" / "guides"
        guides_dir.mkdir(parents=True)

        generator = MkdocsNavGenerator(temp_directory)
        guides_nav = generator._generate_guides_nav()

        assert guides_nav == [], "Should return empty list for empty guides directory"


# 🍽️📖🔚
