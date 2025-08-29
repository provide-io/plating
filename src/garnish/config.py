#
# garnish/config.py
#
"""Configuration management for garnish."""

import os
from pathlib import Path
from typing import Optional

import attrs


@attrs.define
class GarnishConfig:
    """Configuration for garnish operations."""
    
    # Terraform/OpenTofu configuration
    terraform_binary: str = attrs.field(
        default=None,
        metadata={"help": "Path to terraform/tofu binary"}
    )
    plugin_cache_dir: Path = attrs.field(
        default=None,
        metadata={"help": "Terraform plugin cache directory"}
    )
    
    # Test execution configuration
    test_timeout: int = attrs.field(
        default=120,
        metadata={"help": "Timeout for test execution in seconds"}
    )
    test_parallel: int = attrs.field(
        default=4,
        metadata={"help": "Number of parallel test executions"}
    )
    
    # Output configuration
    output_dir: Path = attrs.field(
        default=Path("./docs"),
        metadata={"help": "Default output directory for documentation"}
    )
    
    # Component directories
    resources_dir: Path = attrs.field(
        default=Path("./resources"),
        metadata={"help": "Directory containing resource definitions"}
    )
    data_sources_dir: Path = attrs.field(
        default=Path("./data_sources"),
        metadata={"help": "Directory containing data source definitions"}
    )
    functions_dir: Path = attrs.field(
        default=Path("./functions"),
        metadata={"help": "Directory containing function definitions"}
    )
    
    def __attrs_post_init__(self):
        """Initialize derived configuration values."""
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
        config_dict = {}
        
        # Map environment variables to config fields
        env_mapping = {
            "GARNISH_TF_BINARY": "terraform_binary",
            "TF_PLUGIN_CACHE_DIR": "plugin_cache_dir",
            "GARNISH_TEST_TIMEOUT": "test_timeout",
            "GARNISH_TEST_PARALLEL": "test_parallel",
            "GARNISH_OUTPUT_DIR": "output_dir",
        }
        
        for env_var, field_name in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                field = attrs.fields_dict(cls)[field_name]
                if field.type == Path:
                    config_dict[field_name] = Path(value)
                elif field.type == int:
                    config_dict[field_name] = int(value)
                else:
                    config_dict[field_name] = value
        
        return cls(**config_dict)
    
    def get_terraform_env(self) -> dict[str, str]:
        """Get environment variables for terraform execution."""
        env = os.environ.copy()
        
        if self.plugin_cache_dir and self.plugin_cache_dir.exists():
            env["TF_PLUGIN_CACHE_DIR"] = str(self.plugin_cache_dir)
        
        return env


# Global configuration instance
_config: Optional[GarnishConfig] = None


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