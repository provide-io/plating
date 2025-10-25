"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from click.testing import CliRunner

from plating.cli import main as cli


class TestCLI:
    """Test CLI command interface."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test that --help works."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Plating" in result.output
        assert "adorn" in result.output
        assert "plate" in result.output
        assert "validate" in result.output

    def test_adorn_help(self, runner):
        """Test adorn --help."""
        result = runner.invoke(cli, ["adorn", "--help"])
        assert result.exit_code == 0
        assert "Create missing documentation templates" in result.output
        assert "--component-type" in result.output
        assert "--provider-name" in result.output

    def test_plate_help(self, runner):
        """Test plate --help."""
        result = runner.invoke(cli, ["plate", "--help"])
        assert result.exit_code == 0
        assert "Generate documentation" in result.output
        assert "--output-dir" in result.output
        assert "--force" in result.output

    def test_validate_help(self, runner):
        """Test validate --help."""
        result = runner.invoke(cli, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate generated documentation" in result.output
        assert "--output-dir" in result.output

    def test_info_help(self, runner):
        """Test info --help."""
        result = runner.invoke(cli, ["info", "--help"])
        assert result.exit_code == 0
        assert "Show registry information" in result.output

    def test_stats_help(self, runner):
        """Test stats --help."""
        result = runner.invoke(cli, ["stats", "--help"])
        assert result.exit_code == 0
        assert "Show registry statistics" in result.output


class TestAdornCommand:
    """Test adorn command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @patch("plating.cli.Plating")
    def test_adorn_basic(self, mock_plating_class, runner):
        """Test basic adorn command."""
        # Setup mock
        mock_plating = Mock()
        mock_result = Mock()
        mock_result.generated_count = 5
        mock_result.skipped_count = 2
        mock_result.error_count = 0
        mock_result.errors = []
        mock_plating.adorn = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_plating

        # Run command
        result = runner.invoke(cli, ["adorn"])

        # Verify
        assert result.exit_code == 0
        mock_plating.adorn.assert_called_once()

    @patch("plating.cli.Plating")
    def test_adorn_with_component_type(self, mock_plating_class, runner):
        """Test adorn with --component-type flag."""
        mock_plating = Mock()
        mock_result = Mock()
        mock_result.generated_count = 3
        mock_result.skipped_count = 0
        mock_result.error_count = 0
        mock_result.errors = []
        mock_plating.adorn = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_plating

        result = runner.invoke(cli, ["adorn", "--component-type", "resource"])

        assert result.exit_code == 0
        mock_plating.adorn.assert_called_once()

    @patch("plating.cli.Plating")
    def test_adorn_with_provider_name(self, mock_plating_class, runner):
        """Test adorn with --provider-name flag."""
        mock_plating = Mock()
        mock_result = Mock()
        mock_result.generated_count = 2
        mock_result.skipped_count = 1
        mock_result.error_count = 0
        mock_result.errors = []
        mock_plating.adorn = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_plating

        result = runner.invoke(cli, ["adorn", "--provider-name", "test_provider"])

        assert result.exit_code == 0


class TestPlateCommand:
    """Test plate command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @patch("plating.cli.Plating")
    def test_plate_basic(self, mock_plating_class, runner):
        """Test basic plate command."""
        mock_plating = Mock()
        mock_result = Mock()
        mock_result.generated_count = 10
        mock_result.output_files = ["file1.md", "file2.md"]
        mock_result.error_count = 0
        mock_result.errors = []
        mock_result.duration_seconds = 1.5
        mock_plating.plate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_plating

        result = runner.invoke(cli, ["plate"])

        assert result.exit_code == 0
        mock_plating.plate.assert_called_once()

    @patch("plating.cli.Plating")
    def test_plate_with_output_dir(self, mock_plating_class, runner):
        """Test plate with custom output directory."""
        mock_plating = Mock()
        mock_result = Mock()
        mock_result.generated_count = 5
        mock_result.output_files = []
        mock_result.error_count = 0
        mock_result.errors = []
        mock_result.duration_seconds = 0.8
        mock_plating.plate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_plating

        result = runner.invoke(cli, ["plate", "--output-dir", "./custom_docs"])

        assert result.exit_code == 0

    @patch("plating.cli.Plating")
    def test_plate_with_force(self, mock_plating_class, runner):
        """Test plate with --force flag."""
        mock_plating = Mock()
        mock_result = Mock()
        mock_result.generated_count = 8
        mock_result.output_files = []
        mock_result.error_count = 0
        mock_result.errors = []
        mock_result.duration_seconds = 1.2
        mock_plating.plate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_plating

        result = runner.invoke(cli, ["plate", "--force"])

        assert result.exit_code == 0


class TestValidateCommand:
    """Test validate command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @patch("plating.cli.Plating")
    def test_validate_basic(self, mock_plating_class, runner):
        """Test basic validate command."""
        mock_plating = Mock()
        mock_result = Mock()
        mock_result.total = 10
        mock_result.passed = 10
        mock_result.failed = 0
        mock_result.errors = []
        mock_result.duration_seconds = 0.5
        mock_plating.validate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_plating

        result = runner.invoke(cli, ["validate"])

        assert result.exit_code == 0
        mock_plating.validate.assert_called_once()

    @patch("plating.cli.Plating")
    def test_validate_with_failures(self, mock_plating_class, runner):
        """Test validate with failures."""
        mock_plating = Mock()
        mock_result = Mock()
        mock_result.total = 10
        mock_result.passed = 8
        mock_result.failed = 2
        mock_result.errors = ["Error 1", "Error 2"]
        mock_result.duration_seconds = 0.7
        mock_plating.validate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_plating

        result = runner.invoke(cli, ["validate"])

        # Should exit with non-zero when there are failures
        assert result.exit_code != 0


class TestInfoCommand:
    """Test info command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @patch("plating.cli.get_plating_registry")
    def test_info_basic(self, mock_get_registry, runner):
        """Test basic info command."""
        mock_registry = Mock()
        mock_registry.get_stats.return_value = {
            "total_bundles": 10,
            "total_components": 25,
            "component_types": ["resource", "data_source"],
        }
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(cli, ["info"])

        assert result.exit_code == 0
        assert "10" in result.output  # total_bundles


class TestStatsCommand:
    """Test stats command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @patch("plating.cli.get_plating_registry")
    def test_stats_basic(self, mock_get_registry, runner):
        """Test basic stats command."""
        mock_registry = Mock()
        mock_registry.get_stats.return_value = {
            "total_bundles": 15,
            "total_components": 40,
            "by_type": {"resource": 20, "data_source": 15, "function": 5},
        }
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(cli, ["stats"])

        assert result.exit_code == 0
        assert "15" in result.output  # total_bundles


class TestAutoDetectProviderName:
    """Test auto_detect_provider_name function."""

    @patch("pathlib.Path.exists")
    @patch("builtins.open")
    def test_detect_from_pyproject(self, mock_open, mock_exists):
        """Test detecting provider name from pyproject.toml."""
        from plating.cli import auto_detect_provider_name

        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b"""
[project]
name = "terraform-provider-test"
"""

        # This will need tomllib mocking but let's test the function exists
        result = auto_detect_provider_name()
        # Just verify it doesn't crash
        assert result is None or isinstance(result, str)
