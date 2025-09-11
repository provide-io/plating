#
# plating/api.py
#
"""Main Plating API class providing unified interface to all operations."""

import time
from pathlib import Path
from typing import Any

from provide.foundation import logger

from plating.cleaner import PlatingCleaner
from plating.config import PlatingConfig, get_config
from plating.plating import PlatingBundle, PlatingDiscovery
from plating.results import AdornResult, CleanResult, PlateResult, TestResult, ValidationResult
from plating.schema import SchemaProcessor


class Plating:
    """Unified API for plating operations.
    
    This class provides a single entry point for all plating functionality:
    - Discovering and managing .plating bundles
    - Adorning components with documentation templates
    - Plating (generating) documentation
    - Cleaning generated documentation
    - Testing example files
    - Schema extraction and validation
    
    Example:
        >>> p = Plating()
        >>> p.clean()                    # Clean old docs
        >>> p.adorn()                    # Create missing bundles
        >>> result = p.plate("docs")     # Generate documentation
        >>> print(f"Generated {len(result.plated)} files")
    """

    def __init__(self, provider_dir: Path = None, config: PlatingConfig = None):
        """Initialize plating for a provider directory.

        Args:
            provider_dir: Directory containing the provider code (default: current directory)
            config: Configuration object (default: auto-detected)
        """
        self.provider_dir = Path(provider_dir) if provider_dir else Path.cwd()
        self.config = config or get_config()
        self._bundles = None
        self._schema_processor = None
        self._cleaner = None

    @property
    def bundles(self) -> list[PlatingBundle]:
        """Get list of discovered plating bundles (cached)."""
        if self._bundles is None:
            self._bundles = self.discover_bundles()
        return self._bundles

    @property
    def schema_processor(self) -> SchemaProcessor:
        """Get schema processor (cached)."""
        if self._schema_processor is None:
            try:
                self._schema_processor = SchemaProcessor(provider_name=self.config.provider_name)
            except Exception as e:
                logger.warning(f"Failed to initialize schema processor: {e}")
                self._schema_processor = None
        return self._schema_processor

    @property
    def cleaner(self) -> PlatingCleaner:
        """Get cleaner instance (cached)."""
        if self._cleaner is None:
            self._cleaner = PlatingCleaner()
        return self._cleaner

    def clean(self, output_dir: Path = None, dry_run: bool = False) -> CleanResult:
        """Remove all generated documentation.

        Args:
            output_dir: Directory containing generated docs (default: 'docs')
            dry_run: If True, show what would be removed without actually removing

        Returns:
            CleanResult with details of what was cleaned

        Example:
            >>> result = p.clean("docs")
            >>> print(f"Removed {result.total_items} items, freed {result.bytes_freed} bytes")
        """
        if output_dir is None:
            output_dir = Path("docs")
        else:
            output_dir = Path(output_dir)

        return self.cleaner.clean(output_dir, dry_run=dry_run)

    def adorn(self, component_types: list[str] = None, force: bool = False) -> AdornResult:
        """Create .plating bundles for components missing documentation.

        Args:
            component_types: Optional list of component types to adorn ["resource", "data_source", "function"]
            force: Force adorning even if bundles already exist

        Returns:
            AdornResult with details of what was adorned

        Example:
            >>> result = p.adorn(["resource"])
            >>> print(f"Adorned {result.total_adorned} resources")
        """
        from plating.adorner import adorn_components

        start_time = time.time()
        
        try:
            adorned = adorn_components(component_types)
            
            # Clear cached bundles since we may have created new ones
            self._bundles = None
            
            return AdornResult(
                adorned=adorned,
                skipped=[],  # TODO: Track skipped components
                errors=[],
                duration=time.time() - start_time
            )
        except Exception as e:
            return AdornResult(
                adorned={},
                skipped=[],
                errors=[str(e)],
                duration=time.time() - start_time
            )

    def plate(
        self,
        output_dir: Path = None,
        component_types: list[str] = None,
        clean_first: bool = False,
        force: bool = False,
    ) -> PlateResult:
        """Generate documentation from .plating bundles.

        Args:
            output_dir: Directory to write documentation (default: 'docs')
            component_types: Optional list of component types to plate
            clean_first: Whether to clean output directory first
            force: Force plating even if output exists

        Returns:
            PlateResult with details of what was generated

        Example:
            >>> result = p.plate("docs", clean_first=True)
            >>> if result.success:
            ...     print(f"Generated {len(result.plated)} files")
        """
        from plating.plater import generate_docs

        if output_dir is None:
            output_dir = Path("docs")
        else:
            output_dir = Path(output_dir)

        start_time = time.time()
        errors = []
        cleaned = False

        try:
            # Clean first if requested
            if clean_first:
                clean_result = self.clean(output_dir)
                cleaned = True

            # Generate documentation
            generate_docs(str(output_dir))

            # Find generated files (simple heuristic)
            generated_files = []
            if output_dir.exists():
                generated_files = [str(f) for f in output_dir.rglob("*.md") if f.is_file()]

            bundles_processed = len([b for b in self.bundles if self._bundle_has_examples(b)])

            return PlateResult(
                plated=generated_files,
                bundles_processed=bundles_processed,
                errors=errors,
                duration=time.time() - start_time,
                cleaned_first=cleaned,
            )

        except Exception as e:
            errors.append(str(e))
            return PlateResult(
                plated=[],
                bundles_processed=0,
                errors=errors,
                duration=time.time() - start_time,
                cleaned_first=cleaned,
            )

    def test(self, component_types: list[str] = None, parallel: int = 4) -> TestResult:
        """Run tests on example files in .plating bundles.

        Args:
            component_types: Optional list of component types to test
            parallel: Number of parallel tests to run

        Returns:
            TestResult with test execution results

        Example:
            >>> result = p.test()
            >>> print(f"Tests: {result.passed}/{result.total} passed ({result.success_rate:.1f}%)")
        """
        from plating.test_runner import run_tests

        return run_tests(component_types=component_types, parallel=parallel)

    def discover_bundles(self, component_type: str = None) -> list[PlatingBundle]:
        """Discover all .plating bundles.

        Args:
            component_type: Optional filter for specific component type

        Returns:
            List of discovered PlatingBundle objects

        Example:
            >>> bundles = p.discover_bundles("resource")
            >>> print(f"Found {len(bundles)} resource bundles")
        """
        discovery = PlatingDiscovery()
        return discovery.discover_bundles(component_type)

    def get_bundle(self, name: str) -> PlatingBundle | None:
        """Get a specific bundle by name.

        Args:
            name: Name of the bundle to find

        Returns:
            PlatingBundle if found, None otherwise

        Example:
            >>> bundle = p.get_bundle("my_resource")
            >>> if bundle:
            ...     template = bundle.load_main_template()
        """
        for bundle in self.bundles:
            if bundle.name == name:
                return bundle
        return None

    def add_bundle(self, bundle: PlatingBundle) -> None:
        """Add a custom bundle to the collection.

        Args:
            bundle: PlatingBundle to add

        Example:
            >>> custom_bundle = PlatingBundle(name="custom", plating_dir=path, component_type="resource")
            >>> p.add_bundle(custom_bundle)
        """
        if self._bundles is None:
            self._bundles = self.discover_bundles()
        self._bundles.append(bundle)

    def extract_schema(self) -> dict[str, Any] | None:
        """Extract provider schema.

        Returns:
            Provider schema dictionary, or None if extraction failed

        Example:
            >>> schema = p.extract_schema()
            >>> if schema:
            ...     resources = schema.get("provider_schemas", {})
        """
        if self.schema_processor:
            try:
                return self.schema_processor.extract_provider_schema()
            except Exception as e:
                logger.error(f"Schema extraction failed: {e}")
                return None
        return None

    def validate_schema(self) -> ValidationResult:
        """Validate provider schema.

        Returns:
            ValidationResult with validation details

        Example:
            >>> result = p.validate_schema()
            >>> if not result.valid:
            ...     print(f"Validation errors: {result.errors}")
        """
        errors = []
        warnings = []

        try:
            schema = self.extract_schema()
            if schema is None:
                errors.append("Failed to extract schema")
            else:
                # Basic validation
                if not schema.get("provider_schemas"):
                    errors.append("No provider schemas found")

                # Check for common issues
                for provider_key, provider_data in schema.get("provider_schemas", {}).items():
                    if not provider_data.get("resource_schemas") and not provider_data.get("data_source_schemas"):
                        warnings.append(f"Provider {provider_key} has no resources or data sources")

        except Exception as e:
            errors.append(f"Validation failed: {e}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def status(self) -> dict[str, Any]:
        """Get plating status information.

        Returns:
            Dictionary with status information

        Example:
            >>> status = p.status()
            >>> print(f"Found {status['bundles']['total']} bundles")
        """
        bundles = self.bundles
        bundle_types = {}
        missing_templates = 0
        missing_examples = 0

        for bundle in bundles:
            comp_type = bundle.component_type
            if comp_type not in bundle_types:
                bundle_types[comp_type] = 0
            bundle_types[comp_type] += 1

            # Check for missing assets
            if not bundle.load_main_template():
                missing_templates += 1
            if not bundle.load_examples():
                missing_examples += 1

        return {
            "bundles": {
                "total": len(bundles),
                "by_type": bundle_types,
                "missing_templates": missing_templates,
                "missing_examples": missing_examples,
            },
            "provider_dir": str(self.provider_dir),
            "config": {
                "provider_name": self.config.provider_name,
                "terraform_binary": self.config.terraform_binary,
            },
        }

    def _bundle_has_examples(self, bundle: PlatingBundle) -> bool:
        """Check if a bundle has examples."""
        try:
            examples = bundle.load_examples()
            return len(examples) > 0
        except Exception:
            return False


# 🍽️✨🎯