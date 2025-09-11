#
# plating/test_runner/utils.py
#
"""Utilities for test runner functionality."""

from provide.foundation.process import ProcessError, run_command

from plating.config import get_config

# Cache terraform version to avoid repeated subprocess calls
_terraform_version_cache = None


def get_terraform_version() -> tuple[str, str]:
    """Get the Terraform/OpenTofu binary and version being used.

    Returns:
        Tuple of (binary_name, version_string)
    """
    global _terraform_version_cache

    # Return cached version if available
    if _terraform_version_cache is not None:
        return _terraform_version_cache

    # Get binary from config
    config = get_config()
    tf_binary = config.terraform_binary
    binary_name = "OpenTofu" if "tofu" in tf_binary else "Terraform"

    try:
        result = run_command([tf_binary, "-version"], capture_output=True, timeout=5)
        version_lines = result.stdout.strip().split("\n")
        if version_lines:
            version_string = version_lines[0]
        else:
            version_string = "Unknown version"
    except ProcessError:
        version_string = "Unable to determine version"

    _terraform_version_cache = (binary_name, version_string)
    return _terraform_version_cache


# 🛠️🔧⚙️