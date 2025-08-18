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
        assert "scaffold" in result.output
        assert "render" in result.output
        assert "test" in result.output

    def test_scaffold_command_exists(self, runner: CliRunner):
        """Test that the scaffold subcommand exists."""
        result = runner.invoke(main, ["scaffold", "--help"])
        assert result.exit_code == 0
        assert "Scaffold" in result.output

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

    @patch("garnish.cli.scaffold_garnish")
    def test_scaffold_invokes_correct_logic(self, mock_scaffold, runner: CliRunner):
        """Test that scaffold command invokes the scaffolding logic."""
        mock_scaffold.return_value = {"resource": 1}
        result = runner.invoke(main, ["scaffold"])
        assert result.exit_code == 0
        mock_scaffold.assert_called_once()
        assert "Scaffolded 1 components" in result.output

    @patch("garnish.cli.generate_docs")
    def test_render_invokes_correct_logic(self, mock_render, runner: CliRunner):
        """Test that render command invokes the rendering logic."""
        result = runner.invoke(main, ["render", "--force"])
        assert result.exit_code == 0
        mock_render.assert_called_once()
        assert "Documentation generation completed successfully!" in result.output


# 🥄🧪🪄
