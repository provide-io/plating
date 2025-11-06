# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Guide and template file processing for plating."""

from pathlib import Path
from typing import NamedTuple

from provide.foundation import logger
from provide.foundation.file import atomic_write_text, ensure_parent_dir
from provide.foundation.file.safe import safe_read_text
import yaml

from plating.errors import PlatingError


class TemplateFile(NamedTuple):
    """Represents a template file with parsed metadata."""

    source_path: Path
    template_output: str
    frontmatter: str
    content: str


class GuideProcessingError(PlatingError):
    """Error during guide or template processing."""

    def __init__(self, message: str, file_path: Path | None = None):
        """Initialize guide processing error.

        Args:
            message: Error message
            file_path: Path to the file that caused the error
        """
        super().__init__(message)
        self.file_path = file_path

    def to_user_message(self) -> str:
        """Convert to user-friendly message."""
        if self.file_path:
            return f"{self.message} (file: {self.file_path})"
        return self.message


def parse_frontmatter(content: str) -> tuple[str, str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter_with_delimiters, body_content)
    """
    if not content.startswith("---"):
        return "", content

    # Find closing delimiter
    close_idx = content.find("---", 3)
    if close_idx == -1:
        return "", content

    # Extract frontmatter section (including delimiters)
    frontmatter_section = content[: close_idx + 3]
    # Extract body (everything after closing delimiter)
    body = content[close_idx + 3 :].lstrip("\n")

    return frontmatter_section, body


def extract_frontmatter_field(frontmatter: str, field_name: str) -> str | None:
    """Extract a field value from YAML frontmatter.

    Args:
        frontmatter: Frontmatter section (with or without delimiters)
        field_name: Name of the field to extract

    Returns:
        Field value as string, or None if not found
    """
    if not frontmatter:
        return None

    try:
        # Remove delimiters if present
        lines = frontmatter.split("\n")
        if lines[0].strip() == "---":
            lines = lines[1:]
        if lines and lines[-1].strip() == "---":
            lines = lines[:-1]

        yaml_content = "\n".join(lines)
        if not yaml_content.strip():
            return None

        data = yaml.safe_load(yaml_content)
        if isinstance(data, dict):
            value = data.get(field_name)
            return str(value) if value is not None else None
        return None
    except (yaml.YAMLError, AttributeError) as e:
        logger.debug(f"Failed to parse frontmatter field {field_name}: {e}")
        return None


def validate_template_output_path(template_output: str, source_file: Path) -> Path:
    """Validate that a template_output path is safe and well-formed.

    Args:
        template_output: The template_output value from frontmatter
        source_file: Source file path (for error messages)

    Returns:
        Validated Path object (relative to output directory)

    Raises:
        GuideProcessingError: If path is invalid or unsafe
    """
    if not template_output:
        raise GuideProcessingError(
            "template_output field is empty",
            file_path=source_file,
        )

    # Convert to Path and normalize
    try:
        output_path = Path(template_output)
    except (TypeError, ValueError) as e:
        raise GuideProcessingError(
            f"Invalid template_output path: {e}",
            file_path=source_file,
        )

    # Check for absolute paths
    if output_path.is_absolute():
        raise GuideProcessingError(
            f"template_output must be relative, not absolute: {template_output}",
            file_path=source_file,
        )

    # Check for path traversal attempts
    # Normalize and check if it tries to escape the output directory
    try:
        # Resolve against a fake base to detect traversal
        fake_base = Path("/fake/base")
        resolved = (fake_base / output_path).resolve()
        if not str(resolved).startswith(str(fake_base)):
            raise GuideProcessingError(
                f"template_output contains path traversal: {template_output}",
                file_path=source_file,
            )
    except (RuntimeError, OSError) as e:
        raise GuideProcessingError(
            f"Invalid template_output path: {e}",
            file_path=source_file,
        )

    # Check for invalid characters (basic validation)
    invalid_chars = {"<", ">", ":", '"', "|", "?", "*"}
    if any(char in str(output_path) for char in invalid_chars):
        raise GuideProcessingError(
            f"template_output contains invalid characters: {template_output}",
            file_path=source_file,
        )

    # Must end with .md
    if output_path.suffix != ".md":
        raise GuideProcessingError(
            f"template_output must end with .md: {template_output}",
            file_path=source_file,
        )

    return output_path


def parse_template_file(file_path: Path) -> TemplateFile:
    """Parse a template file and extract its metadata.

    Args:
        file_path: Path to the .tmpl.md template file

    Returns:
        TemplateFile with parsed metadata

    Raises:
        GuideProcessingError: If file is invalid or missing required fields
    """
    try:
        content = safe_read_text(file_path)
    except OSError as e:
        raise GuideProcessingError(
            f"Failed to read template file: {e}",
            file_path=file_path,
        )

    # Parse frontmatter
    frontmatter, body = parse_frontmatter(content)
    if not frontmatter:
        raise GuideProcessingError(
            "Template file must have YAML frontmatter",
            file_path=file_path,
        )

    # Extract template_output field
    template_output = extract_frontmatter_field(frontmatter, "template_output")
    if not template_output:
        raise GuideProcessingError(
            "Template file must have 'template_output' field in frontmatter",
            file_path=file_path,
        )

    # Validate the output path
    validated_output = validate_template_output_path(template_output, file_path)

    return TemplateFile(
        source_path=file_path,
        template_output=str(validated_output),
        frontmatter=frontmatter,
        content=content,  # Full content including frontmatter
    )


def process_template_file(template: TemplateFile, output_dir: Path) -> Path:
    """Process a template file and write it to its destination.

    Args:
        template: Parsed template file
        output_dir: Base output directory for documentation

    Returns:
        Path where the file was written

    Raises:
        GuideProcessingError: If writing fails
    """
    output_path = output_dir / template.template_output

    try:
        # Ensure parent directory exists
        ensure_parent_dir(output_path)

        # Write the content atomically
        atomic_write_text(output_path, template.content)

        logger.debug(f"Wrote template {template.source_path.name} to {output_path}")
        return output_path

    except OSError as e:
        raise GuideProcessingError(
            f"Failed to write template output: {e}",
            file_path=template.source_path,
        )
