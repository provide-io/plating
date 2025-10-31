#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from provide.foundation import logger

from plating.bundles import PlatingBundle
from plating.schema.helpers import get_component_schema
from plating.templating.engine import template_engine
from plating.types import ArgumentInfo, ComponentType, PlateResult, PlatingContext, SchemaInfo

#
# plating/core/doc_generator.py
#
"""Documentation generation utilities."""


def _extract_component_metadata(
    bundle: PlatingBundle, component_type: ComponentType, provider_name: str | None
) -> tuple[bool, str | None]:
    """Extract metadata from a component by inspecting the component class.

    Args:
        bundle: PlatingBundle for the component
        component_type: Type of component (resource, data_source, function)
        provider_name: Provider name (used for constructing module paths)

    Returns:
        Tuple of (is_test_only, component_of)
    """
    try:
        # Strip provider prefix from component name if present
        component_name = bundle.name
        if provider_name and component_name.startswith(f"{provider_name}_"):
            component_name = component_name[len(provider_name) + 1 :]

        # Construct the module path
        # For pyvider components, the pattern is: pyvider.components.{type}s.{name}
        type_dir = f"{component_type.value}s"  # resource -> resources, data_source -> data_sources

        # First try using the component name directly
        module_name = f"pyvider.components.{type_dir}.{component_name}"

        # Import the module
        import importlib

        try:
            module = importlib.import_module(module_name)
        except ImportError:
            # If direct import fails, try using the plating directory name
            # Extract module name from plating_dir (e.g., "nested_data_test_suite.plating" -> "nested_data_test_suite")
            plating_dir_name = bundle.plating_dir.name.replace(".plating", "")
            module_name = f"pyvider.components.{type_dir}.{plating_dir_name}"
            module = importlib.import_module(module_name)

        # Look for classes in the module that have metadata attributes
        # and match the component's registered name
        full_component_name = bundle.name
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and (
                hasattr(attr, "_is_test_only") or hasattr(attr, "_parent_capability")
            ):
                # Check if this is the right component by matching the registered name
                if (
                    hasattr(attr, "_registered_name") and attr._registered_name == full_component_name
                ) or not hasattr(attr, "_registered_name"):
                    is_test_only = bool(getattr(attr, "_is_test_only", False))
                    component_of = getattr(attr, "_parent_capability", None)
                    return is_test_only, component_of

        return False, None
    except (ImportError, AttributeError) as e:
        logger.debug(f"Could not extract metadata for {bundle.name}: {e}")
        return False, None


def _determine_subcategory(
    schema_info: SchemaInfo | None, is_test_only: bool, component_of: str | None = None
) -> str:
    """Determine the subcategory for a component based on its metadata.

    Args:
        schema_info: Schema information containing component_of metadata
        is_test_only: Whether the component is marked as test_only
        component_of: Component category from decorator (takes precedence over schema_info)

    Returns:
        Subcategory string: "Test Mode", "Lens", or "Utilities"
    """
    # Test Mode takes precedence
    if is_test_only or (schema_info and schema_info.test_only):
        return "Test Mode"

    # Lens category for components with component_of="lens"
    # Check direct parameter first, then schema_info
    if component_of == "lens" or (schema_info and schema_info.component_of == "lens"):
        return "Lens"

    # Default to Utilities
    return "Utilities"


def _inject_subcategory(content: str, subcategory: str) -> str:
    """Inject subcategory into YAML frontmatter if present.

    Args:
        content: Markdown content with optional YAML frontmatter
        subcategory: Subcategory value to inject (e.g., "Test Mode", "Lens", "Utilities")

    Returns:
        Content with subcategory added to frontmatter
    """
    # Check if content starts with frontmatter (---)
    if not content.startswith("---"):
        # No frontmatter, add one with subcategory
        return f"""---
subcategory: "{subcategory}"
---

{content}"""

    # Find end of frontmatter
    lines = content.split("\n")
    frontmatter_end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            frontmatter_end = i
            break

    if frontmatter_end == -1:
        # Malformed frontmatter, just return original content
        return content

    # Check if subcategory already exists
    has_subcategory = any(line.strip().startswith("subcategory:") for line in lines[1:frontmatter_end])

    if has_subcategory:
        # Already has subcategory, don't modify
        return content

    # Insert subcategory before the closing ---
    lines.insert(frontmatter_end, f'subcategory: "{subcategory}"')
    return "\n".join(lines)


