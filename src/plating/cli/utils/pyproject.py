# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Utilities for reading and parsing pyproject.toml files."""

from pathlib import Path
from types import ModuleType

from provide.foundation import logger
from provide.foundation.file.safe import safe_read_text
from provide.foundation.serialization import toml_loads


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


#: Accepted spellings for the provider-name key, canonical first. The table is
#: already scoped to pyvider, so `name` says everything `provider_name` does;
#: the alias is read because pyvider's docs and providers in the wild use it.
_PROVIDER_NAME_KEYS = ("name", "provider_name")


def _pyvider_sections(pyproject: dict) -> list[dict]:
    """Return pyvider's config tables, most specific first.

    `[tool.pyvider]` is the PEP 518 location and what pyvider's own CLI reads;
    the top-level `[pyvider]` table is what plating read first, so it stays
    accepted behind it.
    """
    sections = []
    tool = pyproject.get("tool")
    if isinstance(tool, dict) and isinstance(tool.get("pyvider"), dict):
        sections.append(tool["pyvider"])
    if isinstance(pyproject.get("pyvider"), dict):
        sections.append(pyproject["pyvider"])
    return sections


def _load_pyproject(pyproject_path: Path) -> dict | None:
    """Parse pyproject.toml, returning None if it is absent or unreadable."""
    try:
        if not pyproject_path.exists():
            return None
        pyproject = toml_loads(safe_read_text(pyproject_path))
    except Exception as e:
        logger.debug(f"Failed to read pyproject.toml: {e}")
        return None
    return pyproject if isinstance(pyproject, dict) else None


def get_pyvider_component_packages(pyproject_path: Path) -> list[str] | None:
    """Get component packages from pyvider's section in pyproject.toml.

    Checks `[tool.pyvider]` before the top-level `[pyvider]` table.

    Args:
        pyproject_path: Path to pyproject.toml file

    Returns:
        List of component package names if configured, None otherwise
    """
    pyproject = _load_pyproject(pyproject_path)
    if pyproject is None:
        return None

    for section in _pyvider_sections(pyproject):
        component_packages = section.get("component_packages")
        if component_packages and isinstance(component_packages, list):
            return list(component_packages)

    return None


def get_provider_name_from_pyproject(pyproject_path: Path) -> str | None:
    """Get provider name from pyproject.toml if configured.

    Checks `[tool.pyvider]`, then the top-level `[pyvider]` table, then
    `[tool.plating]` for backward compatibility. Either `name` or
    `provider_name` is accepted as the key.

    Args:
        pyproject_path: Path to pyproject.toml file

    Returns:
        Provider name if found, None otherwise
    """
    pyproject = _load_pyproject(pyproject_path)
    if pyproject is None:
        return None

    # pyvider's own sections first, under either spelling of the key.
    for section in _pyvider_sections(pyproject):
        for key in _PROVIDER_NAME_KEYS:
            provider_name = section.get(key)
            if provider_name:
                return str(provider_name)

    # Fallback to [tool.plating] provider_name for backward compatibility
    tool = pyproject.get("tool")
    plating = tool.get("plating") if isinstance(tool, dict) else None
    if isinstance(plating, dict) and plating.get("provider_name"):
        return str(plating["provider_name"])

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
