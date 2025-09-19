from __future__ import annotations

from typing import Any

from jinja2 import Environment, Template

#
# plating/generation/renderer.py
#
"""Template rendering utilities using Jinja2."""


class TemplateRenderer:
    """Renders Jinja2 templates with provided context."""

    def __init__(self) -> None:
        self.env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render_template(self, template_content: str, context: dict[str, Any]) -> str:
        """Render a template string with the provided context.

        Args:
            template_content: Jinja2 template content
            context: Template variables and data

        Returns:
            Rendered template content
        """
        template = self.env.from_string(template_content)
        return template.render(**context)

    def render_template_file(self, template_path: str, context: dict[str, Any]) -> str:
        """Render a template file with the provided context.

        Args:
            template_path: Path to template file
            context: Template variables and data

        Returns:
            Rendered template content
        """
        template = self.env.get_template(template_path)
        return template.render(**context)

    def create_template(self, template_content: str) -> Template:
        """Create a Jinja2 template object from content.

        Args:
            template_content: Jinja2 template content

        Returns:
            Compiled Jinja2 template
        """
        return self.env.from_string(template_content)
