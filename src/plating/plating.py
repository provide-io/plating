from __future__ import annotations

#
# plating/plating.py
#
"""Modern async API for plating operations with full foundation integration."""

from pathlib import Path
import time
from typing import Any

from provide.foundation import logger, metrics
from provide.foundation.resilience import BackoffStrategy, CircuitBreaker, RetryPolicy

from plating.async_template_engine import template_engine
from plating.bundles import PlatingBundle
from plating.decorators import plating_metrics, with_metrics, with_retry, with_timing
from plating.discovery import PlatingDiscovery
from plating.markdown_validator import get_markdown_validator
from plating.registry import get_plating_registry
from plating.schema import SchemaProcessor
from plating.types import AdornResult, ComponentType, PlateResult, PlatingContext, ValidationResult


class Plating:
    """Modern async API for all plating operations with foundation integration."""

    def __init__(
        self, context: PlatingContext | None = None, package_name: str = "pyvider.components"
    ) -> None:
        """Initialize plating API with foundation context.

        Args:
            context: PlatingContext with configuration (optional)
            package_name: Package to search for plating bundles
        """
        self.context = context or PlatingContext(provider_name="default")
        self.package_name = package_name

        # Foundation patterns
        self.registry = get_plating_registry(package_name)
        self.validator = get_markdown_validator()

        # Resilience patterns
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            backoff=BackoffStrategy.EXPONENTIAL,
            base_delay=0.5,
            max_delay=10.0,
            retryable_errors=(IOError, OSError, Exception),
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=30.0, expected_exception=(Exception,)
        )

    @with_timing
    @with_retry()
    @with_metrics("adorn")
    async def adorn(
        self,
        output_dir: Path | None = None,
        component_types: list[ComponentType] | None = None,
        templates_only: bool = False,
    ) -> AdornResult:
        """Generate template structure for discovered components.

        Args:
            output_dir: Directory to write templates (default: .plating)
            component_types: Specific component types to adorn
            templates_only: Only generate templates, skip discovery

        Returns:
            AdornResult with generation statistics
        """
        if not component_types:
            component_types = [ComponentType.RESOURCE, ComponentType.DATA_SOURCE, ComponentType.FUNCTION]

        output_dir = output_dir or Path(".plating")
        output_dir.mkdir(exist_ok=True)

        start_time = time.monotonic()
        templates_generated = 0

        for component_type in component_types:
            components = self.registry.get_components_with_templates(component_type)
            logger.info(f"Found {len(components)} {component_type.value} components to adorn")

            for component in components:
                try:
                    template_dir = output_dir / component_type.value / component.name
                    template_dir.mkdir(parents=True, exist_ok=True)

                    # Generate basic template if it doesn't exist
                    template_file = template_dir / f"{component.name}.tmpl.md"
                    if not template_file.exists() or not templates_only:
                        await self._generate_template(component, template_file)
                        templates_generated += 1

                except Exception as e:
                    logger.error(f"Failed to adorn {component.name}: {e}")

        duration = time.monotonic() - start_time
        return AdornResult(
            duration=duration,
            templates_generated=templates_generated,
            components_discovered=sum(len(self.registry.get_components(ct)) for ct in component_types),
        )

    @with_timing
    @with_retry()
    @with_metrics("plate")
    async def plate(
        self,
        output_dir: Path | None = None,
        component_types: list[ComponentType] | None = None,
        force: bool = False,
        validate_markdown: bool = True,
    ) -> PlateResult:
        """Generate documentation from plating bundles.

        Args:
            output_dir: Output directory for documentation
            component_types: Component types to generate
            force: Overwrite existing files
            validate_markdown: Enable markdown validation

        Returns:
            PlateResult with generation statistics
        """
        output_dir = output_dir or Path("docs")
        output_dir.mkdir(parents=True, exist_ok=True)

        if not component_types:
            component_types = [ComponentType.RESOURCE, ComponentType.DATA_SOURCE, ComponentType.FUNCTION]

        start_time = time.monotonic()
        result = PlateResult(duration_seconds=0.0, files_generated=0, errors=[], output_files=[])

        for component_type in component_types:
            components = self.registry.get_components_with_templates(component_type)
            logger.info(f"Generating docs for {len(components)} {component_type.value} components")

            await self._render_component_docs(components, component_type, output_dir, force, result)

        result.duration_seconds = time.monotonic() - start_time

        # Validate if requested
        if validate_markdown and result.output_files:
            validation_result = await self.validate(output_dir, component_types)
            result.errors.extend(validation_result.errors)

        return result

    async def validate(
        self, output_dir: Path | None = None, component_types: list[ComponentType] | None = None
    ) -> ValidationResult:
        """Validate generated documentation.

        Args:
            output_dir: Directory containing documentation
            component_types: Component types to validate

        Returns:
            ValidationResult with any errors found
        """
        output_dir = output_dir or Path("docs")
        component_types = component_types or [
            ComponentType.RESOURCE,
            ComponentType.DATA_SOURCE,
            ComponentType.FUNCTION,
        ]

        errors = []
        files_checked = 0

        for component_type in component_types:
            type_dir = output_dir / component_type.value.replace("_", "_")
            if not type_dir.exists():
                continue

            for md_file in type_dir.glob("*.md"):
                try:
                    validation_result = await self.validator.validate_file(md_file)
                    if not validation_result.is_valid:
                        errors.extend(validation_result.errors)
                    files_checked += 1
                except Exception as e:
                    errors.append(f"Failed to validate {md_file}: {e}")

        return ValidationResult(errors=errors, files_checked=files_checked, is_valid=len(errors) == 0)

    async def _render_component_docs(
        self,
        components: list[PlatingBundle],
        component_type: ComponentType,
        output_dir: Path,
        force: bool,
        result: PlateResult,
    ) -> None:
        """Render documentation for a list of components."""
        output_subdir = output_dir / component_type.value.replace("_", "_")
        output_subdir.mkdir(parents=True, exist_ok=True)

        for component in components:
            try:
                output_file = output_subdir / f"{component.name}.md"

                if output_file.exists() and not force:
                    logger.debug(f"Skipping existing file: {output_file}")
                    continue

                # Load and render template
                template_content = component.load_main_template()
                if not template_content:
                    logger.warning(f"No template found for {component.name}")
                    continue

                # Get component schema if available
                provider_schema = self._get_component_schema(component, component_type, {})

                # Extract metadata for functions
                signature = None
                arguments = None
                if component_type == ComponentType.FUNCTION:
                    from plating.discovery.templates import TemplateMetadataExtractor
                    extractor = TemplateMetadataExtractor()
                    metadata = extractor.extract_function_metadata(component.name, component_type.value)
                    signature = metadata.get("signature_markdown", "")
                    if metadata.get("arguments_markdown"):
                        # Convert markdown arguments to ArgumentInfo objects
                        from plating.types import ArgumentInfo
                        arg_lines = metadata["arguments_markdown"].split('\n')
                        arguments = []
                        for line in arg_lines:
                            if line.strip().startswith('- `'):
                                # Parse "- `name` (type) - description"
                                parts = line.strip()[3:].split('`', 1)
                                if len(parts) >= 2:
                                    name = parts[0]
                                    rest = parts[1].strip()
                                    if rest.startswith('(') and ')' in rest:
                                        type_end = rest.find(')')
                                        arg_type = rest[1:type_end]
                                        description = rest[type_end+1:].strip(' -')
                                        arguments.append(ArgumentInfo(name=name, type=arg_type, description=description))

                # Create context for rendering
                context_dict = self.context.to_dict() if self.context else {}

                # Load examples from the component bundle
                examples = component.load_examples()

                render_context = PlatingContext(
                    name=component.name,  # Always use component.name, not context name
                    component_type=component_type,
                    description=f"Terraform {component_type.value} for {component.name}",
                    schema=provider_schema,
                    signature=signature,
                    arguments=arguments,
                    examples=examples,
                    **{k: v for k, v in context_dict.items() if k not in ['name', 'component_type', 'schema', 'signature', 'arguments', 'examples', 'description']}
                )

                # Render with template engine
                rendered_content = await template_engine.render(component, render_context)

                # Write output
                output_file.write_text(rendered_content, encoding="utf-8")
                result.files_generated += 1
                result.output_files.append(output_file)

                logger.info(f"Generated {component_type.value} docs: {output_file}")

            except Exception as e:
                logger.error(f"Failed to render {component.name}: {e}")

    def _get_component_schema(
        self, component: PlatingBundle, component_type: ComponentType, provider_schema: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Extract component schema from provider schema."""
        if not provider_schema:
            return None

        schemas = provider_schema.get(f"{component_type.value}_schemas", {})
        if not schemas:
            return None

        # Try to find schema by component name
        for name, schema in schemas.items():
            if name == component.name or name == f"pyvider_{component.name}":
                return schema

        return None

    def get_registry_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        stats = {"total_components": 0, "component_types": []}

        for component_type in [ComponentType.RESOURCE, ComponentType.DATA_SOURCE, ComponentType.FUNCTION]:
            components = self.registry.get_components(component_type)
            with_templates = self.registry.get_components_with_templates(component_type)

            stats[component_type.value] = {
                "total": len(components),
                "with_templates": len(with_templates),
            }
            stats["total_components"] += len(components)
            if components:
                stats["component_types"].append(component_type.value)

        return stats

    async def _generate_template(self, component: PlatingBundle, template_file: Path) -> None:
        """Generate a basic template for a component."""
        template_content = f"""---
page_title: "{component.component_type.title()}: {component.name}"
description: |-
  Terraform {component.component_type} for {component.name}
---

# {component.name} ({component.component_type.title()})

Terraform {component.component_type} for {component.name}

## Example Usage

{{{{ example("example") }}}}

## Schema

{{{{ schema_markdown }}}}
"""
        template_file.write_text(template_content, encoding="utf-8")


# Global API instance
_global_api: Plating | None = None


def plating(context: PlatingContext | None = None) -> Plating:
    """Get or create global plating API instance.

    Args:
        context: Optional PlatingContext for configuration

    Returns:
        Plating API instance
    """
    global _global_api
    if _global_api is None:
        _global_api = Plating(context)
    return _global_api


# 🍲🚀⚡✨
