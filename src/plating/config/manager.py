#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Configuration manager for loading provider source configurations."""

from pathlib import Path
import tomllib
from typing import Any

from provide.foundation import logger


class ConfigManager:
    """Manages loading configuration from multiple sources."""

    @staticmethod
    def get_global_config_path() -> Path:
        """Get the path to the global configuration file.

        Returns:
            Path to ~/.config/plating/config.toml
        """
        return Path.home() / ".config" / "plating" / "config.toml"

    @staticmethod
    def load_global_config() -> dict[str, Any]:
        """Load global configuration from ~/.config/plating/config.toml.

        Returns:
            Dictionary with global configuration, empty if file doesn't exist
        """
        config_path = ConfigManager.get_global_config_path()

        if not config_path.exists():
            logger.debug(f"Global config not found at {config_path}")
            return {}

        try:
            with config_path.open("rb") as f:
                config = tomllib.load(f)
                logger.debug(f"Loaded global config from {config_path}")
                return config
        except Exception as e:
            logger.warning(f"Error loading global config from {config_path}: {e}")
            return {}

    @staticmethod
    def load_project_config(project_dir: Path | None = None) -> dict[str, Any]:
        """Load project configuration from pyproject.toml.

        Args:
            project_dir: Project directory to search for pyproject.toml.
                        If None, searches from current directory upwards.

        Returns:
            Dictionary with project configuration under [tool.plating.provider]
        """
        if project_dir is None:
            project_dir = Path.cwd()

        # Search upwards for pyproject.toml
        current_dir = project_dir.resolve()
        for _ in range(10):  # Limit search depth
            pyproject_path = current_dir / "pyproject.toml"

            if pyproject_path.exists():
                try:
                    with pyproject_path.open("rb") as f:
                        config = tomllib.load(f)
                        logger.debug(f"Loaded project config from {pyproject_path}")

                        # Extract [tool.plating.provider] section if it exists
                        plating_config = config.get("tool", {}).get("plating", {})
                        return plating_config

                except Exception as e:
                    logger.warning(f"Error loading project config from {pyproject_path}: {e}")
                    return {}

            # Move up one directory
            parent = current_dir.parent
            if parent == current_dir:
                break
            current_dir = parent

        logger.debug("No pyproject.toml found in project hierarchy")
        return {}

    @staticmethod
    def get_provider_config(
        provider_name: str,
        global_config: dict[str, Any] | None = None,
        project_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get provider-specific configuration.

        Merges global and project configs with project taking precedence.

        Args:
            provider_name: Name of the provider to get config for
            global_config: Global configuration dict (loaded if None)
            project_config: Project configuration dict (loaded if None)

        Returns:
            Dictionary with provider configuration
        """
        if global_config is None:
            global_config = ConfigManager.load_global_config()

        if project_config is None:
            project_config = ConfigManager.load_project_config()

        # Get default provider config from global
        global_provider_config = global_config.get("provider", {})

        # Get default provider config from project
        project_provider_config = project_config.get("provider", {})

        # Get provider-specific config from global
        global_providers = global_config.get("providers", {})
        global_specific = global_providers.get(provider_name, {})

        # Get provider-specific config from project
        project_providers = project_config.get("providers", {})
        project_specific = project_providers.get(provider_name, {})

        # Merge with precedence: project-specific > global-specific > project-default > global-default
        merged = {}
        merged.update(global_provider_config)
        merged.update(project_provider_config)
        merged.update(global_specific)
        merged.update(project_specific)

        return merged

    @staticmethod
    def save_global_config(config: dict[str, Any]) -> None:
        """Save global configuration to ~/.config/plating/config.toml.

        Args:
            config: Configuration dictionary to save
        """
        import tomli_w

        config_path = ConfigManager.get_global_config_path()

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with config_path.open("wb") as f:
                tomli_w.dump(config, f)
            logger.debug(f"Saved global config to {config_path}")
        except Exception as e:
            logger.error(f"Error saving global config to {config_path}: {e}")
            raise


# 🍽️📖🔚
