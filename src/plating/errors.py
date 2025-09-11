"""
Custom error types for plating.
"""

from pathlib import Path
from typing import Any
from provide.foundation.errors import FoundationError


class PlatingError(FoundationError):
    """Base error for all plating-related errors."""

    pass


class BundleError(PlatingError):
    """Error related to plating bundles."""

    def __init__(self, bundle_name: str, message: str):
        self.bundle_name = bundle_name
        super().__init__(f"Bundle '{bundle_name}': {message}")


class PlatingRenderError(PlatingError):
    """Error during documentation plating."""

    def __init__(self, bundle_name: str, reason: str):
        self.bundle_name = bundle_name
        self.reason = reason
        super().__init__(f"Failed to plate '{bundle_name}': {reason}")


class DressingError(PlatingError):
    """Error during component dressing."""

    def __init__(self, component_name: str, component_type: str, reason: str):
        self.component_name = component_name
        self.component_type = component_type
        self.reason = reason
        super().__init__(
            f"Failed to dress {component_type} '{component_name}': {reason}"
        )


class SchemaError(PlatingError):
    """Error related to schema extraction or processing."""

    def __init__(self, provider_name: str, reason: str):
        self.provider_name = provider_name
        self.reason = reason
        super().__init__(f"Schema error for provider '{provider_name}': {reason}")


class TemplateError(PlatingError):
    """Error during template rendering."""

    def __init__(self, template_path: Path | str, reason: str):
        self.template_path = template_path
        self.reason = reason
        super().__init__(f"Template error in '{template_path}': {reason}")


class DiscoveryError(PlatingError):
    """Error during bundle discovery."""

    def __init__(self, package_name: str, reason: str):
        self.package_name = package_name
        self.reason = reason
        super().__init__(f"Discovery error for package '{package_name}': {reason}")


class ConfigurationError(PlatingError):
    """Error in plating configuration."""

    def __init__(self, config_key: str, reason: str):
        self.config_key = config_key
        self.reason = reason
        super().__init__(f"Configuration error for '{config_key}': {reason}")


class TestRunnerError(PlatingError):
    """Error during test execution."""

    def __init__(self, test_name: str, reason: str):
        self.test_name = test_name
        self.reason = reason
        super().__init__(f"Test '{test_name}' failed: {reason}")


class FileSystemError(PlatingError):
    """Error related to file system operations."""

    def __init__(self, path: Path | str, operation: str, reason: str):
        self.path = path
        self.operation = operation
        self.reason = reason
        super().__init__(f"File system error during {operation} on '{path}': {reason}")


def handle_error(error: Exception, logger: Any = None, reraise: bool = False) -> str:
    """
    Handle an error with proper logging and optional re-raising.

    Args:
        error: The exception to handle
        logger: Optional logger instance to use
        reraise: Whether to re-raise the error after handling

    Returns:
        A formatted error message
    """
    error_msg = str(error)

    if isinstance(error, PlatingError):
        # It's one of our custom errors, we have more context
        if logger:
            logger.error(error_msg)
    elif isinstance(error, FileNotFoundError):
        error_msg = f"File not found: {error}"
        if logger:
            logger.error(error_msg)
    elif isinstance(error, PermissionError):
        error_msg = f"Permission denied: {error}"
        if logger:
            logger.error(error_msg)
    elif isinstance(error, (OSError, IOError)):
        error_msg = f"I/O error: {error}"
        if logger:
            logger.error(error_msg)
    else:
        # Generic error
        error_msg = f"Unexpected error: {error}"
        if logger:
            logger.exception("Unexpected error occurred")

    if reraise:
        raise

    return error_msg


# 🍲❌🪄
