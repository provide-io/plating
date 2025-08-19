#!/usr/bin/env python3
#
# garnish/cli.py
#
"""CLI interface for documentation generation."""

from pathlib import Path

import click
from pyvider.telemetry import logger

from garnish.errors import GarnishError, handle_error
from garnish.plater import generate_docs
from garnish.dresser import dress_components


@click.group()
def main() -> None:
    """Garnish - Documentation generator for Terraform/OpenTofu providers."""
    pass


@main.command("dress")
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function"]),
    multiple=True,
    help="Filter by component type (can be used multiple times).",
)
def dress_command(component_type: tuple[str, ...]) -> None:
    """Dress components with missing .garnish directories."""
    try:
        print("👗 Dressing components with .garnish directories...")

        component_types = list(component_type) if component_type else None
        results = dress_components(component_types)

        total = sum(results.values())
        if total > 0:
            print(f"✅ Dressed {total} components:")
            for comp_type, count in results.items():
                if count > 0:
                    print(f"  - {count} {comp_type}{'s' if count != 1 else ''}")
        else:
            print("ℹ️ No missing .garnish directories found")

        click.secho("✅ Dressing completed successfully!", fg="green")

    except GarnishError as e:
        # Our custom errors have good messages
        click.secho(f"❌ {e}", fg="red", err=True)
        logger.error(f"Dressing failed: {e}")
        raise click.Abort() from e
    except Exception as e:
        import traceback
        
        error_msg = handle_error(e, logger)
        click.secho(f"❌ Dressing failed: {error_msg}", fg="red", err=True)
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
def plate_command(
    output_dir: str, provider_dir: str, component_type: tuple[str, ...], force: bool
) -> None:
    """Plate all garnish bundles into final documentation."""
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

        print("🍽️ Plating documentation...")
        generate_docs(output_dir=output_dir)
        click.secho("✅ Documentation plated successfully!", fg="green")

    except GarnishError as e:
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
        ".garnish",
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
def render_command(
    output_dir: str, provider_dir: str, component_type: tuple[str, ...], force: bool
) -> None:
    """(Deprecated) Alias for 'plate' command. Use 'garnish plate' instead."""
    click.echo("Note: 'render' is deprecated. Please use 'plate' instead.")
    # Call the plate command directly
    ctx = click.get_current_context()
    ctx.invoke(plate_command, output_dir=output_dir, provider_dir=provider_dir, 
               component_type=component_type, force=force)


@main.command("test")
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
    help="Number of tests to run in parallel.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False),
    default=".garnish-tests",
    help="Temporary directory for test execution.",
)
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False),
    help="File to write test results to.",
)
@click.option(
    "--output-format",
    type=click.Choice(["json", "markdown", "html"]),
    default="json",
    help="Format for test results output.",
)
def test_command(
    component_type: tuple[str, ...],
    parallel: int,
    output_dir: str,
    output_file: str | None,
    output_format: str,
) -> None:
    """Run all garnish example files as Terraform tests."""
    try:
        # Import here to avoid circular imports
        from .test_runner import run_garnish_tests

        component_types = list(component_type) if component_type else None
        results = run_garnish_tests(
            component_types=component_types,
            parallel=parallel,
            output_dir=Path(output_dir),
            output_file=Path(output_file) if output_file else None,
            output_format=output_format,
        )

        # Display results
        total_tests = results["total"]
        passed = results["passed"]
        failed = results["failed"]
        warnings = results.get("warnings", 0)
        skipped = results.get("skipped", 0)

        if total_tests == 0:
            print("ℹ️ No garnish examples found to test")
            return

        print("\n📊 Test Results:")
        print(f"  Total: {total_tests}")
        print(f"  ✅ Passed: {passed}")
        if failed > 0:
            print(f"  ❌ Failed: {failed}")
        if warnings > 0:
            print(f"  ⚠️  Warnings: {warnings}")
        if skipped > 0:
            print(f"  ⏭️  Skipped: {skipped}")

        # Show warnings if any
        if warnings > 0:
            print("\n⚠️  Tests with warnings:")
            for test_name, details in results.get("test_details", {}).items():
                if details.get("warnings"):
                    print(f"  - {test_name} ({len(details['warnings'])} warnings)")
                    for warning in details["warnings"][:2]:  # Show first 2 warnings
                        print(f"    • {warning['message']}")
                    if len(details["warnings"]) > 2:
                        print(f"    • ... and {len(details['warnings']) - 2} more")

        if failed > 0:
            print("\n❌ Failed tests:")
            for test_name, error in results["failures"].items():
                print(f"  - {test_name}: {error}")
            click.secho("\n❌ Some tests failed!", fg="red", err=True)
            raise click.Abort()
        else:
            click.secho("\n✅ All tests passed!", fg="green")

    except GarnishError as e:
        # Our custom errors have good messages
        click.secho(f"❌ {e}", fg="red", err=True)
        logger.error(f"Test execution failed: {e}")
        raise click.Abort() from e
    except Exception as e:
        import traceback
        
        error_msg = handle_error(e, logger)
        click.secho(f"❌ Test execution failed: {error_msg}", fg="red", err=True)
        click.secho(f"Stack trace:\n{traceback.format_exc()}", fg="red", err=True)
        raise click.Abort() from e


if __name__ == "__main__":
    main()


# 🥄📚🪄
