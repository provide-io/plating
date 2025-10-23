"""
Custom error types for plating with context and user-friendly messages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from provide.foundation.errors import FoundationError
except ImportError:
    FoundationError = Exception


class PlatingError(FoundationError):
    """Base error for all plating-related errors with context support."""

    def to_user_message(self) -> str:
        """Convert error to user-friendly message for CLI display.

        Returns:
            Human-readable error message suitable for end users
        """
        return str(self)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for structured logging.

        Returns:
            Dictionary with error details for logging
        """
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
        }


class BundleError(PlatingError):
    """Error related to plating bundles."""

    def __init__(self, bundle_name: str, message: str, bundle_path: Path | None = None):
        self.bundle_name = bundle_name
        self.message = message
        self.bundle_path = bundle_path
        super().__init__(f"Bundle '{bundle_name}': {message}")

    def to_user_message(self) -> str:
        """Convert to user-friendly message."""
        if self.bundle_path:
            return f"Error in bundle '{self.bundle_name}' at {self.bundle_path}: {self.message}"
        return f"Error in bundle '{self.bundle_name}': {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to structured dict for logging."""
        return {
            "error_type": "BundleError",
            "bundle_name": self.bundle_name,
            "message": self.message,
            "bundle_path": str(self.bundle_path) if self.bundle_path else None,
        }


class PlatingRenderError(PlatingError):
    """Error during documentation plating."""

    def __init__(self, bundle_name: str, reason: str, output_path: Path | None = None):
        self.bundle_name = bundle_name
        self.reason = reason
        self.output_path = output_path
        super().__init__(f"Failed to plate '{bundle_name}': {reason}")

    def to_user_message(self) -> str:
        """Convert to user-friendly message."""
        base = f"Failed to generate documentation for '{self.bundle_name}': {self.reason}"
        if self.output_path:
            return f"{base}\nOutput path: {self.output_path}"
        return base

    def to_dict(self) -> dict[str, Any]:
        """Convert to structured dict for logging."""
        return {
            "error_type": "PlatingRenderError",
            "bundle_name": self.bundle_name,
            "reason": self.reason,
            "output_path": str(self.output_path) if self.output_path else None,
        }


class AdorningError(PlatingError):
    """Error during component adorning."""

    def __init__(
        self, component_name: str, component_type: str, reason: str, template_path: Path | None = None
    ):
        self.component_name = component_name
        self.component_type = component_type
        self.reason = reason
        self.template_path = template_path
        super().__init__(f"Failed to adorn {component_type} '{component_name}': {reason}")

    def to_user_message(self) -> str:
        """Convert to user-friendly message."""
        base = f"Failed to create template for {self.component_type} '{self.component_name}': {self.reason}"
        if self.template_path:
            return f"{base}\nTemplate path: {self.template_path}"
        return base

    def to_dict(self) -> dict[str, Any]:
        """Convert to structured dict for logging."""
        return {
            "error_type": "AdorningError",
            "component_name": self.component_name,
            "component_type": self.component_type,
            "reason": self.reason,
            "template_path": str(self.template_path) if self.template_path else None,
        }


class SchemaError(PlatingError):
    """Error related to schema extraction or processing."""

    def __init__(self, provider_name: str, reason: str, component_name: str | None = None):
        self.provider_name = provider_name
        self.reason = reason
        self.component_name = component_name
        super().__init__(f"Schema error for provider '{provider_name}': {reason}")

    def to_user_message(self) -> str:
        """Convert to user-friendly message."""
        if self.component_name:
            return f"Schema error for {self.component_name} in provider '{self.provider_name}': {self.reason}"
        return f"Schema error for provider '{self.provider_name}': {self.reason}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to structured dict for logging."""
        return {
            "error_type": "SchemaError",
            "provider_name": self.provider_name,
            "component_name": self.component_name,
            "reason": self.reason,
        }


