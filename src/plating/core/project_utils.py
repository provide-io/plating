# 
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from pathlib import Path

from provide.foundation import logger

#
# plating/core/project_utils.py
#
"""Project detection and directory utilities."""


def find_project_root(start_dir: Path | None = None) -> Path | None:
    """Find the project root by looking for key files.

    Args:
        start_dir: Directory to start searching from (defaults to current working directory)

    Returns:
        Path to project root or None if not found
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    # Look for project marker files
    project_markers = ["pyproject.toml", "pyvider.toml", ".git", "setup.py", "setup.cfg"]

    while current != current.parent:  # Stop at filesystem root
        for marker in project_markers:
            if (current / marker).exists():
                logger.debug(f"Found project root at {current} (marker: {marker})")
                return current
        current = current.parent

    logger.warning(f"No project root found starting from {start_dir}")
    return None


def get_output_directory(output_dir: Path | None, project_root: Path | None = None) -> Path:
    """Determine the appropriate output directory for documentation.

    Args:
        output_dir: Explicitly specified output directory
        project_root: Project root directory

    Returns:
        Resolved output directory path
    """
    if output_dir is not None:
        # If output_dir is absolute, use as-is
        if output_dir.is_absolute():
            return output_dir
        # If relative and we have project root, make it relative to project root
        if project_root:
            return project_root / output_dir
        # Otherwise relative to current directory
        return Path.cwd() / output_dir

    # Default behavior: try to use project_root/docs if available
    if project_root:
        return project_root / "docs"

    # Fallback to current directory/docs
    return Path.cwd() / "docs"

# 🍽️📖🔚
