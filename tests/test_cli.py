"""
Tests for the garnish CLI.
"""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from garnish.cli import main


class TestGarnishCli:
    """Tests for the garnish CLI."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_garnish_command_exists(self, runner: CliRunner):
        """Test that the garnish command exists and shows help."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Garnish - Documentation generator" in result.output
        assert "dress" in result.output
        assert "plate" in result.output
        assert "test" in result.output

    def test_dress_command_exists(self, runner: CliRunner):
        """Test that the dress subcommand exists."""
        result = runner.invoke(main, ["dress", "--help"])
        assert result.exit_code == 0
        assert "Dress" in result.output

    def test_plate_command_exists(self, runner: CliRunner):
        """Test that the plate subcommand exists."""
        result = runner.invoke(main, ["plate", "--help"])
        assert result.exit_code == 0
        assert "Plate" in result.output

    def test_test_command_exists(self, runner: CliRunner):
        """Test that the test subcommand exists."""
        result = runner.invoke(main, ["test", "--help"])
        assert result.exit_code == 0
        assert "Run all garnish example files" in result.output

    @patch("garnish.cli.dress_components")
    def test_dress_invokes_correct_logic(self, mock_dress, runner: CliRunner):
        """Test that dress command invokes the dressing logic."""
        mock_dress.return_value = {"resource": 1}
        result = runner.invoke(main, ["dress"])
        assert result.exit_code == 0
        mock_dress.assert_called_once()
        assert "Dressed 1 components" in result.output

    @patch("garnish.cli.generate_docs")
    def test_plate_invokes_correct_logic(self, mock_render, runner: CliRunner):
        """Test that plate command invokes the plating logic."""
        result = runner.invoke(main, ["plate", "--force"])
        assert result.exit_code == 0
        mock_render.assert_called_once()
        assert "Documentation plated successfully!" in result.output

    def test_render_backward_compatibility(self, runner: CliRunner):
        """Test that render command still works but shows deprecation."""
        with patch("garnish.cli.generate_docs"):
            result = runner.invoke(main, ["render", "--force"])
            assert result.exit_code == 0
            assert "'render' is deprecated" in result.output
            assert "use 'plate' instead" in result.output


# 🥄🧪🪄
