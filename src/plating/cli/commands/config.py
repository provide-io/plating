# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Config command implementation."""

import sys

import click
from provide.foundation import perr, pout

from plating.config.manager import ConfigManager


@click.group("config")
def config_command() -> None:
    """Manage plating provider configuration."""
    pass


@config_command.command("show")
def show_config() -> None:
    """Show current global configuration."""
    try:
        config = ConfigManager.load_global_config()

        if not config:
            pout("No global configuration found.")
            pout(f"Create one at: {ConfigManager.get_global_config_path()}")
            return

        pout("📋 Global configuration:")
        pout("")

        # Show default provider config
        provider_config = config.get("provider", {})
        if provider_config:
            pout("  Default provider settings:")
            for key, value in provider_config.items():
                pout(f"    {key}: {value}")
            pout("")

        # Show per-provider configs
        providers = config.get("providers", {})
        if providers:
            pout("  Provider-specific settings:")
            for provider_name, provider_settings in providers.items():
                pout(f"    {provider_name}:")
                for key, value in provider_settings.items():
                    pout(f"      {key}: {value}")
            pout("")

    except Exception as e:
        perr(f"❌ Error reading configuration: {e}")
        sys.exit(1)


@config_command.command("set")
@click.argument("key")
@click.argument("value")
def set_config(key: str, value: str) -> None:
    """Set a global default configuration value.

    Examples:
        plating config set default-source local
        plating config set registry-url registry.terraform.io
        plating config set namespace local
    """
    try:
        # Load existing config
        config = ConfigManager.load_global_config()

        # Ensure provider section exists
        if "provider" not in config:
            config["provider"] = {}

        # Map friendly keys to config keys
        key_mapping = {
            "default-source": "source",
            "registry-url": "registry_url",
            "namespace": "namespace",
        }

        config_key = key_mapping.get(key, key)

        # Validate source value
        if config_key == "source" and value not in ("auto", "local", "remote"):
            perr(f"❌ Error: source must be 'auto', 'local', or 'remote', got '{value}'")
            sys.exit(1)

        # Set the value
        config["provider"][config_key] = value

        # Save config
        ConfigManager.save_global_config(config)

        pout(f"✅ Set {key} = {value}")
        pout(f"   Saved to: {ConfigManager.get_global_config_path()}")

    except Exception as e:
        perr(f"❌ Error saving configuration: {e}")
        sys.exit(1)


@config_command.command("set-provider")
@click.argument("provider_name")
@click.option("--source", type=click.Choice(["local", "remote"]), help="Provider source")
@click.option("--registry-url", type=str, help="Registry URL")
@click.option("--namespace", type=str, help="Provider namespace")
def set_provider_config(
    provider_name: str, source: str | None, registry_url: str | None, namespace: str | None
) -> None:
    """Set provider-specific configuration.

    Examples:
        plating config set-provider pyvider --source local
        plating config set-provider aws --source remote --namespace hashicorp
    """
    try:
        # Validate that at least one option is provided
        if not any([source, registry_url, namespace]):
            perr("❌ Error: At least one option (--source, --registry-url, --namespace) must be provided")
            sys.exit(1)

        # Load existing config
        config = ConfigManager.load_global_config()

        # Ensure providers section exists
        if "providers" not in config:
            config["providers"] = {}

        if provider_name not in config["providers"]:
            config["providers"][provider_name] = {}

        # Set values
        if source:
            config["providers"][provider_name]["source"] = source
        if registry_url:
            config["providers"][provider_name]["registry_url"] = registry_url
        if namespace:
            config["providers"][provider_name]["namespace"] = namespace

        # Save config
        ConfigManager.save_global_config(config)

        pout(f"✅ Updated provider '{provider_name}':")
        for key, value in config["providers"][provider_name].items():
            pout(f"   {key}: {value}")
        pout(f"   Saved to: {ConfigManager.get_global_config_path()}")

    except Exception as e:
        perr(f"❌ Error saving configuration: {e}")
        sys.exit(1)


# 🍽️📖🔚
