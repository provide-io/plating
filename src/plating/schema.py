#
# plating/schema.py
#
"""Schema extraction and processing for documentation generation."""

import json
from pathlib import Path
import shutil
from typing import TYPE_CHECKING, Any

import attrs
from provide.foundation import logger, metrics, pout
from provide.foundation.hub import Hub
from provide.foundation.process import ProcessError, run_command
from provide.foundation.resilience import BackoffStrategy, RetryExecutor, RetryPolicy
from provide.foundation.utils import timed_block

from plating.config import get_config
from plating.errors import SchemaError
from plating.models import FunctionInfo, ProviderInfo, ResourceInfo
from plating.schema_utils.formatters import (
    parse_function_arguments,
    parse_function_signature,
    parse_schema_to_markdown,
    parse_variadic_argument,
)

if TYPE_CHECKING:
    from .generator import DocsGenerator


class SchemaProcessor:
    """Handles schema extraction and processing."""

    def __init__(self, generator: "DocsGenerator") -> None:
        self.generator = generator
        # Set up retry policy for schema operations
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            backoff=BackoffStrategy.EXPONENTIAL,
            base_delay=1.0,
            max_delay=10.0,
            retryable_errors=(ProcessError, SchemaError, Exception),
        )
        self.retry_executor = RetryExecutor(self.retry_policy)
        # Initialize foundation hub for component discovery
        self.hub = Hub()

    def extract_provider_schema(self) -> dict[str, Any]:
        """Extract provider schema using foundation's component discovery."""
        with timed_block(logger, "schema_extraction_total") as timer:
            try:
                result = self._extract_schema_via_discovery()
                metrics.counter("plating.schema_extractions_success").inc()
                metrics.gauge("plating.schema_extraction_duration").set(timer.get("duration", 0))
                return result
            except Exception:
                metrics.counter("plating.schema_extractions_failed").inc()
                raise

    def _extract_schema_via_discovery(self) -> dict[str, Any]:
        """Extract schema by discovering components and inspecting their schemas."""
        logger.info("Discovering components via foundation hub...")
        pout("🔍 Discovering components via foundation hub...")

        try:
            # Use foundation's discovery with pyvider components entry point
            self.hub.discover_components("pyvider.components")
        except Exception as e:
            raise SchemaError(self.generator.provider_name, f"Component discovery failed: {e}")

        # Get components by dimension from foundation registry
        providers = self._get_components_by_dimension("provider")
        resources = self._get_components_by_dimension("resource")
        data_sources = self._get_components_by_dimension("data_source")
        functions = self._get_components_by_dimension("function")

        provider_schema = {
            "provider_schemas": {
                f"registry.terraform.io/local/providers/{self.generator.provider_name}": {
                    "provider": self._get_provider_schema(providers),
                    "resource_schemas": self._get_component_schemas(resources),
                    "data_source_schemas": self._get_component_schemas(data_sources),
                    "functions": self._get_function_schemas(functions),
                }
            }
        }
        return provider_schema

    def _get_components_by_dimension(self, dimension: str) -> dict[str, Any]:
        """Get components from foundation hub by dimension."""
        components = {}
        try:
            names = self.hub.list_components(dimension=dimension)
            for name in names:
                component = self.hub.get_component(name, dimension=dimension)
                if component:
                    components[name] = component
        except Exception as e:
            logger.warning(f"Failed to get {dimension} components: {e}")
        return components

    def _get_provider_schema(self, providers: dict[str, Any]) -> dict[str, Any]:
        if not providers:
            return {"block": {"attributes": {}}}

        try:
            provider_component = next(iter(providers.values()))
            if hasattr(provider_component, "get_schema"):
                schema = provider_component.get_schema()
                return attrs.asdict(schema)
        except Exception as e:
            logger.warning(f"Failed to get provider schema: {e}")

        return {"block": {"attributes": {}}}

    def _get_component_schemas(self, components: dict[str, Any]) -> dict[str, Any]:
        """Get schemas for resources or data sources."""
        schemas = {}
        for name, component in components.items():
            if hasattr(component, "get_schema"):
                schema = component.get_schema()
                schemas[name] = attrs.asdict(schema)
            elif hasattr(component, "__pyvider_schema__"):
                schema_attr = component.__pyvider_schema__
                schemas[name] = schema_attr
        return schemas

    def _get_function_schemas(self, functions: dict[str, Any]) -> dict[str, Any]:
        """Get schemas for functions."""
        schemas = {}
        for name, func in functions.items():
            if hasattr(func, "get_schema"):
                schema = func.get_schema()
                schemas[name] = attrs.asdict(schema)
            elif hasattr(func, "__pyvider_schema__"):
                schemas[name] = func.__pyvider_schema__
        return schemas

    def _extract_schema_via_terraform(self) -> dict[str, Any]:
        """Fallback: Extract schema by building provider and using Terraform CLI."""
        config = get_config()
        tf_binary = config.terraform_binary or "terraform"

        # Build the provider binary with retry
        pout(f"Building provider in {self.generator.provider_dir}")
        try:
            self.retry_executor.execute_sync(
                run_command,
                ["python", "-m", "build"],
                cwd=self.generator.provider_dir,
                capture_output=True,
            )
        except ProcessError as e:
            logger.error(
                "Provider build failed",
                command=e.cmd,
                returncode=e.returncode,
                stdout=e.stdout,
                stderr=e.stderr,
            )
            raise SchemaError(f"Failed to build provider: {e}")

        # Find the built provider binary
        self._find_provider_binary()

        # Create a temporary directory for Terraform operations
        temp_dir = self.generator.provider_dir / ".pyvbuild_temp"
        temp_dir.mkdir(exist_ok=True)

        try:
            # Create basic Terraform configuration
            tf_config = f'''
terraform {{
  required_providers {{
    {self.generator.provider_name} = {{
      source = "local/providers/{self.generator.provider_name}"
    }}
  }}
}}

provider "{self.generator.provider_name}" {{}}
'''

            tf_file = temp_dir / "main.tf"
            tf_file.write_text(tf_config)

            # Initialize Terraform with retry
            try:
                self.retry_executor.execute_sync(
                    run_command,
                    [tf_binary, "init"],
                    cwd=temp_dir,
                    capture_output=True,
                )
            except ProcessError as e:
                logger.error(
                    "Terraform init failed",
                    command=e.cmd,
                    returncode=e.returncode,
                    stdout=e.stdout,
                    stderr=e.stderr,
                )
                raise SchemaError(f"Failed to initialize Terraform: {e}")

            # Extract schema with retry
            try:
                schema_result = self.retry_executor.execute_sync(
                    run_command,
                    [tf_binary, "providers", "schema", "-json"],
                    cwd=temp_dir,
                    capture_output=True,
                )
            except ProcessError as e:
                logger.error(
                    "Schema extraction failed",
                    command=e.cmd,
                    returncode=e.returncode,
                    stdout=e.stdout,
                    stderr=e.stderr,
                )
                raise SchemaError(f"Failed to extract provider schema: {e}")

            schema_data = json.loads(schema_result.stdout)
            return schema_data

        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _find_provider_binary(self) -> Path:
        """Find the provider binary after building."""
        # Look for the provider binary in common locations
        binary_paths = [
            self.generator.provider_dir / "terraform-provider-*",
            self.generator.provider_dir / "dist" / "terraform-provider-*",
            self.generator.provider_dir / "bin" / "terraform-provider-*",
        ]

        import glob

        for pattern in binary_paths:
            matches = glob.glob(str(pattern))
            if matches:
                return Path(matches[0])

        raise FileNotFoundError(f"Could not find provider binary for {self.generator.provider_name}")

    def parse_provider_schema(self) -> None:
        """Parse extracted provider schema into internal structures."""
        schema = self.generator.provider_schema
        if not schema:
            return

        # Create provider info
        provider_schema = schema.get("provider_schemas", {}).get(
            f"registry.terraform.io/local/providers/{self.generator.provider_name}", {}
        )
        provider_config_schema = provider_schema.get("provider", {})

        self.generator.provider_info = ProviderInfo(
            name=self.generator.provider_name,
            description=provider_config_schema.get(
                "description", f"Terraform provider for {self.generator.provider_name}"
            ),
            short_name=self.generator.provider_name,
            rendered_name=self.generator.rendered_provider_name,
        )

        # Process resources
        resources = provider_schema.get("resource_schemas", {})
        if isinstance(resources, tuple):
            resources = {}
        for resource_name, resource_schema in resources.items():
            if self.generator.ignore_deprecated and resource_schema.get("deprecated", False):
                continue

            schema_markdown = parse_schema_to_markdown(resource_schema)

            self.generator.resources[resource_name] = ResourceInfo(
                name=resource_name,
                type="Resource",
                description=resource_schema.get("description", ""),
                schema_markdown=schema_markdown,
                schema=resource_schema,
            )

        # Process data sources
        data_sources = provider_schema.get("data_source_schemas", {})
        for ds_name, ds_schema in data_sources.items():
            if self.generator.ignore_deprecated and ds_schema.get("deprecated", False):
                continue

            schema_markdown = parse_schema_to_markdown(ds_schema)

            self.generator.data_sources[ds_name] = ResourceInfo(
                name=ds_name,
                type="Data Source",
                description=ds_schema.get("description", ""),
                schema_markdown=schema_markdown,
                schema=ds_schema,
            )

        # Process functions
        functions = provider_schema.get("functions", {})
        for func_name, func_schema in functions.items():
            signature_markdown = parse_function_signature(func_schema)
            arguments_markdown = parse_function_arguments(func_schema)
            variadic_markdown = parse_variadic_argument(func_schema)

            self.generator.functions[func_name] = FunctionInfo(
                name=func_name,
                description=func_schema.get("description", ""),
                summary=func_schema.get("summary", ""),
                signature_markdown=signature_markdown,
                arguments_markdown=arguments_markdown,
                has_variadic="variadic_parameter" in func_schema.get("signature", {}),
                variadic_argument_markdown=variadic_markdown,
            )


# 🍲🥄📊🪄
