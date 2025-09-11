"""
Comprehensive tests for the plater module.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from plating.plater import (
    PlatingPlater,
    _format_component_type,
    _format_example,
    _format_function_arguments,
    _format_function_signature,
    _format_type_string,
    _get_output_subdir,
    _plate_schema_markdown,
    generate_docs,
)
from plating.plating import PlatingBundle


class TestPlatingPlater:
    """Test suite for PlatingPlater."""

    @pytest.fixture
    def mock_bundle(self, tmp_path):
        """Create a mock PlatingBundle for testing."""
        plating_dir = tmp_path / "test.plating"
        plating_dir.mkdir()

        # Create docs directory with template
        docs_dir = plating_dir / "docs"
        docs_dir.mkdir()
        template_file = docs_dir / "test.tmpl.md"
        template_file.write_text("# {{ name }}\n\n{{ component_type }}: {{ description }}")

        # Create examples directory
        examples_dir = plating_dir / "examples"
        examples_dir.mkdir()
        example_file = examples_dir / "example.tf"
        example_file.write_text('resource "test" "example" {}')

        bundle = PlatingBundle(name="test", plating_dir=plating_dir, component_type="resource")
        return bundle

    @pytest.fixture
    def mock_schema_processor(self):
        """Create a mock schema processor."""
        processor = Mock()
        processor.provider_name = "test_provider"
        processor.extract_provider_schema = Mock(
            return_value={
                "provider_schemas": {
                    "test_provider": {
                        "resource_schemas": {
                            "test": {
                                "block": {
                                    "attributes": {
                                        "id": {
                                            "type": "string",
                                            "description": "The ID",
                                            "computed": True,
                                        },
                                        "name": {
                                            "type": "string",
                                            "description": "The name",
                                            "required": True,
                                        },
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )
        return processor

    def test_renderer_initialization_without_bundles(self):
        """Test PlatingPlater initialization without bundles."""
        plater = PlatingPlater()

        assert plater.bundles == []
        assert plater.schema_processor is None
        assert plater.provider_schema is None

    def test_renderer_initialization_with_bundles(self, mock_bundle):
        """Test PlatingPlater initialization with bundles."""
        plater = PlatingPlater(bundles=[mock_bundle])

        assert len(plater.bundles) == 1
        assert plater.bundles[0] == mock_bundle

    def test_renderer_initialization_with_schema_processor(self, mock_bundle, mock_schema_processor):
        """Test PlatingPlater initialization with schema processor."""
        plater = PlatingPlater(bundles=[mock_bundle], schema_processor=mock_schema_processor)

        assert plater.schema_processor == mock_schema_processor
        assert plater.provider_schema is not None
        mock_schema_processor.extract_provider_schema.assert_called_once()

    def test_renderer_with_failed_schema_extraction(self, mock_bundle):
        """Test plater handles failed schema extraction gracefully."""
        mock_processor = Mock()
        mock_processor.extract_provider_schema.side_effect = Exception("Schema error")

        # Should not raise exception
        plater = PlatingPlater(bundles=[mock_bundle], schema_processor=mock_processor)

        assert plater.provider_schema is None

    def test_plate_creates_output_directory(self, mock_bundle, tmp_path):
        """Test that plate creates output directory if it doesn't exist."""
        output_dir = tmp_path / "output"
        assert not output_dir.exists()

        plater = PlatingPlater(bundles=[mock_bundle])
        plater.plate(output_dir)

        assert output_dir.exists()

    def test_plate_single_bundle(self, mock_bundle, tmp_path):
        """Test plating a single bundle."""
        output_dir = tmp_path / "output"
        plater = PlatingPlater(bundles=[mock_bundle])

        plater.plate(output_dir)

        # Check output file was created
        expected_file = output_dir / "resources" / "test.md"
        assert expected_file.exists()

        content = expected_file.read_text()
        assert "# test" in content
        assert "Resource:" in content

    def test_plate_multiple_bundles(self, tmp_path):
        """Test plating multiple bundles."""
        bundles = []
        for i in range(3):
            plating_dir = tmp_path / f"test{i}.plating"
            plating_dir.mkdir()
            docs_dir = plating_dir / "docs"
            docs_dir.mkdir()
            template_file = docs_dir / f"test{i}.tmpl.md"
            template_file.write_text(f"# Test {i}")

            bundle = PlatingBundle(name=f"test{i}", plating_dir=plating_dir, component_type="resource")
            bundles.append(bundle)

        output_dir = tmp_path / "output"
        plater = PlatingPlater(bundles=bundles)

        plater.plate(output_dir)

        # Check all files were created
        for i in range(3):
            expected_file = output_dir / "resources" / f"test{i}.md"
            assert expected_file.exists()
            content = expected_file.read_text()
            assert f"# Test {i}" in content

    def test_plate_with_force_flag(self, mock_bundle, tmp_path):
        """Test plate with force flag overwrites existing files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)

        # Create existing file
        existing_file = output_dir / "resources" / "test.md"
        existing_file.parent.mkdir(parents=True)
        existing_file.write_text("OLD CONTENT")

        plater = PlatingPlater(bundles=[mock_bundle])

        # Without force, should skip
        plater.plate(output_dir, force=False)
        assert "OLD CONTENT" in existing_file.read_text()

        # With force, should overwrite
        plater.plate(output_dir, force=True)
        assert "OLD CONTENT" not in existing_file.read_text()
        assert "# test" in existing_file.read_text()

    def test_plate_bundle_without_template(self, tmp_path):
        """Test that bundles without templates are skipped gracefully."""
        plating_dir = tmp_path / "no_template.plating"
        plating_dir.mkdir()

        bundle = PlatingBundle(name="no_template", plating_dir=plating_dir, component_type="resource")

        output_dir = tmp_path / "output"
        plater = PlatingPlater(bundles=[bundle])

        # Should not raise exception
        plater.plate(output_dir)

        # No file should be created
        expected_file = output_dir / "resources" / "no_template.md"
        assert not expected_file.exists()

    def test_plate_with_error_handling(self, tmp_path):
        """Test that plate handles bundle errors gracefully."""
        # Create bundle with invalid template syntax
        plating_dir = tmp_path / "bad.plating"
        plating_dir.mkdir()
        docs_dir = plating_dir / "docs"
        docs_dir.mkdir()
        template_file = docs_dir / "bad.tmpl.md"
        template_file.write_text("# {{ name")  # Missing closing }}

        bundle = PlatingBundle(name="bad", plating_dir=plating_dir, component_type="resource")

        output_dir = tmp_path / "output"
        plater = PlatingPlater(bundles=[bundle])

        # Should not raise exception (this is the important part)
        plater.plate(output_dir)

        # Output file should not exist due to error
        expected_file = output_dir / "resources" / "bad.md"
        assert not expected_file.exists()

    def test_get_schema_for_component_resource(self, mock_bundle, mock_schema_processor):
        """Test getting schema for a resource component."""
        plater = PlatingPlater(bundles=[mock_bundle], schema_processor=mock_schema_processor)

        schema = plater._get_schema_for_component(mock_bundle)

        assert schema is not None
        assert "block" in schema
        assert "attributes" in schema["block"]

    def test_get_schema_for_component_with_pyvider_prefix(self, mock_schema_processor):
        """Test getting schema for component with pyvider_ prefix."""
        mock_schema_processor.extract_provider_schema.return_value = {
            "provider_schemas": {
                "test_provider": {"resource_schemas": {"pyvider_test": {"block": {"attributes": {}}}}}
            }
        }

        bundle = PlatingBundle(name="test", plating_dir=Path("/tmp/test.plating"), component_type="resource")

        plater = PlatingPlater(bundles=[bundle], schema_processor=mock_schema_processor)

        schema = plater._get_schema_for_component(bundle)
        assert schema is not None

    def test_get_schema_for_data_source(self, mock_schema_processor):
        """Test getting schema for a data source component."""
        mock_schema_processor.extract_provider_schema.return_value = {
            "provider_schemas": {
                "test_provider": {"data_source_schemas": {"test_data": {"block": {"attributes": {}}}}}
            }
        }

        bundle = PlatingBundle(
            name="test_data", plating_dir=Path("/tmp/test.plating"), component_type="data_source"
        )

        plater = PlatingPlater(bundles=[bundle], schema_processor=mock_schema_processor)

        schema = plater._get_schema_for_component(bundle)
        assert schema is not None

    def test_get_schema_for_function(self, mock_schema_processor):
        """Test getting schema for a function component."""
        mock_schema_processor.extract_provider_schema.return_value = {
            "provider_schemas": {
                "test_provider": {
                    "functions": {"test_func": {"signature": {"parameters": [], "return_type": "string"}}}
                }
            }
        }

        bundle = PlatingBundle(
            name="test_func", plating_dir=Path("/tmp/test.plating"), component_type="function"
        )

        plater = PlatingPlater(bundles=[bundle], schema_processor=mock_schema_processor)

        schema = plater._get_schema_for_component(bundle)
        assert schema is not None
        assert "signature" in schema

    def test_plate_template_with_custom_functions(self, mock_bundle):
        """Test _plate_template with custom template functions."""
        plater = PlatingPlater(bundles=[mock_bundle])

        template_content = "# {{ name }}\n{{ schema() }}\n{{ example('test') }}"
        context = {
            "name": "test_component",
            "schema_markdown": "## Schema\nTest schema",
            "examples": {"test": 'resource "test" "example" {}'},
        }
        partials = {}

        result = plater._plate_template(template_content, context, partials)

        assert "# test_component" in result
        assert "## Schema" in result
        assert "```terraform" in result

    def test_plate_template_with_partials(self, mock_bundle):
        """Test _plate_template with partial templates."""
        plater = PlatingPlater(bundles=[mock_bundle])

        template_content = "# {{ name }}\n{{ include('_footer.md') }}"
        context = {"name": "test_component"}
        partials = {"_footer.md": "---\nFooter content"}

        result = plater._plate_template(template_content, context, partials)

        assert "# test_component" in result
        assert "Footer content" in result


class TestHelperFunctions:
    """Test helper functions in the renderer module."""

    def test_build_context_data_basic(self):
        """Test _build_context_data with basic inputs."""
        bundle = PlatingBundle(name="test", plating_dir=Path("/tmp/test.plating"), component_type="resource")
        plater = PlatingPlater()

        context = plater._build_context_data(bundle, None, "test_provider")

        assert context["name"] == "test"
        assert context["component_type"] == "Resource"
        assert context["provider_name"] == "test_provider"

    def test_build_context_data_with_schema(self):
        """Test _build_context_data with schema."""
        bundle = PlatingBundle(name="test", plating_dir=Path("/tmp/test.plating"), component_type="resource")
        plater = PlatingPlater()

        schema = {
            "description": "Test resource",
            "block": {"attributes": {"id": {"type": "string", "computed": True}}},
        }

        context = plater._build_context_data(bundle, schema, "test_provider")

        assert context["description"] == "Test resource"
        assert "schema_markdown" in context

    def test_build_context_data_with_function_schema(self):
        """Test _build_context_data with function schema."""
        bundle = PlatingBundle(
            name="test_func", plating_dir=Path("/tmp/test.plating"), component_type="function"
        )
        plater = PlatingPlater()

        schema = {"signature": {"parameters": [{"name": "input", "type": "string"}], "return_type": "string"}}

        context = plater._build_context_data(bundle, schema, "test_provider")

        assert "signature" in context
        assert "arguments" in context

    def test_format_component_type(self):
        """Test _format_component_type."""
        assert _format_component_type("resource") == "Resource"
        assert _format_component_type("data_source") == "Data Source"
        assert _format_component_type("function") == "Function"
        assert _format_component_type("unknown") == "Unknown"

    def test_get_output_subdir(self):
        """Test _get_output_subdir."""
        assert _get_output_subdir("resource") == "resources"
        assert _get_output_subdir("data_source") == "data_sources"
        assert _get_output_subdir("function") == "functions"
        assert _get_output_subdir("unknown") == "resources"

    def test_format_example(self):
        """Test _format_example."""
        assert _format_example("") == ""
        assert _format_example("test") == "```terraform\ntest\n```"
        assert "```terraform" in _format_example("resource {}")

    def test_format_type_string_simple(self):
        """Test _format_type_string with simple types."""
        assert _format_type_string("string") == "String"
        assert _format_type_string("number") == "Number"
        assert _format_type_string("bool") == "Bool"
        assert _format_type_string(None) == "Dynamic"
        assert _format_type_string("") == "Dynamic"

    def test_format_type_string_complex(self):
        """Test _format_type_string with complex types."""
        assert _format_type_string(["list", "string"]) == "List of String"
        assert _format_type_string(["set", "number"]) == "Set of Number"
        assert _format_type_string(["map", "bool"]) == "Map of Bool"

        # Object type
        obj_type = ["object", {"name": "string", "age": "number"}]
        result = _format_type_string(obj_type)
        assert "Object(" in result
        assert "name: String" in result
        assert "age: Number" in result

    def test_plate_schema_markdown_basic(self):
        """Test _plate_schema_markdown with basic schema."""
        schema = {
            "block": {
                "attributes": {
                    "id": {"type": "string", "description": "The ID", "computed": True},
                    "name": {"type": "string", "description": "The name", "required": True},
                    "tags": {"type": ["map", "string"], "description": "Tags", "optional": True},
                }
            }
        }

        result = _plate_schema_markdown(schema)

        assert "## Schema" in result
        assert "### Required" in result
        assert "`name` (String) - The name" in result
        assert "### Optional" in result
        assert "`tags` (Map of String) - Tags" in result
        assert "### Read-Only" in result
        assert "`id` (String) - The ID" in result

    def test_plate_schema_markdown_with_blocks(self):
        """Test _plate_schema_markdown with nested blocks."""
        schema = {
            "block": {"attributes": {}, "block_types": {"config": {"max_items": 1}, "rules": {"max_items": 0}}}
        }

        result = _plate_schema_markdown(schema)

        assert "### Blocks" in result
        assert "`config` (Optional)" in result
        assert "`rules` (Optional, List)" in result

    def test_plate_schema_markdown_empty(self):
        """Test _plate_schema_markdown with empty schema."""
        assert _plate_schema_markdown({}) == ""
        assert _plate_schema_markdown({"block": {}}) == ""
        assert _plate_schema_markdown({"block": {"attributes": {}}}) == ""

    def test_format_function_signature(self):
        """Test _format_function_signature."""
        schema = {
            "signature": {
                "parameters": [{"name": "input", "type": "string"}, {"name": "count", "type": "number"}],
                "return_type": "list(string)",
            }
        }

        result = _format_function_signature(schema)
        assert result == "(input: string, count: number) -> list(string)"

    def test_format_function_signature_with_variadic(self):
        """Test _format_function_signature with variadic parameter."""
        schema = {
            "signature": {
                "parameters": [{"name": "first", "type": "string"}],
                "variadic_parameter": {"name": "rest", "type": "string"},
                "return_type": "string",
            }
        }

        result = _format_function_signature(schema)
        assert result == "(first: string, ...rest: string) -> string"

    def test_format_function_arguments(self):
        """Test _format_function_arguments."""
        schema = {
            "signature": {
                "parameters": [
                    {"name": "input", "type": "string", "description": "Input value"},
                    {"name": "count", "type": "number", "description": "Number of items"},
                ],
                "variadic_parameter": {"name": "values", "type": "string", "description": "Additional values"},
            }
        }

        result = _format_function_arguments(schema)
        assert "- `input` (string) - Input value" in result
        assert "- `count` (number) - Number of items" in result
        assert "- `...values` (string) - Additional values" in result


class TestGenerateDocsFunction:
    """Test the generate_docs main entry point."""

    @patch("plating.plater.PlatingDiscovery")
    @patch("plating.plater.PlatingPlater")
    def test_generate_docs_basic(self, MockPlater, MockDiscovery, tmp_path):
        """Test generate_docs with basic parameters."""
        # Set up mocks
        mock_bundle = Mock()
        mock_discovery = MockDiscovery.return_value
        mock_discovery.discover_bundles.return_value = [mock_bundle]

        mock_plater = MockPlater.return_value

        # Call generate_docs
        output_dir = tmp_path / "docs"
        generate_docs(output_dir=output_dir)

        # Verify calls
        MockDiscovery.assert_called_once_with("pyvider.components")
        mock_discovery.discover_bundles.assert_called_once_with(None)
        MockPlater.assert_called_once_with([mock_bundle], None)
        mock_plater.plate.assert_called_once_with(Path(output_dir), False)

    @patch("plating.plater.PlatingDiscovery")
    @patch("plating.plater.PlatingPlater")
    @patch("plating.plater.SchemaProcessor")
    def test_generate_docs_with_provider_name(self, MockSchemaProcessor, MockPlater, MockDiscovery, tmp_path):
        """Test generate_docs with provider name for schema extraction."""
        # Set up mocks
        mock_bundle = Mock()
        mock_discovery = MockDiscovery.return_value
        mock_discovery.discover_bundles.return_value = [mock_bundle]

        mock_schema_processor = MockSchemaProcessor.return_value

        # Call generate_docs
        output_dir = tmp_path / "docs"
        generate_docs(output_dir=output_dir, provider_name="test_provider")

        # Verify schema processor was created
        MockSchemaProcessor.assert_called_once()
        MockPlater.assert_called_once_with([mock_bundle], mock_schema_processor)

    @patch("plating.plater.PlatingDiscovery")
    @patch("plating.plater.logger")
    def test_generate_docs_no_bundles(self, mock_logger, MockDiscovery, tmp_path):
        """Test generate_docs when no bundles are found."""
        # Set up mocks
        mock_discovery = MockDiscovery.return_value
        mock_discovery.discover_bundles.return_value = []

        # Call generate_docs
        output_dir = tmp_path / "docs"
        generate_docs(output_dir=output_dir)

        # Should log warning
        mock_logger.warning.assert_called_once()

    @patch("plating.plater.PlatingDiscovery")
    @patch("plating.plater.PlatingPlater")
    def test_generate_docs_with_component_type_filter(self, MockPlater, MockDiscovery, tmp_path):
        """Test generate_docs with component type filter."""
        # Set up mocks
        mock_bundle = Mock()
        mock_discovery = MockDiscovery.return_value
        mock_discovery.discover_bundles.return_value = [mock_bundle]

        # Call generate_docs
        output_dir = tmp_path / "docs"
        generate_docs(output_dir=output_dir, component_type="resource")

        # Verify discovery was called with filter
        mock_discovery.discover_bundles.assert_called_once_with("resource")

    @patch("plating.plater.PlatingDiscovery")
    @patch("plating.plater.PlatingPlater")
    def test_generate_docs_with_force_flag(self, MockPlater, MockDiscovery, tmp_path):
        """Test generate_docs with force flag."""
        # Set up mocks
        mock_bundle = Mock()
        mock_discovery = MockDiscovery.return_value
        mock_discovery.discover_bundles.return_value = [mock_bundle]

        mock_plater = MockPlater.return_value

        # Call generate_docs
        output_dir = tmp_path / "docs"
        generate_docs(output_dir=output_dir, force=True)

        # Verify plate was called with force=True
        mock_plater.plate.assert_called_once_with(Path(output_dir), True)
