#!/usr/bin/env python3
#
# plating/cli.py
#
"""CLI interface for documentation generation."""

from pathlib import Path

import click
from provide.foundation import logger, pout

from plating.errors import PlatingError, handle_error
from plating.operations import adorn_missing_components, clean_docs, full_pipeline, plate_documentation, validate_examples


@click.group()
def main() -> None:
    """Plating - Documentation generator for Terraform/OpenTofu providers."""
    pass


@main.command("adorn")
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function"]),
    multiple=True,
    help="Filter by component type (can be used multiple times).",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force adorning even if bundles already exist.",
)
def adorn_command(component_type: tuple[str, ...], force: bool) -> None:
    """Adorn components with missing .plating directories."""
    try:
        component_types = list(component_type) if component_type else None
        result = adorn_missing_components(component_types, force)

        if result.total_adorned > 0:
            pout(f"✅ Adorned {result.total_adorned} components")
            for comp_type, bundles in result.adorned.items():
                if bundles:
                    pout(f"  - {len(bundles)} {comp_type}{'s' if len(bundles) != 1 else ''}")
        else:
            pout("ℹ️ No missing .plating directories found")

        if result.errors:
            for error in result.errors:
                pout(f"❌ Error: {error}")

        click.secho("✅ Adorning completed successfully!", fg="green")

    except PlatingError as e:
        # Our custom errors have good messages
        click.secho(f"❌ {e}", fg="red", err=True)
        logger.error(f"Adorning failed: {e}")
        raise click.Abort() from e
    except Exception as e:
        import traceback

        error_msg = handle_error(e, logger)
        click.secho(f"❌ Adorning failed: {error_msg}", fg="red", err=True)
        click.secho(f"Stack trace:\n{traceback.format_exc()}", fg="red", err=True)
        raise click.Abort() from e


@main.command("plate")
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, resolve_path=True),
    default="docs",
    help="Output directory for plated documentation.",
)
@click.option(
    "--provider-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Path to the provider directory.",
)
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function"]),
    multiple=True,
    help="Filter by component type (can be used multiple times).",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force documentation generation even if not in a provider directory.",
)
def plate_command(output_dir: str, provider_dir: str, component_type: tuple[str, ...], force: bool) -> None:
    """Plate all plating bundles into final documentation."""
    try:
        provider_path = Path(provider_dir)

        # Validate that we're in a provider directory unless --force is used
        if not force and not _is_provider_directory(provider_path):
            click.secho(
                "❌ This does not appear to be a provider directory. "
                "Expected to find a pyproject.toml with provider configuration "
                "or templates directory. Use --force to override.",
                fg="red",
                err=True,
            )
            raise click.Abort()

        component_types = list(component_type) if component_type else None
        result = plate_documentation(output_dir, component_types, clean_first=False)
        
        if result.success:
            pout(f"✅ Generated {len(result.plated)} documentation files")
            click.secho("✅ Documentation plated successfully!", fg="green")
        else:
            for error in result.errors:
                pout(f"❌ Error: {error}")
            raise PlatingError("Documentation generation failed")

    except PlatingError as e:
        # Our custom errors have good messages
        click.secho(f"❌ {e}", fg="red", err=True)
        logger.error(f"Documentation plating failed: {e}")
        raise click.Abort() from e
    except Exception as e:
        import traceback

        error_msg = handle_error(e, logger)
        click.secho(f"❌ Documentation plating failed: {error_msg}", fg="red", err=True)
        click.secho(f"Stack trace:\n{traceback.format_exc()}", fg="red", err=True)
        raise click.Abort() from e


def _is_provider_directory(path: Path) -> bool:
    """Check if the given path appears to be a provider directory."""
    # Check for pyproject.toml with terraform-provider or pyvider in name
    pyproject_toml = path / "pyproject.toml"
    if pyproject_toml.exists():
        try:
            import tomllib

            with open(pyproject_toml, "rb") as f:
                data = tomllib.load(f)

            # Check project name for provider indicators
            project_name = data.get("project", {}).get("name", "")
            if "terraform-provider" in project_name or "pyvider" in project_name:
                return True

            # Check for pyvider configuration
            if "tool" in data and "pyvider" in data["tool"]:
                return True

        except Exception:
            pass

    # Check for templates directory (common in provider repos)
    if (path / "templates").exists():
        return True

    # Check for provider-specific files
    provider_indicators = [
        "terraform-registry-manifest.json",
        "pyvider.toml",
        ".plating",
    ]

    for indicator in provider_indicators:
        if (path / indicator).exists():
            return True

    return False


