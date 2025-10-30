"""
Comprehensive tests for the adorner module.
"""

from provide.testkit.mocking import AsyncMock, Mock, patch
import pytest

from plating.adorner import PlatingAdorner, adorn_components, adorn_missing_components
from plating.adorner.finder import ComponentFinder
from plating.templating.generator import TemplateGenerator


class TestPlatingAdorner:
    """Test suite for PlatingAdorner."""

    @pytest.fixture
    def adorner(self):
        """Create a PlatingAdorner instance."""
        return PlatingAdorner("pyvider.components")

    def test_initialization(self, adorner):
        """Test PlatingAdorner initialization."""
        assert adorner.plating_discovery is not None
        assert adorner.template_generator is not None
        assert adorner.component_finder is not None

    @pytest.mark.asyncio
    async def test_adorn_missing_no_components(self, adorner, mock_foundation_hub):
        """Test adorn_missing when no components are found."""
        # Mock the hub discovery to return no components
        mock_foundation_hub.discover_components.return_value = None
        mock_foundation_hub.list_components.return_value = []
        mock_foundation_hub.get_component.return_value = None

        # Replace adorner's hub
        adorner.hub = mock_foundation_hub

        with patch.object(adorner.plating_discovery, "discover_bundles") as mock_discover:
            mock_discover.return_value = []

            result = await adorner.adorn_missing()

            assert result == {"resource": 0, "data_source": 0, "function": 0}
            mock_foundation_hub.discover_components.assert_called_once_with("pyvider.components")

    @pytest.mark.asyncio
    async def test_adorn_missing_with_existing_bundles(
        self, adorner, mock_foundation_hub, mock_component_class
    ):
        """Test adorn_missing skips components with existing bundles."""
        # Mock components returned by hub
        mock_foundation_hub.discover_components.return_value = None
        mock_foundation_hub.list_components.return_value = ["existing_resource"]
        mock_foundation_hub.get_component.return_value = mock_component_class

        # Replace adorner's hub
        adorner.hub = mock_foundation_hub

        # Mock existing bundle
        mock_bundle = Mock(name="PlatingBundle")
        mock_bundle.name = "existing_resource"

        with patch.object(adorner.plating_discovery, "discover_bundles") as mock_discover:
            mock_discover.return_value = [mock_bundle]

            result = await adorner.adorn_missing()

            # Should not adorn the existing component
            assert result == {"resource": 0, "data_source": 0, "function": 0}

    @pytest.mark.asyncio
    async def test_adorn_missing_with_new_components(self, adorner, mock_component_class, mock_foundation_hub):
        """Test adorn_missing dresses new components."""
        # Mock components returned by hub - only return component for resource dimension
        mock_foundation_hub.discover_components.return_value = None

        def mock_list_components(dimension=None):
            if dimension == "resource":
                return ["new_resource"]
            return []  # No components for other dimensions

        mock_foundation_hub.list_components.side_effect = mock_list_components
        mock_foundation_hub.get_component.return_value = mock_component_class

        # Replace adorner's hub
        adorner.hub = mock_foundation_hub

        with patch.object(adorner.plating_discovery, "discover_bundles") as mock_discover:
            mock_discover.return_value = []  # No existing bundles

            with patch.object(adorner, "_adorn_component") as mock_dress:
                mock_dress.return_value = True

                result = await adorner.adorn_missing()

                mock_dress.assert_called_once_with("new_resource", "resource", mock_component_class)
                assert result == {"resource": 1, "data_source": 0, "function": 0}

    @pytest.mark.asyncio
    async def test_adorn_missing_with_component_type_filter(
        self, adorner, mock_component_class, mock_foundation_hub
    ):
        """Test adorn_missing filters by component type."""
        # Mock foundation hub to return components for both resource and data_source dimensions
        mock_foundation_hub.discover_components.return_value = None

        def mock_list_components(dimension=None):
            if dimension == "resource":
                return ["test_resource"]
            elif dimension == "data_source":
                return ["test_data"]
            return []

        mock_foundation_hub.list_components.side_effect = mock_list_components
        mock_foundation_hub.get_component.return_value = mock_component_class

        # Replace adorner's hub
        adorner.hub = mock_foundation_hub

        with patch.object(adorner.plating_discovery, "discover_bundles") as mock_discover:
            mock_discover.return_value = []

            with patch.object(adorner, "_adorn_component") as mock_dress:
                mock_dress.return_value = True

                # Only dress resources
                result = await adorner.adorn_missing(["resource"])

                assert mock_dress.call_count == 1
                assert result == {"resource": 1, "data_source": 0, "function": 0}

    @pytest.mark.asyncio
    async def test_adorn_component_success(self, adorner, mock_component_class, tmp_path):
        """Test successful dressing of a component."""
        # Setup mock source file
        source_file = tmp_path / "test_component.py"
        source_file.write_text("# Test component")

        with patch.object(adorner.component_finder, "find_source") as mock_find:
            mock_find.return_value = source_file

            with patch.object(adorner.template_generator, "generate_template") as mock_template:
                mock_template.return_value = "# Template content"

                with patch.object(adorner.template_generator, "generate_example") as mock_example:
                    mock_example.return_value = "# Example content"

                    result = await adorner._adorn_component("test_component", "resource", mock_component_class)

                    assert result is True

                    # Check that .plating directory was created
                    plating_dir = tmp_path / "test_component.plating"
                    assert plating_dir.exists()
                    assert (plating_dir / "docs").exists()
                    assert (plating_dir / "examples").exists()

                    # Check template file
                    template_file = plating_dir / "docs" / "test_component.tmpl.md"
                    assert template_file.exists()
                    assert template_file.read_text() == "# Template content"

                    # Check example file
                    example_file = plating_dir / "examples" / "example.tf"
                    assert example_file.exists()
                    assert example_file.read_text() == "# Example content"

    @pytest.mark.asyncio
    async def test_adorn_component_no_source_file(self, adorner, mock_component_class):
        """Test dressing fails when source file cannot be found."""
        with patch.object(adorner.component_finder, "find_source") as mock_find:
            mock_find.return_value = None

            result = await adorner._adorn_component("test_component", "resource", mock_component_class)

            assert result is False

    @pytest.mark.asyncio
    async def test_adorn_component_handles_exceptions(self, adorner, mock_component_class):
        """Test dressing handles exceptions gracefully."""
        with patch.object(adorner.component_finder, "find_source") as mock_find:
            mock_find.side_effect = Exception("Test error")

            result = await adorner._adorn_component("test_component", "resource", mock_component_class)

            assert result is False


