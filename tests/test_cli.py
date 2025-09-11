"""
Tests for the garnish CLI.
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

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
        assert "test" in result.output

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
        """Test that the test subcommand exists."""
        result = runner.invoke(main, ["test", "--help"])
        assert result.exit_code == 0
        assert "Run all plating example files" in result.output

    @patch("plating.cli.adorn_components")
    def test_adorn_invokes_correct_logic(self, mock_dress, runner: CliRunner):
        """Test that adorn command invokes the adorning logic."""
        mock_dress.return_value = {"resource": 1}
        result = runner.invoke(main, ["adorn"])
        assert result.exit_code == 0
        mock_dress.assert_called_once()
        assert "Adorned 1 components" in result.output

    @patch("plating.cli.generate_docs")
    def test_plate_invokes_correct_logic(self, mock_render, runner: CliRunner):
        """Test that plate command invokes the plating logic."""
        result = runner.invoke(main, ["plate", "--force"])
        assert result.exit_code == 0
        mock_render.assert_called_once()
        assert "Documentation plated successfully!" in result.output

    def test_render_backward_compatibility(self, runner: CliRunner):
        """Test that render command still works but shows deprecation."""
        with patch("plating.cli.generate_docs"):
            result = runner.invoke(main, ["render", "--force"])
            assert result.exit_code == 0
            assert "'render' is deprecated" in result.output
            assert "use 'plate' instead" in result.output


# 🥄🧪🪄