# Add 'render' as an alias for 'plate' for backward compatibility
@main.command("render", hidden=True)  # Hidden from help but still works
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False),
    default="docs",
    help="Output directory for plated documentation.",
)
@click.option(
    "--provider-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default=".",
    help="Path to the provider directory.",
)
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function"]),
    multiple=True,
    help="Filter by component type (can be used multiple times).",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force documentation generation even if not in a provider directory.",
)
def render_command(output_dir: str, provider_dir: str, component_type: tuple[str, ...], force: bool) -> None:
    """(Deprecated) Alias for 'plate' command. Use 'garnish plate' instead."""
    click.echo("Note: 'render' is deprecated. Please use 'plate' instead.")
    # Call the plate command directly
    ctx = click.get_current_context()
    ctx.invoke(
        plate_command,
        output_dir=output_dir,
        provider_dir=provider_dir,
        component_type=component_type,
        force=force,
    )


@main.command("clean")
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False),
    default="docs",
    help="Directory containing generated documentation to clean.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be removed without actually removing it.",
)
def clean_command(output_dir: str, dry_run: bool) -> None:
    """Clean all generated documentation files."""
    try:
        result = clean_docs(output_dir, dry_run)
        
        if dry_run:
            pout(f"🔍 Would remove {result.total_items} items ({result.bytes_freed} bytes)")
            for item in result.removed_items[:10]:  # Show first 10 items
                pout(f"  - {item}")
            if len(result.removed_items) > 10:
                pout(f"  ... and {len(result.removed_items) - 10} more items")
        else:
            pout(f"🧹 Removed {result.total_items} items, freed {result.bytes_freed} bytes")
        
        click.secho("✅ Cleaning completed successfully!", fg="green")
        
    except PlatingError as e:
        click.secho(f"❌ {e}", fg="red", err=True)
        logger.error(f"Cleaning failed: {e}")
        raise click.Abort() from e
    except Exception as e:
        import traceback
        
        error_msg = handle_error(e, logger)
        click.secho(f"❌ Cleaning failed: {error_msg}", fg="red", err=True)
        click.secho(f"Stack trace:\n{traceback.format_exc()}", fg="red", err=True)
        raise click.Abort() from e


@main.command("validate")
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function"]),
    multiple=True,
    help="Filter by component type (can be used multiple times).",
)
@click.option(
    "--parallel",
    type=int,
    default=4,
    help="Number of validations to run in parallel.",
)
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False),
    help="File to write validation results to.",
)
@click.option(
    "--output-format",
    type=click.Choice(["json", "markdown", "html"]),
    default="json",
    help="Format for validation results output.",
)
def validate_command(
    component_type: tuple[str, ...],
    parallel: int,
    output_file: str | None,
    output_format: str,
) -> None:
    """Validate all plating example files."""
    try:
        component_types = list(component_type) if component_type else None
        result = validate_examples(
            component_types=component_types,
            parallel=parallel,
            output_file=Path(output_file) if output_file else None,
            output_format=output_format,
        )

        # Display results
        if result.total == 0:
            pout("ℹ️ No plating examples found to validate")
            return

        pout("\n📊 Validation Results:")
        pout(f"  Total: {result.total}")
        pout(f"  ✅ Passed: {result.passed}")
        if result.failed > 0:
            pout(f"  ❌ Failed: {result.failed}")
        if result.warnings > 0:
            pout(f"  ⚠️  Warnings: {result.warnings}")
        if result.skipped > 0:
            pout(f"  ⏭️  Skipped: {result.skipped}")

        # Show warnings if any
        if result.warnings > 0:
            pout("\n⚠️  Validations with warnings:")
            for validation_name, details in result.test_details.items():
                if details.get("warnings"):
                    pout(f"  - {validation_name} ({len(details['warnings'])} warnings)")
                    for warning in details["warnings"][:2]:  # Show first 2 warnings
                        pout(f"    • {warning['message']}")
                    if len(details["warnings"]) > 2:
                        pout(f"    • ... and {len(details['warnings']) - 2} more")

        if result.failed > 0:
            pout("\n❌ Failed validations:")
            for validation_name, error in result.failures.items():
                pout(f"  - {validation_name}: {error}")
            click.secho("\n❌ Some validations failed!", fg="red", err=True)
            raise click.Abort()
        else:
            click.secho("\n✅ All validations passed!", fg="green")

    except PlatingError as e:
        click.secho(f"❌ {e}", fg="red", err=True)
        logger.error(f"Validation execution failed: {e}")
        raise click.Abort() from e
    except Exception as e:
        import traceback

        error_msg = handle_error(e, logger)
        click.secho(f"❌ Validation execution failed: {error_msg}", fg="red", err=True)
        click.secho(f"Stack trace:\n{traceback.format_exc()}", fg="red", err=True)
        raise click.Abort() from e


