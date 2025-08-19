"""
Tests for template functions.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from jinja2 import Environment

from garnish.template_functions import TemplateFunctions


class TestTemplateFunctions:
    """Tests for template functions."""

    @pytest.fixture
    def template_functions(self):
        """Create a TemplateFunctions instance."""
        mock_bundle = Mock()
        mock_bundle.load_examples.return_value = {
            "basic": "# Basic example\nresource \"test\" \"example\" {}",
            "advanced": "# Advanced example\nmodule \"test\" {}"
        }
        mock_bundle.load_partials.return_value = {
            "header": "# Header content",
            "footer": "# Footer content"
        }
        
        mock_schema_processor = Mock()
        mock_schema_processor.get_component_schema.return_value = {
            "arguments": [{"name": "id", "type": "string", "required": True}],
            "attributes": [{"name": "name", "type": "string"}]
        }
        
        return TemplateFunctions(
            bundle=mock_bundle,
            schema_processor=mock_schema_processor,
            provider_name="test_provider",
            component_name="test_resource",
            component_type="resource"
        )

    def test_initialization(self, template_functions):
        """Test TemplateFunctions initialization."""
        assert template_functions.provider_name == "test_provider"
        assert template_functions.component_name == "test_resource"
        assert template_functions.component_type == "resource"
        assert template_functions.bundle is not None
        assert template_functions.schema_processor is not None

    def test_get_functions(self, template_functions):
        """Test get_functions returns all template functions."""
        functions = template_functions.get_functions()
        
        assert "example" in functions
        assert "schema" in functions
        assert "partial" in functions
        assert "anchor" in functions
        assert callable(functions["example"])
        assert callable(functions["schema"])
        assert callable(functions["partial"])
        assert callable(functions["anchor"])

    def test_example_function(self, template_functions):
        """Test example function returns example content."""
        functions = template_functions.get_functions()
        example_func = functions["example"]
        
        result = example_func("basic")
        assert result == "```terraform\n# Basic example\nresource \"test\" \"example\" {}\n```"
        
        result = example_func("advanced")
        assert result == "```terraform\n# Advanced example\nmodule \"test\" {}\n```"
        
        # Test missing example
        result = example_func("missing")
        assert result == "<!-- Example 'missing' not found -->"

    def test_schema_function(self, template_functions):
        """Test schema function returns formatted schema."""
        functions = template_functions.get_functions()
        schema_func = functions["schema"]
        
        result = schema_func()
        assert "## Schema" in result
        assert "### Required" in result
        assert "`id`" in result
        assert "string" in result

    def test_schema_function_no_processor(self):
        """Test schema function when no schema processor is available."""
        mock_bundle = Mock()
        mock_bundle.load_examples.return_value = {}
        mock_bundle.load_partials.return_value = {}
        
        tf = TemplateFunctions(
            bundle=mock_bundle,
            schema_processor=None,
            provider_name="test",
            component_name="test",
            component_type="resource"
        )
        
        functions = tf.get_functions()
        schema_func = functions["schema"]
        
        result = schema_func()
        assert result == "<!-- Schema not available -->"

    def test_partial_function(self, template_functions):
        """Test partial function includes partial content."""
        functions = template_functions.get_functions()
        partial_func = functions["partial"]
        
        # Create a mock environment for rendering
        env = Environment()
        env.from_string = Mock(return_value=Mock(render=Mock(return_value="Rendered header")))
        
        with patch.object(template_functions, '_get_jinja_env', return_value=env):
            result = partial_func("header")
            assert result == "Rendered header"
        
        # Test missing partial
        result = partial_func("missing")
        assert result == "<!-- Partial 'missing' not found -->"

    def test_anchor_function(self, template_functions):
        """Test anchor function creates proper anchors."""
        functions = template_functions.get_functions()
        anchor_func = functions["anchor"]
        
        result = anchor_func("Test Header")
        assert result == "test-header"
        
        result = anchor_func("Complex Header-Name_123")
        assert result == "complex-header-name_123"
        
        result = anchor_func("Header with Special@#$Characters")
        assert result == "header-with-specialcharacters"

    def test_format_schema_section(self, template_functions):
        """Test _format_schema_section method."""
        schema = {
            "arguments": [
                {"name": "id", "type": "string", "required": True, "description": "Resource ID"},
                {"name": "name", "type": "string", "required": False, "description": "Resource name"},
                {"name": "tags", "type": "map(string)", "required": False}
            ]
        }
        
        result = template_functions._format_schema_section(schema, "arguments")
        
        assert "### Required" in result
        assert "### Optional" in result
        assert "`id`" in result
        assert "Resource ID" in result
        assert "`name`" in result
        assert "`tags`" in result
        assert "map(string)" in result

    def test_format_schema_section_all_optional(self, template_functions):
        """Test _format_schema_section with all optional arguments."""
        schema = {
            "arguments": [
                {"name": "name", "type": "string", "required": False},
                {"name": "description", "type": "string", "required": False}
            ]
        }
        
        result = template_functions._format_schema_section(schema, "arguments")
        
        assert "### Required" not in result
        assert "### Optional" in result
        assert "`name`" in result
        assert "`description`" in result

    def test_get_jinja_env(self, template_functions):
        """Test _get_jinja_env creates proper Jinja2 environment."""
        env = template_functions._get_jinja_env()
        
        assert env is not None
        # Check that custom functions are registered
        assert "example" in env.globals
        assert "schema" in env.globals
        assert "partial" in env.globals
        assert "anchor" in env.globals