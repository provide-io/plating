#
# tests/test_foundation_integration.py
#
"""Tests for foundation integration patterns."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from provide.foundation.testing import (
    MockContext,
    reset_foundation_setup_for_testing,
    temp_config_file
)

from plating.types import (
    PlatingContext, 
    ComponentType, 
    SchemaInfo, 
    ArgumentInfo,
    AdornResult,
    PlateResult, 
    ValidationResult
)
from plating.registry import PlatingRegistry, get_plating_registry, reset_plating_registry
from plating.markdown_validator import MarkdownValidator, get_markdown_validator, reset_markdown_validator


class TestPlatingContext:
    """Test PlatingContext with foundation.Context integration."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_foundation_setup_for_testing()
    
    def test_plating_context_inherits_foundation_context(self):
        """Test that PlatingContext properly extends foundation.Context."""
        context = PlatingContext(
            name="test_resource",
            component_type=ComponentType.RESOURCE,
            provider_name="test_provider"
        )
        
        # Should have foundation Context methods
        assert hasattr(context, "to_dict")
        assert hasattr(context, "from_dict")
        assert hasattr(context, "save_config")
        assert hasattr(context, "load_config")
        
        # Should have plating-specific properties
        assert context.name == "test_resource"
        assert context.component_type == ComponentType.RESOURCE
        assert context.provider_name == "test_provider"
    
    def test_plating_context_to_dict_includes_foundation_fields(self):
        """Test that to_dict includes both foundation and plating fields."""
        context = PlatingContext(
            name="test_resource",
            component_type=ComponentType.RESOURCE,
            provider_name="test_provider",
            description="A test resource"
        )
        
        # Set some foundation context fields
        context.log_level = "DEBUG"
        context.no_color = True
        
        result = context.to_dict()
        
        # Should include plating fields
        assert result["name"] == "test_resource"
        assert result["component_type"] == "Resource"
        assert result["provider_name"] == "test_provider"
        assert result["description"] == "A test resource"
        
        # Should include foundation fields
        assert result["log_level"] == "DEBUG"
        assert result["no_color"] is True
    
    def test_plating_context_from_dict_handles_component_types(self):
        """Test from_dict properly handles ComponentType conversion."""
        context = PlatingContext()
        
        # Test with display name
        data = {
            "name": "test",
            "component_type": "Data Source",
            "provider_name": "provider"
        }
        context.from_dict(data)
        
        assert context.component_type == ComponentType.DATA_SOURCE
        
        # Test with enum value
        data["component_type"] = "function"
        context.from_dict(data)
        
        assert context.component_type == ComponentType.FUNCTION
    
    def test_plating_context_save_and_load_config(self, tmp_path):
        """Test config persistence using foundation patterns."""
        context = PlatingContext(
            name="test_resource",
            component_type=ComponentType.RESOURCE,
            provider_name="test_provider"
        )
        
        config_file = tmp_path / "config.json"
        
        # Save context
        context.save_context(config_file)
        
        # Load context
        loaded_context = PlatingContext.load_context(config_file)
        
        assert loaded_context.name == "test_resource"
        assert loaded_context.component_type == ComponentType.RESOURCE
        assert loaded_context.provider_name == "test_provider"


