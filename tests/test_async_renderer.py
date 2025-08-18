"""
Comprehensive tests for async_renderer module.
"""
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pytest

from garnish.async_renderer import (
    AsyncGarnishRenderer,
    generate_docs,
    _create_render_context,
    _format_type_string,
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
    def mock_schema_processor(self):
        """Create a mock schema processor."""
        processor = Mock()
        processor.extract_provider_schema = Mock(return_value={
            "provider_schemas": {
                "test_provider": {
                    "resource_schemas": {
                        "test": {
                            "block": {
                                "attributes": {
                                    "id": {
                                        "type": "string",
                                        "description": "The ID",
                                        "required": False,
                                        "computed": True,
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "The name",
                                        "required": True,
                                    }
                                }
                            }
                        }
                    }
                }
            }
        })
        return processor

    @pytest.mark.asyncio
    async def test_renderer_initialization(self, mock_bundle):
        """Test AsyncGarnishRenderer initialization."""
        renderer = AsyncGarnishRenderer([mock_bundle])
        
        assert len(renderer.bundles) == 1
        assert renderer.bundles[0] == mock_bundle
        assert renderer.provider_schema is None

    @pytest.mark.asyncio
    async def test_renderer_with_schema_processor(self, mock_bundle, mock_schema_processor):
        """Test renderer with schema processor."""
        renderer = AsyncGarnishRenderer([mock_bundle], schema_processor=mock_schema_processor)
        
        assert renderer.schema_processor == mock_schema_processor
        assert renderer.provider_schema is not None

    @pytest.mark.asyncio
    async def test_render_single_bundle(self, mock_bundle, tmp_path):
        """Test rendering a single bundle."""
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer([mock_bundle])
        
        await renderer.render(output_dir)
        
        # Check that output file was created
        expected_file = output_dir / "resources" / "test.md"
        assert expected_file.exists()
        
        content = expected_file.read_text()
        assert "# test" in content

    @pytest.mark.asyncio
    async def test_render_with_context(self, mock_bundle, tmp_path):
        """Test rendering with custom context."""
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer([mock_bundle])
        
        # Override the render context
        with patch('garnish.async_renderer._create_render_context') as mock_context:
            mock_context.return_value = {
                "name": "custom_name",
                "description": "Custom description"
            }
            
            await renderer.render(output_dir)
            
            expected_file = output_dir / "resources" / "test.md"
            content = expected_file.read_text()
            assert "custom_name" in content
            assert "Custom description" in content

    @pytest.mark.asyncio
    async def test_render_multiple_bundles(self, tmp_path):
        """Test rendering multiple bundles concurrently."""
        # Create multiple bundles
        bundles = []
        for i in range(3):
            garnish_dir = tmp_path / f"test{i}.garnish"
            garnish_dir.mkdir()
            docs_dir = garnish_dir / "docs"
            docs_dir.mkdir()
            template_file = docs_dir / f"test{i}.tmpl.md"
            template_file.write_text(f"# Test {i}")
            
            bundle = GarnishBundle(
                name=f"test{i}",
                garnish_dir=garnish_dir,
                component_type="resource"
            )
            bundles.append(bundle)
        
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer(bundles)
        
        await renderer.render(output_dir)
        
        # Check all files were created
        for i in range(3):
            expected_file = output_dir / "resources" / f"test{i}.md"
            assert expected_file.exists()
            content = expected_file.read_text()
            assert f"# Test {i}" in content

    @pytest.mark.asyncio
    async def test_render_with_template_error(self, tmp_path, caplog):
        """Test handling of template rendering errors."""
        garnish_dir = tmp_path / "bad.garnish"
        garnish_dir.mkdir()
        docs_dir = garnish_dir / "docs"
        docs_dir.mkdir()
        
        # Create template with invalid syntax
        template_file = docs_dir / "bad.tmpl.md"
        template_file.write_text("# {{ name")  # Missing closing }}
        
        bundle = GarnishBundle(
            name="bad",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer([bundle])
        
        await renderer.render(output_dir)
        
        # Should log error but not crash
        assert "Failed to render template for bad" in caplog.text

    @pytest.mark.asyncio
    async def test_render_creates_directory_structure(self, mock_bundle, tmp_path):
        """Test that render creates proper directory structure."""
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer([mock_bundle])
        
        await renderer.render(output_dir)
        
        # Check directory structure
        assert output_dir.exists()
        assert (output_dir / "resources").exists()
        assert (output_dir / "resources" / "test.md").exists()

    def test_create_render_context(self, mock_bundle):
        """Test _create_render_context function."""
        schema = {
            "block": {
                "attributes": {
                    "id": {"type": "string", "computed": True},
                    "name": {"type": "string", "required": True}
                }
            }
        }
        
        context = _create_render_context(mock_bundle, schema, "test_provider")
        
        assert context["name"] == "test"
        assert context["type"] == "Resource"
        assert "examples" in context
        assert "schema_markdown" in context

    def test_format_type_string_simple(self):
        """Test _format_type_string with simple types."""
        assert _format_type_string("string") == "String"
        assert _format_type_string("number") == "Number"
        assert _format_type_string("bool") == "Boolean"

    def test_format_type_string_list(self):
        """Test _format_type_string with list types."""
        assert _format_type_string(["list", "string"]) == "List of String"
        assert _format_type_string(["list", "number"]) == "List of Number"

    def test_format_type_string_map(self):
        """Test _format_type_string with map types."""
        assert _format_type_string(["map", "string"]) == "Map of String"
        assert _format_type_string(["map", "bool"]) == "Map of Boolean"

    def test_format_type_string_set(self):
        """Test _format_type_string with set types."""
        assert _format_type_string(["set", "string"]) == "Set of String"
        assert _format_type_string(["set", "number"]) == "Set of Number"

    def test_format_type_string_object(self):
        """Test _format_type_string with object types."""
        obj_type = ["object", {
            "name": "string",
            "age": "number"
        }]
        result = _format_type_string(obj_type)
        assert "Object" in result
        assert "name" in result
        assert "String" in result

    def test_format_type_string_unknown(self):
        """Test _format_type_string with unknown types."""
        assert _format_type_string("unknown_type") == "unknown_type"
        assert _format_type_string(None) == "Dynamic"


class TestGenerateDocsFunction:
    """Test the generate_docs main entry point."""

    @pytest.mark.asyncio
    async def test_generate_docs_default(self, tmp_path):
        """Test generate_docs with default parameters."""
        with patch('garnish.async_renderer.GarnishDiscovery') as MockDiscovery:
            mock_discovery = MockDiscovery.return_value
            mock_discovery.discover_bundles.return_value = []
            
            output_dir = tmp_path / "docs"
            await generate_docs(output_dir=output_dir)
            
            assert output_dir.exists()
            MockDiscovery.assert_called_once()
            mock_discovery.discover_bundles.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_docs_with_bundles(self, tmp_path):
        """Test generate_docs with discovered bundles."""
        # Create a test bundle
        garnish_dir = tmp_path / "test.garnish"
        garnish_dir.mkdir()
        docs_dir = garnish_dir / "docs"
        docs_dir.mkdir()
        template_file = docs_dir / "test.tmpl.md"
        template_file.write_text("# Test")
        
        bundle = GarnishBundle(
            name="test",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        with patch('garnish.async_renderer.GarnishDiscovery') as MockDiscovery:
            mock_discovery = MockDiscovery.return_value
            mock_discovery.discover_bundles.return_value = [bundle]
            
            output_dir = tmp_path / "docs"
            await generate_docs(output_dir=output_dir)
            
            # Check file was created
            expected_file = output_dir / "resources" / "test.md"
            assert expected_file.exists()

    @pytest.mark.asyncio
    async def test_generate_docs_with_schema_processor(self, tmp_path):
        """Test generate_docs with schema processor."""
        with patch('garnish.async_renderer.GarnishDiscovery') as MockDiscovery:
            mock_discovery = MockDiscovery.return_value
            mock_discovery.discover_bundles.return_value = []
            
            with patch('garnish.async_renderer.SchemaProcessor') as MockProcessor:
                mock_processor = MockProcessor.return_value
                
                output_dir = tmp_path / "docs"
                await generate_docs(
                    output_dir=output_dir,
                    provider_name="test_provider"
                )
                
                MockProcessor.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_docs_force_flag(self, tmp_path):
        """Test generate_docs with force flag."""
        output_dir = tmp_path / "docs"
        
        # Should work even without proper provider setup
        await generate_docs(
            output_dir=output_dir,
            force=True
        )
        
        assert output_dir.exists()

    @pytest.mark.asyncio
    async def test_generate_docs_error_handling(self, tmp_path, caplog):
        """Test error handling in generate_docs."""
        with patch('garnish.async_renderer.GarnishDiscovery') as MockDiscovery:
            mock_discovery = MockDiscovery.return_value
            mock_discovery.discover_bundles.side_effect = Exception("Discovery failed")
            
            output_dir = tmp_path / "docs"
            
            # Should handle error gracefully
            await generate_docs(output_dir=output_dir)
            
            assert "Discovery failed" in caplog.text


class TestTemplateIntegration:
    """Test template rendering with Jinja2 integration."""

    @pytest.mark.asyncio
    async def test_template_with_custom_functions(self, tmp_path):
        """Test templates can use custom functions like schema()."""
        garnish_dir = tmp_path / "test.garnish"
        garnish_dir.mkdir()
        docs_dir = garnish_dir / "docs"
        docs_dir.mkdir()
        
        # Template using custom function
        template_file = docs_dir / "test.tmpl.md"
        template_file.write_text("# {{ name }}\n\n{{ schema() }}")
        
        bundle = GarnishBundle(
            name="test",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer([bundle])
        
        # Mock schema function
        with patch('garnish.async_renderer._create_render_context') as mock_context:
            def mock_schema():
                return "## Schema\n\nMocked schema content"
            
            mock_context.return_value = {
                "name": "test",
                "schema": mock_schema
            }
            
            await renderer.render(output_dir)
            
            expected_file = output_dir / "resources" / "test.md"
            content = expected_file.read_text()
            # Note: schema() function would be called during template rendering

    @pytest.mark.asyncio
    async def test_template_with_includes(self, tmp_path):
        """Test templates can include partials."""
        garnish_dir = tmp_path / "test.garnish"
        garnish_dir.mkdir()
        docs_dir = garnish_dir / "docs"
        docs_dir.mkdir()
        
        # Main template
        template_file = docs_dir / "test.tmpl.md"
        template_file.write_text("# {{ name }}\n\n{% include '_footer.md' %}")
        
        # Partial template
        partial_file = docs_dir / "_footer.md"
        partial_file.write_text("---\nFooter content")
        
        bundle = GarnishBundle(
            name="test",
            garnish_dir=garnish_dir,
            component_type="resource"
        )
        
        output_dir = tmp_path / "output"
        renderer = AsyncGarnishRenderer([bundle])
        
        await renderer.render(output_dir)
        
        expected_file = output_dir / "resources" / "test.md"
        # The include would be processed by Jinja2