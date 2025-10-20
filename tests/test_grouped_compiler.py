"""
Unit tests for GroupedExampleCompiler using TDD approach.
"""

from pathlib import Path

import pytest

from plating.bundles import PlatingBundle
from plating.compiler import ExampleGroup, GroupedExampleCompiler


class TestExampleGroup:
    """Test suite for ExampleGroup dataclass."""

    def test_example_group_initialization(self):
        """Test that ExampleGroup can be initialized."""
        group = ExampleGroup(name="full_stack")

        assert group.name == "full_stack"
        assert group.components == {}
        assert group.fixtures == {}
        assert group.component_types == set()

    def test_example_group_with_components(self):
        """Test ExampleGroup with components."""
        group = ExampleGroup(
            name="full_stack",
            components={"network": "resource \"net\" {}", "database": "resource \"db\" {}"},
            component_types={"resource"},
        )

        assert len(group.components) == 2
        assert "network" in group.components
        assert "database" in group.components
        assert "resource" in group.component_types


class TestGroupedExampleCompiler:
    """Test suite for GroupedExampleCompiler functionality."""

    def test_compiler_initialization(self):
        """Test that compiler can be initialized with required attributes."""
        compiler = GroupedExampleCompiler(provider_name="testprovider", provider_version="1.0.0")

        assert compiler.provider_name == "testprovider"
        assert compiler.provider_version == "1.0.0"

    def test_compiler_default_initialization(self):
        """Test compiler initialization with defaults."""
        compiler = GroupedExampleCompiler(provider_name="testprovider")

        assert compiler.provider_name == "testprovider"
        assert compiler.provider_version == "0.0.5"

    def test_discover_groups_single_component(self, tmp_path):
        """Test discovering example groups from a single component."""
        # Create bundle with grouped example
        plating_dir = tmp_path / "network.plating"
        examples_dir = plating_dir / "examples"
        full_stack_dir = examples_dir / "full_stack"
        full_stack_dir.mkdir(parents=True)

        # Create main.tf in group
        (full_stack_dir / "main.tf").write_text('resource "network" "test" {}')

        bundle = PlatingBundle(name="network", plating_dir=plating_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups([bundle])

        assert len(groups) == 1
        assert "full_stack" in groups
        assert groups["full_stack"].name == "full_stack"
        assert "network" in groups["full_stack"].components
        assert "resource" in groups["full_stack"].component_types

    def test_discover_groups_multiple_components(self, tmp_path):
        """Test discovering groups from multiple components."""
        # Create first bundle
        network_dir = tmp_path / "network.plating"
        (network_dir / "examples" / "full_stack").mkdir(parents=True)
        (network_dir / "examples" / "full_stack" / "main.tf").write_text(
            'resource "network" "test" {}'
        )

        # Create second bundle
        database_dir = tmp_path / "database.plating"
        (database_dir / "examples" / "full_stack").mkdir(parents=True)
        (database_dir / "examples" / "full_stack" / "main.tf").write_text(
            'resource "database" "test" {}'
        )

        bundles = [
            PlatingBundle(name="network", plating_dir=network_dir, component_type="resource"),
            PlatingBundle(name="database", plating_dir=database_dir, component_type="resource"),
        ]

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups(bundles)

        assert len(groups) == 1
        assert "full_stack" in groups
        assert len(groups["full_stack"].components) == 2
        assert "network" in groups["full_stack"].components
        assert "database" in groups["full_stack"].components

    def test_discover_groups_with_fixtures(self, tmp_path):
        """Test discovering groups with fixture files."""
        plating_dir = tmp_path / "network.plating"
        examples_dir = plating_dir / "examples"
        full_stack_dir = examples_dir / "full_stack"
        fixtures_dir = full_stack_dir / "fixtures"
        fixtures_dir.mkdir(parents=True)

        (full_stack_dir / "main.tf").write_text('resource "network" "test" {}')
        (fixtures_dir / "config.json").write_text('{"key": "value"}')
        (fixtures_dir / "data.txt").write_text("test data")

        bundle = PlatingBundle(name="network", plating_dir=plating_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups([bundle])

        assert "full_stack" in groups
        assert len(groups["full_stack"].fixtures) == 2
        assert "config.json" in groups["full_stack"].fixtures
        assert "data.txt" in groups["full_stack"].fixtures

    def test_discover_groups_ignores_flat_examples(self, tmp_path):
        """Test that discovery ignores flat .tf files in examples/."""
        plating_dir = tmp_path / "network.plating"
        examples_dir = plating_dir / "examples"
        examples_dir.mkdir(parents=True)

        # Create flat example (should be ignored by grouped compiler)
        (examples_dir / "basic.tf").write_text('resource "network" "basic" {}')

        # Create grouped example
        full_stack_dir = examples_dir / "full_stack"
        full_stack_dir.mkdir(parents=True)
        (full_stack_dir / "main.tf").write_text('resource "network" "advanced" {}')

        bundle = PlatingBundle(name="network", plating_dir=plating_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups([bundle])

        assert len(groups) == 1
        assert "full_stack" in groups
        assert "basic" not in groups

    def test_compile_creates_provider_tf(self, tmp_path):
        """Test that compilation creates provider.tf file."""
        plating_dir = tmp_path / "network.plating"
        (plating_dir / "examples" / "full_stack").mkdir(parents=True)
        (plating_dir / "examples" / "full_stack" / "main.tf").write_text(
            'resource "network" "test" {}'
        )

        bundle = PlatingBundle(name="network", plating_dir=plating_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="testprovider", provider_version="1.0.0")
        groups = compiler.discover_groups([bundle])

        output_dir = tmp_path / "output"
        compiler.compile_groups(groups, output_dir)

        provider_tf = output_dir / "full_stack" / "provider.tf"
        assert provider_tf.exists()

        content = provider_tf.read_text()
        assert "testprovider" in content
        assert "1.0.0" in content
        assert "terraform {" in content
        assert "required_providers {" in content

    def test_compile_creates_component_tf_files(self, tmp_path):
        """Test that compilation creates .tf files for each component."""
        # Create two bundles with same group
        network_dir = tmp_path / "network.plating"
        (network_dir / "examples" / "full_stack").mkdir(parents=True)
        (network_dir / "examples" / "full_stack" / "main.tf").write_text(
            'resource "network" "test" {}'
        )

        database_dir = tmp_path / "database.plating"
        (database_dir / "examples" / "full_stack").mkdir(parents=True)
        (database_dir / "examples" / "full_stack" / "main.tf").write_text(
            'resource "database" "test" {}'
        )

        bundles = [
            PlatingBundle(name="network", plating_dir=network_dir, component_type="resource"),
            PlatingBundle(name="database", plating_dir=database_dir, component_type="resource"),
        ]

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups(bundles)

        output_dir = tmp_path / "output"
        compiler.compile_groups(groups, output_dir)

        group_dir = output_dir / "full_stack"
        assert (group_dir / "network.tf").exists()
        assert (group_dir / "database.tf").exists()

        # Check content
        network_content = (group_dir / "network.tf").read_text()
        assert 'resource "network" "test"' in network_content

    def test_compile_copies_fixtures(self, tmp_path):
        """Test that compilation copies fixture files."""
        plating_dir = tmp_path / "network.plating"
        full_stack_dir = plating_dir / "examples" / "full_stack"
        fixtures_dir = full_stack_dir / "fixtures"
        fixtures_dir.mkdir(parents=True)

        (full_stack_dir / "main.tf").write_text('resource "network" "test" {}')
        (fixtures_dir / "config.json").write_text('{"key": "value"}')

        # Create nested fixture
        nested_dir = fixtures_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "data.txt").write_text("nested data")

        bundle = PlatingBundle(name="network", plating_dir=plating_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups([bundle])

        output_dir = tmp_path / "output"
        compiler.compile_groups(groups, output_dir)

        output_fixtures = output_dir / "full_stack" / "fixtures"
        assert (output_fixtures / "config.json").exists()
        assert (output_fixtures / "nested" / "data.txt").exists()

        assert (output_fixtures / "config.json").read_text() == '{"key": "value"}'
        assert (output_fixtures / "nested" / "data.txt").read_text() == "nested data"

    def test_compile_generates_readme(self, tmp_path):
        """Test that compilation generates README.md."""
        plating_dir = tmp_path / "network.plating"
        (plating_dir / "examples" / "full_stack").mkdir(parents=True)
        (plating_dir / "examples" / "full_stack" / "main.tf").write_text(
            'resource "network" "test" {}'
        )

        bundle = PlatingBundle(name="network", plating_dir=plating_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups([bundle])

        output_dir = tmp_path / "output"
        compiler.compile_groups(groups, output_dir)

        readme = output_dir / "full_stack" / "README.md"
        assert readme.exists()

        content = readme.read_text()
        assert "Full Stack Example" in content or "full_stack" in content.lower()
        assert "terraform init" in content
        assert "terraform plan" in content
        assert "terraform apply" in content

    def test_compile_with_custom_output_dir(self, tmp_path):
        """Test compilation with custom output directory for grouped examples."""
        plating_dir = tmp_path / "network.plating"
        (plating_dir / "examples" / "full_stack").mkdir(parents=True)
        (plating_dir / "examples" / "full_stack" / "main.tf").write_text(
            'resource "network" "test" {}'
        )

        bundle = PlatingBundle(name="network", plating_dir=plating_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups([bundle])

        # Use a completely custom path
        custom_output_dir = tmp_path / "custom_scenarios"
        compiler.compile_groups(groups, custom_output_dir)

        # Should create in custom path
        assert (custom_output_dir / "full_stack").exists()
        assert (custom_output_dir / "full_stack" / "provider.tf").exists()

    def test_compile_detects_tf_filename_collision(self, tmp_path):
        """Test that discovery fails on .tf filename collision."""
        # Create two bundles with SAME NAME
        network1_dir = tmp_path / "network1.plating"
        (network1_dir / "examples" / "full_stack").mkdir(parents=True)
        (network1_dir / "examples" / "full_stack" / "main.tf").write_text(
            'resource "network" "first" {}'
        )

        network2_dir = tmp_path / "network2.plating"
        (network2_dir / "examples" / "full_stack").mkdir(parents=True)
        (network2_dir / "examples" / "full_stack" / "main.tf").write_text(
            'resource "network" "second" {}'
        )

        bundles = [
            PlatingBundle(name="network", plating_dir=network1_dir, component_type="resource"),
            PlatingBundle(name="network", plating_dir=network2_dir, component_type="data_source"),
        ]

        compiler = GroupedExampleCompiler(provider_name="test")

        with pytest.raises(ValueError) as exc_info:
            groups = compiler.discover_groups(bundles)

        error_msg = str(exc_info.value)
        assert "collision" in error_msg.lower()
        assert "full_stack" in error_msg
        assert "network" in error_msg

    def test_compile_detects_fixture_collision(self, tmp_path):
        """Test that discovery fails on fixture filename collision."""
        # Create two bundles with same fixture filename
        network_dir = tmp_path / "network.plating"
        network_fixtures = network_dir / "examples" / "full_stack" / "fixtures"
        network_fixtures.mkdir(parents=True)
        (network_dir / "examples" / "full_stack" / "main.tf").write_text('resource "net" {}')
        (network_fixtures / "config.json").write_text('{"network": true}')

        database_dir = tmp_path / "database.plating"
        database_fixtures = database_dir / "examples" / "full_stack" / "fixtures"
        database_fixtures.mkdir(parents=True)
        (database_dir / "examples" / "full_stack" / "main.tf").write_text('resource "db" {}')
        (database_fixtures / "config.json").write_text('{"database": true}')

        bundles = [
            PlatingBundle(name="network", plating_dir=network_dir, component_type="resource"),
            PlatingBundle(name="database", plating_dir=database_dir, component_type="resource"),
        ]

        compiler = GroupedExampleCompiler(provider_name="test")

        with pytest.raises(ValueError) as exc_info:
            groups = compiler.discover_groups(bundles)

        error_msg = str(exc_info.value)
        assert "collision" in error_msg.lower()
        assert "config.json" in error_msg
        assert "fixtures" in error_msg.lower()

    def test_compile_returns_count(self, tmp_path):
        """Test that compile_groups returns count of compiled groups."""
        # Create bundles for two different groups
        network_dir = tmp_path / "network.plating"
        (network_dir / "examples" / "full_stack").mkdir(parents=True)
        (network_dir / "examples" / "full_stack" / "main.tf").write_text('resource "net" {}')
        (network_dir / "examples" / "minimal").mkdir(parents=True)
        (network_dir / "examples" / "minimal" / "main.tf").write_text('resource "net" {}')

        bundle = PlatingBundle(name="network", plating_dir=network_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups([bundle])

        output_dir = tmp_path / "output"
        count = compiler.compile_groups(groups, output_dir)

        assert count == 2

    def test_discover_groups_multiple_groups_per_bundle(self, tmp_path):
        """Test discovering multiple groups from single bundle."""
        plating_dir = tmp_path / "network.plating"
        examples_dir = plating_dir / "examples"

        # Create two different groups
        (examples_dir / "full_stack").mkdir(parents=True)
        (examples_dir / "full_stack" / "main.tf").write_text('resource "net" "full" {}')

        (examples_dir / "minimal").mkdir(parents=True)
        (examples_dir / "minimal" / "main.tf").write_text('resource "net" "min" {}')

        bundle = PlatingBundle(name="network", plating_dir=plating_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups([bundle])

        assert len(groups) == 2
        assert "full_stack" in groups
        assert "minimal" in groups
        assert groups["full_stack"].components["network"] != groups["minimal"].components["network"]

    def test_discover_groups_ignores_dirs_without_main_tf(self, tmp_path):
        """Test that discovery ignores directories without main.tf."""
        plating_dir = tmp_path / "network.plating"
        examples_dir = plating_dir / "examples"

        # Create directory without main.tf
        (examples_dir / "incomplete").mkdir(parents=True)
        (examples_dir / "incomplete" / "README.md").write_text("This has no main.tf")

        # Create valid directory
        (examples_dir / "valid").mkdir(parents=True)
        (examples_dir / "valid" / "main.tf").write_text('resource "net" {}')

        bundle = PlatingBundle(name="network", plating_dir=plating_dir, component_type="resource")

        compiler = GroupedExampleCompiler(provider_name="test")
        groups = compiler.discover_groups([bundle])

        assert len(groups) == 1
        assert "valid" in groups
        assert "incomplete" not in groups
