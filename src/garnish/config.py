#
# garnish/config.py
#
"""Configuration management for garnish."""

import os
from pathlib import Path
from typing import Any

import attrs
from provide.foundation.config import BaseConfig, field


@attrs.define
class GarnishConfig(BaseConfig):
    """Configuration for garnish operations."""

    # Terraform/OpenTofu configuration
    terraform_binary: str | None = field(
        default=None,
        description="Path to terraform/tofu binary",
        env_var="GARNISH_TF_BINARY"
    )
    plugin_cache_dir: Path | None = field(
        default=None,
        description="Terraform plugin cache directory",
        env_var="TF_PLUGIN_CACHE_DIR"
    )

    # Test execution configuration
    test_timeout: int = field(
        default=120,
        description="Timeout for test execution in seconds",
        env_var="GARNISH_TEST_TIMEOUT"
    )
    test_parallel: int = field(
        default=4,
        description="Number of parallel test executions",
        env_var="GARNISH_TEST_PARALLEL"
    )

    # Output configuration
    output_dir: Path = field(
        default=Path("./docs"),
        description="Default output directory for documentation",
        env_var="GARNISH_OUTPUT_DIR"
    )

    # Component directories
    resources_dir: Path = field(
        default=Path("./resources"),
        description="Directory containing resource definitions"
    )
    data_sources_dir: Path = field(
        default=Path("./data_sources"),
        description="Directory containing data source definitions"
    )
    functions_dir: Path = field(
        default=Path("./functions"),
        description="Directory containing function definitions"
    )

    def __attrs_post_init__(self) -> None:
        """Initialize derived configuration values."""
        super().__attrs_post_init__()
        
        # Auto-detect terraform binary if not specified
        if self.terraform_binary is None:
            import shutil
            self.terraform_binary = (
                shutil.which("tofu") or
                shutil.which("terraform") or
                "terraform"
            )

        # Set default plugin cache directory
        if self.plugin_cache_dir is None:
            self.plugin_cache_dir = Path.home() / ".terraform.d" / "plugin-cache"

    @classmethod
    def from_env(cls) -> "GarnishConfig":
        """Create configuration from environment variables."""
        # Create an instance with defaults
        config = cls()
        
        # Load environment overrides using the field metadata
        env_updates = {}
        for field_info in attrs.fields(cls):
            env_var = field_info.metadata.get("env_var")
            if env_var and env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion based on field type
                field_type = field_info.type
                if field_type == Path or field_type == Path | None:
                    env_updates[field_info.name] = Path(value)
                elif field_type == int or field_type == int | None:
                    env_updates[field_info.name] = int(value)
                else:
                    env_updates[field_info.name] = value
        
        # Apply updates
        if env_updates:
            config = attrs.evolve(config, **env_updates)
        
        return config

    def get_terraform_env(self) -> dict[str, str]:
        """Get environment variables for terraform execution."""
        env = os.environ.copy()

        if self.plugin_cache_dir and self.plugin_cache_dir.exists():
            env["TF_PLUGIN_CACHE_DIR"] = str(self.plugin_cache_dir)

        return env


# Global configuration instance
_config: GarnishConfig | None = None


def get_config() -> GarnishConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = GarnishConfig.from_env()
    return _config


def set_config(config: GarnishConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
