#
# plating/error_handling.py
#
"""Centralized error handling and reporting for plating."""

from pathlib import Path
import subprocess

from provide.foundation import perr, pout


class ErrorReporter:
    """Centralized error reporting for plating operations."""

    @staticmethod
    def report_subprocess_error(
        cmd: list[str], error: subprocess.CalledProcessError, context: str = ""
    ) -> None:
        """Report subprocess execution errors consistently."""
        perr(f"❌ Error executing command: {' '.join(cmd)}")
        if context:
            pout(f"📍 Context: {context}")
        if error.stderr:
            perr(f"Error output:\n{error.stderr}")
        if error.returncode:
            perr(f"Exit code: {error.returncode}")

    @staticmethod
    def report_file_error(path: Path, operation: str, error: Exception) -> None:
        """Report file operation errors consistently."""
        perr(f"❌ File operation failed: {operation}")
        pout(f"📁 Path: {path}")
        perr(f"Error: {error}")

    @staticmethod
    def report_validation_error(component: str, errors: list[str], warnings: list[str] | None = None) -> None:
        """Report validation errors and warnings consistently."""
        perr(f"❌ Validation failed for {component}")
        for error in errors:
            perr(f"  ✗ {error}")
        if warnings:
            for warning in warnings:
                pout(f"  ⚠️  {warning}")

    @staticmethod
    def report_warning(message: str, details: str | None = None) -> None:
        """Report warnings consistently."""
        pout(f"⚠️  {message}")
        if details:
            pout(f"  {details}")

    @staticmethod
    def report_success(message: str, details: str | None = None) -> None:
        """Report success messages consistently."""
        pout(f"✅ {message}")
        if details:
            pout(f"  {details}")


def handle_subprocess_execution(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 120,
    context: str = "",
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Execute subprocess with consistent error handling.

    Args:
        cmd: Command to execute
        cwd: Working directory for command
        timeout: Command timeout in seconds
        context: Context description for error reporting
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess result

    Raises:
        subprocess.CalledProcessError: If command fails
        subprocess.TimeoutExpired: If command times out
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            error = subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
            ErrorReporter.report_subprocess_error(cmd, error, context)
            raise error

        return result

    except subprocess.TimeoutExpired:
        ErrorReporter.report_warning(f"Command timed out after {timeout} seconds", f"Command: {' '.join(cmd)}")
        raise
    except FileNotFoundError:
        ErrorReporter.report_warning(
            f"Command not found: {cmd[0]}",
            "Please ensure the required tool is installed",
        )
        raise
