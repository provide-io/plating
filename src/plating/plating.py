#
# plating/api.py
#
"""Modern async API for plating operations with full foundation integration."""

from pathlib import Path
import time

from attrs import define
from provide.foundation import logger, metrics
from provide.foundation.resilience import BackoffStrategy, CircuitBreaker, RetryPolicy

from plating.async_template_engine import template_engine
from plating.decorators import plating_metrics, with_metrics, with_retry, with_timing
from plating.markdown_validator import get_markdown_validator
from plating.registry import get_plating_registry
from plating.schema import SchemaProcessor
from plating.types import AdornResult, ComponentType, PlateResult, PlatingContext, ValidationResult


class Plating:
    """Modern async API for all plating operations with foundation integration."""

    def __init__(self, context: PlatingContext | None = None, package_name: str = "pyvider.components"):
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
            failure_threshold=3, recovery_timeout=30.0, expected_exception=Exception
        )

        # Schema processor
        self._schema_processor = None
        if self.context.provider_name:
            mock_generator = type(
                "MockGenerator", (), {"provider_name": self.context.provider_name, "provider_dir": Path.cwd()}
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
                    components_without_templates = [c for c in components if not c.has_main_template()]

                    for component in components_without_templates:
                        await self._create_component_template(component, component_type)
                        result.templates_generated += 1

                    result.components_processed += len(components)

                except Exception as e:
                    logger.error(f"Failed to adorn {component_type.value}: {e}")
                    result.errors.append(f"{component_type.value}: {e!s}")

        return result

    @with_timing
    @with_retry(max_attempts=2, retryable_errors=(IOError, OSError))
    @with_metrics("plate_operation")
    async def plate(
        self,
        output_dir: Path,
        component_types: list[ComponentType] | None = None,
        force: bool = False,
        validate_markdown: bool = True,
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
                        await self._render_component_docs(component, component_type, output_dir, force, result)

                    result.bundles_processed += len(components)

                except Exception as e:
                    logger.error(f"Failed to plate {component_type.value}: {e}")
                    result.errors.append(f"{component_type.value}: {e!s}")

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
        self, output_dir: Path | None = None, component_types: list[ComponentType] | None = None
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
            return ValidationResult(total=0, failed=1, errors=["Documentation directory not found"])

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
        self, component: "PlatingBundle", component_type: ComponentType
    ) -> None:
        """Create a basic template for a component."""
        from plating.adorner import TemplateGenerator

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
        result: PlateResult,
    ) -> None:
        """Render documentation for a single component."""
        # Build context
        context = PlatingContext(
            name=component.name, component_type=component_type, provider_name=self.context.provider_name
        )

        # Get schema if available
        if self._schema_processor:
            try:
                provider_schema = self._schema_processor.extract_provider_schema()
                component_schema = self._get_component_schema(component, component_type, provider_schema)
                if component_schema:
                    from plating.types import SchemaInfo

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
            result.errors.append(f"{component.name}: {e!s}")

    def _get_component_schema(
        self, component: "PlatingBundle", component_type: ComponentType, provider_schema: dict
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

    def get_registry_stats(self) -> dict:
        """Get statistics about the component registry."""
        return self.registry.get_registry_stats()


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


@define
class PlatingBundle:
    """Represents a single .plating bundle with its assets."""

    name: str
    plating_dir: Path
    component_type: str

    @property
    def docs_dir(self) -> Path:
        """Directory containing documentation templates and partials."""
        return self.plating_dir / "docs"

    @property
    def examples_dir(self) -> Path:
        """Directory containing example Terraform files."""
        return self.plating_dir / "examples"

    @property
    def fixtures_dir(self) -> Path:
        """Directory containing fixture files for tests (inside examples dir)."""
        return self.examples_dir / "fixtures"

    def has_main_template(self) -> bool:
        """Check if this bundle has a main template."""
        template_file = self.docs_dir / f"{self.name}.tmpl.md"
        main_template = self.docs_dir / "main.md.j2"
        return template_file.exists() or main_template.exists()

    def has_examples(self) -> bool:
        """Check if this bundle has examples."""
        if not self.examples_dir.exists():
            return False
        return any(self.examples_dir.glob("*.tf"))

    def load_main_template(self) -> str | None:
        """Load the main template file for this component."""
        template_file = self.docs_dir / f"{self.name}.tmpl.md"
        main_template = self.docs_dir / "main.md.j2"

        for template_path in [template_file, main_template]:
            if template_path.exists():
                try:
                    return template_path.read_text(encoding="utf-8")
                except Exception:
                    return None
        return None

    def load_examples(self) -> dict[str, str]:
        """Load all example files as a dictionary."""
        examples: dict[str, str] = {}
        if not self.examples_dir.exists():
            return examples

        for example_file in self.examples_dir.glob("*.tf"):
            try:
                examples[example_file.stem] = example_file.read_text(encoding="utf-8")
            except Exception:
                continue
        return examples

    def load_partials(self) -> dict[str, str]:
        """Load all partial files from docs directory."""
        partials: dict[str, str] = {}
        if not self.docs_dir.exists():
            return partials

        for partial_file in self.docs_dir.glob("_*"):
            if partial_file.is_file():
                try:
                    partials[partial_file.name] = partial_file.read_text(encoding="utf-8")
                except Exception:
                    continue
        return partials

    def load_fixtures(self) -> dict[str, str]:
        """Load all fixture files from fixtures directory."""
        fixtures: dict[str, str] = {}
        if not self.fixtures_dir.exists():
            return fixtures

        for fixture_file in self.fixtures_dir.rglob("*"):
            if fixture_file.is_file():
                try:
                    rel_path = fixture_file.relative_to(self.fixtures_dir)
                    fixtures[str(rel_path)] = fixture_file.read_text(encoding="utf-8")
                except Exception:
                    continue
        return fixtures


class PlatingDiscovery:
    """Discovers .plating bundles from installed packages."""

    def __init__(self, package_name: str = "pyvider.components"):
        self.package_name = package_name

    def discover_bundles(self, component_type: str | None = None) -> list[PlatingBundle]:
        """Discover all .plating bundles from the installed package."""
        bundles: list[PlatingBundle] = []

        try:
            import importlib.util

            spec = importlib.util.find_spec(self.package_name)
            if not spec or not spec.origin:
                return bundles
        except (ModuleNotFoundError, ValueError):
            return bundles

        package_path = Path(spec.origin).parent

        for plating_dir in package_path.rglob("*.plating"):
            if not plating_dir.is_dir() or plating_dir.name.startswith("."):
                continue

            bundle_component_type = self._determine_component_type(plating_dir)
            if component_type and bundle_component_type != component_type:
                continue

            sub_component_bundles = self._discover_sub_components(plating_dir, bundle_component_type)
            if sub_component_bundles:
                bundles.extend(sub_component_bundles)
            else:
                component_name = plating_dir.name.replace(".plating", "")
                bundle = PlatingBundle(
                    name=component_name, plating_dir=plating_dir, component_type=bundle_component_type
                )
                bundles.append(bundle)

        return bundles

    def _discover_sub_components(self, plating_dir: Path, component_type: str) -> list[PlatingBundle]:
        """Discover individual components within a multi-component .plating bundle."""
        sub_bundles = []

        for item in plating_dir.iterdir():
            if not item.is_dir():
                continue

            docs_dir = item / "docs"
            if docs_dir.exists() and docs_dir.is_dir():
                sub_component_type = item.name
                if sub_component_type not in ["resource", "data_source", "function"]:
                    sub_component_type = component_type

                bundle = PlatingBundle(name=item.name, plating_dir=item, component_type=sub_component_type)
                sub_bundles.append(bundle)

        return sub_bundles

    def _determine_component_type(self, plating_dir: Path) -> str:
        """Determine component type from the .plating directory path."""
        path_parts = plating_dir.parts

        if "resources" in path_parts:
            return "resource"
        elif "data_sources" in path_parts:
            return "data_source"
        elif "functions" in path_parts:
            return "function"
        else:
            return "resource"


# 🍲🚀⚡✨
