#
# plating/api.py
#
"""Unified API for all plating operations."""

import asyncio
import time
from pathlib import Path

from provide.foundation import logger

from .async_template_engine import template_engine
from .decorators import with_metrics, with_retry, with_timing, async_rate_limited, plating_metrics
from .plating import PlatingBundle, PlatingDiscovery  
from .schema import SchemaProcessor
from .types import (
    ComponentType,
    PlatingContext,
    SchemaInfo,
    ArgumentInfo,
    AdornResult,
    PlateResult,
    ValidationResult
)


class Plating:
    """Unified API for all plating operations."""
    
    def __init__(
        self,
        package_name: str = "pyvider.components",
        provider_name: str | None = None
    ):
        """Initialize plating API.
        
        Args:
            package_name: Package to search for plating bundles
            provider_name: Provider name for schema extraction
        """
        self.package_name = package_name
        self.provider_name = provider_name
        self._discovery = PlatingDiscovery(package_name)
        self._schema_processor = None
        
        if provider_name:
            # Create mock generator for schema processor
            mock_generator = type(
                "MockGenerator",
                (),
                {"provider_name": provider_name, "provider_dir": Path.cwd()},
            )()
            self._schema_processor = SchemaProcessor(mock_generator)
    
    @with_timing
    @with_metrics("adorn_operation")
    async def adorn(self, component_types: list[ComponentType] | None = None) -> AdornResult:
        """Adorn components with documentation templates and examples.
        
        Args:
            component_types: Optional list of component types to filter
            
        Returns:
            AdornResult with operation statistics
        """
        from .adorner import adorn_missing_components
        
        # Convert enum to string for adorner compatibility
        component_type_strs = None
        if component_types:
            component_type_strs = [ct.value for ct in component_types]
        
        async with plating_metrics.track_operation("adorn", types=len(component_types or [])):
            # Use existing adorner logic
            result = await adorn_missing_components(component_type_strs)
            
            return AdornResult(
                components_processed=result.get("total", 0),
                templates_generated=result.get("resources", 0) + result.get("data_sources", 0) + result.get("functions", 0),
                examples_created=result.get("total", 0),  # Assume 1:1 ratio
                errors=result.get("errors", [])
            )
    
    @with_timing  
    @with_retry(max_attempts=2, retryable_errors=(IOError, OSError))
    @with_metrics("plate_operation")
    async def plate(
        self,
        output_dir: Path,
        component_types: list[ComponentType] | None = None,
        force: bool = False
    ) -> PlateResult:
        """Generate documentation from plating bundles.
        
        Args:
            output_dir: Directory to write documentation
            component_types: Optional list of component types to filter
            force: Force overwrite existing files
            
        Returns:
            PlateResult with operation statistics
        """
        start_time = time.perf_counter()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        errors = []
        output_files = []
        
        # Discover bundles
        bundles = await self._discover_bundles(component_types)
        
        if not bundles:
            logger.warning(f"No plating bundles found in {self.package_name}")
            return PlateResult(
                bundles_processed=0,
                files_generated=0,
                duration_seconds=time.perf_counter() - start_time,
                errors=["No bundles found"],
                output_files=[]
            )
        
        # Extract schema if processor available
        provider_schema = None
        if self._schema_processor:
            try:
                provider_schema = self._schema_processor.extract_provider_schema()
            except Exception as e:
                logger.warning(f"Schema extraction failed: {e}")
                errors.append(f"Schema extraction failed: {e}")
        
        # Process bundles with rate limiting
        async with async_rate_limited(rate=5.0, burst=10):  # 5 bundles per second
            tasks = []
            for bundle in bundles:
                task = asyncio.create_task(
                    self._plate_bundle(bundle, output_dir, provider_schema, force)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        bundles_processed = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"Bundle {bundles[i].name}: {result}")
            elif result:  # result is output file path
                bundles_processed += 1
                output_files.append(result)
        
        duration = time.perf_counter() - start_time
        
        return PlateResult(
            bundles_processed=bundles_processed,
            files_generated=len(output_files),
            duration_seconds=duration,
            errors=errors,
            output_files=output_files
        )
    
    @with_timing
    @with_metrics("validate_operation") 
    async def validate(self, component_types: list[ComponentType] | None = None) -> ValidationResult:
        """Validate example files using terraform.
        
        Args:
            component_types: Optional list of component types to filter
            
        Returns:
            ValidationResult with validation statistics
        """
        from .validator.adapters import PlatingValidator
        
        # Convert enum to string for validator compatibility
        component_type_strs = None
        if component_types:
            component_type_strs = [ct.value for ct in component_types]
        
        async with plating_metrics.track_operation("validate", types=len(component_types or [])):
            validator = PlatingValidator(fallback_to_simple=True)
            
            # Run validation (currently sync, but wrapped in async for API consistency)
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                validator.run_validation,
                component_type_strs
            )
            
            return ValidationResult(
                total=result.get("total", 0),
                passed=result.get("passed", 0), 
                failed=result.get("failed", 0),
                skipped=result.get("skipped", 0),
                duration_seconds=result.get("duration", 0.0),
                failures=result.get("failures", {}),
                terraform_version=result.get("terraform_version", "")
            )
    
    async def _discover_bundles(self, component_types: list[ComponentType] | None) -> list[PlatingBundle]:
        """Discover plating bundles asynchronously."""
        # Run discovery in thread pool since it's I/O bound
        def discover():
            if component_types:
                all_bundles = []
                for ct in component_types:
                    bundles = self._discovery.discover_bundles(ct.value)
                    all_bundles.extend(bundles)
                return all_bundles
            else:
                return self._discovery.discover_bundles()
        
        return await asyncio.get_event_loop().run_in_executor(None, discover)
    
    async def _plate_bundle(
        self,
        bundle: PlatingBundle,
        output_dir: Path,
        provider_schema: dict | None,
        force: bool
    ) -> Path | None:
        """Plate a single bundle asynchronously."""
        # Get schema for component
        schema = self._get_schema_for_component(bundle, provider_schema)
        
        # Create typed context
        context = PlatingContext(
            name=bundle.name,
            component_type=ComponentType(bundle.component_type),
            provider_name=self.provider_name or "provider",
            description=schema.get("description", "") if schema else "",
            schema=SchemaInfo.from_dict(schema) if schema else None
        )
        
        # Load examples
        examples = await asyncio.get_event_loop().run_in_executor(
            None, bundle.load_examples
        )
        context.examples = examples
        
        # Handle function-specific context
        if bundle.component_type == "function" and schema and "signature" in schema:
            context.signature = self._format_function_signature(schema)
            context.arguments = self._parse_function_arguments(schema)
        
        # Render template
        rendered = await template_engine.render(bundle, context)
        
        if not rendered:
            return None
        
        # Determine output path
        output_path = output_dir / context.component_type.output_subdir / f"{bundle.name}.md"
        
        # Check if file exists and force flag
        if output_path.exists() and not force:
            logger.debug(f"Output file {output_path} exists, skipping (use force=True to overwrite)")
            return None
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.get_event_loop().run_in_executor(
            None, output_path.write_text, rendered
        )
        
        logger.info(f"Successfully plated {bundle.name} to {output_path}")
        return output_path
    
    def _get_schema_for_component(self, bundle: PlatingBundle, provider_schema: dict | None) -> dict | None:
        """Get schema for a component from the provider schema."""
        if not provider_schema:
            return None
        
        provider_schemas = provider_schema.get("provider_schemas", {})
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
    
    def _format_function_signature(self, schema: dict) -> str:
        """Format function signature from schema."""
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
    
    def _parse_function_arguments(self, schema: dict) -> list[ArgumentInfo]:
        """Parse function arguments from schema."""
        signature = schema.get("signature", {})
        arguments = []
        
        # Parameters
        for param in signature.get("parameters", []):
            arguments.append(ArgumentInfo(
                name=param.get("name", "arg"),
                type=param.get("type", "any"),
                description=param.get("description", ""),
                required=True
            ))
        
        # Variadic parameter
        if "variadic_parameter" in signature:
            variadic = signature["variadic_parameter"]
            arguments.append(ArgumentInfo(
                name=f"...{variadic.get('name', 'args')}",
                type=variadic.get("type", "any"),
                description=variadic.get("description", ""),
                required=False
            ))
        
        return arguments


# Global API instance
plating = Plating()


# 🍲🚀🎯🔧