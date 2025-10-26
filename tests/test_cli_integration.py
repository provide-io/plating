"""Comprehensive CLI integration tests using provide-testkit.

These tests use CliTestRunner from provide-testkit for enhanced CLI testing
with proper async handling, output capture, and assertion helpers.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from provide.testkit import CliTestRunner

from plating.cli import main as cli
from plating.types import ComponentType


@pytest.fixture
def runner():
    """Create enhanced CLI test runner from provide-testkit."""
    return CliTestRunner()


class TestCLIHelp:
    """Test CLI help text and command structure."""

    def test_main_help(self, runner):
        """Test main --help command."""
        result = runner.invoke(cli, ["--help"])
        runner.assert_success(result)
        runner.assert_output_contains(result, "Plating")
        runner.assert_output_contains(result, "adorn")
        runner.assert_output_contains(result, "plate")
        runner.assert_output_contains(result, "validate")

    def test_adorn_help(self, runner):
        """Test adorn --help command."""
        result = runner.invoke(cli, ["adorn", "--help"])
        runner.assert_success(result)
        runner.assert_output_contains(result, "Create missing documentation templates")
        runner.assert_output_contains(result, "--component-type")

    def test_plate_help(self, runner):
        """Test plate --help command."""
        result = runner.invoke(cli, ["plate", "--help"])
        runner.assert_success(result)
        runner.assert_output_contains(result, "Generate documentation")
        runner.assert_output_contains(result, "--output-dir")

    def test_validate_help(self, runner):
        """Test validate --help command."""
        result = runner.invoke(cli, ["validate", "--help"])
        runner.assert_success(result)
        runner.assert_output_contains(result, "Validate generated documentation")

    def test_info_help(self, runner):
        """Test info --help command."""
        result = runner.invoke(cli, ["info", "--help"])
        runner.assert_success(result)
        runner.assert_output_contains(result, "Show registry information")

    def test_stats_help(self, runner):
        """Test stats --help command."""
        result = runner.invoke(cli, ["stats", "--help"])
        runner.assert_success(result)
        runner.assert_output_contains(result, "Show registry statistics")


class TestAdornCommand:
    """Test adorn command execution."""

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_adorn_success(self, mock_plating_class, mock_auto_detect, runner):
        """Test successful adorn command execution."""
        # Setup mock
        mock_api = Mock()
        mock_result = Mock()
        mock_result.generated_count = 5
        mock_result.skipped_count = 2
        mock_result.error_count = 0
        mock_result.errors = []
        mock_result.success = True
        mock_api.adorn = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        # Execute command
        result = runner.invoke(cli, ["adorn"])

        # Verify success
        runner.assert_success(result)
        runner.assert_output_contains(result, "Generated 5 template")
        mock_api.adorn.assert_called_once()

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_adorn_with_component_type(self, mock_plating_class, mock_auto_detect, runner):
        """Test adorn with --component-type flag."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.generated_count = 3
        mock_result.skipped_count = 0
        mock_result.error_count = 0
        mock_result.errors = []
        mock_result.success = True
        mock_api.adorn = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["adorn", "--component-type", "resource"])

        runner.assert_success(result)
        # Verify the API was called with correct component type
        call_args = mock_api.adorn.call_args
        assert call_args is not None

    @patch("plating.cli.Plating")
    def test_adorn_with_provider_name(self, mock_plating_class, runner):
        """Test adorn with --provider-name flag."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.generated_count = 4
        mock_result.skipped_count = 1
        mock_result.error_count = 0
        mock_result.errors = []
        mock_result.success = True
        mock_api.adorn = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["adorn", "--provider-name", "test_provider"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "Generated 4")

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_adorn_with_errors(self, mock_plating_class, mock_auto_detect, runner):
        """Test adorn command with errors."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.generated_count = 2
        mock_result.skipped_count = 0
        mock_result.error_count = 2
        mock_result.errors = ["Error 1", "Error 2"]
        mock_result.success = False
        mock_api.adorn = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["adorn"])

        # Should fail when there are errors
        runner.assert_error(result, exit_code=1)
        runner.assert_output_contains(result, "Error 1")

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_adorn_with_exception(self, mock_plating_class, mock_auto_detect, runner):
        """Test adorn command when exception occurs."""
        from plating.errors import PlatingError

        mock_api = Mock()
        mock_api.adorn = AsyncMock(side_effect=PlatingError("Test error"))
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["adorn"])

        runner.assert_error(result, exit_code=1)
        runner.assert_output_contains(result, "Error")


