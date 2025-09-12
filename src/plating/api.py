#
# plating/api.py
#
"""Modern async API for plating operations with full foundation integration."""

import asyncio
import time
from pathlib import Path

from provide.foundation import logger, metrics
from provide.foundation.resilience import RetryPolicy, BackoffStrategy, CircuitBreaker

from .async_template_engine import template_engine
from .decorators import with_metrics, with_retry, with_timing, plating_metrics
from .markdown_validator import get_markdown_validator
from .registry import get_plating_registry
from .schema import SchemaProcessor
from .types import (
    ComponentType,
    PlatingContext,
    AdornResult,
    PlateResult,
    ValidationResult
)


class Plating:
    """Modern async API for all plating operations with foundation integration."""
    
    def __init__(
        self,
        context: PlatingContext | None = None,
        package_name: str = "pyvider.components"
    ):
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
            retryable_errors=(IOError, OSError, Exception)
        )
        
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0,
            expected_exception=Exception
        )
        
        # Schema processor
        self._schema_processor = None
        if self.context.provider_name:
            mock_generator = type(
                "MockGenerator", (), 
                {"provider_name": self.context.provider_name, "provider_dir": Path.cwd()}
            )()
            self._schema_processor = SchemaProcessor(mock_generator)
    
    @with_timing
    @with_metrics("adorn_operation")
    async def adorn(self, component_types: list[ComponentType]) -> AdornResult:
        """Create missing documentation templates and examples.
        
        Args:
            component_types: Component types to process
            
        Returns:
            AdornResult with operation statistics
        """
        result = AdornResult()
        
        async with plating_metrics.track_operation("adorn", types=len(component_types)):
            for component_type in component_types:
                try:
                    # Get components from registry
                    components = self.registry.get_components(component_type)
                    components_without_templates = [
                        c for c in components if not c.has_main_template()
                    ]
                    
                    for component in components_without_templates:
                        await self._create_component_template(component, component_type)
                        result.templates_generated += 1
                    
                    result.components_processed += len(components)
                    
                except Exception as e:
                    logger.error(f"Failed to adorn {component_type.value}: {e}")
                    result.errors.append(f"{component_type.value}: {str(e)}")
        
        return result
    
    @with_timing
    @with_retry(max_attempts=2, retryable_errors=(IOError, OSError))
    @with_metrics("plate_operation") 
    async def plate(
        self,
        output_dir: Path,
        component_types: list[ComponentType] | None = None,
        force: bool = False,
        validate_markdown: bool = True
    ) -> PlateResult:
        """Generate documentation from plating bundles.
        
        Args:
            output_dir: Directory to write documentation
            component_types: Component types to filter (None = all)
            force: Force overwrite existing files
            validate_markdown: Run markdown validation
            
        Returns:
            PlateResult with operation statistics
        """
        start_time = time.perf_counter()
        result = PlateResult()
        
        # Determine component types
        if component_types is None:
            component_types = self.registry.get_all_component_types()
        
        async with plating_metrics.track_operation("plate", types=len(component_types)):
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for component_type in component_types:
                try:
                    components = self.registry.get_components_with_templates(component_type)
                    
                    for component in components:
                        await self._render_component_docs(
                            component, component_type, output_dir, force, result
                        )
                    
                    result.bundles_processed += len(components)
                    
                except Exception as e:
                    logger.error(f"Failed to plate {component_type.value}: {e}")
                    result.errors.append(f"{component_type.value}: {str(e)}")
        
        # Markdown validation
        if validate_markdown and result.output_files:
            validation_result = self.validator.validate_files(result.output_files)
            if not validation_result.success:
                result.errors.extend(validation_result.lint_errors)
        
        result.duration_seconds = time.perf_counter() - start_time
        metrics.gauge("plating.plate_duration").set(result.duration_seconds)
        
        return result
    
    @with_timing
    @with_metrics("validate_operation")
    async def validate(
        self,
        output_dir: Path | None = None,
        component_types: list[ComponentType] | None = None
    ) -> ValidationResult:
        """Validate generated documentation.
        
        Args:
            output_dir: Directory containing documentation (default: docs/)
            component_types: Component types to validate (None = all)
            
        Returns:
            ValidationResult with validation statistics
        """
        start_time = time.perf_counter()
        
        if output_dir is None:
            output_dir = Path("docs")
        
        if not output_dir.exists():
            return ValidationResult(
                total=0,
                failed=1,
                errors=["Documentation directory not found"]
            )
        
        # Find markdown files
        markdown_files = list(output_dir.rglob("*.md"))
        
        # Filter by component types if specified
        if component_types:
            filtered_files = []
            for component_type in component_types:
                subdir = component_type.output_subdir
                filtered_files.extend(output_dir.glob(f"{subdir}/*.md"))
            markdown_files = filtered_files
        
        async with plating_metrics.track_operation("validate", files=len(markdown_files)):
            # Validate markdown
            result = self.validator.validate_files(markdown_files)
            result.duration_seconds = time.perf_counter() - start_time
            
            metrics.gauge("plating.validation_duration").set(result.duration_seconds)
        
        return result
    
    async def _create_component_template(
        self, 
        component: "PlatingBundle", 
        component_type: ComponentType
    ) -> None:
        """Create a basic template for a component."""
        from .adorner import TemplateGenerator
        
        template_dir = component.plating_dir / "docs"
        template_dir.mkdir(parents=True, exist_ok=True)
        
        generator = TemplateGenerator()
        template_content = await generator.generate_template(component.name, component_type.value, None)
        
        template_file = template_dir / "main.md.j2"
        template_file.write_text(template_content)
        
        logger.info(f"Created template for {component_type.value}/{component.name}")
    
    async def _render_component_docs(
        self,
        component: "PlatingBundle",
        component_type: ComponentType,
        output_dir: Path,
        force: bool,
        result: PlateResult
    ) -> None:
        """Render documentation for a single component."""
        # Build context
        context = PlatingContext(
            name=component.name,
            component_type=component_type,
            provider_name=self.context.provider_name
        )
        
        # Get schema if available
        if self._schema_processor:
            try:
                provider_schema = self._schema_processor.extract_provider_schema()
                component_schema = self._get_component_schema(
                    component, component_type, provider_schema
                )
                if component_schema:
                    from .types import SchemaInfo
                    context.schema = SchemaInfo.from_dict(component_schema)
            except Exception as e:
                logger.warning(f"Failed to extract schema for {component.name}: {e}")
        
        # Load examples
        context.examples = component.load_examples()
        
        # Render template
        try:
            rendered = await template_engine.render(component, context)
            
            # Write output
            subdir = component_type.output_subdir
            output_subdir = output_dir / subdir
            output_subdir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_subdir / f"{component.name}.md"
            
            if output_file.exists() and not force:
                logger.debug(f"Skipping existing file: {output_file}")
                return
            
            output_file.write_text(rendered)
            result.files_generated += 1
            result.output_files.append(output_file)
            
            logger.info(f"Generated {component_type.value} docs: {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to render {component.name}: {e}")
            result.errors.append(f"{component.name}: {str(e)}")
    
    def _get_component_schema(
        self,
        component: "PlatingBundle",
        component_type: ComponentType,
        provider_schema: dict
    ) -> dict | None:
        """Extract component schema from provider schema."""
        if not provider_schema:
            return None
        
        provider_schemas = provider_schema.get("provider_schemas", {})
        
        for provider_data in provider_schemas.values():
            if component_type == ComponentType.RESOURCE:
                schemas = provider_data.get("resource_schemas", {})
            elif component_type == ComponentType.DATA_SOURCE:
                schemas = provider_data.get("data_source_schemas", {})
            elif component_type == ComponentType.FUNCTION:
                schemas = provider_data.get("functions", {})
            else:
                continue
            
            # Try exact match and with prefix
            for name in [component.name, f"pyvider_{component.name}"]:
                if name in schemas:
                    return schemas[name]
        
        return None
    
    @with_timing
    @with_metrics("adorn_set_operation")
    async def adorn_set(self, component_set_name: str) -> AdornResult:
        """Create missing documentation templates for all components in a ComponentSet.
        
        Args:
            component_set_name: Name of the ComponentSet to process
            
        Returns:
            AdornResult with operation statistics
        """
        component_set = self.registry.get_set(component_set_name)
        if not component_set:
            raise ValueError(f"ComponentSet '{component_set_name}' not found")
        
        result = AdornResult()
        
        async with plating_metrics.track_operation("adorn_set", set_name=component_set_name):
            # Process each domain in the set
            for domain in component_set.get_domains():
                components_in_domain = component_set.filter_by_domain(domain)
                
                for component_ref in components_in_domain:
                    try:
                        # Convert ComponentReference to ComponentType
                        comp_type = ComponentType(component_ref.component_type)
                        
                        # Get the actual component bundle
                        bundle = self.registry.get_component(comp_type, component_ref.name)
                        if bundle and not bundle.has_main_template():
                            await self._create_component_template(bundle, comp_type)
                            result.templates_generated += 1
                        
                        result.components_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to adorn {component_ref}: {e}")
                        result.errors.append(f"{component_ref}: {str(e)}")
        
        logger.info(f"Adorned ComponentSet '{component_set_name}': {result.templates_generated} templates created")
        return result
    
    @with_timing
    @with_retry(max_attempts=2, retryable_errors=(IOError, OSError))
    @with_metrics("plate_set_operation")
    async def plate_set(
        self,
        component_set_name: str,
        output_dir: Path,
        domain: str | None = None,
        force: bool = False,
        validate_markdown: bool = True
    ) -> PlateResult:
        """Generate documentation for all components in a ComponentSet.
        
        Args:
            component_set_name: Name of the ComponentSet to process
            output_dir: Directory to write documentation
            domain: Optional domain to filter by (None = all domains)
            force: Force overwrite existing files
            validate_markdown: Run markdown validation
            
        Returns:
            PlateResult with operation statistics
        """
        component_set = self.registry.get_set(component_set_name)
        if not component_set:
            raise ValueError(f"ComponentSet '{component_set_name}' not found")
        
        start_time = time.perf_counter()
        result = PlateResult()
        
        # Determine domains to process
        domains_to_process = [domain] if domain else list(component_set.get_domains())
        
        async with plating_metrics.track_operation(
            "plate_set", 
            set_name=component_set_name, 
            domains=len(domains_to_process)
        ):
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for process_domain in domains_to_process:
                components_in_domain = component_set.filter_by_domain(process_domain)
                
                for component_ref in components_in_domain:
                    try:
                        # Convert ComponentReference to ComponentType
                        comp_type = ComponentType(component_ref.component_type)
                        
                        # Get the actual component bundle
                        bundle = self.registry.get_component(comp_type, component_ref.name)
                        if bundle and bundle.has_main_template():
                            await self._render_component_docs(
                                bundle, comp_type, output_dir, force, result
                            )
                        
                        result.bundles_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to plate {component_ref}: {e}")
                        result.errors.append(f"{component_ref}: {str(e)}")
        
        # Markdown validation
        if validate_markdown and result.output_files:
            validation_result = self.validator.validate_files(result.output_files)
            if not validation_result.success:
                result.errors.extend(validation_result.lint_errors)
        
        result.duration_seconds = time.perf_counter() - start_time
        metrics.gauge("plating.plate_set_duration").set(result.duration_seconds)
        
        logger.info(f"Plated ComponentSet '{component_set_name}': {result.files_generated} files generated")
        return result
    
    @with_timing
    @with_metrics("validate_set_operation")
    async def validate_set(
        self,
        component_set_name: str,
        output_dir: Path | None = None,
        domain: str | None = None
    ) -> ValidationResult:
        """Validate generated documentation for a ComponentSet.
        
        Args:
            component_set_name: Name of the ComponentSet to validate
            output_dir: Directory containing documentation (default: docs/)
            domain: Optional domain to filter by
            
        Returns:
            ValidationResult with validation statistics
        """
        component_set = self.registry.get_set(component_set_name)
        if not component_set:
            raise ValueError(f"ComponentSet '{component_set_name}' not found")
        
        start_time = time.perf_counter()
        
        if output_dir is None:
            output_dir = Path("docs")
        
        if not output_dir.exists():
            return ValidationResult(
                total=0,
                failed=1,
                errors=[f"Documentation directory not found: {output_dir}"]
            )
        
        # Find markdown files for components in the set
        markdown_files = []
        domains_to_check = [domain] if domain else list(component_set.get_domains())
        
        for check_domain in domains_to_check:
            components_in_domain = component_set.filter_by_domain(check_domain)
            
            for component_ref in components_in_domain:
                try:
                    comp_type = ComponentType(component_ref.component_type)
                    subdir = comp_type.output_subdir
                    doc_file = output_dir / subdir / f"{component_ref.name}.md"
                    
                    if doc_file.exists():
                        markdown_files.append(doc_file)
                        
                except ValueError:
                    # Skip unknown component types
                    logger.warning(f"Unknown component type: {component_ref.component_type}")
        
        async with plating_metrics.track_operation(
            "validate_set", 
            set_name=component_set_name,
            files=len(markdown_files)
        ):
            # Validate markdown files
            result = self.validator.validate_files(markdown_files)
            result.duration_seconds = time.perf_counter() - start_time
            
            metrics.gauge("plating.validation_set_duration").set(result.duration_seconds)
        
        logger.info(f"Validated ComponentSet '{component_set_name}': {result.total} files checked")
        return result
    
    @with_timing
    @with_metrics("generate_all_domains_operation")
    async def generate_all_domains(
        self,
        component_set_name: str,
        output_dir: Path,
        force: bool = False
    ) -> dict[str, PlateResult]:
        """Generate documentation for all domains in a ComponentSet.
        
        Args:
            component_set_name: Name of the ComponentSet
            output_dir: Base output directory
            force: Force overwrite existing files
            
        Returns:
            Dictionary mapping domain names to PlateResult objects
        """
        component_set = self.registry.get_set(component_set_name)
        if not component_set:
            raise ValueError(f"ComponentSet '{component_set_name}' not found")
        
        results = {}
        
        async with plating_metrics.track_operation(
            "generate_all_domains",
            set_name=component_set_name,
            domains=len(component_set.get_domains())
        ):
            for domain in component_set.get_domains():
                domain_output_dir = output_dir / domain
                
                try:
                    result = await self.plate_set(
                        component_set_name=component_set_name,
                        output_dir=domain_output_dir,
                        domain=domain,
                        force=force,
                        validate_markdown=True
                    )
                    results[domain] = result
                    
                except Exception as e:
                    logger.error(f"Failed to generate docs for domain '{domain}': {e}")
                    # Create error result
                    error_result = PlateResult()
                    error_result.errors.append(f"Domain '{domain}': {str(e)}")
                    results[domain] = error_result
        
        logger.info(f"Generated all domains for ComponentSet '{component_set_name}'")
        return results
    
    def register_component_set(self, component_set: ComponentSet) -> None:
        """Register a ComponentSet with the registry.
        
        Args:
            component_set: The ComponentSet to register
        """
        self.registry.register_set(component_set)
    
    def get_component_sets(self, tag: str | None = None) -> list[ComponentSet]:
        """Get all ComponentSets, optionally filtered by tag.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            List of ComponentSet objects
        """
        return self.registry.list_sets(tag=tag)
    
    def find_sets_containing_component(
        self,
        component_name: str,
        component_type: ComponentType,
        domain: str | None = None
    ) -> list[ComponentSet]:
        """Find ComponentSets that contain a specific component.
        
        Args:
            component_name: Name of the component
            component_type: Type of the component
            domain: Optional domain to filter by
            
        Returns:
            List of ComponentSet objects
        """
        return self.registry.find_sets_containing(
            component_name,
            component_type.value,
            domain
        )
    
    def create_component_set_from_components(
        self,
        name: str,
        description: str,
        component_filters: dict[str, list[str]],
        tags: set[str] | None = None
    ) -> ComponentSet:
        """Create a ComponentSet from existing registered components.
        
        Args:
            name: Name for the new ComponentSet
            description: Description of the ComponentSet
            component_filters: Dict of domain -> list of component names
            tags: Optional tags for the set
            
        Returns:
            Created and registered ComponentSet
        """
        return self.registry.create_set_from_components(
            name, description, component_filters, tags
        )
    
    def get_registry_stats(self) -> dict:
        """Get statistics about the component registry."""
        base_stats = self.registry.get_registry_stats()
        set_stats = self.registry.get_set_stats()
        
        return {
            **base_stats,
            "component_sets": set_stats
        }


# Global instance for convenience
_global_api = None

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