#
# garnish/error_handling.py
#
"""Centralized error handling and reporting for garnish."""

import subprocess
import sys
from pathlib import Path
from typing import Optional, Any

from rich.console import Console

console = Console()


class ErrorReporter:
    """Centralized error reporting for garnish operations."""

    @staticmethod
    def report_subprocess_error(
        cmd: list[str],
        error: subprocess.CalledProcessError,
        context: str = ""
    ) -> None:
        """Report subprocess execution errors consistently."""
        console.print(f"[red]Error executing command: {' '.join(cmd)}[/red]")
        if context:
            console.print(f"[yellow]Context: {context}[/yellow]")
        if error.stderr:
            console.print(f"[red]Error output:[/red]\n{error.stderr}")
        if error.returncode:
            console.print(f"[red]Exit code: {error.returncode}[/red]")

    @staticmethod
    def report_file_error(
        path: Path,
        operation: str,
        error: Exception
    ) -> None:
        """Report file operation errors consistently."""
        console.print(f"[red]File operation failed: {operation}[/red]")
        console.print(f"[yellow]Path: {path}[/yellow]")
        console.print(f"[red]Error: {error}[/red]")

    @staticmethod
    def report_validation_error(
        component: str,
        errors: list[str],
        warnings: Optional[list[str]] = None
    ) -> None:
        """Report validation errors and warnings consistently."""
        console.print(f"[red]Validation failed for {component}[/red]")
        for error in errors:
            console.print(f"  [red]✗[/red] {error}")
        if warnings:
            for warning in warnings:
                console.print(f"  [yellow]⚠[/yellow] {warning}")

    @staticmethod
    def report_warning(message: str, details: Optional[str] = None) -> None:
        """Report warnings consistently."""
        console.print(f"[yellow]Warning: {message}[/yellow]")
        if details:
            console.print(f"[dim]{details}[/dim]")

    @staticmethod
    def report_success(message: str, details: Optional[str] = None) -> None:
        """Report success messages consistently."""
        console.print(f"[green]✓ {message}[/green]")
        if details:
            console.print(f"[dim]{details}[/dim]")


def handle_subprocess_execution(
    cmd: list[str],
    cwd: Optional[Path] = None,
    timeout: int = 120,
    context: str = "",
    capture_output: bool = True
) -> subprocess.CompletedProcess:
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
            check=False
        )
        
        if result.returncode != 0:
            error = subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
            ErrorReporter.report_subprocess_error(cmd, error, context)
            raise error
            
        return result
        
    except subprocess.TimeoutExpired as e:
        ErrorReporter.report_warning(
            f"Command timed out after {timeout} seconds",
            f"Command: {' '.join(cmd)}"
        )
        raise
    except FileNotFoundError:
        ErrorReporter.report_warning(
            f"Command not found: {cmd[0]}",
            "Please ensure the required tool is installed"
        )
        raise