def _inject_test_mode_subcategory(content: str) -> str:
    """Inject 'subcategory: Test Mode' into YAML frontmatter if present.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Content with subcategory added to frontmatter
    """
    # Check if content starts with frontmatter (---)
    if not content.startswith("---"):
        # No frontmatter, add one with subcategory
        return f"""---
subcategory: "Test Mode"
---

{content}"""

    # Find end of frontmatter
    lines = content.split("\n")
    frontmatter_end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            frontmatter_end = i
            break

    if frontmatter_end == -1:
        # Malformed frontmatter, just return original content
        return content

    # Check if subcategory already exists
    has_subcategory = any(line.strip().startswith("subcategory:") for line in lines[1:frontmatter_end])

    if has_subcategory:
        # Already has subcategory, don't modify
        return content

    # Insert subcategory before the closing ---
    lines.insert(frontmatter_end, 'subcategory: "Test Mode"')
    return "\n".join(lines)


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
    output_subdir = output_dir / component_type.output_subdir
    output_subdir.mkdir(parents=True, exist_ok=True)

    for component in components:
        try:
            # Strip provider prefix from filename if present (for resources and data sources)
            component_name = component.name
            if context.provider_name and component_type in [ComponentType.RESOURCE, ComponentType.DATA_SOURCE]:
                prefix = f"{context.provider_name}_"
                if component_name.startswith(prefix):
                    component_name = component_name[len(prefix) :]

            output_file = output_subdir / f"{component_name}.md"

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

            # Extract component metadata by importing and inspecting the class
            try:
                is_test_only, component_of = _extract_component_metadata(
                    component, component_type, context.provider_name
                )
            except Exception as meta_e:
                logger.warning(
                    f"Could not extract metadata for {component.name}, using schema info only: {meta_e}"
                )
                is_test_only, component_of = False, None

            # Extract metadata for functions
            signature = None
            arguments = None
            if component_type == ComponentType.FUNCTION:
                from plating.templating.metadata import TemplateMetadataExtractor

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

            # Determine and inject appropriate subcategory based on component metadata
            subcategory = _determine_subcategory(schema_info, is_test_only, component_of)
            rendered_content = _inject_subcategory(rendered_content, subcategory)

            # Write output
            output_file.write_text(rendered_content, encoding="utf-8")
            result.files_generated += 1
            result.output_files.append(output_file)

            logger.info(f"Generated {component_type.value} docs: {output_file}")

        except Exception as e:
            import traceback

            logger.error(f"Failed to render {component.name}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")


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
    provider_name = context.provider_name
    if not provider_name:
        raise ValueError("Provider name is required in PlatingContext for index generation")
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

    # Helper function to strip provider prefix if present
    def strip_provider_prefix(name: str, prefix: str) -> str:
        """Remove provider prefix from component name if present."""
        prefix_with_underscore = f"{prefix}_"
        if name.startswith(prefix_with_underscore):
            return name[len(prefix_with_underscore) :]
        return name

    # Helper function to check if component is test mode
    def is_test_mode_component(component_name: str, component_type: ComponentType) -> bool:
        """Check if component is a test mode component by reading its metadata."""
        # Try to get the component schema which contains test_only metadata
        schema_info = get_component_schema(
            PlatingBundle(name=component_name, plating_dir=Path(), component_type=component_type.value),
            component_type,
            provider_schema,
        )
        if schema_info and schema_info.test_only:
            return True

        # Fallback to heuristic-based detection for components without schema
        test_indicators = ["_test", "test_", "warning_example", "verifier"]
        return any(indicator in component_name.lower() for indicator in test_indicators)

    # Add links to resources (excluding test mode)
    resource_components = registry.get_components_with_templates(ComponentType.RESOURCE)
    test_resources = []
    if resource_components:
        for component in sorted(resource_components, key=lambda c: c.name):
            clean_name = strip_provider_prefix(component.name, provider_name)
            if is_test_mode_component(component.name, ComponentType.RESOURCE):
                test_resources.append((component, clean_name))
            else:
                index_content += f"- [`{provider_name}_{clean_name}`](./{ComponentType.RESOURCE.output_subdir}/{clean_name}.md)\n"
    else:
        index_content += "No resources available.\n"

    index_content += "\n## Data Sources\n\n"

    # Add links to data sources (excluding test mode)
    data_source_components = registry.get_components_with_templates(ComponentType.DATA_SOURCE)
    test_data_sources = []
    if data_source_components:
        for component in sorted(data_source_components, key=lambda c: c.name):
            clean_name = strip_provider_prefix(component.name, provider_name)
            if is_test_mode_component(component.name, ComponentType.DATA_SOURCE):
                test_data_sources.append((component, clean_name))
            else:
                index_content += f"- [`{provider_name}_{clean_name}`](./{ComponentType.DATA_SOURCE.output_subdir}/{clean_name}.md)\n"
    else:
        index_content += "No data sources available.\n"

    index_content += "\n## Functions\n\n"

    # Add links to functions
    function_components = registry.get_components_with_templates(ComponentType.FUNCTION)
    if function_components:
        for component in sorted(function_components, key=lambda c: c.name):
            index_content += (
                f"- [`{component.name}`](./{ComponentType.FUNCTION.output_subdir}/{component.name}.md)\n"
            )
    else:
        index_content += "No functions available.\n"

    # Add Test Mode section if there are test components
    if test_resources or test_data_sources:
        index_content += "\n## Test Mode\n\n"
        index_content += "_Test-only components for testing and development purposes._\n\n"

        if test_resources:
            index_content += "### Test Resources\n\n"
            for component, clean_name in test_resources:
                index_content += f"- [`{provider_name}_{clean_name}`](./{ComponentType.RESOURCE.output_subdir}/{clean_name}.md)\n"
            index_content += "\n"

        if test_data_sources:
            index_content += "### Test Data Sources\n\n"
            for component, clean_name in test_data_sources:
                index_content += f"- [`{provider_name}_{clean_name}`](./{ComponentType.DATA_SOURCE.output_subdir}/{clean_name}.md)\n"

    # Write the index file
    index_file.write_text(index_content, encoding="utf-8")
    result.files_generated += 1
    result.output_files.append(index_file)

    logger.info(f"Generated provider index: {index_file}")


# 🍽️📖🔚
