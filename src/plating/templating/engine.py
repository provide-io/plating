#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from jinja2 import DictLoader, Environment, TemplateError as Jinja2TemplateError, select_autoescape
from provide.foundation import logger
import yaml

from plating.decorators import plating_metrics, with_metrics, with_timing
from plating.errors import FileSystemError, TemplateError
from plating.types import PlatingContext

if TYPE_CHECKING:
    from plating.bundles import PlatingBundle

"""Modern async template engine with foundation integration and error handling."""


class AsyncTemplateEngine:
    """Async-first template engine with foundation integration."""

    def __init__(self) -> None:
        self._jinja_env = None
        self._template_cache: dict[str, str] = {}

    def _get_jinja_env(self, templates: dict[str, str]) -> Environment:
        """Get or create Jinja2 environment with templates."""
        env = Environment(
            loader=DictLoader(templates),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=True,  # Enable async template rendering
        )

        # Add custom template functions
        env.globals.update(
            {
                "schema": lambda: "",  # Will be overridden per template
                "example": self._format_example,
                "include": lambda filename: templates.get(filename, ""),
            }
        )

        return env

    @with_timing
    @with_metrics("template_render")
    async def render(self, bundle: PlatingBundle, context: PlatingContext) -> str:
        """Render template with context and partials.

        Args:
            bundle: PlatingBundle containing template and assets
            context: Type-safe context for rendering

        Returns:
            Rendered template string

        Raises:
            TemplateError: If template rendering fails
            FileSystemError: If template loading fails
        """
        try:
            # Load template and partials concurrently
            template_task = asyncio.create_task(self._load_template(bundle))
            partials_task = asyncio.create_task(self._load_partials(bundle))

            template_content, partials = await asyncio.gather(template_task, partials_task)

            if not template_content:
                logger.debug(f"No template found for {bundle.name}, skipping")
                return ""

            # Prepare templates dict
            templates = {"main.tmpl": template_content}
            templates.update(partials)

            # Create Jinja environment
            env = self._get_jinja_env(templates)

            # Convert context to dict
            context_dict = context.to_dict()

            # Override template functions with context-aware implementations
            env.globals["example"] = lambda key: self._format_example_with_context(key, context.examples)

            # Override schema function to return actual schema
            if context.schema:
                env.globals["schema"] = lambda: context.schema.to_markdown()
            else:
                env.globals["schema"] = lambda: ""

            # Render template asynchronously
            template = env.get_template("main.tmpl")

            async with plating_metrics.track_operation("template_render", bundle=bundle.name):
                rendered = await template.render_async(**context_dict)
                # Apply global header/footer injection
                return self._apply_global_wrappers(rendered, context)

        except Jinja2TemplateError as e:
            # Extract line number if available
            line_number = getattr(e, "lineno", None)
            error_msg = str(e)

            logger.error(
                "Template rendering failed",
                bundle=bundle.name,
                error=error_msg,
                line_number=line_number,
                **context.to_dict(),
            )

            raise TemplateError(
                template_path=bundle.plating_dir / "docs" / f"{bundle.name}.tmpl.md",
                reason=error_msg,
                line_number=line_number,
                template_context=getattr(e, "source", None),
            ) from e

        except OSError as e:
            logger.error("File system error during template rendering", bundle=bundle.name, error=str(e))
            raise FileSystemError(
                path=bundle.plating_dir,
                operation="read template",
                reason=str(e),
                caused_by=e,
            ) from e

        except Exception as e:
            logger.exception("Unexpected error during template rendering", bundle=bundle.name)
            raise TemplateError(
                template_path=bundle.plating_dir / "docs" / f"{bundle.name}.tmpl.md",
                reason=f"Unexpected error: {type(e).__name__}: {e}",
            ) from e

    @with_timing
    @with_metrics("template_render_batch")
    async def render_batch(self, items: list[tuple[PlatingBundle, PlatingContext]]) -> list[str]:
        """Render multiple templates in parallel.

        Args:
            items: List of (bundle, context) tuples to render

        Returns:
            List of rendered template strings

        Raises:
            TemplateError: If any template rendering fails
            FileSystemError: If any template loading fails
        """
        tasks = [asyncio.create_task(self.render(bundle, context)) for bundle, context in items]

        async with plating_metrics.track_operation("batch_render", count=len(items)):
            return await asyncio.gather(*tasks)

    async def _load_template(self, bundle: PlatingBundle) -> str:
        """Load main template from bundle.

        Uses run_in_executor to wrap blocking file I/O operations in the async
        event loop's thread pool. This prevents blocking the event loop while
        maintaining async semantics.

        Args:
            bundle: PlatingBundle to load template from

        Returns:
            Template content as string

        Raises:
            FileSystemError: If template file cannot be read
        """
        cache_key = f"{bundle.plating_dir}:{bundle.name}:main"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        try:
            # Wrap blocking file I/O in executor to avoid blocking event loop
            template_content = await asyncio.get_event_loop().run_in_executor(None, bundle.load_main_template)

            self._template_cache[cache_key] = template_content
            return template_content

        except (OSError, FileNotFoundError) as e:
            logger.error("Failed to load template", bundle=bundle.name, error=str(e))
            raise FileSystemError(
                path=bundle.plating_dir / "docs" / f"{bundle.name}.tmpl.md",
                operation="read",
                reason=str(e),
                caused_by=e,
            ) from e

    async def _load_partials(self, bundle: PlatingBundle) -> dict[str, str]:
        """Load partial templates from bundle.

        Uses run_in_executor to wrap blocking file I/O operations in the async
        event loop's thread pool. This prevents blocking the event loop while
        maintaining async semantics.

        Args:
            bundle: PlatingBundle to load partials from

        Returns:
            Dictionary of partial name to content

        Raises:
            FileSystemError: If partial files cannot be read
        """
        import json

        cache_key = f"{bundle.plating_dir}:{bundle.name}:partials"
        if cache_key in self._template_cache:
            return json.loads(self._template_cache[cache_key])

        try:
            # Wrap blocking file I/O in executor to avoid blocking event loop
            partials = await asyncio.get_event_loop().run_in_executor(None, bundle.load_partials)

            self._template_cache[cache_key] = json.dumps(partials)
            return partials

        except OSError as e:
            logger.error("Failed to load partials", bundle=bundle.name, error=str(e))
            raise FileSystemError(
                path=bundle.plating_dir / "docs" / "_partials",
                operation="read",
                reason=str(e),
                caused_by=e,
            ) from e

    def _format_example(self, example_code: str) -> str:
        """Format example code for display."""
        if not example_code:
            return ""
        return f"```terraform\n{example_code}\n```"

    def _format_example_with_context(self, key: str, examples: dict[str, str]) -> str:
        """Format example code by looking up the key in the examples dictionary."""
        if not key or not examples:
            return ""

        example_content = examples.get(key, "")
        if not example_content:
            # Only log as debug since examples are often optional
            logger.debug(f"Optional example '{key}' not found in examples")
            return ""

        return f"```terraform\n{example_content}\n```"

    def _apply_global_wrappers(self, rendered_content: str, context: PlatingContext) -> str:
        """Apply global header/footer to rendered markdown content.

        Checks frontmatter for opt-out flags and injects global header/footer
        content at appropriate locations if not explicitly skipped.

        Args:
            rendered_content: The rendered markdown content with frontmatter
            context: The plating context containing global_partials_dir

        Returns:
            Modified markdown content with global header/footer injected
        """
        # Parse frontmatter and body
        frontmatter, body = self._parse_frontmatter(rendered_content)

        # Check for opt-out flags
        skip_header = self._should_skip_header(frontmatter)
        skip_footer = self._should_skip_footer(frontmatter)

        # Load global header/footer content
        global_header = self._load_global_file("_global_header.md", context)
        global_footer = self._load_global_file("_global_footer.md", context)

        # Inject header into body if not skipped
        if not skip_header and global_header:
            body = self._inject_header_into_body(body, global_header)

        # Append footer to body if not skipped
        if not skip_footer and global_footer:
            body = body.rstrip() + "\n\n" + global_footer.rstrip() + "\n"

        # Reconstruct markdown with frontmatter and modified body
        if frontmatter:
            return frontmatter + "\n" + body
        return body

    def _parse_frontmatter(self, content: str) -> tuple[str, str]:
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

    def _should_skip_header(self, frontmatter: str) -> bool:
        """Check if skip_global_header flag is set in frontmatter."""
        return self._check_frontmatter_flag(frontmatter, "skip_global_header")

    def _should_skip_footer(self, frontmatter: str) -> bool:
        """Check if skip_global_footer flag is set in frontmatter."""
        return self._check_frontmatter_flag(frontmatter, "skip_global_footer")

    def _check_frontmatter_flag(self, frontmatter: str, flag_name: str) -> bool:
        """Check if a boolean flag is set to true in frontmatter."""
        if not frontmatter:
            return False

        try:
            # Extract YAML content between delimiters
            lines = frontmatter.split("\n")
            yaml_lines = [line for line in lines[1:-1] if line.strip()]  # Skip delimiters
            yaml_content = "\n".join(yaml_lines)

            if not yaml_content:
                return False

            data = yaml.safe_load(yaml_content)
            if isinstance(data, dict):
                return data.get(flag_name, False) is True
            return False
        except (yaml.YAMLError, AttributeError):
            logger.debug(f"Failed to parse frontmatter flag {flag_name}")
            return False

    def _load_global_file(self, filename: str, context: PlatingContext) -> str:
        """Load global header/footer file from configured directory.

        Args:
            filename: Name of the global file (e.g., '_global_header.md')
            context: The plating context containing global_partials_dir

        Returns:
            File content as string, or empty string if file not found or no directory configured
        """
        if not hasattr(context, "global_partials_dir") or not context.global_partials_dir:
            logger.debug(f"No global_partials_dir configured, skipping {filename}")
            return ""

        try:
            global_file = context.global_partials_dir / filename
            if global_file.exists():
                logger.debug(f"Loaded global file: {global_file}")
                return global_file.read_text(encoding="utf-8")
            else:
                logger.debug(f"Global file not found: {global_file}")
        except (OSError, ValueError) as e:
            logger.warning(f"Failed to load global file {filename}: {e}")

        return ""

    def _inject_header_into_body(self, body: str, header: str) -> str:
        """Inject global header into body after H1 heading and description.

        Placement: After the H1 heading and the first paragraph/description.

        Args:
            body: The markdown body content
            header: The header content to inject

        Returns:
            Modified body with header injected
        """
        lines = body.split("\n")

        # Find H1 heading
        h1_idx = -1
        for i, line in enumerate(lines):
            if line.startswith("# "):
                h1_idx = i
                break

        if h1_idx == -1:
            # No H1 found, prepend header
            return header + "\n\n" + body

        # Find the first non-empty line after H1 (the description)
        desc_idx = -1
        for i in range(h1_idx + 1, len(lines)):
            if lines[i].strip():
                desc_idx = i
                break

        # Insert after description if found, otherwise after H1
        insert_idx = h1_idx + 1 if desc_idx == -1 else desc_idx + 1

        # Insert header at the calculated position
        lines.insert(insert_idx, "")  # Add blank line before header
        lines.insert(insert_idx + 1, header)
        lines.insert(insert_idx + 2, "")  # Add blank line after header

        return "\n".join(lines)

    def clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()


# Global template engine instance
template_engine = AsyncTemplateEngine()


# 🍲⚡🎨📝

# 🍽️📖🔚
