#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Tests for the modern async API."""

from pathlib import Path

from provide.foundation import perr, pout  # Foundation I/O helpers
from provide.testkit.mocking import Mock, patch
import pytest

# Use the testkit utilities available via conftest.py fixtures
from plating import (
    AdornResult,
    ArgumentInfo,
    ComponentType,
    PlateResult,
    Plating,
    PlatingContext,
    SchemaInfo,
    ValidationResult,
)
from plating.registry import reset_plating_registry


class TestModernAPI:
    """Test the modern async Plating API."""

    def setup_method(self):
        """Setup for each test using foundation patterns."""
        # Foundation setup is handled by foundation_test_setup fixture
        reset_plating_registry()
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
        assert ComponentType.DATA_SOURCE.output_subdir == "data-sources"
        assert ComponentType.FUNCTION.output_subdir == "functions"

    def test_plating_context(self):
        """Test PlatingContext dataclass."""
        context = PlatingContext(
            name="test_resource",
            component_type=ComponentType.RESOURCE,
            provider_name="test_provider",
            description="A test resource",
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
                    "name": {"type": "string", "required": True, "description": "Name"},
                }
            },
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
        arg = ArgumentInfo(name="input", type="string", description="Input parameter", required=True)

        assert arg.name == "input"
        assert arg.type == "string"
        assert arg.description == "Input parameter"
        assert arg.required is True

    def test_result_types(self):
        """Test result type dataclasses."""
        # AdornResult
        adorn_result = AdornResult(
            components_processed=5, templates_generated=3, examples_created=2, errors=[]
        )
        assert adorn_result.success is True
        assert adorn_result.components_processed == 5

        # PlateResult
        plate_result = PlateResult(
            bundles_processed=3,
            files_generated=3,
            duration_seconds=1.5,
            errors=[],
            output_files=[Path("test.md")],
        )
        assert plate_result.success is True
        assert plate_result.duration_seconds == 1.5

        # ValidationResult
        validation_result = ValidationResult(total=10, passed=8, failed=2, skipped=0, duration_seconds=30.0)
        assert validation_result.success is False  # Because failed > 0
        assert validation_result.total == 10

    @pytest.mark.asyncio
    async def test_plating_api_initialization(self):
        """Test Plating API initialization using foundation patterns."""
        # Use mock context as base
        mock_base_context = Mock(name="MockContext")

        # Create PlatingContext with foundation context features
        context = PlatingContext(
            provider_name="test_provider",
            log_level="DEBUG",  # Foundation context feature
            no_color=True,  # Foundation context feature
        )

        pout(f"Initializing API with provider: {context.provider_name}", color="cyan")

        api = Plating(context=context, package_name="test.components")

        assert api.package_name == "test.components"
        assert api.context.provider_name == "test_provider"
        assert api.context.log_level == "DEBUG"  # Foundation feature
        assert api.registry is not None
        assert api.retry_policy is not None

        pout("API initialization test completed", color="green")

    @pytest.mark.asyncio
    @patch("plating.registry.PlatingDiscovery")
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
        with (
            patch("plating.templating.generator.TemplateGenerator") as mock_template_gen,
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch("pathlib.Path.write_text") as mock_write_text,
        ):
            # Make the mock method async and return a future
            async def mock_generate_template(*args, **kwargs):
                return "# Mock Template"

            mock_template_gen.return_value.generate_template = mock_generate_template

            from plating.types import PlatingContext

            api = Plating(PlatingContext(provider_name="pyvider"), "pyvider.components")
            result = await api.adorn(component_types=[ComponentType.RESOURCE])

            # Verify result
            assert isinstance(result, AdornResult)
            assert result.templates_generated == 1
            assert result.success is True

            # Verify file operations were called
            mock_mkdir.assert_called()
            mock_write_text.assert_called_once()  # Just verify it was called

    @pytest.mark.asyncio
    @patch("plating.registry.PlatingDiscovery")
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

        from plating.types import PlatingContext

        api = Plating(PlatingContext(provider_name="pyvider"), "pyvider.components")

        # Should have registry configured
        assert api.registry is not None

        # Should have components available
        components = api.registry.get_components(ComponentType.RESOURCE)
        assert len(components) == 1
        assert components[0].name == "test_resource"

    @pytest.mark.asyncio
    async def test_plate_operation_comprehensive(self, tmp_path):
        """Test comprehensive plate operation with minimal mocking."""
        # Create a real bundle structure in tmp_path
        bundle_dir = tmp_path / "test_resource.plating"
        bundle_dir.mkdir()

        # Create docs directory and template
        docs_dir = bundle_dir / "docs"
        docs_dir.mkdir()
        template_file = docs_dir / "test_resource.tmpl.md"
        template_file.write_text("""---
page_title: "Resource: test_resource"
description: Test resource description
---

# test_resource (Resource)

Test resource for unit testing.

## Example Usage

{{ example("basic") }}

## Schema

{{ schema() }}
""")

        # Create examples directory and file
        examples_dir = bundle_dir / "examples"
        examples_dir.mkdir()
        example_file = examples_dir / "basic.tf"
        example_file.write_text('resource "test_resource" "example" {\n  name = "test"\n}')

        # Create a minimal registry that returns our test bundle
        from plating.bundles import PlatingBundle

        test_bundle = PlatingBundle(name="test_resource", plating_dir=bundle_dir, component_type="resource")

        # Mock the registry to return our test bundle
        with patch("plating.registry.get_plating_registry") as mock_registry_factory:
            mock_registry = Mock()
            mock_registry.get_components_with_templates.return_value = [test_bundle]
            mock_registry_factory.return_value = mock_registry

            # Create output directory
            output_dir = tmp_path / "docs_output"

            from plating.types import PlatingContext

            api = Plating(PlatingContext(provider_name="pyvider"), "pyvider.components")
            api.registry = mock_registry

            result = await api.plate(
                output_dir,
                component_types=[ComponentType.RESOURCE],
                validate_markdown=False,  # Disable markdown validation for simplicity
            )

            # Should succeed
            assert result.success is True
            assert result.files_generated >= 1
            assert len(result.output_files) >= 1

            # Check that files were actually created
            expected_file = output_dir / "resources" / "test_resource.md"
            assert expected_file.exists()
            content = expected_file.read_text()
            assert "test_resource" in content
            assert "Resource" in content

    @pytest.mark.asyncio
    @patch("plating.registry.PlatingDiscovery")
    async def test_validate_operation(self, mock_discovery, tmp_path):
        """Test validation operation using foundation patterns."""
        # Mock discovery
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_bundles.return_value = []
        mock_discovery.return_value = mock_discovery_instance

        # Use pytest's tmp_path (which works well with foundation patterns)
        docs_dir = tmp_path

        # Create test markdown file in the correct subdirectory structure
        # The validate method looks for files in component_type subdirectories
        resource_dir = docs_dir / "resources"  # ComponentType.RESOURCE.output_subdir = "resources"
        resource_dir.mkdir(parents=True, exist_ok=True)
        test_file = resource_dir / "test.md"
        test_file.write_text("# Test Header\n\nSome content.\n")

        pout(f"Testing validation in {docs_dir}", color="cyan")  # Foundation I/O

        from plating.types import PlatingContext

        api = Plating(PlatingContext(provider_name="pyvider"), "pyvider.components")
        result = await api.validate(docs_dir)

        # Should validate successfully
        assert result.total == 1
        assert result.success is True  # With our lenient MD047 config

        pout("Validation test completed successfully", color="green")

    @pytest.mark.asyncio
    @patch("plating.registry.PlatingDiscovery")
    async def test_error_handling(self, mock_discovery):
        """Test error handling in API operations using foundation patterns."""
        # Mock discovery to raise exception
        mock_discovery.side_effect = Exception("Discovery failed")

        try:
            # Should handle registry creation errors gracefully
            from plating.types import PlatingContext

            api = Plating(PlatingContext(provider_name="pyvider"), "pyvider.components")
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
            ComponentType,
            Plating,
            plating_metrics,
            template_engine,
        )

        # Basic smoke tests
        assert Plating is not None
        assert ComponentType.RESOURCE is not None
        assert template_engine is not None
        assert plating_metrics is not None


# 🍽️📖🔚
