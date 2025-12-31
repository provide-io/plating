# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Utilities for reading and parsing pyproject.toml files."""

from pathlib import Path

from provide.foundation import logger
from provide.foundation.file.safe import safe_read_text
from provide.foundation.serialization import toml_loads


from types import ModuleType


def load_tomllib_module() -> ModuleType | None:
    """Load tomllib or tomli module.

    Returns:
        tomllib module or None if not available
    """
    try:
        import tomllib

        return tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]

            return tomllib
        except ImportError:
            return None


def get_pyvider_component_packages(pyproject_path: Path) -> list[str] | None:
    """Get component packages from [pyvider] section in pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml file

    Returns:
        List of component package names if configured, None otherwise
    """
    try:
        if not pyproject_path.exists():
            return None

        content = safe_read_text(pyproject_path)
        pyproject = toml_loads(content)

        if "pyvider" in pyproject:
            component_packages = pyproject["pyvider"].get("component_packages")
            if component_packages and isinstance(component_packages, list):
                return list(component_packages)
    except Exception as e:
        logger.debug(f"Failed to read [pyvider] section from pyproject.toml: {e}")

    return None


def get_provider_name_from_pyproject(pyproject_path: Path) -> str | None:
    """Get provider name from pyproject.toml if configured.

    Checks [pyvider] section first, then [tool.plating] for backward compatibility.

    Args:
        pyproject_path: Path to pyproject.toml file

    Returns:
        Provider name if found, None otherwise
    """
    if not pyproject_path.exists():
        return None

    try:
        content = safe_read_text(pyproject_path)
        pyproject = toml_loads(content)

        # First check for provider_name in [pyvider] section
        if "pyvider" in pyproject:
            provider_name = pyproject["pyvider"].get("name")
            if provider_name:
                return str(provider_name)

        # Fallback to [tool.plating] provider_name for backward compatibility
        if (
            "tool" in pyproject
            and "plating" in pyproject["tool"]
            and "provider_name" in pyproject["tool"]["plating"]
        ):
            return str(pyproject["tool"]["plating"]["provider_name"])
    except Exception as e:
        logger.debug(f"Failed to read provider name from pyproject.toml: {e}")

    return None


def extract_provider_from_package_name(package_name: str) -> str | None:
    """Extract provider name from package name patterns.

    Args:
        package_name: Package name to parse

    Returns:
        Provider name if pattern matches, None otherwise
    """
    # Handle terraform-provider-{name} pattern
    if package_name.startswith("terraform-provider-"):
        return package_name.replace("terraform-provider-", "")

    # Handle {name}-provider pattern
    if package_name.endswith("-provider"):
        return package_name.replace("-provider", "")

    return None
