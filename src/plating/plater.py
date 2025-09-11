#
# plating/plater.py
#
"""Garnish documentation plating system."""

from pathlib import Path

from jinja2 import DictLoader, Environment, select_autoescape
from provide.foundation import logger, metrics
from provide.foundation.utils import timed_block

from plating.errors import PlatingRenderError, handle_error
from plating.plating import PlatingBundle, PlatingDiscovery
from plating.schema import SchemaProcessor


class PlatingPlater:
    """Documentation plater using .plating bundles."""

    def __init__(
        self,
        bundles: list[PlatingBundle] | None = None,
        schema_processor: SchemaProcessor | None = None,
    ):
        """Initialize plater with bundles and optional schema processor.

        Args:
            bundles: List of PlatingBundle objects to render
            schema_processor: Optional schema processor for schema extraction
        """
        self.bundles = bundles or []
        self.schema_processor = schema_processor
        self.provider_schema = None

        if self.schema_processor:
            try:
                self.provider_schema = self.schema_processor.extract_provider_schema()
            except Exception as e:
                handle_error(e, logger)
                logger.warning(f"Failed to extract provider schema: {e}")

    def plate(self, output_dir: Path, force: bool = False) -> None:
        """Plate all bundles to the output directory.

        Args:
            output_dir: Directory to write plated documentation
            force: Force plating even if output exists
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        with timed_block(logger, "plating_total_time") as timer:
            for bundle in self.bundles:
                try:
                    with timed_block(logger, f"bundle_plating_{bundle.name}"):
                        self._plate_bundle(bundle, output_dir, force)
                        # Track successful bundle processing
                        metrics.counter("plating.bundles_processed").inc()
                except PlatingRenderError:
                    metrics.counter("plating.bundle_errors").inc()
                    raise  # Re-raise our custom errors
                except Exception as e:
                    metrics.counter("plating.bundle_errors").inc()
                    error = PlatingRenderError(bundle.name, str(e))
                    handle_error(error, logger)
                    logger.error(f"Failed to plate bundle {bundle.name}: {e}")
                    
        # Record overall metrics  
        metrics.gauge("plating.total_duration_seconds").set(timer.get("duration", 0))
        metrics.gauge("plating.bundles_count").set(len(self.bundles))

    def _plate_bundle(self, bundle: PlatingBundle, output_dir: Path, force: bool) -> None:
        """Plate a single bundle.

        Args:
            bundle: The PlatingBundle to render
            output_dir: Directory to write output
            force: Force overwrite existing files
        """
        # Load bundle assets
        logger.trace(f"Loading assets for bundle {bundle.name}")
        template_content = bundle.load_main_template()
        if not template_content:
            logger.debug(f"No template found for {bundle.name}, skipping")
            return

        examples = bundle.load_examples()
        partials = bundle.load_partials()

        # Get schema for this component
        schema = self._get_schema_for_component(bundle)
        provider_name = self.schema_processor.provider_name if self.schema_processor else "provider"
        
        # Build context data
        context = self._build_context_data(bundle, schema, provider_name)

        # Add examples to context
        context["examples"] = examples

        # Plate template
        try:
            with timed_block(logger, f"template_rendering_{bundle.name}") as render_timer:
                plated = self._plate_template(template_content, context, partials)
                # Track template rendering metrics
                metrics.gauge(f"plating.template_render_time_{bundle.component_type}").set(render_timer.get("duration", 0))
                metrics.counter("plating.templates_rendered").inc()
        except Exception as e:
            metrics.counter("plating.template_render_errors").inc()
            logger.error(f"Template rendering failed for {bundle.name}: {e}")
            return  # Skip this bundle on error

        # Determine output path
        subdir = _get_output_subdir(bundle.component_type)
        output_path = output_dir / subdir / f"{bundle.name}.md"

        # Check if file exists and force flag
        if output_path.exists() and not force:
            logger.debug(f"Output file {output_path} exists, skipping (use force=True to overwrite)")
            return

        # Write output
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(plated)
            logger.info(f"Successfully plated {bundle.name} to {output_path}")
        except OSError as e:
            raise PlatingRenderError(bundle.name, f"Failed to write output file: {e}")

    def _get_schema_for_component(self, bundle: PlatingBundle) -> dict | None:
        """Get schema for a component from the provider schema.

        Args:
            bundle: The bundle to get schema for

        Returns:
            Component schema dict or None
        """
        if not self.provider_schema:
            return None

        # Try to find the component schema
        provider_schemas = self.provider_schema.get("provider_schemas", {})
        for provider_key, provider_data in provider_schemas.items():
            # Check resources
            if bundle.component_type == "resource":
                schemas = provider_data.get("resource_schemas", {})
                if bundle.name in schemas:
                    return schemas[bundle.name]
                if f"pyvider_{bundle.name}" in schemas:
                    return schemas[f"pyvider_{bundle.name}"]

            # Check data sources
            elif bundle.component_type == "data_source":
                schemas = provider_data.get("data_source_schemas", {})
                if bundle.name in schemas:
                    return schemas[bundle.name]
                if f"pyvider_{bundle.name}" in schemas:
                    return schemas[f"pyvider_{bundle.name}"]

            # Check functions
            elif bundle.component_type == "function":
                functions = provider_data.get("functions", {})
                if bundle.name in functions:
                    return functions[bundle.name]
                if f"pyvider_{bundle.name}" in functions:
                    return functions[f"pyvider_{bundle.name}"]

        return None
        
    def _build_context_data(self, bundle: PlatingBundle, schema: dict | None, provider_name: str) -> dict:
        """Build context data for template rendering.
        
        Args:
            bundle: The PlatingBundle
            schema: Component schema dict or None
            provider_name: Name of the provider
            
        Returns:
            Dictionary of context data for template rendering
        """
        # Start with basic bundle info
        formatted_type = _format_component_type(bundle.component_type)
        context = {
            "name": bundle.name,
            "component_type": formatted_type,
            "type": formatted_type,  # Backward compatibility
            "provider_name": provider_name,
        }

        # Add schema-related context if available
        if schema:
            context["description"] = schema.get("description", "")
            context["schema_markdown"] = _plate_schema_markdown(schema)

            # For functions, add signature and arguments
            if bundle.component_type == "function" and "signature" in schema:
                context["signature"] = _format_function_signature(schema)
                context["arguments"] = _format_function_arguments(schema)
        else:
            context["description"] = ""

        return context

    def _plate_template(self, template_content: str, context: dict, partials: dict[str, str]) -> str:
        """Plate a Jinja2 template with context.

        Args:
            template_content: The template string
            context: Rendering context dictionary
            partials: Partial templates dictionary

        Returns:
            Plated template string
        """
        # Set up Jinja2 environment
        templates = {"main.tmpl": template_content}
        templates.update(partials)

        env = Environment(
            loader=DictLoader(templates),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Add custom template functions
        env.globals["schema"] = lambda: context.get("schema_markdown", "")
        env.globals["example"] = lambda name: _format_example(context.get("examples", {}).get(name, ""))
        env.globals["include"] = lambda filename: partials.get(filename, "")

        # Plate template
        template = env.get_template("main.tmpl")
        return template.render(**context)




def _format_component_type(component_type: str) -> str:
    """Format component type for display.

    Args:
        component_type: Raw component type

    Returns:
        Formatted component type
    """
    return {
        "resource": "Resource",
        "data_source": "Data Source",
        "function": "Function",
    }.get(component_type, component_type.title())


def _get_output_subdir(component_type: str) -> str:
    """Get output subdirectory for component type.

    Args:
        component_type: Component type

    Returns:
        Output subdirectory name
    """
    return {
        "resource": "resources",
        "data_source": "data_sources",
        "function": "functions",
    }.get(component_type, "resources")


def _format_example(example_code: str) -> str:
    """Format example code for display.

    Args:
        example_code: Raw example code

    Returns:
        Formatted example with code block
    """
    if not example_code:
        return ""
    return f"```terraform\n{example_code}\n```"


def _plate_schema_markdown(schema: dict) -> str:
    """Plate schema to markdown format.

    Args:
        schema: Schema dictionary

    Returns:
        Markdown formatted schema
    """
    lines = ["## Schema", ""]

    block = schema.get("block", {})
    attributes = block.get("attributes", {})

    # Separate attributes by type
    required_attrs = []
    optional_attrs = []
    computed_attrs = []

    for attr_name, attr_def in attributes.items():
        attr_type = _format_type_string(attr_def.get("type"))
        description = attr_def.get("description", "")

        if attr_def.get("required"):
            required_attrs.append((attr_name, attr_type, description))
        elif attr_def.get("computed") and not attr_def.get("optional"):
            computed_attrs.append((attr_name, attr_type, description))
        else:
            optional_attrs.append((attr_name, attr_type, description))

    # Format sections
    if required_attrs:
        lines.extend(["### Required", ""])
        for name, type_str, desc in required_attrs:
            lines.append(f"- `{name}` ({type_str}) - {desc}")
        lines.append("")

    if optional_attrs:
        lines.extend(["### Optional", ""])
        for name, type_str, desc in optional_attrs:
            lines.append(f"- `{name}` ({type_str}) - {desc}")
        lines.append("")

    if computed_attrs:
        lines.extend(["### Read-Only", ""])
        for name, type_str, desc in computed_attrs:
            lines.append(f"- `{name}` ({type_str}) - {desc}")
        lines.append("")

    # Handle nested blocks
    blocks = block.get("block_types", {})
    if blocks:
        lines.extend(["### Blocks", ""])
        for block_name, block_def in blocks.items():
            max_items = block_def.get("max_items", 0)
            if max_items == 1:
                lines.append(f"- `{block_name}` (Optional)")
            else:
                lines.append(f"- `{block_name}` (Optional, List)")
        lines.append("")

    # Return empty string if no content was generated
    if len(lines) == 2:  # Just "## Schema" and empty line
        return ""

    return "\n".join(lines)


def _format_type_string(type_info) -> str:
    """Format type information to human-readable string.

    Args:
        type_info: Type information (string, list, or dict)

    Returns:
        Formatted type string
    """
    if not type_info:
        return "Dynamic"

    if isinstance(type_info, str):
        return type_info.title()

    if isinstance(type_info, list) and len(type_info) >= 2:
        container_type = type_info[0]
        element_type = type_info[1]

        if container_type == "list":
            return f"List of {_format_type_string(element_type)}"
        elif container_type == "set":
            return f"Set of {_format_type_string(element_type)}"
        elif container_type == "map":
            return f"Map of {_format_type_string(element_type)}"
        elif container_type == "object":
            if isinstance(element_type, dict):
                attrs = ", ".join(f"{k}: {_format_type_string(v)}" for k, v in element_type.items())
                return f"Object({attrs})"
            return "Object"

    return "Dynamic"


def _format_function_signature(schema: dict) -> str:
    """Format function signature from schema.

    Args:
        schema: Function schema

    Returns:
        Formatted function signature
    """
    signature = schema.get("signature", {})
    params = []

    # Parameters
    for param in signature.get("parameters", []):
        param_name = param.get("name", "arg")
        param_type = param.get("type", "any")
        params.append(f"{param_name}: {param_type}")

    # Variadic parameter
    if "variadic_parameter" in signature:
        variadic = signature["variadic_parameter"]
        variadic_name = variadic.get("name", "args")
        variadic_type = variadic.get("type", "any")
        params.append(f"...{variadic_name}: {variadic_type}")

    # Return type
    return_type = signature.get("return_type", "any")
    param_str = ", ".join(params)

    return f"({param_str}) -> {return_type}"


def _format_function_arguments(schema: dict) -> str:
    """Format function arguments from schema.

    Args:
        schema: Function schema

    Returns:
        Formatted arguments list
    """
    signature = schema.get("signature", {})
    lines = []

    # Parameters
    for param in signature.get("parameters", []):
        param_name = param.get("name", "arg")
        param_type = param.get("type", "any")
        description = param.get("description", "")
        lines.append(f"- `{param_name}` ({param_type}) - {description}")

    # Variadic parameter
    if "variadic_parameter" in signature:
        variadic = signature["variadic_parameter"]
        variadic_name = variadic.get("name", "args")
        variadic_type = variadic.get("type", "any")
        description = variadic.get("description", "")
        lines.append(f"- `...{variadic_name}` ({variadic_type}) - {description}")

    return "\n".join(lines)


def generate_docs(
    output_dir: Path | str = "docs",
    provider_name: str | None = None,
    package_name: str = "pyvider.components",
    component_type: str | None = None,
    force: bool = False,
) -> None:
    """Generate documentation for all discovered plating bundles.

    This is the main entry point for documentation generation.

    Args:
        output_dir: Directory to write documentation
        provider_name: Optional provider name for schema extraction
        package_name: Package to search for plating bundles
        component_type: Optional filter for component type
        force: Force overwrite existing files
    """
    # Discover bundles
    discovery = PlatingDiscovery(package_name)
    bundles = discovery.discover_bundles(component_type)

    if not bundles:
        logger.warning(f"No plating bundles found in {package_name}")
        return

    logger.info(f"Found {len(bundles)} plating bundles")

    # Initialize schema processor if provider name given
    schema_processor = None
    if provider_name:
        try:
            # Create mock generator for schema processor
            mock_generator = type(
                "MockGenerator",
                (),
                {"provider_name": provider_name, "provider_dir": Path.cwd()},
            )()
            schema_processor = SchemaProcessor(mock_generator)
        except Exception as e:
            logger.warning(f"Failed to initialize schema processor: {e}")

    # Create renderer and plate
    plater = PlatingPlater(bundles, schema_processor)
    plater.plate(Path(output_dir), force)

    logger.info(f"Documentation generated in {output_dir}")


# 🍲🥄📄🪄
