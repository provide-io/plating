#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Provider source resolution with precedence handling."""

from typing import Any, Literal

from attrs import define, field
from provide.foundation import logger

from plating.config.manager import ConfigManager
from plating.config.runtime import PlatingConfig, get_config
from plating.detection.provider_source import detect_provider_source

ProviderSource = Literal["local", "remote"]


@define
class ProviderSourceResolution:
    """Result of provider source resolution."""

    source: ProviderSource
    """Resolved provider source: 'local' or 'remote'"""

    registry_url: str
    """Registry URL for the provider"""

    namespace: str
    """Provider namespace (e.g., 'local', 'hashicorp')"""

    resolution_path: list[str] = field(factory=list)
    """List of resolution steps taken (for debugging)"""


class ProviderSourceResolver:
    """Resolves provider source with precedence handling.

    Precedence (highest to lowest):
    1. CLI flags (--local, --remote, --registry-url)
    2. Environment variables (PLATING_PROVIDER_SOURCE, PLATING_REGISTRY_URL)
    3. Project config (pyproject.toml [tool.plating.provider])
    4. Global config (~/.config/plating/config.toml)
    5. Auto-detection (based on editable install)
    """

    def __init__(
        self,
        provider_name: str,
        package_name: str | None = None,
        config: PlatingConfig | None = None,
    ) -> None:
        """Initialize the resolver.

        Args:
            provider_name: Name of the provider (e.g., "pyvider")
            package_name: Optional package name for auto-detection
            config: Optional PlatingConfig instance (uses global if None)
        """
        self.provider_name = provider_name
        self.package_name = package_name
        self.config = config or get_config()

    def resolve(
        self,
        cli_source: str | None = None,
        cli_registry_url: str | None = None,
        cli_namespace: str | None = None,
    ) -> ProviderSourceResolution:
        """Resolve provider source with full precedence chain.

        Args:
            cli_source: Source from CLI flags ("local" or "remote")
            cli_registry_url: Registry URL from CLI flags
            cli_namespace: Namespace from CLI flags

        Returns:
            ProviderSourceResolution with final resolved values
        """
        resolution_path: list[str] = []

        # Load config files
        global_config = ConfigManager.load_global_config()
        project_config = ConfigManager.load_project_config()
        provider_config = ConfigManager.get_provider_config(self.provider_name, global_config, project_config)

        # Resolve source (with precedence)
        source = self._resolve_source(cli_source, provider_config, resolution_path)

        # Resolve registry URL (with precedence)
        registry_url = self._resolve_registry_url(cli_registry_url, provider_config, resolution_path)

        # Resolve namespace (with precedence)
        namespace = self._resolve_namespace(cli_namespace, provider_config, source, resolution_path)

        logger.debug(f"Resolved provider source: {source}, registry: {registry_url}, namespace: {namespace}")
        logger.debug(f"Resolution path: {' → '.join(resolution_path)}")

        return ProviderSourceResolution(
            source=source,
            registry_url=registry_url,
            namespace=namespace,
            resolution_path=resolution_path,
        )

    def _resolve_source(
        self,
        cli_source: str | None,
        provider_config: dict[str, Any],
        resolution_path: list[str],
    ) -> ProviderSource:
        """Resolve provider source with precedence."""
        # 1. CLI flags (highest priority)
        if cli_source in ("local", "remote"):
            resolution_path.append(f"CLI flag: {cli_source}")
            return cli_source  # type: ignore

        # 2. Environment variables
        if self.config.provider_source not in ("auto", "") and self.config.provider_source in ("local", "remote"):
            resolution_path.append(f"Environment: {self.config.provider_source}")
            return self.config.provider_source  # type: ignore

        # 3. Provider-specific or default config
        config_source = provider_config.get("source")
        if config_source in ("local", "remote"):
            resolution_path.append(f"Config file: {config_source}")
            return config_source  # type: ignore

        # 4. Auto-detection (lowest priority, default)
        if self.config.auto_detect_enabled:
            detected_source = detect_provider_source(self.provider_name, self.package_name)
            resolution_path.append(f"Auto-detected: {detected_source}")
            return detected_source

        # 5. Final fallback
        resolution_path.append("Fallback: local")
        return "local"

    def _resolve_registry_url(
        self,
        cli_registry_url: str | None,
        provider_config: dict[str, Any],
        resolution_path: list[str],
    ) -> str:
        """Resolve registry URL with precedence."""
        # 1. CLI flags
        if cli_registry_url:
            resolution_path.append(f"Registry URL from CLI: {cli_registry_url}")
            return cli_registry_url

        # 2. Environment variables
        if self.config.provider_registry_url != "registry.terraform.io":
            resolution_path.append(f"Registry URL from env: {self.config.provider_registry_url}")
            return self.config.provider_registry_url

        # 3. Provider-specific or default config
        config_registry_url = provider_config.get("registry_url")
        if config_registry_url:
            resolution_path.append(f"Registry URL from config: {config_registry_url}")
            return config_registry_url

        # 4. Default
        resolution_path.append(f"Registry URL default: {self.config.provider_registry_url}")
        return self.config.provider_registry_url

    def _resolve_namespace(
        self,
        cli_namespace: str | None,
        provider_config: dict[str, Any],
        source: ProviderSource,
        resolution_path: list[str],
    ) -> str:
        """Resolve namespace with precedence."""
        # 1. CLI flags
        if cli_namespace:
            resolution_path.append(f"Namespace from CLI: {cli_namespace}")
            return cli_namespace

        # 2. Environment variables
        if self.config.provider_namespace != "local":
            resolution_path.append(f"Namespace from env: {self.config.provider_namespace}")
            return self.config.provider_namespace

        # 3. Provider-specific or default config
        config_namespace = provider_config.get("namespace")
        if config_namespace:
            resolution_path.append(f"Namespace from config: {config_namespace}")
            return config_namespace

        # 4. Smart default based on source
        if source == "local":
            resolution_path.append("Namespace default (local): local")
            return "local"
        else:
            # For remote, use provide-io as default namespace
            resolution_path.append("Namespace default (remote): provide-io")
            return "provide-io"


def resolve_provider_source(
    provider_name: str,
    package_name: str | None = None,
    cli_source: str | None = None,
    cli_registry_url: str | None = None,
    cli_namespace: str | None = None,
    config: PlatingConfig | None = None,
) -> ProviderSourceResolution:
    """Convenience function to resolve provider source.

    Args:
        provider_name: Name of the provider
        package_name: Optional package name for auto-detection
        cli_source: Optional source from CLI flags
        cli_registry_url: Optional registry URL from CLI flags
        cli_namespace: Optional namespace from CLI flags
        config: Optional PlatingConfig instance

    Returns:
        ProviderSourceResolution with resolved values
    """
    resolver = ProviderSourceResolver(provider_name, package_name, config)
    return resolver.resolve(cli_source, cli_registry_url, cli_namespace)


# 🍽️📖🔚
