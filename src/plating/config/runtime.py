#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Configuration management for plating."""

import os
from pathlib import Path

from attrs import define
from provide.foundation.config import RuntimeConfig, field

from plating.config.defaults import (
    DEFAULT_AUTO_DETECT_ENABLED,
    DEFAULT_DATA_SOURCES_DIR,
    DEFAULT_EXAMPLE_PLACEHOLDER,
    DEFAULT_FALLBACK_ARGUMENTS_MARKDOWN,
    DEFAULT_FALLBACK_SIGNATURE_FORMAT,
    DEFAULT_FUNCTIONS_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PROVIDER_NAMESPACE,
    DEFAULT_PROVIDER_REGISTRY_URL,
    DEFAULT_PROVIDER_SOURCE,
    DEFAULT_RESOURCES_DIR,
    DEFAULT_TEST_PARALLEL,
    DEFAULT_TEST_TIMEOUT,
    ENV_PLATING_AUTO_DETECT,
    ENV_PLATING_EXAMPLE_PLACEHOLDER,
    ENV_PLATING_FALLBACK_ARGUMENTS,
    ENV_PLATING_FALLBACK_SIGNATURE,
    ENV_PLATING_OUTPUT_DIR,
    ENV_PLATING_PROVIDER_NAMESPACE,
    ENV_PLATING_PROVIDER_SOURCE,
    ENV_PLATING_REGISTRY_URL,
    ENV_PLATING_TEST_PARALLEL,
    ENV_PLATING_TEST_TIMEOUT,
    ENV_PLATING_TF_BINARY,
    ENV_TF_PLUGIN_CACHE_DIR,
)


@define
class PlatingConfig(RuntimeConfig):
    """Configuration for plating operations."""

    # Template generation configuration
    example_placeholder: str = field(
        default=DEFAULT_EXAMPLE_PLACEHOLDER,
        description="Placeholder when no example is available",
        env_var=ENV_PLATING_EXAMPLE_PLACEHOLDER,
    )
    fallback_signature_format: str = field(
        default=DEFAULT_FALLBACK_SIGNATURE_FORMAT,
        description="Fallback signature format for unknown functions",
        env_var=ENV_PLATING_FALLBACK_SIGNATURE,
    )
    fallback_arguments_markdown: str = field(
        default=DEFAULT_FALLBACK_ARGUMENTS_MARKDOWN,
        description="Fallback arguments documentation",
        env_var=ENV_PLATING_FALLBACK_ARGUMENTS,
    )

    # Terraform/OpenTofu configuration
    terraform_binary: str | None = field(
        default=None,
        description="Path to terraform/tofu binary",
        env_var=ENV_PLATING_TF_BINARY,
    )
    plugin_cache_dir: Path | None = field(
        default=None,
        description="Terraform plugin cache directory",
        env_var=ENV_TF_PLUGIN_CACHE_DIR,
    )

    # Provider source configuration
    provider_source: str = field(
        default=DEFAULT_PROVIDER_SOURCE,
        description="Provider source type: 'auto', 'local', or 'remote'",
        env_var=ENV_PLATING_PROVIDER_SOURCE,
    )
    provider_registry_url: str = field(
        default=DEFAULT_PROVIDER_REGISTRY_URL,
        description="Provider registry URL for remote providers",
        env_var=ENV_PLATING_REGISTRY_URL,
    )
    provider_namespace: str = field(
        default=DEFAULT_PROVIDER_NAMESPACE,
        description="Provider namespace (e.g., 'local', 'hashicorp')",
        env_var=ENV_PLATING_PROVIDER_NAMESPACE,
    )
    auto_detect_enabled: bool = field(
        default=DEFAULT_AUTO_DETECT_ENABLED,
        description="Enable auto-detection of provider source",
        env_var=ENV_PLATING_AUTO_DETECT,
    )

    # Test execution configuration
    test_timeout: int = field(
        default=DEFAULT_TEST_TIMEOUT,
        description="Timeout for test execution in seconds",
        env_var=ENV_PLATING_TEST_TIMEOUT,
    )
    test_parallel: int = field(
        default=DEFAULT_TEST_PARALLEL,
        description="Number of parallel test executions",
        env_var=ENV_PLATING_TEST_PARALLEL,
    )

    # Output configuration
    output_dir: Path = field(
        factory=lambda: Path(DEFAULT_OUTPUT_DIR),
        description="Default output directory for documentation",
        env_var=ENV_PLATING_OUTPUT_DIR,
    )

    # Component directories
    resources_dir: Path = field(
        factory=lambda: Path(DEFAULT_RESOURCES_DIR),
        description="Directory containing resource definitions",
    )
    data_sources_dir: Path = field(
        factory=lambda: Path(DEFAULT_DATA_SOURCES_DIR),
        description="Directory containing data source definitions",
    )
    functions_dir: Path = field(
        factory=lambda: Path(DEFAULT_FUNCTIONS_DIR),
        description="Directory containing function definitions",
    )

    # Content merging configuration
    provides_content: bool = field(
        default=False,
        description="Indicates this package provides mergeable content in plating/",
    )
    merge_content_from: list[str] = field(
        factory=list,
        description="List of package names to merge content from",
    )
    exclude_from_merge: list[str] = field(
        factory=list,
        description="Directories to exclude from content merging (e.g., ['templates', 'partials'])",
    )

    def __attrs_post_init__(self) -> None:
        """Initialize derived configuration values."""
        super().__attrs_post_init__()

        # Auto-detect terraform binary if not specified
        if self.terraform_binary is None:
            import shutil

            self.terraform_binary = shutil.which("tofu") or shutil.which("terraform") or "terraform"

        # Set default plugin cache directory
        if self.plugin_cache_dir is None:
            self.plugin_cache_dir = Path.home() / ".terraform.d" / "plugin-cache"

    def get_terraform_env(self) -> dict[str, str]:
        """Get environment variables for terraform execution."""
        env = os.environ.copy()

        if self.plugin_cache_dir and self.plugin_cache_dir.exists():
            env["TF_PLUGIN_CACHE_DIR"] = str(self.plugin_cache_dir)

        return env


# Global configuration instance
_config: PlatingConfig | None = None


def get_config(project_root: Path | None = None) -> PlatingConfig:
    """Get the global configuration instance.

    Loads configuration from pyproject.toml [tool.plating] section if available,
    then merges with environment variables (env vars take precedence).

    Args:
        project_root: Optional project root directory to search for pyproject.toml

    Returns:
        PlatingConfig instance
    """
    global _config
    if _config is None:
        # Import here to avoid circular dependency
        from plating.cli.utils.pyproject import get_plating_config_from_pyproject

        # Load from pyproject.toml if available
        pyproject_path = None
        if project_root:
            pyproject_path = project_root / "pyproject.toml"
        else:
            pyproject_path = Path.cwd() / "pyproject.toml"

        plating_config = get_plating_config_from_pyproject(pyproject_path)

        # Start with env-based config (takes precedence)
        _config = PlatingConfig.from_env()

        # Merge pyproject.toml config (only for fields not set by env)
        if plating_config:
            if "merge_content_from" in plating_config and not _config.merge_content_from:
                _config.merge_content_from = plating_config["merge_content_from"]
            if "exclude_from_merge" in plating_config and not _config.exclude_from_merge:
                _config.exclude_from_merge = plating_config["exclude_from_merge"]
            if "provides_content" in plating_config:
                _config.provides_content = plating_config["provides_content"]

    return _config


def set_config(config: PlatingConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


# 🍽️📖🔚
