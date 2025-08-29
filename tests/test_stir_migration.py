#
# tests/test_stir_migration.py
#
"""TDD tests for migrating garnish test to use tofusoup stir."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import pytest

from garnish.garnish import GarnishBundle, GarnishDiscovery
from garnish.test_runner import (
    run_garnish_tests,
    _create_test_suite,
    prepare_test_suites_for_stir,
    run_tests_with_stir,
    parse_stir_results,
    GarnishTestAdapter,
)


class TestGarnishTestSuitePreparation:
    """Tests for preparing garnish test suites for stir execution."""

    def test_prepare_single_bundle_test_suite(self, tmp_path):
        """Test preparing a test suite from a single garnish bundle."""
        # Given: A mock garnish bundle with examples
        bundle = Mock(spec=GarnishBundle)
        bundle.name = "test_resource"
        bundle.component_type = "resource"
        bundle.load_examples.return_value = {
            "example": 'resource "test" "example" { name = "test" }'
        }
        bundle.load_fixtures.return_value = {}
        bundle.fixtures_dir = tmp_path / "fixtures"

        # When: Preparing test suite
        output_dir = tmp_path / "test_output"
        suite_dir = prepare_test_suites_for_stir([bundle], output_dir)[0]

        # Then: Test suite should be created with correct structure
        assert suite_dir.exists()
        assert suite_dir.name == "resource_test_resource_test"
        assert (suite_dir / "provider.tf").exists()
        assert (suite_dir / "test_resource.tf").exists()
        
        # Verify provider.tf content
        provider_content = (suite_dir / "provider.tf").read_text()
        assert "pyvider" in provider_content
        
        # Verify example file content
        example_content = (suite_dir / "test_resource.tf").read_text()
        assert 'resource "test" "example"' in example_content

    def test_prepare_multiple_bundles_test_suites(self, tmp_path):
        """Test preparing test suites from multiple garnish bundles."""
        # Given: Multiple mock garnish bundles
        bundles = []
        for i in range(3):
            bundle = Mock(spec=GarnishBundle)
            bundle.name = f"test_component_{i}"
            bundle.component_type = ["resource", "data_source", "function"][i]
            bundle.load_examples.return_value = {
                "example": f'resource "test_{i}" "example" {{ }}'
            }
            bundle.load_fixtures.return_value = {}
            bundle.fixtures_dir = tmp_path / f"fixtures_{i}"
            bundles.append(bundle)

        # When: Preparing test suites
        output_dir = tmp_path / "test_output"
        suite_dirs = prepare_test_suites_for_stir(bundles, output_dir)

        # Then: All test suites should be created
        assert len(suite_dirs) == 3
        for i, suite_dir in enumerate(suite_dirs):
            assert suite_dir.exists()
            expected_type = ["resource", "data_source", "function"][i]
            assert suite_dir.name == f"{expected_type}_test_component_{i}_test"

    def test_prepare_bundle_with_fixtures(self, tmp_path):
        """Test preparing a test suite with fixture files."""
        # Given: A bundle with fixtures
        bundle = Mock(spec=GarnishBundle)
        bundle.name = "test_with_fixtures"
        bundle.component_type = "resource"
        bundle.load_examples.return_value = {
            "example": 'resource "test" "example" { fixture_path = "../fixtures/data.json" }'
        }
        bundle.load_fixtures.return_value = {
            "data.json": '{"key": "value"}',
            "nested/config.yaml": "config: test"
        }
        bundle.fixtures_dir = tmp_path / "fixtures"

        # When: Preparing test suite
        output_dir = tmp_path / "test_output"
        suite_dir = prepare_test_suites_for_stir([bundle], output_dir)[0]

        # Then: Fixtures should be created at parent level
        fixtures_dir = suite_dir.parent / "fixtures"
        assert fixtures_dir.exists()
        assert (fixtures_dir / "data.json").exists()
        assert (fixtures_dir / "nested" / "config.yaml").exists()
        
        # Verify fixture contents
        assert json.loads((fixtures_dir / "data.json").read_text()) == {"key": "value"}
        assert "config: test" in (fixtures_dir / "nested" / "config.yaml").read_text()

    def test_prepare_bundle_with_multiple_examples(self, tmp_path):
        """Test preparing a test suite with multiple example files."""
        # Given: A bundle with multiple examples
        bundle = Mock(spec=GarnishBundle)
        bundle.name = "multi_example"
        bundle.component_type = "resource"
        bundle.load_examples.return_value = {
            "example": 'resource "test" "basic" { }',
            "advanced": 'resource "test" "advanced" { count = 3 }',
            "complex": 'resource "test" "complex" { for_each = var.items }'
        }
        bundle.load_fixtures.return_value = {}
        bundle.fixtures_dir = tmp_path / "fixtures"

        # When: Preparing test suite
        output_dir = tmp_path / "test_output"
        suite_dir = prepare_test_suites_for_stir([bundle], output_dir)[0]

        # Then: All example files should be created with unique names
        assert (suite_dir / "multi_example.tf").exists()  # Default example
        assert (suite_dir / "multi_example_advanced.tf").exists()
        assert (suite_dir / "multi_example_complex.tf").exists()

    def test_skip_bundles_without_examples(self, tmp_path):
        """Test that bundles without examples are skipped."""
        # Given: Bundles with and without examples
        bundle_with = Mock(spec=GarnishBundle)
        bundle_with.name = "with_examples"
        bundle_with.component_type = "resource"
        bundle_with.load_examples.return_value = {"example": "resource {}"}
        bundle_with.load_fixtures.return_value = {}
        bundle_with.fixtures_dir = tmp_path / "fixtures1"

        bundle_without = Mock(spec=GarnishBundle)
        bundle_without.name = "without_examples"
        bundle_without.component_type = "data_source"
        bundle_without.load_examples.return_value = {}
        bundle_without.load_fixtures.return_value = {}
        bundle_without.fixtures_dir = tmp_path / "fixtures2"

        # When: Preparing test suites
        output_dir = tmp_path / "test_output"
        suite_dirs = prepare_test_suites_for_stir([bundle_with, bundle_without], output_dir)

        # Then: Only bundle with examples should have test suite
        assert len(suite_dirs) == 1
        assert suite_dirs[0].name == "resource_with_examples_test"


class TestTofusoupStirIntegration:
    """Tests for integration with tofusoup stir command."""

    @patch('subprocess.run')
    def test_run_stir_with_default_options(self, mock_run, tmp_path):
        """Test running tofusoup stir with default options."""
        # Given: A test directory with prepared suites
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_suite_1").mkdir()
        (test_dir / "test_suite_2").mkdir()

        # Mock successful stir execution
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"total": 2, "passed": 2, "failed": 0}',
            stderr=""
        )

        # When: Running tests with stir
        result = run_tests_with_stir(test_dir)

        # Then: Stir should be called with correct arguments
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "soup"
        assert args[1] == "stir"
        assert str(test_dir) in args
        assert "--output-json" in args

    @patch('subprocess.run')
    def test_run_stir_with_parallel_option(self, mock_run, tmp_path):
        """Test running stir with parallel execution option."""
        # Given: Test directory and parallel setting
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"total": 1, "passed": 1, "failed": 0}',
            stderr=""
        )

        # When: Running with parallel option
        result = run_tests_with_stir(test_dir, parallel=8)

        # Then: Parallel option should be passed to stir
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        # Note: Need to check how stir handles parallel option
        # This might need adjustment based on actual stir CLI

    @patch('subprocess.run')
    def test_handle_stir_execution_failure(self, mock_run, tmp_path):
        """Test handling when stir execution fails."""
        # Given: Stir fails to execute
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: Failed to initialize terraform"
        )

        # When/Then: Should raise appropriate exception
        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            run_tests_with_stir(test_dir)
        
        assert "Failed to initialize terraform" in str(exc_info.value)

    @patch('subprocess.run')
    def test_handle_stir_not_found(self, mock_run, tmp_path):
        """Test handling when soup/stir command is not found."""
        # Given: Soup command not found
        test_dir = tmp_path / "tests"
        mock_run.side_effect = FileNotFoundError("soup command not found")

        # When/Then: Should raise informative error
        with pytest.raises(RuntimeError) as exc_info:
            run_tests_with_stir(test_dir)
        
        assert "tofusoup" in str(exc_info.value).lower()
        assert ("not found" in str(exc_info.value).lower() or 
                "not installed" in str(exc_info.value).lower())


class TestStirResultParsing:
    """Tests for parsing and transforming stir results."""

    def test_parse_successful_stir_json_output(self):
        """Test parsing successful JSON output from stir."""
        # Given: JSON output from stir
        stir_output = {
            "total": 5,
            "passed": 4,
            "failed": 1,
            "warnings": 2,
            "skipped": 0,
            "test_details": {
                "resource_test_1_test": {
                    "success": True,
                    "duration": 5.2,
                    "resources": 3,
                    "data_sources": 1
                },
                "resource_test_2_test": {
                    "success": False,
                    "duration": 2.1,
                    "last_log": "Error applying configuration"
                }
            }
        }

        # When: Parsing stir results
        garnish_results = parse_stir_results(stir_output)

        # Then: Results should be transformed to garnish format
        assert garnish_results["total"] == 5
        assert garnish_results["passed"] == 4
        assert garnish_results["failed"] == 1
        assert garnish_results["warnings"] == 2
        assert "test_details" in garnish_results
        assert "resource_test_1_test" in garnish_results["test_details"]

    def test_parse_stir_results_with_bundle_info(self):
        """Test enriching stir results with garnish bundle information."""
        # Given: Stir output and bundle information
        stir_output = {
            "total": 2,
            "passed": 2,
            "failed": 0,
            "test_details": {
                "resource_my_resource_test": {"success": True},
                "data_source_my_data_test": {"success": True}
            }
        }
        
        # Create proper mock fixtures_dir with rglob support
        mock_fixtures_dir = Mock()
        mock_fixtures_dir.exists.return_value = True
        mock_fixtures_dir.rglob.return_value = []  # No fixtures for simplicity
        
        mock_no_fixtures_dir = Mock()
        mock_no_fixtures_dir.exists.return_value = False
        
        bundles = [
            Mock(name="my_resource", component_type="resource", 
                 load_examples=Mock(return_value={"ex1": "", "ex2": ""}),
                 fixtures_dir=mock_fixtures_dir),
            Mock(name="my_data", component_type="data_source",
                 load_examples=Mock(return_value={"ex1": ""}),
                 fixtures_dir=mock_no_fixtures_dir)
        ]

        # When: Parsing with bundle enrichment
        garnish_results = parse_stir_results(stir_output, bundles)

        # Then: Bundle information should be added
        assert "bundles" in garnish_results
        assert "my_resource" in garnish_results["bundles"]
        assert garnish_results["bundles"]["my_resource"]["component_type"] == "resource"
        assert garnish_results["bundles"]["my_resource"]["examples_count"] == 2
        assert garnish_results["bundles"]["my_resource"]["has_fixtures"] is True
        
        assert "my_data" in garnish_results["bundles"]
        assert garnish_results["bundles"]["my_data"]["examples_count"] == 1
        assert garnish_results["bundles"]["my_data"]["has_fixtures"] is False

    def test_parse_empty_stir_results(self):
        """Test parsing when stir returns no test results."""
        # Given: Empty stir output
        stir_output = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "test_details": {}
        }

        # When: Parsing empty results
        garnish_results = parse_stir_results(stir_output)

        # Then: Should handle gracefully
        assert garnish_results["total"] == 0
        assert garnish_results["passed"] == 0
        assert garnish_results["failed"] == 0
        assert garnish_results["test_details"] == {}


class TestGarnishTestAdapter:
    """Tests for the main adapter that coordinates the migration."""

    @patch('garnish.test_runner.GarnishDiscovery')
    @patch('garnish.test_runner.prepare_test_suites_for_stir')
    @patch('garnish.test_runner.run_tests_with_stir')
    @patch('garnish.test_runner.parse_stir_results')
    def test_full_test_flow_with_stir(self, mock_parse, mock_run_stir, 
                                      mock_prepare, mock_discovery, tmp_path):
        """Test the complete flow from garnish discovery to stir execution."""
        # Given: Mock garnish bundles and stir results
        mock_bundles = [
            Mock(name="test1", component_type="resource"),
            Mock(name="test2", component_type="data_source")
        ]
        mock_discovery.return_value.discover_bundles.return_value = mock_bundles
        
        mock_prepare.return_value = [
            tmp_path / "resource_test1_test",
            tmp_path / "data_source_test2_test"
        ]
        
        mock_stir_output = {
            "total": 2, "passed": 2, "failed": 0,
            "test_details": {}
        }
        mock_run_stir.return_value = mock_stir_output
        mock_parse.return_value = mock_stir_output

        # When: Running garnish tests through adapter
        adapter = GarnishTestAdapter()
        results = adapter.run_tests(component_types=["resource", "data_source"])

        # Then: All components should be called in order
        mock_discovery.return_value.discover_bundles.assert_called()
        mock_prepare.assert_called_once_with(mock_bundles, adapter.output_dir)
        mock_run_stir.assert_called_once()
        mock_parse.assert_called_once_with(mock_stir_output, mock_bundles)
        
        assert results["total"] == 2
        assert results["passed"] == 2

    @patch('garnish.test_runner.GarnishDiscovery')
    def test_adapter_with_no_bundles_found(self, mock_discovery):
        """Test adapter behavior when no garnish bundles are found."""
        # Given: No bundles discovered
        mock_discovery.return_value.discover_bundles.return_value = []

        # When: Running tests
        adapter = GarnishTestAdapter()
        results = adapter.run_tests()

        # Then: Should return empty results without calling stir
        assert results["total"] == 0
        assert results["passed"] == 0
        assert results["failed"] == 0

    @patch('garnish.test_runner.GarnishDiscovery')
    @patch('garnish.test_runner.prepare_test_suites_for_stir')
    def test_adapter_cleanup_on_failure(self, mock_prepare, mock_discovery, tmp_path):
        """Test that adapter cleans up temporary directories on failure."""
        # Given: Preparation fails
        mock_discovery.return_value.discover_bundles.return_value = [Mock()]
        mock_prepare.side_effect = Exception("Preparation failed")
        
        # Create a mock temp directory
        adapter = GarnishTestAdapter()
        adapter.output_dir = tmp_path / "temp_test_dir"
        adapter.output_dir.mkdir()

        # When/Then: Should clean up even on failure
        with pytest.raises(Exception):
            adapter.run_tests()
        
        # Verify cleanup would be called (in real implementation)
        # Note: This would need proper implementation in the adapter

    @patch('subprocess.run')
    def test_backward_compatibility_mode(self, mock_run, tmp_path):
        """Test fallback to old test runner when stir is not available."""
        # Given: Stir is not available
        mock_run.side_effect = FileNotFoundError()
        
        # When: Running tests with fallback enabled
        adapter = GarnishTestAdapter(fallback_to_simple=True)
        
        # Mock the simple runner
        with patch('garnish.test_runner._run_simple_tests') as mock_simple:
            mock_simple.return_value = {"total": 1, "passed": 1, "failed": 0}
            
            # Create a mock bundle
            with patch('garnish.test_runner.GarnishDiscovery') as mock_disc:
                mock_bundle = Mock(
                    name="test", 
                    component_type="resource",
                    load_examples=Mock(return_value={"ex": ""}),
                    load_fixtures=Mock(return_value={}),
                    fixtures_dir=Mock(exists=Mock(return_value=False))
                )
                mock_disc.return_value.discover_bundles.return_value = [mock_bundle]
                
                results = adapter.run_tests()
        
        # Then: Should fall back to simple runner
        mock_simple.assert_called_once()
        assert results["total"] == 1


class TestCLIIntegration:
    """Tests for CLI integration with new stir-based flow."""

    @patch('garnish.cli.GarnishTestAdapter')
    def test_cli_test_command_uses_adapter(self, mock_adapter_class):
        """Test that CLI test command uses the new adapter."""
        # Given: Mock adapter
        mock_adapter = Mock()
        mock_adapter.run_tests.return_value = {
            "total": 3, "passed": 3, "failed": 0, "failures": {}
        }
        mock_adapter_class.return_value = mock_adapter

        # When: Running CLI test command
        from garnish.cli import test
        from click.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(test, [])

        # Then: Should use adapter and show results
        mock_adapter.run_tests.assert_called_once()
        assert result.exit_code == 0
        assert "✅ All tests passed!" in result.output

    @patch('garnish.cli.GarnishTestAdapter')
    def test_cli_passes_options_to_adapter(self, mock_adapter_class):
        """Test that CLI options are passed to the adapter."""
        # Given: Mock adapter
        mock_adapter = Mock()
        mock_adapter.run_tests.return_value = {
            "total": 1, "passed": 1, "failed": 0, "failures": {}
        }
        mock_adapter_class.return_value = mock_adapter

        # When: Running with options
        from garnish.cli import test
        from click.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(test, [
            '--component-type', 'resource',
            '--parallel', '8',
            '--output-format', 'json',
            '--output-file', 'results.json'
        ])

        # Then: Options should be passed to adapter
        mock_adapter.run_tests.assert_called_once()
        call_args = mock_adapter.run_tests.call_args
        assert call_args[1].get('component_types') == ['resource']
        assert call_args[1].get('parallel') == 8


class TestReportGeneration:
    """Tests for test report generation compatibility."""

    def test_generate_markdown_report_from_stir_results(self, tmp_path):
        """Test that markdown reports work with stir results."""
        # Given: Stir-formatted results
        results = {
            "total": 3,
            "passed": 2,
            "failed": 1,
            "warnings": 1,
            "timestamp": "2024-01-01T12:00:00",
            "terraform_version": "OpenTofu v1.6.0",
            "test_details": {
                "resource_test1_test": {
                    "success": True,
                    "duration": 5.2,
                    "resources": 2
                },
                "resource_test2_test": {
                    "success": False,
                    "duration": 3.1,
                    "last_log": "Apply failed"
                }
            },
            "bundles": {
                "test1": {"component_type": "resource", "examples_count": 2},
                "test2": {"component_type": "resource", "examples_count": 1}
            }
        }

        # When: Generating markdown report
        from garnish.test_runner import _generate_markdown_report
        report_file = tmp_path / "report.md"
        _generate_markdown_report(results, report_file)

        # Then: Report should be generated with correct content
        assert report_file.exists()
        content = report_file.read_text()
        assert "# Garnish Test Report" in content
        assert "Total Tests: 3" in content
        assert "Passed: 2 ✅" in content
        assert "Failed: 1 ❌" in content
        assert "OpenTofu v1.6.0" in content
        assert "test1" in content
        assert "Apply failed" in content


class TestErrorHandling:
    """Tests for error handling during migration."""

    def test_handle_missing_tofusoup_gracefully(self):
        """Test graceful handling when tofusoup is not installed."""
        # Given: Tofusoup not available
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("soup not found")
            
            # When: Trying to run tests
            adapter = GarnishTestAdapter(fallback_to_simple=False)
            
            # Then: Should raise informative error
            with pytest.raises(RuntimeError) as exc_info:
                adapter.run_tests()
            
            assert "tofusoup" in str(exc_info.value).lower()
            assert "install" in str(exc_info.value).lower()

    def test_handle_incompatible_stir_version(self):
        """Test handling when stir version is incompatible."""
        # Given: Stir returns unexpected format
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout='{"incompatible": "format"}',  # Missing expected fields
                stderr=""
            )
            
            # When: Parsing results
            adapter = GarnishTestAdapter()
            with patch.object(adapter, '_discover_bundles', return_value=[Mock()]):
                with patch.object(adapter, '_prepare_test_suites', return_value=[Path("/test")]):
                    # Then: Should handle gracefully
                    with pytest.raises(KeyError) as exc_info:
                        adapter.run_tests()

    def test_preserve_garnish_specific_errors(self):
        """Test that garnish-specific errors are preserved and reported."""
        # Given: Garnish bundle with invalid structure
        from garnish.errors import GarnishError
        
        with patch('garnish.test_runner.GarnishDiscovery') as mock_disc:
            mock_disc.return_value.discover_bundles.side_effect = GarnishError(
                "Invalid garnish bundle structure"
            )
            
            # When: Running tests
            adapter = GarnishTestAdapter()
            
            # Then: Should preserve garnish error
            with pytest.raises(GarnishError) as exc_info:
                adapter.run_tests()
            
            assert "Invalid garnish bundle structure" in str(exc_info.value)


# --- Test Fixtures ---

@pytest.fixture
def mock_garnish_bundle():
    """Create a mock GarnishBundle for testing."""
    bundle = Mock(spec=GarnishBundle)
    bundle.name = "test_component"
    bundle.component_type = "resource"
    bundle.root_dir = Path("/test/bundle")
    bundle.docs_dir = Path("/test/bundle/docs")
    bundle.examples_dir = Path("/test/bundle/examples")
    bundle.fixtures_dir = Path("/test/bundle/fixtures")
    bundle.load_examples.return_value = {
        "example": 'resource "test" "example" { }'
    }
    bundle.load_fixtures.return_value = {}
    return bundle


@pytest.fixture
def temp_test_directory(tmp_path):
    """Create a temporary test directory structure."""
    test_dir = tmp_path / "garnish_tests"
    test_dir.mkdir()
    
    # Create some test suites
    for i in range(3):
        suite = test_dir / f"test_suite_{i}"
        suite.mkdir()
        (suite / "provider.tf").write_text('provider "test" {}')
        (suite / "main.tf").write_text(f'resource "test" "res_{i}" {{}}')
    
    return test_dir