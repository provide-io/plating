"""
Unit tests for GarnishBundle class using TDD approach.
"""
import tempfile
from pathlib import Path
import pytest

from garnish.garnish import GarnishBundle


class TestGarnishBundle:
    """Test suite for GarnishBundle functionality."""

    def test_bundle_initialization(self):
        """Test that a GarnishBundle can be initialized with required attributes."""
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=Path("/tmp/test.garnish"),
            component_type="resource"
        )
        
        assert bundle.name == "test_resource"
        assert bundle.garnish_dir == Path("/tmp/test.garnish")
        assert bundle.component_type == "resource"

    def test_bundle_docs_dir_property(self):
        """Test that docs_dir property returns correct path."""
        bundle = GarnishBundle(
            name="test",
            garnish_dir=Path("/tmp/test.garnish"),
            component_type="resource"
        )
        
        assert bundle.docs_dir == Path("/tmp/test.garnish/docs")

    def test_bundle_examples_dir_property(self):
        """Test that examples_dir property returns correct path."""
        bundle = GarnishBundle(
            name="test",
            garnish_dir=Path("/tmp/test.garnish"),
            component_type="resource"
        )
        
        assert bundle.examples_dir == Path("/tmp/test.garnish/examples")

    def test_bundle_fixtures_dir_property(self):
        """Test that fixtures_dir property returns correct path."""
        bundle = GarnishBundle(
            name="test",
            garnish_dir=Path("/tmp/test.garnish"),
            component_type="resource"
        )
        
        assert bundle.fixtures_dir == Path("/tmp/test.garnish/examples/fixtures")

    def test_load_main_template_with_existing_file(self, tmp_path):
        """Test loading main template when file exists."""
        # Create test structure
        garnish_dir = tmp_path / "test.garnish"
        docs_dir = garnish_dir / "docs"
        docs_dir.mkdir(parents=True)
        
        template_content = "# {{ name }} Resource\n\n{{ description }}"
        template_file = docs_dir / "test_resource.tmpl.md"
        template_file.write_text(template_content)
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        loaded_content = bundle.load_main_template()
        assert loaded_content == template_content

    def test_load_main_template_with_missing_file(self, tmp_path):
        """Test loading main template when file doesn't exist."""
        garnish_dir = tmp_path / "test.garnish"
        garnish_dir.mkdir()
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        loaded_content = bundle.load_main_template()
        assert loaded_content is None

    def test_load_main_template_with_read_error(self, tmp_path):
        """Test loading main template handles read errors gracefully."""
        garnish_dir = tmp_path / "test.garnish"
        docs_dir = garnish_dir / "docs"
        docs_dir.mkdir(parents=True)
        
        # Create a directory instead of file to cause read error
        template_file = docs_dir / "test_resource.tmpl.md"
        template_file.mkdir()
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        loaded_content = bundle.load_main_template()
        assert loaded_content is None

    def test_load_examples_with_multiple_files(self, tmp_path):
        """Test loading multiple example files."""
        garnish_dir = tmp_path / "test.garnish"
        examples_dir = garnish_dir / "examples"
        examples_dir.mkdir(parents=True)
        
        # Create example files
        example1 = examples_dir / "example.tf"
        example1.write_text('resource "test" "example" {}')
        
        example2 = examples_dir / "advanced.tf"
        example2.write_text('resource "test" "advanced" { count = 2 }')
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        examples = bundle.load_examples()
        assert len(examples) == 2
        assert "example" in examples
        assert "advanced" in examples
        assert examples["example"] == 'resource "test" "example" {}'
        assert examples["advanced"] == 'resource "test" "advanced" { count = 2 }'

    def test_load_examples_with_empty_directory(self, tmp_path):
        """Test loading examples from empty directory."""
        garnish_dir = tmp_path / "test.garnish"
        examples_dir = garnish_dir / "examples"
        examples_dir.mkdir(parents=True)
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        examples = bundle.load_examples()
        assert examples == {}

    def test_load_examples_with_missing_directory(self, tmp_path):
        """Test loading examples when directory doesn't exist."""
        garnish_dir = tmp_path / "test.garnish"
        garnish_dir.mkdir()
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        examples = bundle.load_examples()
        assert examples == {}

    def test_load_examples_ignores_non_tf_files(self, tmp_path):
        """Test that load_examples only loads .tf files."""
        garnish_dir = tmp_path / "test.garnish"
        examples_dir = garnish_dir / "examples"
        examples_dir.mkdir(parents=True)
        
        # Create various files
        (examples_dir / "example.tf").write_text('resource "test" "example" {}')
        (examples_dir / "README.md").write_text("# Examples")
        (examples_dir / "config.json").write_text('{"key": "value"}')
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        examples = bundle.load_examples()
        assert len(examples) == 1
        assert "example" in examples
        assert "README" not in examples
        assert "config" not in examples

    def test_load_fixtures_with_nested_files(self, tmp_path):
        """Test loading fixtures from nested directory structure."""
        garnish_dir = tmp_path / "test.garnish"
        fixtures_dir = garnish_dir / "examples" / "fixtures"
        fixtures_dir.mkdir(parents=True)
        
        # Create nested fixture files
        (fixtures_dir / "data.json").write_text('{"key": "value"}')
        
        nested_dir = fixtures_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "config.yaml").write_text("key: value")
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        fixtures = bundle.load_fixtures()
        assert len(fixtures) == 2
        assert "data.json" in fixtures
        assert "nested/config.yaml" in fixtures
        assert fixtures["data.json"] == '{"key": "value"}'
        assert fixtures["nested/config.yaml"] == "key: value"

    def test_load_fixtures_with_missing_directory(self, tmp_path):
        """Test loading fixtures when fixtures directory doesn't exist."""
        garnish_dir = tmp_path / "test.garnish"
        garnish_dir.mkdir()
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        fixtures = bundle.load_fixtures()
        assert fixtures == {}

    def test_load_partials_from_docs_directory(self, tmp_path):
        """Test loading partial templates from docs directory."""
        garnish_dir = tmp_path / "test.garnish"
        docs_dir = garnish_dir / "docs"
        docs_dir.mkdir(parents=True)
        
        # Create partial files
        (docs_dir / "_header.md").write_text("## Header")
        (docs_dir / "_footer.md").write_text("## Footer")
        (docs_dir / "main.tmpl.md").write_text("# Main")  # Should not be included
        
        bundle = GarnishBundle(
            name="test_resource",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        partials = bundle.load_partials()
        assert len(partials) == 2
        assert "_header.md" in partials
        assert "_footer.md" in partials
        assert "main.tmpl.md" not in partials
        assert partials["_header.md"] == "## Header"

    def test_component_type_validation(self):
        """Test that component_type accepts valid values."""
        valid_types = ["resource", "data_source", "function"]
        
        for comp_type in valid_types:
            bundle = GarnishBundle(
                name="test",
                garnish_dir=Path("/tmp/test.garnish"),
                component_type=comp_type
            )
            assert bundle.component_type == comp_type

    def test_bundle_equality(self):
        """Test that bundles with same attributes are equal."""
        bundle1 = GarnishBundle(
            name="test",
            garnish_dir=Path("/tmp/test.garnish"),
            component_type="resource"
        )
        
        bundle2 = GarnishBundle(
            name="test",
            garnish_dir=Path("/tmp/test.garnish"),
            component_type="resource"
        )
        
        assert bundle1 == bundle2

    def test_bundle_inequality(self):
        """Test that bundles with different attributes are not equal."""
        bundle1 = GarnishBundle(
            name="test1",
            garnish_dir=Path("/tmp/test.garnish"),
            component_type="resource"
        )
        
        bundle2 = GarnishBundle(
            name="test2",
            garnish_dir=Path("/tmp/test.garnish"),
            component_type="resource"
        )
        
        assert bundle1 != bundle2