class TestTemplateGenerator:
    """Test suite for TemplateGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a TemplateGenerator instance."""
        return TemplateGenerator()

    @pytest.fixture
    def mock_component(self):
        """Create a mock component with documentation."""
        mock = Mock()
        mock.__doc__ = "Test component description\nMore details here"
        return mock

    @pytest.mark.asyncio
    async def test_generate_template_resource(self, generator, mock_component):
        """Test generating template for a resource."""
        template = await generator.generate_template("test_resource", "resource", mock_component)

        assert "Resource: test_resource" in template
        assert "Test component description" in template
        assert "{{ example(" in template
        assert "{{ schema()" in template
        assert "terraform import" in template

    @pytest.mark.asyncio
    async def test_generate_template_data_source(self, generator, mock_component):
        """Test generating template for a data source."""
        template = await generator.generate_template("test_data", "data_source", mock_component)

        assert "Data Source: test_data" in template
        assert "Test component description" in template
        assert "{{ example(" in template
        assert "{{ schema()" in template
        assert "terraform import" not in template

    @pytest.mark.asyncio
    async def test_generate_template_function(self, generator, mock_component):
        """Test generating template for a function."""
        template = await generator.generate_template("test_func", "function", mock_component)

        assert "Function: test_func" in template
        assert "Test component description" in template
        assert "{{ signature_markdown }}" in template
        assert "{{ arguments_markdown }}" in template
        assert "{% if has_variadic %}" in template

    @pytest.mark.asyncio
    async def test_generate_template_no_docstring(self, generator):
        """Test generating template when component has no docstring."""
        mock_component = Mock()
        del mock_component.__doc__  # No docstring

        template = await generator.generate_template("test_resource", "resource", mock_component)

        assert "Terraform resource for test_resource" in template

    @pytest.mark.asyncio
    async def test_generate_example_resource(self, generator):
        """Test generating example for a resource."""
        example = await generator.generate_example("test_resource", "resource")

        assert 'resource "test_resource" "example"' in example
        assert "output" in example
        assert "test_resource.example.id" in example

    @pytest.mark.asyncio
    async def test_generate_example_data_source(self, generator):
        """Test generating example for a data source."""
        example = await generator.generate_example("test_data", "data_source")

        assert 'data "test_data" "example"' in example
        assert "output" in example
        assert "data.test_data.example" in example

    @pytest.mark.asyncio
    async def test_generate_example_function(self, generator):
        """Test generating example for a function."""
        example = await generator.generate_example("test_func", "function")

        assert "test_func(" in example
        assert "locals" in example
        assert "output" in example

    @pytest.mark.asyncio
    async def test_generate_example_unknown_type(self, generator):
        """Test generating example for unknown component type."""
        example = await generator.generate_example("test_unknown", "unknown")

        assert "Example usage for test_unknown" in example


class TestComponentFinder:
    """Test suite for ComponentFinder."""

    @pytest.fixture
    def finder(self):
        """Create a ComponentFinder instance."""
        return ComponentFinder()

    @pytest.mark.asyncio
    async def test_find_source_success(self, finder, tmp_path):
        """Test finding source file successfully."""
        # Create a test file
        test_file = tmp_path / "test_component.py"
        test_file.write_text("class TestComponent: pass")

        # Create a mock component class
        mock_component = Mock()

        with patch("inspect.getfile") as mock_getfile:
            mock_getfile.return_value = str(test_file)

            result = await finder.find_source(mock_component)

            assert result == test_file

    @pytest.mark.asyncio
    async def test_find_source_failure(self, finder):
        """Test handling failure to find source file."""
        mock_component = Mock()

        with patch("inspect.getfile") as mock_getfile:
            mock_getfile.side_effect = Exception("Cannot find source")

            result = await finder.find_source(mock_component)

            assert result is None


class TestAdornerAPI:
    """Test the public API functions."""

    @patch("plating.adorner.api.PlatingAdorner")
    @pytest.mark.asyncio
    async def test_adorn_missing_components_async(self, MockDresser):
        """Test async adorn_missing_components function."""
        mock_adorner = MockDresser.return_value
        mock_adorner.adorn_missing = AsyncMock(return_value={"resource": 2})

        result = await adorn_missing_components(["resource"])

        MockDresser.assert_called_once()
        mock_adorner.adorn_missing.assert_called_once_with(["resource"])
        assert result == {"resource": 2}

    @patch("plating.adorner.api.asyncio.run")
    def test_adorn_components_sync(self, mock_run):
        """Test sync adorn_components function."""
        mock_run.return_value = {"resource": 3}

        result = adorn_components(["resource"])

        mock_run.assert_called_once()
        assert result == {"resource": 3}


# 🍲🥄👗🧪🪄