class TestPlateCommand:
    """Test plate command execution."""

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_plate_success(self, mock_plating_class, mock_auto_detect, runner):
        """Test successful plate command execution."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.files_generated = 10
        mock_result.bundles_processed = 5
        mock_result.output_files = ["file1.md", "file2.md", "file3.md"]
        mock_result.duration_seconds = 1.5
        mock_result.errors = []
        mock_api.plate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["plate"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "Generated 10 files")
        runner.assert_output_contains(result, "1.5")
        mock_api.plate.assert_called_once()

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_plate_with_output_dir(self, mock_plating_class, mock_auto_detect, runner):
        """Test plate with custom output directory."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.files_generated = 5
        mock_result.bundles_processed = 3
        mock_result.output_files = []
        mock_result.duration_seconds = 0.8
        mock_result.errors = []
        mock_api.plate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["plate", "--output-dir", "./custom_docs"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "Generated 5")

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_plate_with_force(self, mock_plating_class, mock_auto_detect, runner):
        """Test plate with --force flag."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.files_generated = 8
        mock_result.bundles_processed = 4
        mock_result.output_files = []
        mock_result.duration_seconds = 1.2
        mock_result.errors = []
        mock_api.plate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["plate", "--force"])

        runner.assert_success(result)
        # Verify force flag was passed
        call_kwargs = mock_api.plate.call_args.kwargs
        assert call_kwargs.get("force") is True

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_plate_with_no_validate(self, mock_plating_class, mock_auto_detect, runner):
        """Test plate with --no-validate flag."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.files_generated = 6
        mock_result.bundles_processed = 3
        mock_result.output_files = []
        mock_result.duration_seconds = 0.9
        mock_result.errors = []
        mock_api.plate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["plate", "--no-validate"])

        runner.assert_success(result)
        # Verify validate flag was passed as False
        call_kwargs = mock_api.plate.call_args.kwargs
        assert call_kwargs.get("validate") is False

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_plate_with_failure(self, mock_plating_class, mock_auto_detect, runner):
        """Test plate command with failures."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.success = False
        mock_result.files_generated = 0
        mock_result.bundles_processed = 0
        mock_result.output_files = []
        mock_result.errors = ["Template error", "Schema error"]
        mock_api.plate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["plate"])

        runner.assert_error(result, exit_code=1)
        runner.assert_output_contains(result, "failed")

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_plate_with_exception(self, mock_plating_class, mock_auto_detect, runner):
        """Test plate command when exception occurs."""
        from plating.errors import PlatingError

        mock_api = Mock()
        mock_api.plate = AsyncMock(side_effect=PlatingError("Rendering failed"))
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["plate"])

        runner.assert_error(result, exit_code=1)
        runner.assert_output_contains(result, "Error")


class TestValidateCommand:
    """Test validate command execution."""

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_validate_success(self, mock_plating_class, mock_auto_detect, runner):
        """Test successful validation."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.total = 10
        mock_result.passed = 10
        mock_result.failed = 0
        mock_result.errors = []
        mock_result.duration_seconds = 0.5
        mock_api.validate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["validate"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "Passed: 10")
        mock_api.validate.assert_called_once()

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_validate_with_failures(self, mock_plating_class, mock_auto_detect, runner):
        """Test validation with failures."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.total = 10
        mock_result.passed = 8
        mock_result.failed = 2
        mock_result.errors = ["Error 1", "Error 2"]
        mock_result.duration_seconds = 0.7
        mock_api.validate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["validate"])

        # Should exit with error when there are failures
        runner.assert_error(result)
        runner.assert_output_contains(result, "Failed: 2")

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_validate_with_custom_output_dir(self, mock_plating_class, mock_auto_detect, runner):
        """Test validation with custom output directory."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.total = 5
        mock_result.passed = 5
        mock_result.failed = 0
        mock_result.errors = []
        mock_result.duration_seconds = 0.3
        mock_api.validate = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["validate", "--output-dir", "./custom_docs"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "5")


