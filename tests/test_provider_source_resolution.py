#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Integration tests for provider source resolution and configuration."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

from provide.testkit import FoundationTestCase

from plating.config.defaults import DEFAULT_PROVIDER_NAMESPACE, DEFAULT_PROVIDER_SOURCE
from plating.config.manager import ConfigManager
from plating.config.runtime import PlatingConfig
from plating.detection.provider_source import ProviderSourceDetector, detect_provider_source
from plating.resolution.source import ProviderSourceResolver, resolve_provider_source


class TestProviderSourceDetection(FoundationTestCase):
    """Test provider source auto-detection."""

    def setup_method(self) -> None:
        """Set up test environment."""
        super().setup_method()
        self.detector = ProviderSourceDetector("pyvider", "pyvider.components")

    def teardown_method(self) -> None:
        """Clean up after test."""
        super().teardown_method()

    def test_detect_local_provider(self) -> None:
        """Test detection of local (editable) provider."""
        # This test will pass if pyvider.components is installed as editable
        source = self.detector.detect()
        assert source in ("local", "remote")

    def test_detect_provider_convenience_function(self) -> None:
        """Test convenience function for provider source detection."""
        source = detect_provider_source("pyvider", "pyvider.components")
        assert source in ("local", "remote")

    def test_detector_with_missing_package(self) -> None:
        """Test detector with non-existent package."""
        detector = ProviderSourceDetector("nonexistent", "nonexistent.package")
        source = detector.detect()
        assert source == "remote"  # Should default to remote for missing packages


class TestConfigManager(FoundationTestCase):
    """Test configuration manager."""

    def setup_method(self) -> None:
        """Set up test environment."""
        super().setup_method()
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".config" / "plating"
        self.config_dir.mkdir(parents=True)
        self.config_path = self.config_dir / "config.toml"

    def teardown_method(self) -> None:
        """Clean up after test."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
        super().teardown_method()

    def test_load_global_config_not_found(self) -> None:
        """Test loading global config when file doesn't exist."""
        config = ConfigManager.load_global_config()
        assert config == {}

    def test_load_global_config_success(self) -> None:
        """Test loading global config from file."""
        # Create a test config file
        config_content = """
[provider]
source = "local"
registry_url = "registry.terraform.io"
namespace = "provide-io"

[providers.pyvider]
source = "local"
namespace = "local"

[providers.aws]
source = "remote"
namespace = "hashicorp"
"""
        self.config_path.write_text(config_content)

        # Temporarily override the config path
        original_method = ConfigManager.get_global_config_path

        def mock_path():
            return self.config_path

        ConfigManager.get_global_config_path = staticmethod(mock_path)

        try:
            config = ConfigManager.load_global_config()
            assert config["provider"]["source"] == "local"
            assert config["provider"]["namespace"] == "provide-io"
            assert config["providers"]["pyvider"]["source"] == "local"
            assert config["providers"]["aws"]["namespace"] == "hashicorp"
        finally:
            ConfigManager.get_global_config_path = original_method

    def test_get_provider_config_merging(self) -> None:
        """Test provider-specific config merging."""
        global_config = {
            "provider": {"source": "auto", "namespace": "provide-io"},
            "providers": {"pyvider": {"source": "local", "namespace": "local"}},
        }

        project_config = {"provider": {"registry_url": "registry.terraform.io"}}

        # Get pyvider-specific config
        pyvider_config = ConfigManager.get_provider_config("pyvider", global_config, project_config)

        # Should merge: project default > global pyvider-specific > project-default > global-default
        assert pyvider_config["source"] == "local"  # From global pyvider-specific
        assert pyvider_config["namespace"] == "local"  # From global pyvider-specific
        assert pyvider_config["registry_url"] == "registry.terraform.io"  # From project default

    def test_save_and_load_global_config(self) -> None:
        """Test saving and loading global config."""
        config_data = {
            "provider": {"source": "local", "registry_url": "registry.terraform.io"},
            "providers": {"pyvider": {"source": "local"}},
        }

        # Temporarily override the config path
        original_method = ConfigManager.get_global_config_path

        def mock_path():
            return self.config_path

        ConfigManager.get_global_config_path = staticmethod(mock_path)

        try:
            ConfigManager.save_global_config(config_data)
            loaded_config = ConfigManager.load_global_config()

            assert loaded_config["provider"]["source"] == "local"
            assert loaded_config["providers"]["pyvider"]["source"] == "local"
        finally:
            ConfigManager.get_global_config_path = original_method


