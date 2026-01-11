# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Auto-detection utilities for provider and package names."""

from pathlib import Path

import click
from provide.foundation import logger, pout

from plating.cli.utils.pyproject import (
    extract_provider_from_package_name,
    get_provider_name_from_pyproject,
    get_pyvider_component_packages,
    load_tomllib_module,
)


def auto_detect_package_name() -> str | None:
    """Auto-detect package name from pyproject.toml in current directory.

    First checks [pyvider] section for component_packages.
    Falls back to [project] section name if no pyvider config found.

    Returns:
        Package name if found, None otherwise
    """
    try:
        pyproject_path = Path.cwd() / "pyproject.toml"
        if not pyproject_path.exists():
            return None

        # First check for [pyvider] section with component_packages
        component_packages = get_pyvider_component_packages(pyproject_path)
        if component_packages and len(component_packages) > 0:
            # Return the first component package
            logger.debug(f"Using component package from [pyvider] section: {component_packages[0]}")
            return component_packages[0]

        # Fall back to reading pyproject and getting package name
        tomllib = load_tomllib_module()
        if not tomllib:
            logger.debug("Neither tomllib nor tomli available for parsing pyproject.toml")
            return None

        with pyproject_path.open("rb") as f:
            pyproject = tomllib.load(f)

        # Fall back to package name from [project] section
        if "project" in pyproject and "name" in pyproject["project"]:
            return str(pyproject["project"]["name"])

        return None
    except Exception as e:
        logger.debug(f"Failed to auto-detect package name: {e}")
        return None


def auto_detect_provider_name() -> str | None:
    """Auto-detect provider name from package name or pyproject.toml.

    Returns:
        Provider name if found, None otherwise
    """
    try:
        # First, check if there's explicit config in pyproject.toml
        pyproject_path = Path.cwd() / "pyproject.toml"
        provider_name = get_provider_name_from_pyproject(pyproject_path)
        if provider_name:
            return provider_name

        # Try to extract from package name pattern
        package_name = auto_detect_package_name()
        if package_name:
            return extract_provider_from_package_name(package_name)

        return None
    except Exception as e:
        logger.debug(f"Failed to auto-detect provider name: {e}")
        return None


def get_provider_name(provided_name: str | None) -> str:
    """Get provider name from CLI arg or auto-detect.

    Args:
        provided_name: Provider name from CLI argument (may be None)

    Returns:
        Provider name to use

    Raises:
        click.UsageError: If no provider name provided and auto-detection fails
    """
    if provided_name:
        return provided_name

    detected = auto_detect_provider_name()
    if detected:
        pout(f"🏷️  Auto-detected provider: {detected}")
        return detected

    raise click.UsageError(
        "Could not auto-detect provider name. Please provide --provider-name or add [tool.plating] provider_name to pyproject.toml"
    )


def get_package_name(provided_name: str | None) -> str | None:
    """Get package name from CLI arg, or auto-detect.

    Args:
        provided_name: Package name from CLI argument (may be None)

    Returns:
        Package name to filter to, or None if auto-detection fails
    """
    if provided_name:
        return provided_name

    detected = auto_detect_package_name()
    if detected:
        return detected

    return None
