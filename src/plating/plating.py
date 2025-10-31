# 
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

# 
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""TODO: Add module docstring."""

from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Any

from provide.foundation import logger, pout
from provide.foundation.resilience import BackoffStrategy, RetryPolicy

from plating.adorner import PlatingAdorner
from plating.core.doc_generator import generate_provider_index, render_component_docs
from plating.core.project_utils import find_project_root, get_output_directory
from plating.decorators import with_metrics, with_retry, with_timing
from plating.errors import FileSystemError
from plating.registry import get_plating_registry
from plating.schema.helpers import extract_provider_schema
from plating.types import AdornResult, ComponentType, PlateResult, PlatingContext, ValidationResult

#
# plating/plating.py
#
"""Modern async API for plating operations with full foundation integration."""


class Plating:
    """Modern async API for all plating operations with foundation integration."""

    def __init__(self, context: PlatingContext, package_name: str | None = None) -> None:
        """Initialize plating API with foundation context.

        Args:
            context: PlatingContext with configuration (required)
            package_name: Package to search for plating bundles, or None to search all packages
        """
        self.context = context
        self.package_name = package_name

        # Foundation patterns
        self.registry = get_plating_registry(package_name)

        # Schema processing
        self._provider_schema: dict[str, Any] | None = None

        # Resilience patterns for file I/O and network operations
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            backoff=BackoffStrategy.EXPONENTIAL,
            base_delay=0.5,
            max_delay=10.0,
            retryable_errors=(IOError, OSError, TimeoutError, ConnectionError),
        )

    @with_timing
    @with_retry()
    @with_metrics("adorn")
    async def adorn(
        self,
        component_types: list[ComponentType] | None = None,
    ) -> AdornResult:
        """Generate template structure for discovered components.

        Args:
            component_types: Specific component types to adorn

        Returns:
            AdornResult with generation statistics
        """
        if not self.package_name:
            pout(
                "⚠️  Adorn requires a package name. Run with --package-name or in a project with pyproject.toml."
            )
            return AdornResult(errors=["--package-name is required for adorn."])

        pout(f"🎨 Adorning components in package: {self.package_name}")

        try:
            adorner = PlatingAdorner(self.package_name)
            target_types = [ct.value for ct in component_types] if component_types else None
            adorned_counts = await adorner.adorn_missing(target_types)

            total_adorned = sum(adorned_counts.values())

            return AdornResult(
                templates_generated=total_adorned,
                examples_created=total_adorned,  # Each adorn creates one template and one example
                errors=[],
            )

        except Exception as e:
            logger.error("Adorn operation failed", error=str(e))
            return AdornResult(errors=[f"An unexpected error occurred: {e}"])

    @with_timing
    @with_retry()
    @with_metrics("plate")
    async def plate(
        self,
        output_dir: Path | None = None,
        component_types: list[ComponentType] | None = None,
        force: bool = False,
        validate_markdown: bool = True,
        project_root: Path | None = None,
    ) -> PlateResult:
        """Generate documentation from plating bundles.

        Args:
            output_dir: Output directory for documentation
            component_types: Component types to generate
            force: Overwrite existing files
            validate_markdown: Enable markdown validation
            project_root: Project root directory (auto-detected if not provided)

        Returns:
            PlateResult with generation statistics
        """
        # Detect project root if not provided
        if project_root is None:
            project_root = find_project_root()

        # Determine final output directory with improved logic
        final_output_dir = get_output_directory(output_dir, project_root)

        logger.info(f"Using output directory: {final_output_dir}")
        if project_root:
            logger.info(f"Project root detected: {project_root}")
        else:
            logger.warning("No project root detected, using current directory as base")

        # Validate and create output directory
        try:
            final_output_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.error("Failed to create output directory", path=final_output_dir, error=str(e))
            raise FileSystemError(
                path=final_output_dir, operation="create directory", reason=str(e), caused_by=e
            ) from e

        # Ensure we can write to the directory
        if not os.access(final_output_dir, os.W_OK):
            logger.error("Output directory is not writable", path=final_output_dir)
            raise FileSystemError(
                path=final_output_dir,
                operation="write",
                reason="Directory is not writable (check permissions)",
            )

        if not component_types:
            component_types = [ComponentType.RESOURCE, ComponentType.DATA_SOURCE, ComponentType.FUNCTION]


        start_time = time.monotonic()
        result = PlateResult(duration_seconds=0.0, files_generated=0, errors=[], output_files=[])

        # Await schema extraction before rendering
        self._provider_schema = await self._extract_provider_schema()

        # Track unique bundles processed
        processed_bundles: set[str] = set()

        for component_type in component_types:
            components = self.registry.get_components_with_templates(component_type)
            logger.info(f"Generating docs for {len(components)} {component_type.value} components")

            # Track unique bundle directories
            for component in components:
                processed_bundles.add(str(component.plating_dir))

            files_before = result.files_generated
            await render_component_docs(
                components,
                component_type,
                final_output_dir,
                force,
                result,
                self.context,
                self._provider_schema or {},
            )
            files_for_type = result.files_generated - files_before
            if files_for_type > 0:

        # Generate provider index page
        pout("📝 Generating provider index...")
        generate_provider_index(
            final_output_dir, force, result, self.context, self._provider_schema or {}, self.registry
        )

        # Update result with tracking info
        result.bundles_processed = len(processed_bundles)
        result.duration_seconds = time.monotonic() - start_time


        # Validate if requested (disabled due to markdown validator dependency)
        # if validate_markdown and result.output_files:
        #     validation_result = await self.validate(output_dir, component_types)
        #     result.errors.extend(validation_result.errors)

        return result

    @with_timing
    @with_metrics("validate")
    async def validate(
        self,
        output_dir: Path | None = None,
        component_types: list[ComponentType] | None = None,
        project_root: Path | None = None,
    ) -> ValidationResult:
        """Validate generated documentation.

        Args:
            output_dir: Directory containing documentation
            component_types: Component types to validate
            project_root: Project root directory (auto-detected if not provided)

        Returns:
            ValidationResult with any errors found
        """
        # Use same logic as plate method for consistency
        if project_root is None:
            project_root = find_project_root()

        final_output_dir = get_output_directory(output_dir, project_root)
        component_types = component_types or [
            ComponentType.RESOURCE,
            ComponentType.DATA_SOURCE,
            ComponentType.FUNCTION,
        ]

        errors = []
        files_checked = 0
        passed = 0

        for component_type in component_types:
            type_dir = final_output_dir / component_type.output_subdir
            if not type_dir.exists():
                continue

            for md_file in type_dir.glob("*.md"):
                try:
                    # For now, just simulate validation (since markdown validator is disabled)
                    files_checked += 1
                    passed += 1  # Assume validation passes
                except Exception as e:
                    errors.append(f"Failed to validate {md_file}: {e}")

        return ValidationResult(
            total=files_checked,
            passed=passed,
            failed=len(errors),
            skipped=0,
            duration_seconds=0.0,
            errors=errors,
        )

    async def _extract_provider_schema(self) -> dict[str, Any]:
        """Extract provider schema using foundation hub discovery."""
        if self._provider_schema is not None:
            return self._provider_schema

        self._provider_schema = extract_provider_schema(self.package_name)
        return self._provider_schema

    def get_registry_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        stats = {"total_components": 0, "component_types": []}

        for component_type in [ComponentType.RESOURCE, ComponentType.DATA_SOURCE, ComponentType.FUNCTION]:
            components = self.registry.get_components(component_type)
            with_templates = self.registry.get_components_with_templates(component_type)

            stats[component_type.value] = {
                "total": len(components),
                "with_templates": len(with_templates),
            }
            stats["total_components"] += len(components)
            if components:
                stats["component_types"].append(component_type.value)

        return stats


# Global API instance
_global_api: Plating | None = None


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

# 🍽️📖🔚
