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
) -> bool:
    """Extract metadata from a component by inspecting the component class.

    Args:
        bundle: PlatingBundle for the component
        component_type: Type of component (resource, data_source, function)
        provider_name: Provider name (used for constructing module paths)

    Returns:
        Boolean indicating if component is test_only
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

        # Look for classes in the module that have test_only metadata
        full_component_name = bundle.name
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and hasattr(attr, "_is_test_only"):  # noqa: SIM102
                # Check if this is the right component by matching the registered name
                if (
                    hasattr(attr, "_registered_name") and attr._registered_name == full_component_name
                ) or not hasattr(attr, "_registered_name"):
                    return bool(getattr(attr, "_is_test_only", False))

        return False
    except (ImportError, AttributeError) as e:
        logger.debug(f"Could not extract metadata for {bundle.name}: {e}")
        return False


def _determine_subcategory(schema_info: SchemaInfo | None, is_test_only: bool) -> str | None:
    """Determine the subcategory for a component based on its metadata.

    Subcategories are primarily defined in template frontmatter. This function
    only handles special cases where subcategory is auto-determined:
    - Test-only components get "Test Mode" subcategory

    Args:
        schema_info: Schema information (currently unused - kept for compatibility)
        is_test_only: Whether the component is marked as test_only

    Returns:
        "Test Mode" for test-only components, None otherwise.
        None means the component has no subcategory (will render first per
        Terraform Registry standards).
    """
    # Test Mode is automatically assigned to test-only components
    if is_test_only or (schema_info and schema_info.test_only):
        return "Test Mode"

    # All other subcategories come from template frontmatter
    return None


def group_components_by_capability(
    components: list[tuple[PlatingBundle, ComponentType]],
) -> dict[str, dict[str, list[tuple[PlatingBundle, ComponentType]]]]:
    """Group components by capability (subcategory) and then by component type.

    Returns a nested dictionary: {capability: {component_type: [components]}}
    """
    from collections import defaultdict
    from typing import Any

    grouped: dict[str | None, dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))

    for component, comp_type in components:
        # Extract subcategory from template frontmatter if present
        # If not present, use None (components with no subcategory render first per Terraform Registry standards)
        subcategory = _extract_subcategory_from_template(component)

        # Store grouped components
        grouped[subcategory][comp_type].append((component, comp_type))

    # Sort capabilities: None (uncategorized) first, then alphabetically, "Test Mode" always last
    sorted_grouped: dict[str | None, dict[str, list[Any]]] = {}

    # Add uncategorized components (None key) first if they exist
    if None in grouped:
        sorted_grouped[None] = grouped.pop(None)

    # Add categorized components alphabetically
    test_mode_items = grouped.pop("Test Mode", None)
    for capability in sorted(grouped.keys()):
        sorted_grouped[capability] = grouped[capability]

    # Add Test Mode last
    if test_mode_items:
        sorted_grouped["Test Mode"] = test_mode_items

    return dict(sorted_grouped)


def _extract_subcategory_from_template(component: PlatingBundle) -> str | None:
    """Extract subcategory from component template frontmatter.

    Returns the subcategory value if present, None otherwise.
    """
    try:
        template_content = component.load_main_template()
        if not template_content:
            return None

        # Extract frontmatter
        if not template_content.startswith("---"):
            return None

        # Find end of frontmatter
        lines = template_content.split("\n")
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                # Extract subcategory from frontmatter section
                frontmatter = "\n".join(lines[1:i])
                for line in frontmatter.split("\n"):
                    if line.strip().startswith("subcategory:"):
                        # Extract value: "subcategory: "Value"" -> "Value"
                        value = line.split(":", 1)[1].strip().strip('"')
                        return value
                return None

        return None
    except Exception as e:
        logger.debug(f"Could not extract subcategory from {component.name}: {e}")
        return None


def _inject_subcategory(content: str, subcategory: str | None) -> str:
    """Inject subcategory into YAML frontmatter if needed.

    Subcategories should come from template frontmatter. This function only
    injects when a subcategory is explicitly provided (e.g., "Test Mode").

    Args:
        content: Markdown content with optional YAML frontmatter
        subcategory: Subcategory value to inject, or None to skip injection

    Returns:
        Content with subcategory added to frontmatter (if subcategory is not None)
    """
    # Skip injection if no subcategory specified
    if subcategory is None:
        return content

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
        # Already has subcategory, don't modify (template wins)
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


async def render_component_docs(  # noqa: C901
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
                is_test_only = _extract_component_metadata(component, component_type, context.provider_name)
            except Exception as meta_e:
                logger.warning(
                    f"Could not extract metadata for {component.name}, using schema info only: {meta_e}"
                )
                is_test_only = False

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
            # Most subcategories come from template frontmatter; only "Test Mode" is auto-determined here
            subcategory = _determine_subcategory(schema_info, is_test_only)
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


def generate_provider_index(  # noqa: C901
    output_dir: Path,
    force: bool,
    result: PlateResult,
    context: PlatingContext,
    provider_schema: dict[str, Any],
    registry: Any,
) -> None:
    """Generate provider index page with capability-first grouping."""
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

    # Generate index content with capability-first organization
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

'''

    # Helper function to strip provider prefix if present
    def strip_provider_prefix(name: str, prefix: str) -> str:
        """Remove provider prefix from component name if present."""
        prefix_with_underscore = f"{prefix}_"
        if name.startswith(prefix_with_underscore):
            return name[len(prefix_with_underscore) :]
        return name

    # Collect all components with their types
    all_components = []

    resource_components = registry.get_components_with_templates(ComponentType.RESOURCE)
    if resource_components:
        for component in resource_components:
            all_components.append((component, ComponentType.RESOURCE))

    data_source_components = registry.get_components_with_templates(ComponentType.DATA_SOURCE)
    if data_source_components:
        for component in data_source_components:
            all_components.append((component, ComponentType.DATA_SOURCE))

    function_components = registry.get_components_with_templates(ComponentType.FUNCTION)
    if function_components:
        for component in function_components:
            all_components.append((component, ComponentType.FUNCTION))

    # Group components by capability
    grouped = group_components_by_capability(all_components)

    # Generate capability-first sections
    for capability, types_dict in grouped.items():
        # Skip header for uncategorized (None) section - they render at top level
        if capability is not None:
            index_content += f"## {capability}\n\n"

        # Iterate through component types in order: resources, data_sources, functions
        type_order = [ComponentType.RESOURCE, ComponentType.DATA_SOURCE, ComponentType.FUNCTION]

        for comp_type in type_order:
            if comp_type.value not in types_dict:
                continue

            components = types_dict[comp_type.value]
            if not components:
                continue

            # Add subheader for component type (except for Test Mode which groups all types)
            if capability != "Test Mode":
                type_display = {
                    ComponentType.RESOURCE: "Resources",
                    ComponentType.DATA_SOURCE: "Data Sources",
                    ComponentType.FUNCTION: "Functions",
                }.get(comp_type, str(comp_type))
                index_content += f"### {type_display}\n\n"
            else:
                # For Test Mode, show type subheaders
                type_display = {
                    ComponentType.RESOURCE: "Resources",
                    ComponentType.DATA_SOURCE: "Data Sources",
                    ComponentType.FUNCTION: "Functions",
                }.get(comp_type, str(comp_type))
                index_content += f"### Test {type_display}\n\n"

            # Add component links
            for component, _ in sorted(components, key=lambda x: x[0].name):
                clean_name = strip_provider_prefix(component.name, provider_name)

                if comp_type == ComponentType.FUNCTION:
                    # Functions don't have provider prefix in their names
                    index_content += f"- [`{component.name}`](./{comp_type.output_subdir}/{clean_name}.md)\n"
                else:
                    # Resources and data sources include provider prefix
                    index_content += (
                        f"- [`{provider_name}_{clean_name}`](./{comp_type.output_subdir}/{clean_name}.md)\n"
                    )

            index_content += "\n"

    # Write the index file
    index_file.write_text(index_content, encoding="utf-8")
    result.files_generated += 1
    result.output_files.append(index_file)

    logger.info(f"Generated provider index: {index_file}")


# 🍽️📖🔚