class TemplateError(PlatingError):
    """Error during template rendering with detailed context."""

    def __init__(
        self,
        template_path: Path | str,
        reason: str,
        line_number: int | None = None,
        context: str | None = None,
    ):
        self.template_path = template_path
        self.reason = reason
        self.line_number = line_number
        self.context = context
        super().__init__(f"Template error in '{template_path}': {reason}")

    def to_user_message(self) -> str:
        """Convert to user-friendly message with location context and actionable guidance."""
        parts = [f"Template error in '{self.template_path}'"]
        if self.line_number:
            parts.append(f" at line {self.line_number}")
        parts.append(f": {self.reason}")
        if self.context:
            parts.append(f"\n  {self.context}")

        parts.append("\n\n💡 How to fix:")
        parts.append(f"\n  • Check template syntax at: {self.template_path}")
        if self.line_number:
            parts.append(f"\n  • Look at line {self.line_number} for syntax errors")
        parts.append("\n  • Verify all template variables are defined in context")
        parts.append("\n  • Check for typos in function names (schema, example, include)")
        parts.append("\n  • Ensure Jinja2 syntax is correct: {{ }}, {% %}, {# #}")
        return "".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to structured dict for logging."""
        return {
            "error_type": "TemplateError",
            "template_path": str(self.template_path),
            "reason": self.reason,
            "line_number": self.line_number,
            "context": self.context,
        }


class DiscoveryError(PlatingError):
    """Error during bundle discovery."""

    def __init__(self, package_name: str, reason: str, search_paths: list[Path] | None = None):
        self.package_name = package_name
        self.reason = reason
        self.search_paths = search_paths or []
        super().__init__(f"Discovery error for package '{package_name}': {reason}")

    def to_user_message(self) -> str:
        """Convert to user-friendly message with actionable guidance."""
        msg = f"Could not discover components in package '{self.package_name}': {self.reason}"
        if self.search_paths:
            paths_str = "\n  ".join(str(p) for p in self.search_paths)
            msg += f"\nSearched paths:\n  {paths_str}"

        msg += "\n\n💡 How to fix:"
        msg += f"\n  • Verify '{self.package_name}' is installed: uv pip list | grep {self.package_name}"
        msg += "\n  • Check package has entry points defined in pyproject.toml"
        msg += "\n  • Ensure components are in the correct directory structure"
        msg += f"\n  • Try running: python -m {self.package_name} --help"
        return msg

    def to_dict(self) -> dict[str, Any]:
        """Convert to structured dict for logging."""
        return {
            "error_type": "DiscoveryError",
            "package_name": self.package_name,
            "reason": self.reason,
            "search_paths": [str(p) for p in self.search_paths],
        }


class ConfigurationError(PlatingError):
    """Error in plating configuration."""

    def __init__(self, config_key: str, reason: str, config_file: Path | None = None):
        self.config_key = config_key
        self.reason = reason
        self.config_file = config_file
        super().__init__(f"Configuration error for '{config_key}': {reason}")

    def to_user_message(self) -> str:
        """Convert to user-friendly message with actionable guidance."""
        msg = f"Configuration error for '{self.config_key}': {self.reason}"
        if self.config_file:
            msg += f"\nConfiguration file: {self.config_file}"

        msg += "\n\n💡 How to fix:"
        msg += "\n  • Check configuration in pyproject.toml or plating.toml"
        msg += f"\n  • Verify '{self.config_key}' has a valid value"
        msg += "\n  • Example configuration:"
        msg += "\n    [tool.plating]"
        msg += f"\n    {self.config_key} = \"value\""
        if self.config_file:
            msg += f"\n  • Review settings in: {self.config_file}"
        return msg

    def to_dict(self) -> dict[str, Any]:
        """Convert to structured dict for logging."""
        return {
            "error_type": "ConfigurationError",
            "config_key": self.config_key,
            "reason": self.reason,
            "config_file": str(self.config_file) if self.config_file else None,
        }


class ValidationError(PlatingError):
    """Error during validation execution."""

    def __init__(
        self,
        validation_name: str,
        reason: str,
        file_path: Path | None = None,
        failures: list[str] | None = None,
    ):
        self.validation_name = validation_name
        self.reason = reason
        self.file_path = file_path
        self.failures = failures or []
        super().__init__(f"Validation '{validation_name}' failed: {reason}")

    def to_user_message(self) -> str:
        """Convert to user-friendly message with actionable guidance."""
        msg = f"Validation '{self.validation_name}' failed: {self.reason}"
        if self.file_path:
            msg += f"\nFile: {self.file_path}"
        if self.failures:
            failures_str = "\n  • ".join(self.failures)
            msg += f"\nFailures:\n  • {failures_str}"

        msg += "\n\n💡 How to fix:"
        if self.file_path:
            msg += f"\n  • Review file: {self.file_path}"
        msg += "\n  • Check markdown syntax and frontmatter format"
        msg += "\n  • Ensure all required fields are present"
        msg += "\n  • Verify links are valid and formatted correctly"
        msg += "\n  • Run: plating validate --output-dir docs for detailed errors"
        return msg

    def to_dict(self) -> dict[str, Any]:
        """Convert to structured dict for logging."""
        return {
            "error_type": "ValidationError",
            "validation_name": self.validation_name,
            "reason": self.reason,
            "file_path": str(self.file_path) if self.file_path else None,
            "failures": self.failures,
        }


class FileSystemError(PlatingError):
    """Error related to file system operations."""

    def __init__(self, path: Path | str, operation: str, reason: str, caused_by: Exception | None = None):
        self.path = path
        self.operation = operation
        self.reason = reason
        self.caused_by = caused_by
        super().__init__(f"File system error during {operation} on '{path}': {reason}")

    def to_user_message(self) -> str:
        """Convert to user-friendly message with actionable guidance."""
        msg = f"Failed to {self.operation} file '{self.path}': {self.reason}"
        if self.caused_by:
            msg += f"\nCaused by: {type(self.caused_by).__name__}: {self.caused_by}"

        msg += "\n\n💡 How to fix:"
        if "permission" in self.reason.lower():
            msg += f"\n  • Check file permissions: ls -la {self.path}"
            msg += f"\n  • Try with elevated permissions if appropriate: sudo chown $USER {self.path}"
            msg += f"\n  • Ensure directory is writable: chmod u+w $(dirname {self.path})"
        elif "not found" in self.reason.lower() or "no such file" in self.reason.lower():
            msg += f"\n  • Verify path exists: ls -la $(dirname {self.path})"
            msg += f"\n  • Check for typos in path: {self.path}"
            msg += "\n  • Ensure parent directories exist"
        else:
            msg += f"\n  • Check path is accessible: ls -la {self.path}"
            msg += "\n  • Verify disk space: df -h"
            msg += "\n  • Check for file locks or processes using the file"
        return msg

    def to_dict(self) -> dict[str, Any]:
        """Convert to structured dict for logging."""
        return {
            "error_type": "FileSystemError",
            "path": str(self.path),
            "operation": self.operation,
            "reason": self.reason,
            "caused_by": type(self.caused_by).__name__ if self.caused_by else None,
        }


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


