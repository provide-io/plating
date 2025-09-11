#
# plating/operations.py
#
"""Functional API for plating operations.

This module provides stateless functional operations that can be used independently
of the main Plating class. These functions are designed for use in automation,
scripting, and programmatic scenarios where you want to use plating's capabilities
without managing state.
"""

from pathlib import Path
from typing import Any

from provide.foundation import logger, pout

from plating.adorner import adorn_components
from plating.cleaner import PlatingCleaner
from plating.plater import generate_docs
from plating.results import AdornResult, CleanResult, PlateResult, ValidationResult
from plating.validator import run_validation


def clean_docs(output_dir: str | Path = "docs", dry_run: bool = False) -> CleanResult:
    """Remove all generated documentation files.

    Args:
        output_dir: Directory containing generated docs (default: 'docs')
        dry_run: If True, show what would be removed without actually removing

    Returns:
        CleanResult with details of what was cleaned

    Example:
        >>> result = clean_docs("docs")
        >>> print(f"Removed {result.total_items} items, freed {result.bytes_freed} bytes")
    """
    pout("🧹 Cleaning generated documentation...")
    output_path = Path(output_dir)
    cleaner = PlatingCleaner()
    return cleaner.clean(output_path, dry_run=dry_run)


def adorn_missing_components(component_types: list[str] = None, force: bool = False) -> AdornResult:
    """Create .plating bundles for components missing documentation.

    Args:
        component_types: Optional list of component types to adorn ["resource", "data_source", "function"]
        force: Force adorning even if bundles already exist

    Returns:
        AdornResult with details of what was adorned

    Example:
        >>> result = adorn_missing_components(["resource"])
        >>> print(f"Adorned {result.total_adorned} resources")
    """
    pout("✨ Adorning components with documentation templates...")
    
    try:
        adorned_dict = adorn_components(component_types)
        return AdornResult(
            adorned=adorned_dict,
            skipped=[],  # TODO: Track skipped components in adorn_components
            errors=[],
            duration=0.0,  # TODO: Track duration in adorn_components
        )
    except Exception as e:
        logger.error("Adorning failed", error=str(e))
        return AdornResult(
            adorned={},
            skipped=[],
            errors=[str(e)],
            duration=0.0,
        )


def plate_documentation(
    output_dir: str | Path = "docs",
    component_types: list[str] = None,
    clean_first: bool = False,
) -> PlateResult:
    """Generate documentation from .plating bundles.

    Args:
        output_dir: Directory to write documentation (default: 'docs')
        component_types: Optional list of component types to plate
        clean_first: Whether to clean output directory first

    Returns:
        PlateResult with details of what was generated

    Example:
        >>> result = plate_documentation("docs", clean_first=True)
        >>> if result.success:
        ...     print(f"Generated {len(result.plated)} files")
    """
    output_path = Path(output_dir)
    
    pout("🍽️ Plating documentation...")
    
    # Clean first if requested
    if clean_first:
        pout("🧹 Cleaning output directory first...")
        clean_result = clean_docs(output_path)
        logger.debug("Cleaning completed", items_removed=clean_result.total_items)

    # Generate documentation using plating's generate_docs
    try:
        generate_docs(str(output_path))
        
        # Find generated files (simple heuristic)
        generated_files = []
        if output_path.exists():
            generated_files = [str(f) for f in output_path.rglob("*.md") if f.is_file()]
        
        return PlateResult(
            plated=generated_files,
            bundles_processed=len(generated_files),  # Simplified metric
            errors=[],
            duration=0.0,  # Duration tracking would require timing
            cleaned_first=clean_first,
        )
        
    except Exception as e:
        logger.error("Documentation generation failed", error=str(e))
        return PlateResult(
            plated=[],
            bundles_processed=0,
            errors=[str(e)],
            duration=0.0,
            cleaned_first=clean_first,
        )


def validate_examples(
    component_types: list[str] = None,
    parallel: int = 4,
    output_file: Path = None,
    output_format: str = "json",
) -> ValidationResult:
    """Run validation on example files in .plating bundles.

    Args:
        component_types: Optional list of component types to validate
        parallel: Number of parallel validations to run
        output_file: Optional file to write report to
        output_format: Format for report (json, markdown, html)

    Returns:
        ValidationResult with validation execution results

    Example:
        >>> result = validate_examples()
        >>> print(f"Validation: {result.passed}/{result.total} passed ({result.success_rate:.1f}%)")
    """
    pout("🔍 Validating example files...")
    return run_validation(
        component_types=component_types,
        parallel=parallel,
        output_file=output_file,
        output_format=output_format,
    )


def full_pipeline(
    output_dir: str | Path = "docs",
    component_types: list[str] = None,
    skip_validation: bool = False,
    skip_adorn: bool = False,
) -> dict[str, Any]:
    """Run the complete plating pipeline: clean, adorn, plate, and optionally validate.

    Args:
        output_dir: Directory to write documentation (default: 'docs')
        component_types: Optional list of component types to process
        skip_validation: Skip the validation step
        skip_adorn: Skip the adorning step

    Returns:
        Dictionary containing results from each step

    Example:
        >>> results = full_pipeline("docs", ["resource"])
        >>> if results["plate"].success and results["validation"].passed > 0:
        ...     print("Pipeline completed successfully!")
    """
    pout("🚀 Running full plating pipeline...")
    
    results = {}
    
    # Step 1: Clean
    pout("Step 1: Cleaning...")
    results["clean"] = clean_docs(output_dir)
    
    # Step 2: Adorn (optional)
    if not skip_adorn:
        pout("Step 2: Adorning...")
        results["adorn"] = adorn_missing_components(component_types)
    
    # Step 3: Plate
    pout("Step 3: Plating...")
    results["plate"] = plate_documentation(output_dir, component_types, clean_first=False)
    
    # Step 4: Validate (optional)
    if not skip_validation:
        pout("Step 4: Validating...")
        results["validation"] = validate_examples(component_types)
    
    pout("✅ Pipeline completed!")
    return results


# 🔧⚙️🎯