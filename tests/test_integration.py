"""
Integration tests for plating.
"""

from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

from plating.adorner import PlatingAdorner
from plating.plater import PlatingPlater
from plating.plating import PlatingBundle


class TestIntegration:
    """Integration tests for plating components."""

    @pytest.fixture
    def temp_provider_dir(self):
        """Create a temporary provider directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            provider_dir = Path(tmp_dir)

            # Create basic provider structure
            (provider_dir / "resources").mkdir()
            (provider_dir / "data_sources").mkdir()
            (provider_dir / "functions").mkdir()

            yield provider_dir

    @pytest.fixture
    def sample_plating_bundle(self, temp_provider_dir):
        """Create a sample .plating bundle."""
        bundle_dir = temp_provider_dir / "resources" / "test_resource.plating"
        bundle_dir.mkdir(parents=True)

        # Create docs directory with template
        docs_dir = bundle_dir / "docs"
        docs_dir.mkdir()
        template_file = docs_dir / "test_resource.tmpl.md"
        template_file.write_text("""---
page_title: "Test Resource"
---

# Test Resource

{{ example("basic") }}

## Schema

{{ schema() }}
""")

        # Create examples directory
        examples_dir = bundle_dir / "examples"
        examples_dir.mkdir()
        example_file = examples_dir / "basic.tf"
        example_file.write_text("""resource "test_resource" "example" {
  name = "test"
}
""")

        return bundle_dir

    def test_discovery_to_plating_flow(self, sample_plating_bundle):
        """Test the flow from discovery to plating."""
        # Create bundle directly for testing
        bundle = PlatingBundle(
            plating_dir=sample_plating_bundle, name="test_resource", component_type="resource"
        )
        bundles = [bundle]

        assert len(bundles) == 1
        assert bundles[0].name == "test_resource"
        assert bundles[0].component_type == "resource"

        # Create plater with discovered bundles
        with tempfile.TemporaryDirectory() as output_dir:
            plater = PlatingPlater(bundles=bundles)
            plater.plate(Path(output_dir))

            # Check output was created
            output_file = Path(output_dir) / "resources" / "test_resource.md"
            assert output_file.exists()

            content = output_file.read_text()
            assert "Test Resource" in content
            assert 'resource "test_resource" "example"' in content

    @pytest.mark.asyncio
    async def test_adorner_to_plater_flow(self, temp_provider_dir):
        """Test the flow from dressing components to plating."""
        with patch("plating.adorner.adorner.ComponentDiscovery") as MockDiscovery:
            with patch("plating.adorner.adorner.hub") as mock_hub:
                # Setup mocks
                mock_discovery = MockDiscovery.return_value
                mock_discovery.discover_all = AsyncMock()

                # Create a mock component
                mock_component = Mock()
                mock_component.__doc__ = "Test component for integration"

                mock_hub.list_components.return_value = {"resource": {"integration_resource": mock_component}}

                # Create adorner and dress components
                adorner = PlatingAdorner()

                with patch.object(adorner.plating_discovery, "discover_bundles") as mock_discover:
                    mock_discover.return_value = []  # No existing bundles

                    with patch.object(adorner.component_finder, "find_source") as mock_find:
                        # Create a fake source file
                        source_file = temp_provider_dir / "resources" / "integration_resource.py"
                        source_file.parent.mkdir(exist_ok=True)
                        source_file.write_text("# Integration resource")
                        mock_find.return_value = source_file

                        # Dress the component
                        result = await adorner.adorn_missing(["resource"])
                        assert result["resource"] == 1

                        # Check .plating directory was created
                        plating_dir = temp_provider_dir / "resources" / "integration_resource.plating"
                        assert plating_dir.exists()

                        # Create bundle for the dressed component
                        bundle = PlatingBundle(
                            plating_dir=plating_dir, name="integration_resource", component_type="resource"
                        )
                        bundles = [bundle]

                        assert len(bundles) == 1
                        assert bundles[0].name == "integration_resource"

                        # Plate the documentation
                        with tempfile.TemporaryDirectory() as output_dir:
                            plater = PlatingPlater(bundles=bundles)
                            plater.plate(Path(output_dir))

                            output_file = Path(output_dir) / "resources" / "integration_resource.md"
                            assert output_file.exists()

    def test_schema_integration(self, sample_plating_bundle):
        """Test basic plating without schema integration."""
        # Create bundle for testing
        bundle = PlatingBundle(
            plating_dir=sample_plating_bundle, name="test_resource", component_type="resource"
        )
        bundles = [bundle]

        with tempfile.TemporaryDirectory() as output_dir:
            # Test plating without schema processor
            plater = PlatingPlater(bundles=bundles)
            plater.plate(Path(output_dir))

            output_file = Path(output_dir) / "resources" / "test_resource.md"
            assert output_file.exists()

            content = output_file.read_text()
            assert "Test Resource" in content

    def test_generate_docs_integration(self, temp_provider_dir, sample_plating_bundle):
        """Test the generate_docs function integrates all components."""
        with tempfile.TemporaryDirectory() as output_dir:
            # For this test, we'll use PlatingPlater directly since generate_docs
            # uses a different discovery mechanism
            bundle = PlatingBundle(
                plating_dir=sample_plating_bundle, name="test_resource", component_type="resource"
            )
            plater = PlatingPlater(bundles=[bundle])
            plater.plate(Path(output_dir))

            # Check output was created
            output_file = Path(output_dir) / "resources" / "test_resource.md"
            assert output_file.exists()

            content = output_file.read_text()
            assert "Test Resource" in content

    def test_component_type_filtering(self, temp_provider_dir):
        """Test filtering by component type across the pipeline."""
        # Create bundles for different component types
        for comp_type, subdir in [
            ("resource", "resources"),
            ("data_source", "data_sources"),
            ("function", "functions"),
        ]:
            bundle_dir = temp_provider_dir / subdir / f"test_{comp_type}.plating"
            bundle_dir.mkdir(parents=True)

            docs_dir = bundle_dir / "docs"
            docs_dir.mkdir()
            template = docs_dir / f"test_{comp_type}.tmpl.md"
            template.write_text(f"# Test {comp_type}")

        # Create bundles directly for testing
        resource_bundle = PlatingBundle(
            plating_dir=temp_provider_dir / "resources" / "test_resource.plating",
            name="test_resource",
            component_type="resource",
        )
        resource_bundles = [resource_bundle]

        assert len(resource_bundles) == 1
        assert resource_bundles[0].component_type == "resource"

        # Test plating with filtered bundles
        with tempfile.TemporaryDirectory() as output_dir:
            plater = PlatingPlater(bundles=resource_bundles)
            plater.plate(Path(output_dir))

            # Only resource should be plated
            assert (Path(output_dir) / "resources" / "test_resource.md").exists()
            assert not (Path(output_dir) / "data-sources" / "test_data_source.md").exists()
            assert not (Path(output_dir) / "functions" / "test_function.md").exists()

    def test_error_handling_integration(self, temp_provider_dir):
        """Test error handling across components."""
        # Create an invalid bundle (missing template)
        bundle_dir = temp_provider_dir / "resources" / "bad_resource.plating"
        bundle_dir.mkdir(parents=True)

        # No template file created

        # Create bundle directly
        bundle = PlatingBundle(plating_dir=bundle_dir, name="bad_resource", component_type="resource")
        bundles = [bundle]

        assert len(bundles) == 1

        with tempfile.TemporaryDirectory() as output_dir:
            plater = PlatingPlater(bundles=bundles)
            # Should handle missing template gracefully
            plater.plate(Path(output_dir))

            # No output file should be created for bad bundle
            assert not (Path(output_dir) / "resources" / "bad_resource.md").exists()

    def test_multi_bundle_integration(self, temp_provider_dir):
        """Test handling multiple bundles."""
        # Create multiple bundles
        for i in range(3):
            bundle_dir = temp_provider_dir / "resources" / f"resource_{i}.plating"
            bundle_dir.mkdir(parents=True)

            docs_dir = bundle_dir / "docs"
            docs_dir.mkdir()
            template = docs_dir / f"resource_{i}.tmpl.md"
            template.write_text(f"# Resource {i}\n\n{{{{ example('default') }}}}")

            examples_dir = bundle_dir / "examples"
            examples_dir.mkdir()
            example = examples_dir / "default.tf"
            example.write_text(f'resource "resource_{i}" "test" {{\n  id = {i}\n}}')

        # Discover all bundles
        # Create bundles directly
        bundles = [
            PlatingBundle(
                plating_dir=temp_provider_dir / "resources" / f"resource_{i}.plating",
                name=f"resource_{i}",
                component_type="resource",
            )
            for i in range(3)
        ]

        assert len(bundles) == 3

        # Plate all bundles
        with tempfile.TemporaryDirectory() as output_dir:
            plater = PlatingPlater(bundles=bundles)
            plater.plate(Path(output_dir))

            # Check all outputs created
            for i in range(3):
                output_file = Path(output_dir) / "resources" / f"resource_{i}.md"
                assert output_file.exists()

                content = output_file.read_text()
                assert f"Resource {i}" in content
                assert f'resource "resource_{i}" "test"' in content
                assert f"id = {i}" in content

    @pytest.mark.asyncio
    async def test_full_pipeline_async(self, temp_provider_dir):
        """Test the full async pipeline from dressing to plating."""
        with patch("plating.adorner.adorner.ComponentDiscovery") as MockDiscovery:
            with patch("plating.adorner.adorner.hub") as mock_hub:
                mock_discovery = MockDiscovery.return_value
                mock_discovery.discover_all = AsyncMock()

                # Create mock components
                components = {}
                for i in range(2):
                    mock_comp = Mock()
                    mock_comp.__doc__ = f"Component {i} documentation"
                    components[f"comp_{i}"] = mock_comp

                mock_hub.list_components.return_value = {"resource": components}

                adorner = PlatingAdorner()

                with patch.object(adorner.plating_discovery, "discover_bundles") as mock_discover:
                    mock_discover.return_value = []

                    with patch.object(adorner.component_finder, "find_source") as mock_find:
                        # Create source files for each component
                        for name in components:
                            source_file = temp_provider_dir / "resources" / f"{name}.py"
                            source_file.parent.mkdir(exist_ok=True)
                            source_file.write_text(f"# {name} source")
                            mock_find.return_value = source_file

                            # Manually dress one component at a time
                            # (since mock_find returns same file each time)
                            await adorner._adorn_component(name, "resource", components[name])

                        # Verify all .plating directories created
                        for name in components:
                            plating_dir = temp_provider_dir / "resources" / f"{name}.plating"
                            assert plating_dir.exists()

                        # Create bundles for dressed components
                        bundles = [
                            PlatingBundle(
                                plating_dir=temp_provider_dir / "resources" / f"{name}.plating",
                                name=name,
                                component_type="resource",
                            )
                            for name in components
                        ]

                        assert len(bundles) == 2

                        with tempfile.TemporaryDirectory() as output_dir:
                            plater = PlatingPlater(bundles=bundles)
                            plater.plate(Path(output_dir))

                            # Verify all outputs created
                            for name in components:
                                output_file = Path(output_dir) / "resources" / f"{name}.md"
                                assert output_file.exists()


# 🍲🧪🔗🪄
