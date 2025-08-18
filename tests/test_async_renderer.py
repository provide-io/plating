"""
Tests for async_renderer module focusing on the garnish-specific functionality.
"""
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pytest

from garnish.async_renderer import (
    AsyncGarnishRenderer,
    DocsGenerator,
    generate_docs_async,
    generate_docs,
)
from garnish.garnish import GarnishBundle


class TestAsyncGarnishRenderer:
    """Test suite for AsyncGarnishRenderer."""

    @pytest.fixture
    def mock_bundle(self, tmp_path):
        """Create a mock GarnishBundle for testing."""
        garnish_dir = tmp_path / "test.garnish"
        garnish_dir.mkdir()
        
        # Create docs directory with template
        docs_dir = garnish_dir / "docs"
        docs_dir.mkdir()
        template_file = docs_dir / "test.tmpl.md"
        template_file.write_text("# {{ name }}\n\n{{ description }}")
        
        # Create examples directory
        examples_dir = garnish_dir / "examples"
        examples_dir.mkdir()
        example_file = examples_dir / "example.tf"
        example_file.write_text('resource "test" "example" {}')
        
        bundle = GarnishBundle(
            name="test",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        return bundle

    @pytest.fixture
    def provider_dir(self, tmp_path):
        """Create a mock provider directory."""
        provider_dir = tmp_path / "terraform-provider-test"
        provider_dir.mkdir()
        
        # Create pyproject.toml
        pyproject_file = provider_dir / "pyproject.toml"
        pyproject_file.write_text("""
[project]
name = "terraform-provider-test"

[tool.pyvbuild]
provider_name = "test"
""")
        return provider_dir

    def test_renderer_initialization(self, provider_dir):
        """Test AsyncGarnishRenderer initialization."""
        renderer = AsyncGarnishRenderer(
            provider_dir=provider_dir,
            output_dir=Path("docs")
        )
        
        assert renderer.provider_dir == provider_dir
        assert renderer.output_dir == Path("docs")
        assert renderer.provider_name == "test"  # Detected from pyproject.toml

    def test_provider_name_detection_from_pyproject(self, tmp_path):
        """Test provider name detection from pyproject.toml."""
        provider_dir = tmp_path / "provider"
        provider_dir.mkdir()
        
        # Test tool.pyvbuild.provider_name
        pyproject_file = provider_dir / "pyproject.toml"
        pyproject_file.write_text("""
[tool.pyvbuild]
provider_name = "custom"
""")
        
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        assert renderer.provider_name == "custom"

    def test_provider_name_detection_from_directory(self, tmp_path):
        """Test provider name detection from directory name."""
        provider_dir = tmp_path / "terraform-provider-aws"
        provider_dir.mkdir()
        
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        assert renderer.provider_name == "aws"

    def test_provider_name_fallback(self, tmp_path):
        """Test provider name fallback to 'provider'."""
        provider_dir = tmp_path / "myproject"
        provider_dir.mkdir()
        
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        assert renderer.provider_name == "provider"

    def test_format_type_string_with_cty_objects(self, provider_dir):
        """Test _format_type_string with CTY type objects."""
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        
        # Test with string representation
        assert renderer._format_type_string("string") == "String"
        assert renderer._format_type_string("number") == "Number"
        assert renderer._format_type_string("bool") == "Boolean"
        
        # Test with dict representation
        assert renderer._format_type_string({}) == "String"
        assert renderer._format_type_string({"type": "string"}) == "String"
        
        # Test with None
        assert renderer._format_type_string(None) == "String"

    def test_get_output_subdir(self, provider_dir):
        """Test _get_output_subdir for different component types."""
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        
        assert renderer._get_output_subdir("resource") == "resources"
        assert renderer._get_output_subdir("data_source") == "data_sources"
        assert renderer._get_output_subdir("function") == "functions"
        assert renderer._get_output_subdir("unknown") == "resources"

    @pytest.mark.asyncio
    async def test_render_provider_index(self, provider_dir, tmp_path):
        """Test rendering provider index page."""
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer(
            provider_dir=provider_dir,
            output_dir=output_dir
        )
        
        await renderer._render_provider_index()
        
        index_file = output_dir / "index.md"
        assert index_file.exists()
        content = index_file.read_text()
        assert "# test Provider" in content
        assert "provider \"test\"" in content

    @pytest.mark.asyncio
    async def test_render_component_bundle(self, provider_dir, mock_bundle, tmp_path):
        """Test rendering a single component bundle."""
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer(
            provider_dir=provider_dir,
            output_dir=output_dir
        )
        
        # Add component info
        renderer.component_info["test"] = {
            "name": "test",
            "type": "Resource",
            "description": "Test resource",
            "schema": {},
            "schema_markdown": "## Schema\n\nTest schema"
        }
        
        await renderer._render_component_bundle(mock_bundle)
        
        # Check output file was created
        expected_file = output_dir / "resources" / "test.md"
        assert expected_file.exists()
        content = expected_file.read_text()
        assert "# test" in content

    @pytest.mark.asyncio
    async def test_render_component_bundle_without_template(self, provider_dir, tmp_path):
        """Test that bundles without templates are skipped gracefully."""
        garnish_dir = tmp_path / "no_template.garnish"
        garnish_dir.mkdir()
        
        bundle = GarnishBundle(
            name="no_template",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer(
            provider_dir=provider_dir,
            output_dir=output_dir
        )
        
        # Should not raise exception
        await renderer._render_component_bundle(bundle)
        
        # No file should be created
        expected_file = output_dir / "resources" / "no_template.md"
        assert not expected_file.exists()

    @pytest.mark.asyncio
    async def test_render_template(self, provider_dir):
        """Test _render_template with custom context."""
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        
        template_content = "# {{ name }}\n{{ type }}: {{ description }}"
        component_info = {
            "name": "test_component",
            "type": "Resource",
            "description": "A test component",
            "schema_markdown": "## Schema"
        }
        examples = {"basic": "resource \"test\" \"example\" {}"}
        partials = {"_header.md": "## Header"}
        
        result = await renderer._render_template(
            template_content,
            component_info,
            examples,
            partials
        )
        
        assert "# test_component" in result
        assert "Resource: A test component" in result

    def test_parse_function_signature(self, provider_dir):
        """Test _parse_function_signature."""
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        
        func_schema = {
            "signature": {
                "parameters": [
                    {"name": "input", "type": "string"},
                    {"name": "count", "type": "number"}
                ],
                "return_type": "list(string)"
            }
        }
        
        result = renderer._parse_function_signature(func_schema)
        assert "function(input: string, count: number) -> list(string)" == result

    def test_parse_function_signature_with_variadic(self, provider_dir):
        """Test _parse_function_signature with variadic parameter."""
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        
        func_schema = {
            "signature": {
                "parameters": [
                    {"name": "first", "type": "string"}
                ],
                "variadic_parameter": {
                    "name": "rest",
                    "type": "string"
                },
                "return_type": "string"
            }
        }
        
        result = renderer._parse_function_signature(func_schema)
        assert "function(first: string, ...rest: string) -> string" == result

    def test_parse_function_arguments(self, provider_dir):
        """Test _parse_function_arguments."""
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        
        func_schema = {
            "signature": {
                "parameters": [
                    {"name": "input", "type": "string", "description": "Input value"},
                    {"name": "count", "type": "number", "description": "Number of items"}
                ]
            }
        }
        
        result = renderer._parse_function_arguments(func_schema)
        assert "- `input` (string) - Input value" in result
        assert "- `count` (number) - Number of items" in result

    def test_parse_variadic_argument(self, provider_dir):
        """Test _parse_variadic_argument."""
        renderer = AsyncGarnishRenderer(provider_dir=provider_dir)
        
        func_schema = {
            "signature": {
                "variadic_parameter": {
                    "name": "values",
                    "type": "string",
                    "description": "Variable number of string values"
                }
            }
        }
        
        result = renderer._parse_variadic_argument(func_schema)
        assert "- `values` (string) - Variable number of string values" == result

    @pytest.mark.asyncio
    async def test_render_all_integration(self, provider_dir, tmp_path):
        """Test full render_all integration."""
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer(
            provider_dir=provider_dir,
            output_dir=output_dir
        )
        
        # Mock the schema processor and discovery
        with patch.object(renderer, '_extract_schemas') as mock_extract:
            mock_extract.return_value = {
                "provider_schemas": {
                    "registry.terraform.io/local/providers/test": {
                        "resource_schemas": {},
                        "data_source_schemas": {},
                        "functions": {}
                    }
                }
            }
            
            with patch.object(renderer, '_discover_bundles') as mock_discover:
                mock_discover.return_value = []
                
                await renderer.render_all()
                
                # Check that output directory was created
                assert output_dir.exists()
                # Check that index was created
                assert (output_dir / "index.md").exists()


class TestDocsGenerator:
    """Test the backward compatibility DocsGenerator class."""

    def test_docs_generator_initialization(self, provider_dir):
        """Test DocsGenerator initialization."""
        generator = DocsGenerator(
            provider_dir=provider_dir,
            output_dir="docs",
            provider_name="test"
        )
        
        assert generator.provider_dir == provider_dir
        assert generator.output_dir == Path("docs")
        assert generator.provider_name == "test"

    @patch('garnish.async_renderer.asyncio.run')
    def test_docs_generator_generate(self, mock_asyncio_run, provider_dir, capsys):
        """Test DocsGenerator.generate method."""
        generator = DocsGenerator(
            provider_dir=provider_dir,
            output_dir="docs"
        )
        
        generator.generate()
        
        # Check that asyncio.run was called
        mock_asyncio_run.assert_called_once()
        
        # Check output messages
        captured = capsys.readouterr()
        assert "Generating documentation" in captured.out
        assert "Documentation generated successfully" in captured.out


class TestModuleFunctions:
    """Test module-level functions."""

    @pytest.mark.asyncio
    async def test_generate_docs_async(self, provider_dir, tmp_path):
        """Test generate_docs_async function."""
        output_dir = tmp_path / "output"
        
        with patch('garnish.async_renderer.AsyncGarnishRenderer.render_all') as mock_render:
            await generate_docs_async(
                provider_dir=provider_dir,
                output_dir=str(output_dir),
                provider_name="test"
            )
            
            mock_render.assert_called_once()

    def test_generate_docs_sync(self, provider_dir, tmp_path):
        """Test generate_docs sync function."""
        output_dir = tmp_path / "output"
        
        with patch('garnish.async_renderer.DocsGenerator.generate') as mock_generate:
            generate_docs(
                provider_dir=provider_dir,
                output_dir=str(output_dir),
                provider_name="test"
            )
            
            mock_generate.assert_called_once()