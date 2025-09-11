"""
Tests for the garnish CLI.
"""

from unittest.mock import patch

from click.testing import CliRunner
import pytest

from plating.cli import main


class TestPlatingCli:
    """Tests for the plating CLI."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_plating_command_exists(self, runner: CliRunner):
        """Test that the plating command exists and shows help."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Plating - Documentation generator" in result.output
        assert "adorn" in result.output
        assert "plate" in result.output
        assert "validate" in result.output
        assert "clean" in result.output
        assert "pipeline" in result.output

    def test_adorn_command_exists(self, runner: CliRunner):
        """Test that the adorn subcommand exists."""
        result = runner.invoke(main, ["adorn", "--help"])
        assert result.exit_code == 0
        assert "Adorn" in result.output

    def test_plate_command_exists(self, runner: CliRunner):
        """Test that the plate subcommand exists."""
        result = runner.invoke(main, ["plate", "--help"])
        assert result.exit_code == 0
        assert "Plate" in result.output

    def test_test_command_exists(self, runner: CliRunner):
        """Test that the test subcommand exists but is deprecated."""
        result = runner.invoke(main, ["test", "--help"])
        assert result.exit_code == 0
        assert "Deprecated" in result.output
        assert "validate" in result.output

    @patch("plating.operations.adorn_components")
    def test_adorn_invokes_correct_logic(self, mock_adorn, runner: CliRunner):
        """Test that adorn command invokes the adorning logic."""
        mock_adorn.return_value = {"resource": 1}
        result = runner.invoke(main, ["adorn"])
        assert result.exit_code == 0
        mock_adorn.assert_called_once()
        assert "Adorned 1 components" in result.output

    @patch("plating.cli.plate_documentation")  
    def test_plate_invokes_correct_logic(self, mock_plate, runner: CliRunner):
        """Test that plate command invokes the plating logic."""
        from plating.results import PlateResult
        
        mock_plate.return_value = PlateResult(
            plated=["test.md"], 
            bundles_processed=1, 
            errors=[], 
            duration=1.0, 
            cleaned_first=False
        )
        result = runner.invoke(main, ["plate", "--force"])
        assert result.exit_code == 0
        mock_plate.assert_called_once()
        assert "Documentation plated successfully!" in result.output

    def test_render_backward_compatibility(self, runner: CliRunner):
        """Test that render command still works but shows deprecation."""
        with patch("plating.operations.plate_documentation") as mock_plate:
            from plating.results import PlateResult
            mock_plate.return_value = PlateResult(
                plated=["test.md"], 
                bundles_processed=1, 
                errors=[], 
                duration=1.0, 
                cleaned_first=False
            )
            result = runner.invoke(main, ["render", "--force"])
            assert result.exit_code == 0
            assert "'render' is deprecated" in result.output
            assert "use 'plate' instead" in result.output


# 🥄🧪🪄