@main.command("test", hidden=True)  # Hidden from help but still works
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function"]),
    multiple=True,
    help="Filter by component type (can be used multiple times).",
)
@click.option(
    "--parallel",
    type=int,
    default=4,
    help="Number of validations to run in parallel.",
)
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False),
    help="File to write validation results to.",
)
@click.option(
    "--output-format",
    type=click.Choice(["json", "markdown", "html"]),
    default="json",
    help="Format for validation results output.",
)
def test_command(
    component_type: tuple[str, ...],
    parallel: int,
    output_file: str | None,
    output_format: str,
) -> None:
    """(Deprecated) Alias for 'validate' command. Use 'plating validate' instead."""
    click.echo("Note: 'test' is deprecated. Please use 'validate' instead.")
    # Call the validate command directly
    ctx = click.get_current_context()
    ctx.invoke(
        validate_command,
        component_type=component_type,
        parallel=parallel,
        output_file=output_file,
        output_format=output_format,
    )


@main.command("pipeline")
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False),
    default="docs",
    help="Output directory for documentation.",
)
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function"]),
    multiple=True,
    help="Filter by component type (can be used multiple times).",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    default=False,
    help="Skip the validation step.",
)
@click.option(
    "--skip-adorn",
    is_flag=True,
    default=False,
    help="Skip the adorning step.",
)
def pipeline_command(
    output_dir: str,
    component_type: tuple[str, ...],
    skip_validation: bool,
    skip_adorn: bool,
) -> None:
    """Run the complete plating pipeline: clean, adorn, plate, and validate."""
    try:
        component_types = list(component_type) if component_type else None
        results = full_pipeline(
            output_dir=output_dir,
            component_types=component_types,
            skip_validation=skip_validation,
            skip_adorn=skip_adorn,
        )
        
        # Display pipeline results
        pout("\n📊 Pipeline Results:")
        
        if "clean" in results:
            clean = results["clean"]
            pout(f"🧹 Cleaned: {clean.total_items} items removed")
        
        if "adorn" in results:
            adorn = results["adorn"]
            pout(f"✨ Adorned: {adorn.total_adorned} components")
        
        if "plate" in results:
            plate = results["plate"]
            if plate.success:
                pout(f"🍽️ Plated: {len(plate.plated)} documentation files")
            else:
                pout("❌ Plating failed")
                
        if "validation" in results:
            validation = results["validation"]
            pout(f"🔍 Validation: {validation.passed}/{validation.total} passed")
            
            if validation.failed > 0:
                click.secho(f"\n❌ Pipeline completed with {validation.failed} validation failures!", fg="red", err=True)
                raise click.Abort()
        
        click.secho("\n✅ Pipeline completed successfully!", fg="green")
        
    except PlatingError as e:
        click.secho(f"❌ {e}", fg="red", err=True)
        logger.error(f"Pipeline execution failed: {e}")
        raise click.Abort() from e
    except Exception as e:
        import traceback

        error_msg = handle_error(e, logger)
        click.secho(f"❌ Pipeline execution failed: {error_msg}", fg="red", err=True)
        click.secho(f"Stack trace:\n{traceback.format_exc()}", fg="red", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    main()


# 🥄📚🪄
