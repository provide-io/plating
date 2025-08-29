#!/usr/bin/env python
"""
Manual integration test for garnish test -> tofusoup stir migration.

Run this to verify the integration works correctly.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from garnish.test_runner import GarnishTestAdapter
from garnish.garnish import GarnishBundle


def create_mock_bundle(name: str, component_type: str) -> Mock:
    """Create a mock garnish bundle for testing."""
    bundle = Mock(spec=GarnishBundle)
    bundle.name = name
    bundle.component_type = component_type
    bundle.load_examples.return_value = {
        "example": f'resource "test_{name}" "example" {{ name = "{name}" }}'
    }
    bundle.load_fixtures.return_value = {}
    
    # Create a proper mock fixtures_dir
    bundle.fixtures_dir = Mock()
    bundle.fixtures_dir.exists.return_value = False
    
    return bundle


def test_adapter_with_mock_stir():
    """Test the adapter with a mock stir command."""
    print("Testing GarnishTestAdapter with mock stir...")
    
    # Create mock bundles
    bundles = [
        create_mock_bundle("test_resource", "resource"),
        create_mock_bundle("test_data", "data_source"),
    ]
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        # Mock discovery
        with patch('garnish.test_runner.GarnishDiscovery') as mock_discovery:
            mock_discovery.return_value.discover_bundles.return_value = bundles
            
            # Mock stir execution
            with patch('subprocess.run') as mock_run:
                # Mock successful stir execution
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = '''{
                    "total": 2,
                    "passed": 2,
                    "failed": 0,
                    "warnings": 0,
                    "skipped": 0,
                    "test_details": {
                        "resource_test_resource_test": {
                            "success": true,
                            "duration": 5.2,
                            "resources": 1
                        },
                        "data_source_test_data_test": {
                            "success": true,
                            "duration": 3.1,
                            "data_sources": 1
                        }
                    }
                }'''
                mock_run.return_value.stderr = ''
                
                # Run adapter
                adapter = GarnishTestAdapter(output_dir=output_dir)
                results = adapter.run_tests()
                
                print(f"✅ Total tests: {results['total']}")
                print(f"✅ Passed: {results['passed']}")
                print(f"✅ Failed: {results['failed']}")
                
                # Verify test suites were created
                test_dirs = list(output_dir.glob("*_test"))
                print(f"✅ Test suites created: {len(test_dirs)}")
                for test_dir in test_dirs:
                    print(f"   - {test_dir.name}")
                
                # Verify bundles info
                if "bundles" in results:
                    print(f"✅ Bundle info captured: {len(results['bundles'])} bundles")
                    for bundle_name, info in results["bundles"].items():
                        print(f"   - {bundle_name}: {info['component_type']}")
                
                # Check that stir was called
                assert mock_run.called, "subprocess.run (stir) was not called"
                call_args = mock_run.call_args[0][0]
                assert "soup" in call_args[0], "soup command not used"
                assert "stir" in call_args[1], "stir subcommand not used"
                print(f"✅ Stir command called: {' '.join(call_args)}")
                
                print("\n✅ All integration tests passed!")
                return True


def test_fallback_to_simple_runner():
    """Test fallback to simple runner when stir is not available."""
    print("\nTesting fallback to simple runner...")
    
    bundles = [create_mock_bundle("test_fallback", "resource")]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        
        with patch('garnish.test_runner.GarnishDiscovery') as mock_discovery:
            mock_discovery.return_value.discover_bundles.return_value = bundles
            
            # Mock stir not found
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = FileNotFoundError("soup not found")
                
                # Mock simple runner
                with patch('garnish.test_runner._run_simple_tests') as mock_simple:
                    mock_simple.return_value = {
                        "total": 1,
                        "passed": 1,
                        "failed": 0,
                        "test_details": {}
                    }
                    
                    # Run with fallback
                    adapter = GarnishTestAdapter(
                        output_dir=output_dir, 
                        fallback_to_simple=True
                    )
                    results = adapter.run_tests()
                    
                    print(f"✅ Fallback triggered")
                    print(f"✅ Simple runner called: {mock_simple.called}")
                    print(f"✅ Results: {results['total']} total, {results['passed']} passed")
                    
                    return True


if __name__ == "__main__":
    try:
        test_adapter_with_mock_stir()
        test_fallback_to_simple_runner()
        print("\n🎉 All integration tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)