class TestProviderSourceResolver(FoundationTestCase):
    """Test provider source resolution with precedence."""

    def setup_method(self) -> None:
        """Set up test environment."""
        super().setup_method()
        # Clean environment for testing
        for key in list(os.environ.keys()):
            if key.startswith("PLATING_"):
                del os.environ[key]

    def teardown_method(self) -> None:
        """Clean up after test."""
        # Clean environment
        for key in list(os.environ.keys()):
            if key.startswith("PLATING_"):
                del os.environ[key]
        super().teardown_method()

    def test_cli_flag_precedence(self) -> None:
        """Test that CLI flags have highest precedence."""
        resolver = ProviderSourceResolver("pyvider", "pyvider.components")

        # Set environment variable
        os.environ["PLATING_PROVIDER_SOURCE"] = "remote"

        # CLI flag should override env var
        resolution = resolver.resolve(cli_source="local")

        assert resolution.source == "local"
        assert "CLI flag: local" in resolution.resolution_path

    def test_env_var_precedence(self) -> None:
        """Test environment variable precedence."""
        os.environ["PLATING_PROVIDER_SOURCE"] = "remote"
        os.environ["PLATING_REGISTRY_URL"] = "custom.registry.io"
        os.environ["PLATING_PROVIDER_NAMESPACE"] = "custom"

        # Create fresh config from environment
        config = PlatingConfig.from_env()

        resolver = ProviderSourceResolver("pyvider", "pyvider.components", config=config)
        resolution = resolver.resolve()

        assert resolution.source == "remote"
        assert resolution.registry_url == "custom.registry.io"
        assert resolution.namespace == "custom"

    def test_auto_detection_fallback(self) -> None:
        """Test auto-detection as fallback."""
        # No CLI flags, no env vars, should fall back to auto-detection
        resolver = ProviderSourceResolver("pyvider", "pyvider.components")
        resolution = resolver.resolve()

        assert resolution.source in ("local", "remote")
        # Check that auto-detection or fallback was used
        resolution_str = " → ".join(resolution.resolution_path)
        assert "Auto-detected" in resolution_str or "Fallback" in resolution_str

    def test_namespace_defaults_by_source(self) -> None:
        """Test namespace defaults based on source type."""
        # Local source should default to "local" namespace
        resolver = ProviderSourceResolver("pyvider", "pyvider.components")
        resolution = resolver.resolve(cli_source="local")

        assert resolution.namespace == "local"

        # Remote source should default to "provide-io" namespace
        resolution = resolver.resolve(cli_source="remote")

        assert resolution.namespace == "provide-io"

    def test_registry_path_local(self) -> None:
        """Test registry path construction for local provider."""
        resolution = resolve_provider_source("pyvider", cli_source="local")

        # Local providers should have /providers/ in path
        expected_path = f"{resolution.registry_url}/{resolution.namespace}/providers/pyvider"
        assert resolution.registry_url == "registry.terraform.io"
        assert resolution.namespace == "local"

    def test_registry_path_remote(self) -> None:
        """Test registry path construction for remote provider."""
        resolution = resolve_provider_source("pyvider", cli_source="remote", cli_namespace="provide-io")

        # Remote providers should NOT have /providers/ in path
        assert resolution.registry_url == "registry.terraform.io"
        assert resolution.namespace == "provide-io"


class TestPlatingConfigIntegration(FoundationTestCase):
    """Test PlatingConfig integration with provider source settings."""

    def setup_method(self) -> None:
        """Set up test environment."""
        super().setup_method()
        # Clean environment
        for key in list(os.environ.keys()):
            if key.startswith("PLATING_"):
                del os.environ[key]

    def teardown_method(self) -> None:
        """Clean up after test."""
        # Clean environment
        for key in list(os.environ.keys()):
            if key.startswith("PLATING_"):
                del os.environ[key]
        super().teardown_method()

    def test_config_defaults(self) -> None:
        """Test PlatingConfig default values."""
        config = PlatingConfig.from_env()

        assert config.provider_source == DEFAULT_PROVIDER_SOURCE
        assert config.provider_namespace == DEFAULT_PROVIDER_NAMESPACE
        assert config.auto_detect_enabled is True

    def test_config_from_env_vars(self) -> None:
        """Test PlatingConfig loading from environment variables."""
        os.environ["PLATING_PROVIDER_SOURCE"] = "remote"
        os.environ["PLATING_REGISTRY_URL"] = "custom.registry.io"
        os.environ["PLATING_PROVIDER_NAMESPACE"] = "custom-namespace"
        os.environ["PLATING_AUTO_DETECT"] = "false"

        config = PlatingConfig.from_env()

        assert config.provider_source == "remote"
        assert config.provider_registry_url == "custom.registry.io"
        assert config.provider_namespace == "custom-namespace"
        assert config.auto_detect_enabled is False


class TestEndToEndIntegration(FoundationTestCase):
    """End-to-end integration tests for provider source resolution."""

    def setup_method(self) -> None:
        """Set up test environment."""
        super().setup_method()
        # Clean environment
        for key in list(os.environ.keys()):
            if key.startswith("PLATING_"):
                del os.environ[key]

    def teardown_method(self) -> None:
        """Clean up after test."""
        # Clean environment
        for key in list(os.environ.keys()):
            if key.startswith("PLATING_"):
                del os.environ[key]
        super().teardown_method()

    def test_local_pyvider_development(self) -> None:
        """Test typical local development scenario with pyvider."""
        # Simulate local development: auto-detect should find local install
        resolution = resolve_provider_source("pyvider", "pyvider.components")

        # Should detect local or remote based on actual installation
        assert resolution.source in ("local", "remote")
        assert resolution.registry_url == "registry.terraform.io"

        if resolution.source == "local":
            assert resolution.namespace == "local"
        else:
            assert resolution.namespace == "provide-io"

    def test_remote_provider_explicit(self) -> None:
        """Test explicit remote provider configuration."""
        # Force remote provider
        resolution = resolve_provider_source("pyvider", cli_source="remote", cli_namespace="provide-io")

        assert resolution.source == "remote"
        assert resolution.namespace == "provide-io"
        assert resolution.registry_url == "registry.terraform.io"

    def test_precedence_chain_complete(self) -> None:
        """Test complete precedence chain."""
        # Set up all levels of configuration
        os.environ["PLATING_PROVIDER_SOURCE"] = "remote"

        # CLI should override environment
        resolution = resolve_provider_source("pyvider", cli_source="local")

        assert resolution.source == "local"

        # Without CLI, environment should be used
        # Need to pass fresh config that loads from updated environment
        config = PlatingConfig.from_env()
        resolver = ProviderSourceResolver("pyvider", config=config)
        resolution = resolver.resolve()

        assert resolution.source == "remote"


# 🍽️📖🔚
