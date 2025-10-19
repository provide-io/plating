"""
Unit tests for PlatingBundle class using TDD approach.
"""

from pathlib import Path

from plating.bundles import PlatingBundle


class TestPlatingBundle:
    """Test suite for PlatingBundle functionality."""

    def test_bundle_initialization(self):
        """Test that a PlatingBundle can be initialized with required attributes."""
        bundle = PlatingBundle(
            name="test_resource", plating_dir=Path("/tmp/test.plating"), component_type="resource"
        )

        assert bundle.name == "test_resource"
        assert bundle.plating_dir == Path("/tmp/test.plating")
        assert bundle.component_type == "resource"

    def test_bundle_docs_dir_property(self):
        """Test that docs_dir property returns correct path."""
        bundle = PlatingBundle(name="test", plating_dir=Path("/tmp/test.plating"), component_type="resource")

        assert bundle.docs_dir == Path("/tmp/test.plating/docs")

    def test_bundle_examples_dir_property(self):
        """Test that examples_dir property returns correct path."""
        bundle = PlatingBundle(name="test", plating_dir=Path("/tmp/test.plating"), component_type="resource")

        assert bundle.examples_dir == Path("/tmp/test.plating/examples")

    def test_bundle_fixtures_dir_property(self):
        """Test that fixtures_dir property returns correct path."""
        bundle = PlatingBundle(name="test", plating_dir=Path("/tmp/test.plating"), component_type="resource")

        assert bundle.fixtures_dir == Path("/tmp/test.plating/examples/fixtures")

    def test_load_main_template_with_existing_file(self, tmp_path):
        """Test loading main template when file exists."""
        # Create test structure
        plating_dir = tmp_path / "test.plating"
        docs_dir = plating_dir / "docs"
        docs_dir.mkdir(parents=True)

        template_content = "# {{ name }} Resource\n\n{{ description }}"
        template_file = docs_dir / "test_resource.tmpl.md"
        template_file.write_text(template_content)

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

        loaded_content = bundle.load_main_template()
        assert loaded_content == template_content

    def test_load_main_template_with_missing_file(self, tmp_path):
        """Test loading main template when file doesn't exist."""
        plating_dir = tmp_path / "test.plating"
        plating_dir.mkdir()

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

        loaded_content = bundle.load_main_template()
        assert loaded_content is None

    def test_load_main_template_with_read_error(self, tmp_path):
        """Test loading main template handles read errors gracefully."""
        plating_dir = tmp_path / "test.plating"
        docs_dir = plating_dir / "docs"
        docs_dir.mkdir(parents=True)

        # Create a directory instead of file to cause read error
        template_file = docs_dir / "test_resource.tmpl.md"
        template_file.mkdir()

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

        loaded_content = bundle.load_main_template()
        assert loaded_content is None

    def test_load_examples_with_multiple_files(self, tmp_path):
        """Test loading multiple example files."""
        plating_dir = tmp_path / "test.plating"
        examples_dir = plating_dir / "examples"
        examples_dir.mkdir(parents=True)

        # Create example files
        example1 = examples_dir / "example.tf"
        example1.write_text('resource "test" "example" {}')

        example2 = examples_dir / "advanced.tf"
        example2.write_text('resource "test" "advanced" { count = 2 }')

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

        examples = bundle.load_examples()
        assert len(examples) == 2
        assert "example" in examples
        assert "advanced" in examples
        assert examples["example"] == 'resource "test" "example" {}'
        assert examples["advanced"] == 'resource "test" "advanced" { count = 2 }'

    def test_load_examples_with_empty_directory(self, tmp_path):
        """Test loading examples from empty directory."""
        plating_dir = tmp_path / "test.plating"
        examples_dir = plating_dir / "examples"
        examples_dir.mkdir(parents=True)

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

        examples = bundle.load_examples()
        assert examples == {}

    def test_load_examples_with_missing_directory(self, tmp_path):
        """Test loading examples when directory doesn't exist."""
        plating_dir = tmp_path / "test.plating"
        plating_dir.mkdir()

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

        examples = bundle.load_examples()
        assert examples == {}

    def test_load_examples_ignores_non_tf_files(self, tmp_path):
        """Test that load_examples only loads .tf files."""
        plating_dir = tmp_path / "test.plating"
        examples_dir = plating_dir / "examples"
        examples_dir.mkdir(parents=True)

        # Create various files
        (examples_dir / "example.tf").write_text('resource "test" "example" {}')
        (examples_dir / "README.md").write_text("# Examples")
        (examples_dir / "config.json").write_text('{"key": "value"}')

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

        examples = bundle.load_examples()
        assert len(examples) == 1
        assert "example" in examples
        assert "README" not in examples
        assert "config" not in examples

    def test_load_fixtures_with_nested_files(self, tmp_path):
        """Test loading fixtures from nested directory structure."""
        plating_dir = tmp_path / "test.plating"
        fixtures_dir = plating_dir / "examples" / "fixtures"
        fixtures_dir.mkdir(parents=True)

        # Create nested fixture files
        (fixtures_dir / "data.json").write_text('{"key": "value"}')

        nested_dir = fixtures_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "config.yaml").write_text("key: value")

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

        fixtures = bundle.load_fixtures()
        assert len(fixtures) == 2
        assert "data.json" in fixtures
        assert "nested/config.yaml" in fixtures
        assert fixtures["data.json"] == '{"key": "value"}'
        assert fixtures["nested/config.yaml"] == "key: value"

    def test_load_fixtures_with_missing_directory(self, tmp_path):
        """Test loading fixtures when fixtures directory doesn't exist."""
        plating_dir = tmp_path / "test.plating"
        plating_dir.mkdir()

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

        fixtures = bundle.load_fixtures()
        assert fixtures == {}

    def test_load_partials_from_docs_directory(self, tmp_path):
        """Test loading partial templates from docs directory."""
        plating_dir = tmp_path / "test.plating"
        docs_dir = plating_dir / "docs"
        docs_dir.mkdir(parents=True)

        # Create partial files
        (docs_dir / "_header.md").write_text("## Header")
        (docs_dir / "_footer.md").write_text("## Footer")
        (docs_dir / "main.tmpl.md").write_text("# Main")  # Should not be included

        bundle = PlatingBundle(name="test_resource", plating_dir=plating_dir, component_type="resource")

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
            bundle = PlatingBundle(
                name="test", plating_dir=Path("/tmp/test.plating"), component_type=comp_type
            )
            assert bundle.component_type == comp_type

    def test_bundle_equality(self):
        """Test that bundles with same attributes are equal."""
        bundle1 = PlatingBundle(name="test", plating_dir=Path("/tmp/test.plating"), component_type="resource")

        bundle2 = PlatingBundle(name="test", plating_dir=Path("/tmp/test.plating"), component_type="resource")

        assert bundle1 == bundle2

    def test_bundle_inequality(self):
        """Test that bundles with different attributes are not equal."""
        bundle1 = PlatingBundle(name="test1", plating_dir=Path("/tmp/test.plating"), component_type="resource")

        bundle2 = PlatingBundle(name="test2", plating_dir=Path("/tmp/test.plating"), component_type="resource")

        assert bundle1 != bundle2

    def test_load_examples_with_grouped_examples(self, tmp_path):
        """Test loading both flat and grouped examples."""
        plating_dir = tmp_path / "test.plating"
        examples_dir = plating_dir / "examples"

        # Create flat example
        examples_dir.mkdir(parents=True)
        (examples_dir / "basic.tf").write_text('resource "test" "basic" {}')

        # Create grouped example
        grouped_dir = examples_dir / "full_stack"
        grouped_dir.mkdir(parents=True)
        (grouped_dir / "main.tf").write_text('resource "test" "grouped" {}')

        bundle = PlatingBundle(name="test", plating_dir=plating_dir, component_type="resource")

        examples = bundle.load_examples()
        assert len(examples) == 2
        assert "basic" in examples
        assert "full_stack" in examples
        assert 'resource "test" "basic"' in examples["basic"]
        assert 'resource "test" "grouped"' in examples["full_stack"]

    def test_has_examples_with_grouped_examples(self, tmp_path):
        """Test has_examples returns True for grouped examples."""
        plating_dir = tmp_path / "test.plating"
        examples_dir = plating_dir / "examples"
        grouped_dir = examples_dir / "full_stack"
        grouped_dir.mkdir(parents=True)
        (grouped_dir / "main.tf").write_text('resource "test" "grouped" {}')

        bundle = PlatingBundle(name="test", plating_dir=plating_dir, component_type="resource")

        assert bundle.has_examples() is True

    def test_get_example_groups(self, tmp_path):
        """Test get_example_groups returns list of group names."""
        plating_dir = tmp_path / "test.plating"
        examples_dir = plating_dir / "examples"

        # Create multiple grouped examples
        for group_name in ["full_stack", "minimal", "advanced"]:
            group_dir = examples_dir / group_name
            group_dir.mkdir(parents=True)
            (group_dir / "main.tf").write_text(f'resource "test" "{group_name}" {{}}')

        # Create flat example (should be ignored by get_example_groups)
        (examples_dir / "basic.tf").write_text('resource "test" "basic" {}')

        bundle = PlatingBundle(name="test", plating_dir=plating_dir, component_type="resource")

        groups = bundle.get_example_groups()
        assert len(groups) == 3
        assert "full_stack" in groups
        assert "minimal" in groups
        assert "advanced" in groups
        assert "basic" not in groups  # Flat examples not included

    def test_get_example_groups_empty(self, tmp_path):
        """Test get_example_groups returns empty list when no groups exist."""
        plating_dir = tmp_path / "test.plating"
        bundle = PlatingBundle(name="test", plating_dir=plating_dir, component_type="resource")

        groups = bundle.get_example_groups()
        assert groups == []

    def test_get_example_groups_ignores_dirs_without_main_tf(self, tmp_path):
        """Test that get_example_groups ignores directories without main.tf."""
        plating_dir = tmp_path / "test.plating"
        examples_dir = plating_dir / "examples"

        # Create directory without main.tf
        (examples_dir / "incomplete").mkdir(parents=True)
        (examples_dir / "incomplete" / "README.md").write_text("No main.tf here")

        # Create valid grouped example
        (examples_dir / "valid").mkdir(parents=True)
        (examples_dir / "valid" / "main.tf").write_text('resource "test" {}')

        bundle = PlatingBundle(name="test", plating_dir=plating_dir, component_type="resource")

        groups = bundle.get_example_groups()
        assert len(groups) == 1
        assert "valid" in groups
        assert "incomplete" not in groups

    def test_load_group_fixtures(self, tmp_path):
        """Test load_group_fixtures loads fixtures from grouped example."""
        plating_dir = tmp_path / "test.plating"
        examples_dir = plating_dir / "examples"
        full_stack_dir = examples_dir / "full_stack"
        fixtures_dir = full_stack_dir / "fixtures"
        fixtures_dir.mkdir(parents=True)

        # Create fixture files
        (full_stack_dir / "main.tf").write_text('resource "test" {}')
        (fixtures_dir / "config.json").write_text('{"key": "value"}')
        (fixtures_dir / "data.txt").write_text("test data")

        # Create nested fixture
        nested_dir = fixtures_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "secret.yaml").write_text("password: secret")

        bundle = PlatingBundle(name="test", plating_dir=plating_dir, component_type="resource")

        fixtures = bundle.load_group_fixtures("full_stack")
        assert len(fixtures) == 3
        assert "config.json" in fixtures
        assert "data.txt" in fixtures
        assert "nested/secret.yaml" in fixtures

        # Check that paths are Path objects
        assert isinstance(fixtures["config.json"], Path)
        assert fixtures["config.json"].exists()

    def test_load_group_fixtures_empty(self, tmp_path):
        """Test load_group_fixtures returns empty dict when no fixtures exist."""
        plating_dir = tmp_path / "test.plating"
        examples_dir = plating_dir / "examples"
        full_stack_dir = examples_dir / "full_stack"
        full_stack_dir.mkdir(parents=True)
        (full_stack_dir / "main.tf").write_text('resource "test" {}')

        bundle = PlatingBundle(name="test", plating_dir=plating_dir, component_type="resource")

        fixtures = bundle.load_group_fixtures("full_stack")
        assert fixtures == {}

    def test_load_group_fixtures_nonexistent_group(self, tmp_path):
        """Test load_group_fixtures returns empty dict for nonexistent group."""
        plating_dir = tmp_path / "test.plating"
        bundle = PlatingBundle(name="test", plating_dir=plating_dir, component_type="resource")

        fixtures = bundle.load_group_fixtures("nonexistent")
        assert fixtures == {}
