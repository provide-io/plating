from __future__ import annotations

#
# plating/core/doc_generator.py
#
"""Documentation generation utilities."""

from pathlib import Path
from typing import Any

from provide.foundation import logger
from plating.async_template_engine import template_engine
from plating.bundles import PlatingBundle
from plating.types import ArgumentInfo, ComponentType, PlateResult, PlatingContext, SchemaInfo
from plating.core.schema_helpers import get_component_schema


async def render_component_docs(
    components: list[PlatingBundle],
    component_type: ComponentType,
    output_dir: Path,
    force: bool,
    result: PlateResult,
    context: PlatingContext,
    provider_schema: dict[str, Any],
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
            schema_info = get_component_schema(component, component_type, provider_schema)

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
                    arg_lines = metadata["arguments_markdown"].split("\n")
                    arguments = []
                    for line in arg_lines:
                        if line.strip().startswith("- `"):
                            # Parse "- `name` (type) - description"
                            parts = line.strip()[3:].split("`", 1)
                            if len(parts) >= 2:
                                name = parts[0]
                                rest = parts[1].strip()
                                if rest.startswith("(") and ")" in rest:
                                    type_end = rest.find(")")
                                    arg_type = rest[1:type_end]
                                    description = rest[type_end + 1 :].strip(" -")
                                    arguments.append(
                                        ArgumentInfo(name=name, type=arg_type, description=description)
                                    )

            # Create context for rendering
            context_dict = context.to_dict() if context else {}

            # Load examples from the component bundle
            examples = component.load_examples()

            render_context = PlatingContext(
                name=component.name,  # Always use component.name, not context name
                component_type=component_type,
                description=f"Terraform {component_type.value} for {component.name}",
                schema=schema_info,
                signature=signature,
                arguments=arguments,
                examples=examples,
                **{
                    k: v
                    for k, v in context_dict.items()
                    if k
                    not in [
                        "name",
                        "component_type",
                        "schema",
                        "signature",
                        "arguments",
                        "examples",
                        "description",
                    ]
                },
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


def generate_template(component: PlatingBundle, template_file: Path) -> None:
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


def generate_provider_index(
    output_dir: Path,
    force: bool,
    result: PlateResult,
    context: PlatingContext,
    provider_schema: dict[str, Any],
    registry: Any,
) -> None:
    """Generate provider index page."""
    index_file = output_dir / "index.md"

    if index_file.exists() and not force:
        logger.debug(f"Skipping existing provider index: {index_file}")
        return

    logger.info("Generating provider index page...")

    # Get provider name from context
    provider_name = context.provider_name or "pyvider"
    display_name = provider_name.title()

    # Extract provider schema for configuration documentation
    provider_config_schema = None

    # Look for provider configuration schema
    for schema_key, schema_data in provider_schema.items():
        if "provider" in schema_key.lower():
            provider_config_schema = schema_data
            break

    # Create provider schema info if available
    provider_schema_info = None
    if provider_config_schema:
        provider_schema_info = SchemaInfo.from_dict(provider_config_schema)

    # Create provider example configuration
    provider_example = f'''provider "{provider_name}" {{
  # Configuration options
}}'''

    # Generate index content
    index_content = f'''---
page_title: "{display_name} Provider"
description: |-
  Terraform provider for {provider_name}
---

# {display_name} Provider

Terraform provider for {provider_name} - A Python-based Terraform provider built with the Pyvider framework.

## Example Usage

```terraform
{provider_example}
```

## Schema

{provider_schema_info.to_markdown() if provider_schema_info else "No provider configuration required."}

## Resources

'''

    # Add links to resources
    resource_components = registry.get_components_with_templates(ComponentType.RESOURCE)
    if resource_components:
        for component in sorted(resource_components, key=lambda c: c.name):
            index_content += f"- [`{provider_name}_{component.name}`](./resource/{component.name}.md)\n"
    else:
        index_content += "No resources available.\n"

    index_content += "\n## Data Sources\n\n"

    # Add links to data sources
    data_source_components = registry.get_components_with_templates(ComponentType.DATA_SOURCE)
    if data_source_components:
        for component in sorted(data_source_components, key=lambda c: c.name):
            index_content += f"- [`{provider_name}_{component.name}`](./data_source/{component.name}.md)\n"
    else:
        index_content += "No data sources available.\n"

    index_content += "\n## Functions\n\n"

    # Add links to functions
    function_components = registry.get_components_with_templates(ComponentType.FUNCTION)
    if function_components:
        for component in sorted(function_components, key=lambda c: c.name):
            index_content += f"- [`{component.name}`](./function/{component.name}.md)\n"
    else:
        index_content += "No functions available.\n"

    # Write the index file
    index_file.write_text(index_content, encoding="utf-8")
    result.files_generated += 1
    result.output_files.append(index_file)

    logger.info(f"Generated provider index: {index_file}")