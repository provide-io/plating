#
# plating/markdown_validator.py
#
"""Markdown validation using pymarkdownlnt with foundation integration."""

from pathlib import Path
from typing import Any

from provide.foundation import logger, metrics
from provide.foundation.resilience import RetryPolicy, BackoffStrategy, RetryExecutor
from pymarkdown.api import PyMarkdownApi, PyMarkdownApiException

from .decorators import with_metrics, with_timing
from .types import ValidationResult


class MarkdownValidator:
    """Markdown validation using pymarkdownlnt API."""
    
    def __init__(
        self,
        config_file: Path | None = None,
        strict_mode: bool = True
    ):
        """Initialize markdown validator.
        
        Args:
            config_file: Optional pymarkdown config file
            strict_mode: Enable strict configuration mode
        """
        self._api = PyMarkdownApi()
        self._configure_api(config_file, strict_mode)
        
        # Foundation resilience
        self._retry_policy = RetryPolicy(
            max_attempts=2,
            backoff=BackoffStrategy.FIXED,
            base_delay=0.1,
            max_delay=1.0,
            retryable_errors=(PyMarkdownApiException, OSError)
        )
        self._retry_executor = RetryExecutor(self._retry_policy)
    
    def _configure_api(self, config_file: Path | None, strict_mode: bool) -> None:
        """Configure the PyMarkdown API."""
        if config_file and config_file.exists():
            self._api.configuration_file_path = str(config_file)
            logger.debug(f"Using pymarkdown config: {config_file}")
        
        self._api.enable_strict_configuration = strict_mode
        
        # Common configuration for documentation
        self._api.disable_rule_by_identifier("MD013")  # Allow long lines
        self._api.disable_rule_by_identifier("MD041")  # Don't require H1 first  
        self._api.disable_rule_by_identifier("MD047")  # Don't require newline at EOF
        self._api.set_boolean_property("MD033.allow_raw_html", True)  # Allow HTML
    
    @with_timing
    @with_metrics("markdown_validation")
    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a markdown file.
        
        Args:
            file_path: Path to markdown file to validate
            
        Returns:
            ValidationResult with linting results
        """
        result = ValidationResult(total=1)
        
        if not file_path.exists():
            result.errors.append(f"File not found: {file_path}")
            result.failed = 1
            return result
        
        try:
            scan_result = self._retry_executor.execute_sync(
                self._api.scan_path, str(file_path)
            )
            
            if scan_result.scan_failures:
                result.failed = 1
                result.lint_errors = [
                    f"{failure.scan_file}:{failure.line_number}:{failure.column_number} "
                    f"{failure.rule_id} {failure.rule_description}"
                    for failure in scan_result.scan_failures
                ]
                logger.debug(f"Markdown validation failed for {file_path}: "
                           f"{len(result.lint_errors)} issues")
            else:
                result.passed = 1
                logger.debug(f"Markdown validation passed for {file_path}")
            
            # Handle pragma errors
            if scan_result.pragma_errors:
                result.errors.extend([
                    f"Pragma error: {error}" for error in scan_result.pragma_errors
                ])
            
        except Exception as e:
            logger.error(f"Markdown validation error for {file_path}: {e}")
            result.failed = 1
            result.errors.append(f"Validation error: {str(e)}")
        
        return result
    
    @with_timing  
    @with_metrics("markdown_validation_string")
    def validate_string(self, content: str, filename: str = "string") -> ValidationResult:
        """Validate markdown content from string.
        
        Args:
            content: Markdown content to validate
            filename: Logical filename for error reporting
            
        Returns:
            ValidationResult with linting results
        """
        result = ValidationResult(total=1)
        
        try:
            scan_result = self._retry_executor.execute_sync(
                self._api.scan_string, content
            )
            
            if scan_result.scan_failures:
                result.failed = 1
                result.lint_errors = [
                    f"{filename}:{failure.line_number}:{failure.column_number} "
                    f"{failure.rule_id} {failure.rule_description}"
                    for failure in scan_result.scan_failures
                ]
                logger.debug(f"Markdown validation failed for {filename}: "
                           f"{len(result.lint_errors)} issues")
            else:
                result.passed = 1
                logger.debug(f"Markdown validation passed for {filename}")
            
            # Handle pragma errors
            if scan_result.pragma_errors:
                result.errors.extend([
                    f"Pragma error: {error}" for error in scan_result.pragma_errors
                ])
            
        except Exception as e:
            logger.error(f"Markdown validation error for {filename}: {e}")
            result.failed = 1
            result.errors.append(f"Validation error: {str(e)}")
        
        return result
    
    @with_timing
    @with_metrics("markdown_validation_batch")
    def validate_files(self, file_paths: list[Path]) -> ValidationResult:
        """Validate multiple markdown files.
        
        Args:
            file_paths: List of markdown files to validate
            
        Returns:
            Combined ValidationResult
        """
        combined_result = ValidationResult(total=len(file_paths))
        
        for file_path in file_paths:
            file_result = self.validate_file(file_path)
            
            # Combine results
            combined_result.passed += file_result.passed
            combined_result.failed += file_result.failed
            combined_result.skipped += file_result.skipped
            combined_result.errors.extend(file_result.errors)
            combined_result.lint_errors.extend(file_result.lint_errors)
            
            # Track per-file failures
            if not file_result.success:
                combined_result.failures[str(file_path)] = "; ".join(
                    file_result.errors + file_result.lint_errors
                )
        
        metrics.gauge("markdown_validation.total_files").set(len(file_paths))
        metrics.gauge("markdown_validation.failed_files").set(combined_result.failed)
        
        return combined_result
    
    def get_validator_info(self) -> dict[str, Any]:
        """Get information about the validator configuration.
        
        Returns:
            Dictionary with validator information
        """
        return {
            "api_version": "0.9.32",  # pymarkdownlnt version
            "config_file": getattr(self._api, "configuration_file_path", None),
            "strict_mode": getattr(self._api, "enable_strict_configuration", False),
            "retry_policy": {
                "max_attempts": self._retry_policy.max_attempts,
                "backoff": self._retry_policy.backoff.value,
            }
        }


# Global validator instance
_global_validator = None

def get_markdown_validator(
    config_file: Path | None = None,
    strict_mode: bool = True
) -> MarkdownValidator:
    """Get or create global markdown validator.
    
    Args:
        config_file: Optional pymarkdown config file
        strict_mode: Enable strict configuration mode
        
    Returns:
        MarkdownValidator instance
    """
    global _global_validator
    if _global_validator is None:
        _global_validator = MarkdownValidator(config_file, strict_mode)
    return _global_validator


def reset_markdown_validator() -> None:
    """Reset the global validator (primarily for testing)."""
    global _global_validator
    _global_validator = None


# 📝✅🔍⚡