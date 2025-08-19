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
        assert "render" in result.output
        assert "test" in result.output

    def test_dress_command_exists(self, runner: CliRunner):
        """Test that the dress subcommand exists."""
        result = runner.invoke(main, ["dress", "--help"])
        assert result.exit_code == 0
        assert "Dress" in result.output

    def test_render_command_exists(self, runner: CliRunner):
        """Test that the render subcommand exists."""
        result = runner.invoke(main, ["render", "--help"])
        assert result.exit_code == 0
        assert "Render" in result.output

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
    def test_render_invokes_correct_logic(self, mock_render, runner: CliRunner):
        """Test that render command invokes the rendering logic."""
        result = runner.invoke(main, ["render", "--force"])
        assert result.exit_code == 0
        mock_render.assert_called_once()
        assert "Documentation generation completed successfully!" in result.output


# 🥄🧪🪄