class TestInfoCommand:
    """Test info command execution."""

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_info_basic(self, mock_plating_class, mock_auto_detect, runner):
        """Test basic info command."""
        mock_api = Mock()
        mock_api.get_registry_stats.return_value = {
            "total_components": 25,
            "component_types": ["resource", "data_source", "function"],
            "resource_count": 15,
            "data_source_count": 8,
            "function_count": 2,
        }
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["info"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "25")
        runner.assert_output_contains(result, "resource")

    @patch("plating.cli.Plating")
    def test_info_with_provider_name(self, mock_plating_class, runner):
        """Test info command with --provider-name."""
        mock_api = Mock()
        mock_api.get_registry_stats.return_value = {
            "total_components": 10,
            "component_types": ["resource"],
            "resource_count": 10,
        }
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["info", "--provider-name", "test_provider"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "10")

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_info_with_package_filter(self, mock_plating_class, mock_auto_detect, runner):
        """Test info command with --package-name."""
        mock_api = Mock()
        mock_api.get_registry_stats.return_value = {
            "total_components": 5,
            "component_types": ["resource", "data_source"],
            "resource_count": 3,
            "data_source_count": 2,
        }
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["info", "--package-name", "pyvider.components"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "Filtering to package")


class TestStatsCommand:
    """Test stats command execution."""

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_stats_basic(self, mock_plating_class, mock_auto_detect, runner):
        """Test basic stats command."""
        mock_api = Mock()
        mock_api.get_registry_stats.return_value = {
            "total_components": 40,
            "component_types": ["resource", "data_source", "function"],
            "resource_count": 25,
            "data_source_count": 12,
            "function_count": 3,
        }
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["stats"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "40")
        runner.assert_output_contains(result, "25")

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_stats_with_package_filter(self, mock_plating_class, mock_auto_detect, runner):
        """Test stats with package filter."""
        mock_api = Mock()
        mock_api.get_registry_stats.return_value = {
            "total_components": 15,
            "component_types": ["resource"],
            "resource_count": 15,
        }
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["stats", "--package-name", "pyvider.components"])

        runner.assert_success(result)
        runner.assert_output_contains(result, "15")


class TestProviderNameDetection:
    """Test auto-detection of provider name."""

    @patch("plating.cli.auto_detect_provider_name")
    @patch("plating.cli.Plating")
    def test_auto_detect_used_when_not_provided(self, mock_plating_class, mock_auto_detect, runner):
        """Test that auto-detection is used when provider name not provided."""
        mock_auto_detect.return_value = "auto_detected_provider"
        mock_api = Mock()
        mock_result = Mock()
        mock_result.generated_count = 1
        mock_result.skipped_count = 0
        mock_result.error_count = 0
        mock_result.errors = []
        mock_result.success = True
        mock_api.adorn = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["adorn"])

        runner.assert_success(result)
        mock_auto_detect.assert_called_once()

    @patch("plating.cli.auto_detect_provider_name")
    @patch("plating.cli.Plating")
    def test_explicit_provider_overrides_auto_detect(
        self, mock_plating_class, mock_auto_detect, runner
    ):
        """Test that explicit provider name overrides auto-detection."""
        mock_api = Mock()
        mock_result = Mock()
        mock_result.generated_count = 1
        mock_result.skipped_count = 0
        mock_result.error_count = 0
        mock_result.errors = []
        mock_result.success = True
        mock_api.adorn = AsyncMock(return_value=mock_result)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["adorn", "--provider-name", "explicit_provider"])

        runner.assert_success(result)
        # Auto-detect should not be called when explicit name provided
        mock_auto_detect.assert_not_called()


class TestErrorHandling:
    """Test error handling and output."""

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_unexpected_exception_handling(self, mock_plating_class, mock_auto_detect, runner):
        """Test handling of unexpected exceptions."""
        mock_api = Mock()
        mock_api.adorn = AsyncMock(side_effect=RuntimeError("Unexpected error"))
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["adorn"])

        runner.assert_error(result, exit_code=1)
        runner.assert_output_contains(result, "Unexpected error")
        runner.assert_output_contains(result, "bug")

    @patch("plating.cli.auto_detect_provider_name", return_value="test_provider")
    @patch("plating.cli.Plating")
    def test_plating_error_with_user_message(self, mock_plating_class, mock_auto_detect, runner):
        """Test PlatingError with custom user message."""
        from plating.errors import PlatingError

        mock_api = Mock()
        error = PlatingError("Test error")
        error.to_user_message = Mock(return_value="User-friendly error message")
        mock_api.plate = AsyncMock(side_effect=error)
        mock_plating_class.return_value = mock_api

        result = runner.invoke(cli, ["plate"])

        runner.assert_error(result, exit_code=1)
        runner.assert_output_contains(result, "User-friendly error message")
