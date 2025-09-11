#
# tests/test_modern_api.py
#
"""Tests for the modern async API."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest

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
        """Test Plating API initialization."""
        api = Plating(
            package_name="test.components",
            provider_name="test_provider"
        )
        
        assert api.package_name == "test.components"
        assert api.provider_name == "test_provider"
        assert api._discovery is not None
        assert api._schema_processor is not None
    
    @pytest.mark.asyncio 
    @patch('plating.api.adorn_missing_components')
    async def test_adorn_operation(self, mock_adorn):
        """Test adorn operation with type-safe API."""
        # Mock the adorn function
        mock_adorn.return_value = {
            "total": 5,
            "resources": 3,
            "data_sources": 2,
            "functions": 0,
            "errors": []
        }
        
        api = Plating()
        result = await api.adorn([ComponentType.RESOURCE, ComponentType.DATA_SOURCE])
        
        # Verify function was called with correct string values
        mock_adorn.assert_called_once_with(["resource", "data_source"])
        
        # Verify result
        assert isinstance(result, AdornResult)
        assert result.components_processed == 5
        assert result.templates_generated == 5  # 3 + 2 + 0
        assert result.success is True
    
    @pytest.mark.asyncio
    @patch('plating.api.asyncio.get_event_loop')
    async def test_discover_bundles(self, mock_loop):
        """Test bundle discovery."""
        # Mock executor and discovery
        mock_executor = Mock()
        mock_loop.return_value.run_in_executor = mock_executor
        
        from plating.plating import PlatingBundle
        mock_bundles = [
            PlatingBundle("test1", Path("/test1.plating"), "resource"),
            PlatingBundle("test2", Path("/test2.plating"), "data_source")
        ]
        mock_executor.return_value = mock_bundles
        
        api = Plating()
        bundles = await api._discover_bundles([ComponentType.RESOURCE])
        
        # Verify executor was called
        mock_executor.assert_called_once()
    
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