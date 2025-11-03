#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Provider source auto-detection logic."""

from pathlib import Path
import subprocess
import sys
from typing import Literal

from provide.foundation import logger

ProviderSource = Literal["local", "remote"]


class ProviderSourceDetector:
    """Detects whether a provider should use local or remote source."""

    def __init__(self, provider_name: str, package_name: str | None = None) -> None:
        """Initialize the detector.

        Args:
            provider_name: Name of the provider (e.g., "pyvider")
            package_name: Optional package name to check (defaults to {provider_name}.components)
        """
        self.provider_name = provider_name
        self.package_name = package_name or f"{provider_name}.components"

    def detect(self) -> ProviderSource:
        """Detect the provider source based on installation type.

        Returns:
            "local" if the provider package is installed as editable, "remote" otherwise
        """
        if self._is_editable_install():
            logger.debug(
                f"Provider '{self.provider_name}' detected as editable install → using 'local' source"
            )
            return "local"

        if self._is_local_package():
            logger.debug(f"Provider '{self.provider_name}' found in local sys.path → using 'local' source")
            return "local"

        logger.debug(f"Provider '{self.provider_name}' not found locally → using 'remote' source")
        return "remote"

    def _is_editable_install(self) -> bool:
        """Check if the package is installed as an editable install.

        Returns:
            True if the package is an editable install, False otherwise
        """
        try:
            # Use pip show to check if package is editable
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", self.package_name],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return False

            # Check if the Location points to a development directory
            for line in result.stdout.splitlines():
                if line.startswith("Location:"):
                    location = line.split(":", 1)[1].strip()
                    location_path = Path(location)

                    # Check if it's in a common development location
                    # (e.g., contains /code/, /dev/, /src/, or parent dirs have .git)
                    if any(part in location_path.parts for part in ["code", "dev", "src", "projects"]):
                        return True

                    # Check if parent directories have .git (development repo)
                    current_path = location_path
                    for _ in range(5):  # Check up to 5 levels up
                        if (current_path / ".git").exists():
                            return True
                        if current_path.parent == current_path:
                            break
                        current_path = current_path.parent

                if line.startswith("Editable project location:"):
                    # pip 21.3+ includes explicit editable location
                    return True

            return False

        except Exception as e:
            logger.debug(f"Error checking editable install for {self.package_name}: {e}")
            return False

    def _is_local_package(self) -> bool:
        """Check if the package is available in sys.path.

        Returns:
            True if the package can be imported, False otherwise
        """
        try:
            # Try to import the package
            __import__(self.package_name)
            return True
        except ImportError:
            return False


def detect_provider_source(provider_name: str, package_name: str | None = None) -> ProviderSource:
    """Convenience function to detect provider source.

    Args:
        provider_name: Name of the provider (e.g., "pyvider")
        package_name: Optional package name to check

    Returns:
        "local" or "remote" based on detection
    """
    detector = ProviderSourceDetector(provider_name, package_name)
    return detector.detect()


# 🍽️📖🔚
