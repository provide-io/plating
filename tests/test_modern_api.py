#
# tests/test_modern_api.py
#
"""Tests for the modern async API."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest

from provide.foundation import pout, perr, pin  # Foundation I/O helpers
from provide.foundation.testing import (
    MockContext,
    reset_foundation_setup_for_testing,
    temp_config_file,
    temporary_cert_file  # Can use for temp files
)

from plating import (
    Plating, 
    ComponentType,
    PlatingContext,
    SchemaInfo,
    ArgumentInfo,
    AdornResult,
    PlateResult,
    ValidationResult
)


class TestModernAPI:
    """Test the modern async Plating API."""
    
    def setup_method(self):
        """Setup for each test using foundation patterns."""
        reset_foundation_setup_for_testing()
        pout("Setting up modern API test", color="blue")
    
    def test_component_type_enum(self):
        """Test ComponentType enum functionality."""
        # Test enum values
        assert ComponentType.RESOURCE.value == "resource"
        assert ComponentType.DATA_SOURCE.value == "data_source"
        assert ComponentType.FUNCTION.value == "function"
        
        # Test display names
        assert ComponentType.RESOURCE.display_name == "Resource"
        assert ComponentType.DATA_SOURCE.display_name == "Data Source"
        assert ComponentType.FUNCTION.display_name == "Function"
        
        # Test output subdirs
        assert ComponentType.RESOURCE.output_subdir == "resources"
        assert ComponentType.DATA_SOURCE.output_subdir == "data_sources"
        assert ComponentType.FUNCTION.output_subdir == "functions"
    
    def test_plating_context(self):
        """Test PlatingContext dataclass."""
        context = PlatingContext(
            name="test_resource",
            component_type=ComponentType.RESOURCE,
            provider_name="test_provider",
            description="A test resource"
        )
        
        assert context.name == "test_resource"
        assert context.component_type == ComponentType.RESOURCE
        assert context.provider_name == "test_provider"
        assert context.description == "A test resource"
        
        # Test to_dict conversion
        context_dict = context.to_dict()
        assert context_dict["name"] == "test_resource"
        assert context_dict["component_type"] == "Resource"
        assert context_dict["provider_name"] == "test_provider"
        assert context_dict["description"] == "A test resource"
    
    def test_schema_info(self):
        """Test SchemaInfo dataclass."""
        schema_dict = {
            "description": "Test schema",
            "block": {
                "attributes": {
                    "id": {"type": "string", "computed": True, "description": "ID"},
                    "name": {"type": "string", "required": True, "description": "Name"}
                }
            }
        }
        
        schema = SchemaInfo.from_dict(schema_dict)
        assert schema.description == "Test schema"
        assert "id" in schema.attributes
        assert "name" in schema.attributes
        
        # Test markdown generation
        markdown = schema.to_markdown()
        assert "## Schema" in markdown
        assert "### Required" in markdown
        assert "### Read-Only" in markdown
        assert "`name` (String) - Name" in markdown
        assert "`id` (String) - ID" in markdown
    
    def test_argument_info(self):
        """Test ArgumentInfo dataclass."""
        arg = ArgumentInfo(
            name="input",
            type="string", 
            description="Input parameter",
            required=True
        )
        
        assert arg.name == "input"
        assert arg.type == "string"
        assert arg.description == "Input parameter"
        assert arg.required is True
    
    def test_result_types(self):
        """Test result type dataclasses."""
        # AdornResult
        adorn_result = AdornResult(
            components_processed=5,
            templates_generated=3,
            examples_created=2,
            errors=[]
        )
        assert adorn_result.success is True
        assert adorn_result.components_processed == 5
        
        # PlateResult
        plate_result = PlateResult(
            bundles_processed=3,
            files_generated=3,
            duration_seconds=1.5,
            errors=[],
            output_files=[Path("test.md")]
        )
        assert plate_result.success is True
        assert plate_result.duration_seconds == 1.5
        
        # ValidationResult
        validation_result = ValidationResult(
            total=10,
            passed=8,
            failed=2,
            skipped=0,
            duration_seconds=30.0
        )
        assert validation_result.success is False  # Because failed > 0
        assert validation_result.total == 10
    
    @pytest.mark.asyncio
    async def test_plating_api_initialization(self):
        """Test Plating API initialization using foundation patterns."""
        # Use foundation MockContext as base
        mock_base_context = MockContext()
        
        # Create PlatingContext with foundation context features
        context = PlatingContext(
            provider_name="test_provider",
            log_level="DEBUG",  # Foundation context feature
            no_color=True       # Foundation context feature
        )
        
        pout(f"Initializing API with provider: {context.provider_name}", color="cyan")
        
        api = Plating(context=context, package_name="test.components")
        
        assert api.package_name == "test.components"
        assert api.context.provider_name == "test_provider"
        assert api.context.log_level == "DEBUG"  # Foundation feature
        assert api.registry is not None
        assert api._schema_processor is not None
        
        pout("API initialization test completed", color="green")
    
    @pytest.mark.asyncio 
    @patch('plating.registry.PlatingDiscovery')
    async def test_adorn_operation(self, mock_discovery):
        """Test adorn operation with type-safe API."""
        # Mock the discovery and registry
        mock_bundle = Mock()
        mock_bundle.name = "test_resource"
        mock_bundle.component_type = "resource"
        mock_bundle.has_main_template.return_value = False  # Needs template
        mock_bundle.plating_dir = Path("/mock/path")
        
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_bundles.return_value = [mock_bundle]
        mock_discovery.return_value = mock_discovery_instance
        
        # Mock the template generator and file operations
        with patch('plating.adorner.templates.TemplateGenerator') as mock_template_gen, \
             patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('pathlib.Path.write_text') as mock_write_text:
            
            # Make the mock method async and return a future
            async def mock_generate_template(*args, **kwargs):
                return "# Mock Template"
            mock_template_gen.return_value.generate_template = mock_generate_template
            
            api = Plating()
            result = await api.adorn([ComponentType.RESOURCE])
            
            # Verify result
            assert isinstance(result, AdornResult)
            assert result.templates_generated == 1
            assert result.success is True
            
            # Verify file operations were called
            mock_mkdir.assert_called()
            mock_write_text.assert_called_once()  # Just verify it was called
    
    @pytest.mark.asyncio
    @patch('plating.registry.PlatingDiscovery')
    async def test_registry_integration(self, mock_discovery):
        """Test that API integrates with registry properly."""
        # Mock the discovery
        mock_bundle = Mock()
        mock_bundle.name = "test_resource"
        mock_bundle.component_type = "resource"
        mock_bundle.has_main_template.return_value = True
        mock_bundle.has_examples.return_value = False
        mock_bundle.plating_dir = Path("/mock/path")
        
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_bundles.return_value = [mock_bundle]
        mock_discovery.return_value = mock_discovery_instance
        
        api = Plating()
        
        # Should have registry configured
        assert api.registry is not None
        
        # Should have components available
        components = api.registry.get_components(ComponentType.RESOURCE)
        assert len(components) == 1
        assert components[0].name == "test_resource"
    
    @pytest.mark.asyncio
    @patch('plating.registry.PlatingDiscovery')
    @patch('plating.markdown_validator.PyMarkdownApi')
    async def test_plate_operation_comprehensive(self, mock_md_api, mock_discovery):
        """Test comprehensive plate operation."""
        # Mock discovery
        mock_bundle = Mock()
        mock_bundle.name = "test_resource"
        mock_bundle.component_type = "resource"  
        mock_bundle.has_main_template.return_value = True
        mock_bundle.has_examples.return_value = False
        mock_bundle.load_examples.return_value = {"basic": "resource \"test\" {}"}
        mock_bundle.plating_dir = Path("/mock/path")
        
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_bundles.return_value = [mock_bundle]
        mock_discovery.return_value = mock_discovery_instance
        
        # Mock template engine
        with patch('plating.async_template_engine.template_engine') as mock_engine:
            mock_engine.render.return_value = "# Test Resource\n\nGenerated docs"
            
            # Mock markdown validator
            mock_md_instance = Mock()
            mock_md_instance.scan_path.return_value = Mock(
                scan_failures=[],
                pragma_errors=[]
            )
            mock_md_api.return_value = mock_md_instance
            
            api = Plating()
            
            with patch('pathlib.Path.mkdir'), \
                 patch('pathlib.Path.write_text') as mock_write:
                
                result = await api.plate(
                    Path("docs"),
                    component_types=[ComponentType.RESOURCE],
                    validate_markdown=True
                )
                
                # Should succeed
                assert result.success is True
                assert result.bundles_processed == 1
                assert result.files_generated == 1
                assert len(result.output_files) == 1
                
                # Should write file
                mock_write.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('plating.registry.PlatingDiscovery')
    async def test_validate_operation(self, mock_discovery, tmp_path):
        """Test validation operation using foundation patterns."""
        # Mock discovery  
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_bundles.return_value = []
        mock_discovery.return_value = mock_discovery_instance
        
        # Use pytest's tmp_path (which works well with foundation patterns)
        docs_dir = tmp_path
        
        # Create test markdown file
        test_file = docs_dir / "test.md"
        test_file.write_text("# Test Header\n\nSome content.\n")
        
        pout(f"Testing validation in {docs_dir}", color="cyan")  # Foundation I/O
        
        api = Plating()
        result = await api.validate(docs_dir)
        
        # Should validate successfully
        assert result.total == 1
        assert result.success is True  # With our lenient MD047 config
        
        pout("Validation test completed successfully", color="green")
    
    @pytest.mark.asyncio  
    @patch('plating.registry.PlatingDiscovery')
    async def test_error_handling(self, mock_discovery):
        """Test error handling in API operations using foundation patterns.""" 
        # Mock discovery to raise exception
        mock_discovery.side_effect = Exception("Discovery failed")
        
        try:
            # Should handle registry creation errors gracefully
            api = Plating()
            # API should still be created but registry might have issues
            assert api is not None
            pout("Error handling test passed", color="green")
        except Exception as e:
            perr(f"Unexpected error: {e}", color="red")
            # Re-raise to fail test if error isn't handled properly
            raise
    
    def test_modern_api_imports(self):
        """Test that modern API imports work correctly."""
        # Test that all expected classes can be imported
        from plating import (
            Plating,
            ComponentType, 
            PlatingContext,
            SchemaInfo,
            ArgumentInfo,
            AdornResult,
            PlateResult,
            ValidationResult,
            AsyncTemplateEngine,
            template_engine,
            with_retry,
            with_metrics,
            plating_metrics
        )
        
        # Basic smoke tests
        assert Plating is not None
        assert ComponentType.RESOURCE is not None
        assert template_engine is not None
        assert plating_metrics is not None


# 🧪🚀✨🎯