class TestPlatingRegistry:
    """Test PlatingRegistry with foundation.Registry integration."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_foundation_setup_for_testing()
        reset_plating_registry()
    
    @patch("plating.registry.PlatingDiscovery")
    def test_registry_initialization_uses_foundation_patterns(self, mock_discovery):
        """Test that registry uses foundation Registry properly."""
        # Mock discovery
        mock_bundle = Mock()
        mock_bundle.name = "test_resource"
        mock_bundle.component_type = "resource"
        mock_bundle.has_main_template.return_value = True
        mock_bundle.has_examples.return_value = False
        
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_bundles.return_value = [mock_bundle]
        mock_discovery.return_value = mock_discovery_instance
        
        # Create registry
        registry = PlatingRegistry("test.package")
        
        # Should have foundation Registry methods
        assert hasattr(registry, "register")
        assert hasattr(registry, "list_all")
        assert hasattr(registry, "list_dimension")
        assert hasattr(registry, "get")
        
        # Should have registered the mock bundle
        resources = registry.get_components(ComponentType.RESOURCE)
        assert len(resources) == 1
        assert resources[0].name == "test_resource"
    
    @patch("plating.registry.PlatingDiscovery")
    def test_registry_retry_policy_on_discovery_failure(self, mock_discovery):
        """Test that registry uses retry policy for discovery failures."""
        # Mock discovery to fail then succeed
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_bundles.side_effect = [
            OSError("Network error"),
            []  # Success on retry
        ]
        mock_discovery.return_value = mock_discovery_instance
        
        # Should not raise error due to retry policy
        registry = PlatingRegistry("test.package")
        
        # Discovery should have been called twice (initial + 1 retry)
        assert mock_discovery_instance.discover_bundles.call_count == 2
    
    def test_registry_stats_provide_comprehensive_info(self):
        """Test that registry stats provide comprehensive information."""
        with patch("plating.registry.PlatingDiscovery") as mock_discovery:
            mock_bundle = Mock()
            mock_bundle.name = "test_resource"
            mock_bundle.component_type = "resource"
            mock_bundle.has_main_template.return_value = True
            mock_bundle.has_examples.return_value = True
            
            mock_discovery_instance = Mock()
            mock_discovery_instance.discover_bundles.return_value = [mock_bundle]
            mock_discovery.return_value = mock_discovery_instance
            
            registry = PlatingRegistry("test.package")
            stats = registry.get_registry_stats()
            
            assert stats["total_components"] == 1
            assert "resource" in stats["component_types"]
            assert stats["resource_count"] == 1
            assert stats["resource_with_templates"] == 1
            assert stats["resource_with_examples"] == 1


class TestMarkdownValidator:
    """Test MarkdownValidator with foundation integration."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_foundation_setup_for_testing()
        reset_markdown_validator()
    
    def test_validator_uses_foundation_retry_patterns(self):
        """Test that validator uses foundation retry patterns."""
        validator = MarkdownValidator()
        
        # Should have retry policy configured
        assert validator._retry_policy is not None
        assert validator._retry_policy.max_attempts == 2
        assert validator._retry_executor is not None
    
    def test_validator_integrates_with_foundation_metrics(self):
        """Test that validator uses foundation metrics decorators."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Header\n\nSome content.\n")
            f.flush()
            
            validator = MarkdownValidator()
            
            # This should trigger metrics via decorators
            result = validator.validate_file(Path(f.name))
            
            assert result.total == 1
            # Clean up
            Path(f.name).unlink()
    
    def test_validator_handles_api_exceptions_gracefully(self):
        """Test that validator handles PyMarkdownApiException properly."""
        validator = MarkdownValidator()
        
        # Test with non-existent file
        result = validator.validate_file(Path("/non/existent/file.md"))
        
        assert result.total == 1
        assert result.failed == 1
        assert len(result.errors) > 0
        assert "File not found" in result.errors[0]
    
    def test_validator_string_validation(self):
        """Test string-based validation."""
        validator = MarkdownValidator()
        
        # Valid markdown
        result = validator.validate_string("# Valid Header\n\nContent here.\n")
        assert result.passed == 1
        assert result.failed == 0
        
        # Invalid markdown (if we had strict rules)
        result = validator.validate_string("Some content", "test.md")
        # Should still pass with our lenient config
        assert result.total == 1
    
    def test_validator_batch_processing(self):
        """Test batch validation of multiple files."""
        validator = MarkdownValidator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "test1.md"
            file2 = Path(tmpdir) / "test2.md"
            
            file1.write_text("# Test 1\n\nContent 1")
            file2.write_text("# Test 2\n\nContent 2")
            
            result = validator.validate_files([file1, file2])
            
            assert result.total == 2
            # Should pass with our lenient configuration
            assert result.passed == 2
            assert result.failed == 0


class TestFoundationDataClasses:
    """Test that data classes use attrs properly."""
    
    def test_all_result_classes_use_attrs(self):
        """Test that result classes use attrs.define."""
        # AdornResult
        result = AdornResult(components_processed=5, templates_generated=3)
        assert result.components_processed == 5
        assert result.success is True
        
        # PlateResult  
        result = PlateResult(bundles_processed=2, files_generated=4)
        assert result.bundles_processed == 2
        assert result.success is True
        
        # ValidationResult with markdown support
        result = ValidationResult(
            total=10, 
            passed=8, 
            failed=1,
            lint_errors=["MD001: Header increment"]
        )
        assert result.total == 10
        assert result.success is False  # Due to lint_errors
    
    def test_argument_info_serialization(self):
        """Test ArgumentInfo to_dict and from_dict."""
        arg = ArgumentInfo(
            name="input",
            type="string",
            description="Input parameter", 
            required=True
        )
        
        # Serialize
        data = arg.to_dict()
        expected = {
            "name": "input",
            "type": "string", 
            "description": "Input parameter",
            "required": True
        }
        assert data == expected
        
        # Deserialize
        restored = ArgumentInfo.from_dict(data)
        assert restored.name == arg.name
        assert restored.type == arg.type
        assert restored.description == arg.description
        assert restored.required == arg.required
    
    def test_schema_info_maintains_functionality(self):
        """Test that SchemaInfo maintains all existing functionality."""
        schema = SchemaInfo(
            description="Test schema",
            attributes={
                "id": {"type": "string", "computed": True},
                "name": {"type": "string", "required": True}
            }
        )
        
        markdown = schema.to_markdown()
        assert "## Schema" in markdown
        assert "### Required" in markdown
        assert "### Read-Only" in markdown
        assert "`name` (String)" in markdown
        assert "`id` (String)" in markdown


class TestGlobalInstances:
    """Test global instance management for testing."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_foundation_setup_for_testing()
        reset_plating_registry()
        reset_markdown_validator()
    
    def test_global_registry_management(self):
        """Test global registry creation and reset."""
        # Should create new instance
        registry1 = get_plating_registry()
        assert registry1 is not None
        
        # Should return same instance
        registry2 = get_plating_registry()
        assert registry1 is registry2
        
        # Reset should clear global instance
        reset_plating_registry()
        registry3 = get_plating_registry()
        assert registry3 is not registry1
    
    def test_global_validator_management(self):
        """Test global validator creation and reset."""
        # Should create new instance
        validator1 = get_markdown_validator()
        assert validator1 is not None
        
        # Should return same instance
        validator2 = get_markdown_validator()
        assert validator1 is validator2
        
        # Reset should clear global instance
        reset_markdown_validator()
        validator3 = get_markdown_validator()
        assert validator3 is not validator1


# 🧪⚡🏗️✨