#!/usr/bin/env python3
#
# plating/cli.py
#
"""Modern CLI interface using the async Plating API."""

import asyncio
from pathlib import Path

import click
from provide.foundation import pout, perr

from .api import Plating
from .types import ComponentType, PlatingContext


@click.group()
def main() -> None:
    """Plating - Modern async documentation generator with foundation integration."""
    pass


@main.command("adorn")
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function", "provider"]),
    multiple=True,
    help="Component types to adorn (can be used multiple times).",
)
@click.option(
    "--provider-name",
    type=str,
    help="Provider name for context.",
)
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def adorn_command(
    component_type: tuple[str, ...], 
    provider_name: str | None,
    package_name: str
) -> None:
    """Create missing documentation templates and examples."""
    async def run():
        context = PlatingContext(provider_name=provider_name or "default")
        api = Plating(context, package_name)
        
        # Convert string types to ComponentType enums
        types = [ComponentType(t) for t in component_type] if component_type else list(ComponentType)
        
        pout(f"🎨 Adorning {len(types)} component types...")
        result = await api.adorn(types)
        
        if result.success:
            pout(f"✅ Generated {result.templates_generated} templates")
            pout(f"📦 Processed {result.components_processed} components")
        else:
            perr("❌ Adorn operation failed:")
            for error in result.errors:
                perr(f"  • {error}")

    asyncio.run(run())


@main.command("plate")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("docs"),
    help="Output directory for documentation.",
)
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function", "provider"]),
    multiple=True,
    help="Component types to plate (can be used multiple times).",
)
@click.option(
    "--provider-name",
    type=str,
    help="Provider name for context.",
)
@click.option(
    "--package-name",
    type=str, 
    default="pyvider.components",
    help="Package to search for components.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite existing files.",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Enable/disable markdown validation.",
)
def plate_command(
    output_dir: Path,
    component_type: tuple[str, ...],
    provider_name: str | None,
    package_name: str,
    force: bool,
    validate: bool
) -> None:
    """Generate documentation from plating bundles."""
    async def run():
        context = PlatingContext(provider_name=provider_name or "default")
        api = Plating(context, package_name)
        
        # Convert string types to ComponentType enums
        types = [ComponentType(t) for t in component_type] if component_type else None
        
        pout(f"🍽️ Plating documentation to {output_dir}...")
        result = await api.plate(output_dir, types, force, validate)
        
        if result.success:
            pout(f"✅ Generated {result.files_generated} files in {result.duration_seconds:.2f}s")
            pout(f"📦 Processed {result.bundles_processed} bundles")
            if result.output_files:
                pout("📄 Generated files:")
                for file in result.output_files[:10]:  # Show first 10
                    pout(f"  • {file}")
                if len(result.output_files) > 10:
                    pout(f"  ... and {len(result.output_files) - 10} more")
        else:
            perr("❌ Plate operation failed:")
            for error in result.errors:
                perr(f"  • {error}")

    asyncio.run(run())


@main.command("validate")
@click.option(
    "--output-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("docs"),
    help="Directory containing documentation to validate.",
)
@click.option(
    "--component-type",
    type=click.Choice(["resource", "data_source", "function", "provider"]),
    multiple=True,
    help="Component types to validate (can be used multiple times).",
)
@click.option(
    "--provider-name",
    type=str,
    help="Provider name for context.",
)
@click.option(
    "--package-name",
    type=str,
    default="pyvider.components", 
    help="Package to search for components.",
)
def validate_command(
    output_dir: Path,
    component_type: tuple[str, ...],
    provider_name: str | None,
    package_name: str
) -> None:
    """Validate generated documentation."""
    async def run():
        context = PlatingContext(provider_name=provider_name or "default")
        api = Plating(context, package_name)
        
        # Convert string types to ComponentType enums
        types = [ComponentType(t) for t in component_type] if component_type else None
        
        pout(f"🔍 Validating documentation in {output_dir}...")
        result = await api.validate(output_dir, types)
        
        pout(f"📊 Validation results:")
        pout(f"  • Total files: {result.total}")
        pout(f"  • Passed: {result.passed}")
        pout(f"  • Failed: {result.failed}")
        pout(f"  • Duration: {result.duration_seconds:.2f}s")
        
        if result.success:
            pout("✅ All validations passed")
        else:
            perr("❌ Validation failed:")
            if result.lint_errors:
                perr("  Markdown linting errors:")
                for error in result.lint_errors[:5]:  # Show first 5
                    perr(f"    • {error}")
                if len(result.lint_errors) > 5:
                    perr(f"    ... and {len(result.lint_errors) - 5} more")
            
            if result.errors:
                perr("  General errors:")
                for error in result.errors:
                    perr(f"    • {error}")

    asyncio.run(run())


@main.command("info")
@click.option(
    "--provider-name",
    type=str,
    help="Provider name for context.",
)
@click.option(
    "--package-name",
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def info_command(provider_name: str | None, package_name: str) -> None:
    """Show registry information and statistics."""
    async def run():
        context = PlatingContext(provider_name=provider_name or "default")
        api = Plating(context, package_name)
        
        stats = api.get_registry_stats()
        
        pout("📊 Registry Statistics:")
        pout(f"  • Total components: {stats.get('total_components', 0)}")
        pout(f"  • Component types: {', '.join(stats.get('component_types', []))}")
        
        for comp_type in stats.get('component_types', []):
            count = stats.get(f"{comp_type}_count", 0)
            with_templates = stats.get(f"{comp_type}_with_templates", 0)
            with_examples = stats.get(f"{comp_type}_with_examples", 0)
            
            pout(f"  • {comp_type}: {count} total, {with_templates} with templates, {with_examples} with examples")

    asyncio.run(run())


# ComponentSet commands
@main.group("sets")
def sets_group() -> None:
    """ComponentSet management commands."""
    pass


@sets_group.command("list")
@click.option(
    "--tag",
    type=str,
    help="Filter by tag."
)
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def list_sets_command(tag: str | None, package_name: str) -> None:
    """List all registered ComponentSets."""
    async def run():
        context = PlatingContext(provider_name="default")
        api = Plating(context, package_name)
        
        component_sets = api.get_component_sets(tag=tag)
        
        if not component_sets:
            if tag:
                pout(f"No ComponentSets found with tag '{tag}'")
            else:
                pout("No ComponentSets found")
            return
        
        pout(f"Found {len(component_sets)} ComponentSet(s):")
        for comp_set in component_sets:
            tags_str = ", ".join(sorted(comp_set.tags)) if comp_set.tags else "none"
            domains_str = ", ".join(sorted(comp_set.get_domains())) if comp_set.get_domains() else "none"
            
            pout(f"\n📦 {comp_set.name} (v{comp_set.version})")
            pout(f"   Description: {comp_set.description or 'No description'}")
            pout(f"   Components: {comp_set.total_component_count()}")
            pout(f"   Domains: {domains_str}")
            pout(f"   Tags: {tags_str}")
    
    asyncio.run(run())


@sets_group.command("create")
@click.argument("name")
@click.option(
    "--description",
    type=str,
    help="Description of the ComponentSet."
)
@click.option(
    "--tag",
    type=str,
    multiple=True,
    help="Tags for the ComponentSet (can be used multiple times)."
)
@click.option(
    "--terraform",
    type=str,
    multiple=True,
    help="Terraform component names to include (can be used multiple times)."
)
@click.option(
    "--kubernetes",
    type=str,
    multiple=True,
    help="Kubernetes component names to include (can be used multiple times)."
)
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def create_set_command(
    name: str,
    description: str | None,
    tag: tuple[str, ...],
    terraform: tuple[str, ...],
    kubernetes: tuple[str, ...],
    package_name: str
) -> None:
    """Create a ComponentSet from existing registered components."""
    async def run():
        context = PlatingContext(provider_name="default")
        api = Plating(context, package_name)
        
        # Build component filters
        component_filters = {}
        if terraform:
            component_filters["terraform"] = list(terraform)
        if kubernetes:
            component_filters["kubernetes"] = list(kubernetes)
        
        if not component_filters:
            perr("Error: Must specify at least one component domain (--terraform, --kubernetes)")
            return
        
        try:
            component_set = api.create_component_set_from_components(
                name=name,
                description=description or "",
                component_filters=component_filters,
                tags=set(tag) if tag else None
            )
            
            pout(f"✅ Created ComponentSet '{component_set.name}'")
            pout(f"   Components: {component_set.total_component_count()}")
            pout(f"   Domains: {', '.join(component_set.get_domains())}")
            
        except Exception as e:
            perr(f"Error creating ComponentSet: {e}")
    
    asyncio.run(run())


@sets_group.command("info")
@click.argument("name")
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def info_set_command(name: str, package_name: str) -> None:
    """Show detailed information about a ComponentSet."""
    async def run():
        context = PlatingContext(provider_name="default")
        api = Plating(context, package_name)
        
        registry = api.registry
        component_set = registry.get_set(name)
        
        if not component_set:
            perr(f"ComponentSet '{name}' not found")
            return
        
        pout(f"📦 ComponentSet: {component_set.name}")
        pout(f"Version: {component_set.version}")
        pout(f"Description: {component_set.description or 'No description'}")
        pout(f"Total Components: {component_set.total_component_count()}")
        
        if component_set.tags:
            pout(f"Tags: {', '.join(sorted(component_set.tags))}")
        
        if component_set.metadata:
            pout("\nMetadata:")
            for key, value in component_set.metadata.items():
                pout(f"  {key}: {value}")
        
        pout("\nComponents by Domain:")
        for domain in sorted(component_set.get_domains()):
            components = component_set.filter_by_domain(domain)
            pout(f"  {domain} ({len(components)}):")
            for comp in sorted(components, key=lambda c: (c.component_type, c.name)):
                pout(f"    - {comp}")
    
    asyncio.run(run())


@sets_group.command("adorn")
@click.argument("name")
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def adorn_set_command(name: str, package_name: str) -> None:
    """Create missing templates for all components in a ComponentSet."""
    async def run():
        context = PlatingContext(provider_name="default")
        api = Plating(context, package_name)
        
        try:
            result = await api.adorn_set(name)
            
            if result.success:
                pout(f"✅ Adorned ComponentSet '{name}'")
                pout(f"   Components processed: {result.components_processed}")
                pout(f"   Templates generated: {result.templates_generated}")
            else:
                perr(f"❌ Failed to adorn ComponentSet '{name}'")
                for error in result.errors:
                    perr(f"   Error: {error}")
                    
        except ValueError as e:
            perr(f"Error: {e}")
        except Exception as e:
            perr(f"Unexpected error: {e}")
    
    asyncio.run(run())


@sets_group.command("plate")
@click.argument("name")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("docs"),
    help="Output directory for generated documentation."
)
@click.option(
    "--domain",
    type=str,
    help="Specific domain to generate docs for (default: all domains)."
)
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite existing files."
)
@click.option(
    "--no-validate",
    is_flag=True,
    help="Skip markdown validation."
)
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def plate_set_command(
    name: str,
    output_dir: Path,
    domain: str | None,
    force: bool,
    no_validate: bool,
    package_name: str
) -> None:
    """Generate documentation for all components in a ComponentSet."""
    async def run():
        context = PlatingContext(provider_name="default")
        api = Plating(context, package_name)
        
        try:
            result = await api.plate_set(
                component_set_name=name,
                output_dir=output_dir,
                domain=domain,
                force=force,
                validate_markdown=not no_validate
            )
            
            if result.success:
                pout(f"✅ Generated docs for ComponentSet '{name}'")
                pout(f"   Bundles processed: {result.bundles_processed}")
                pout(f"   Files generated: {result.files_generated}")
                pout(f"   Duration: {result.duration_seconds:.2f}s")
                
                if result.output_files:
                    pout(f"   Output directory: {output_dir}")
            else:
                perr(f"❌ Failed to generate docs for ComponentSet '{name}'")
                for error in result.errors:
                    perr(f"   Error: {error}")
                    
        except ValueError as e:
            perr(f"Error: {e}")
        except Exception as e:
            perr(f"Unexpected error: {e}")
    
    asyncio.run(run())


@sets_group.command("validate")
@click.argument("name")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("docs"),
    help="Directory containing documentation to validate."
)
@click.option(
    "--domain",
    type=str,
    help="Specific domain to validate (default: all domains)."
)
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def validate_set_command(
    name: str,
    output_dir: Path,
    domain: str | None,
    package_name: str
) -> None:
    """Validate generated documentation for a ComponentSet."""
    async def run():
        context = PlatingContext(provider_name="default")
        api = Plating(context, package_name)
        
        try:
            result = await api.validate_set(
                component_set_name=name,
                output_dir=output_dir,
                domain=domain
            )
            
            if result.success:
                pout(f"✅ Validation passed for ComponentSet '{name}'")
                pout(f"   Files checked: {result.total}")
                pout(f"   Duration: {result.duration_seconds:.2f}s")
            else:
                perr(f"❌ Validation failed for ComponentSet '{name}'")
                pout(f"   Files checked: {result.total}")
                pout(f"   Failed: {result.failed}")
                
                for error in result.errors + result.lint_errors:
                    perr(f"   Error: {error}")
                    
        except ValueError as e:
            perr(f"Error: {e}")
        except Exception as e:
            perr(f"Unexpected error: {e}")
    
    asyncio.run(run())


@sets_group.command("generate-all")
@click.argument("name")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("docs"),
    help="Base output directory."
)
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite existing files."
)
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def generate_all_domains_command(
    name: str,
    output_dir: Path,
    force: bool,
    package_name: str
) -> None:
    """Generate documentation for all domains in a ComponentSet."""
    async def run():
        context = PlatingContext(provider_name="default")
        api = Plating(context, package_name)
        
        try:
            results = await api.generate_all_domains(
                component_set_name=name,
                output_dir=output_dir,
                force=force
            )
            
            total_files = 0
            total_errors = 0
            
            pout(f"📄 Generated docs for ComponentSet '{name}' across all domains:")
            
            for domain, result in results.items():
                if result.success:
                    pout(f"   ✅ {domain}: {result.files_generated} files")
                    total_files += result.files_generated
                else:
                    pout(f"   ❌ {domain}: {len(result.errors)} errors")
                    total_errors += len(result.errors)
                    for error in result.errors:
                        perr(f"      Error: {error}")
            
            pout(f"\nSummary:")
            pout(f"   Total files generated: {total_files}")
            pout(f"   Total errors: {total_errors}")
            pout(f"   Output directory: {output_dir}")
                    
        except ValueError as e:
            perr(f"Error: {e}")
        except Exception as e:
            perr(f"Unexpected error: {e}")
    
    asyncio.run(run())


@sets_group.command("remove")
@click.argument("name")
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def remove_set_command(name: str, package_name: str) -> None:
    """Remove a ComponentSet from the registry."""
    async def run():
        context = PlatingContext(provider_name="default")
        api = Plating(context, package_name)
        
        registry = api.registry
        removed = registry.remove_set(name)
        
        if removed:
            pout(f"✅ Removed ComponentSet '{name}'")
        else:
            perr(f"❌ Failed to remove ComponentSet '{name}' (may not exist)")
    
    asyncio.run(run())


@main.command("stats")
@click.option(
    "--package-name", 
    type=str,
    default="pyvider.components",
    help="Package to search for components.",
)
def stats_command(package_name: str) -> None:
    """Show registry statistics including ComponentSets."""
    async def run():
        context = PlatingContext(provider_name="default")
        api = Plating(context, package_name)
        
        stats = api.get_registry_stats()
        
        pout("📊 Registry Statistics:")
        pout(f"   Total components: {stats.get('total_components', 0)}")
        
        component_types = stats.get('component_types', [])
        if component_types:
            pout("\n📦 Components by type:")
            for comp_type in sorted(component_types):
                count = stats.get(f"{comp_type}_count", 0)
                with_templates = stats.get(f"{comp_type}_with_templates", 0)
                with_examples = stats.get(f"{comp_type}_with_examples", 0)
                pout(f"   {comp_type}: {count} total, {with_templates} with templates, {with_examples} with examples")
        
        set_stats = stats.get('component_sets', {})
        if set_stats:
            pout("\n🗂️ ComponentSets:")
            pout(f"   Total sets: {set_stats.get('total_sets', 0)}")
            pout(f"   Total components in sets: {set_stats.get('total_components_in_sets', 0)}")
            
            domains = set_stats.get('domains', [])
            if domains:
                pout(f"   Domains: {', '.join(domains)}")
            
            tags = set_stats.get('tags', [])
            if tags:
                pout(f"   Tags: {', '.join(tags[:10])}{'...' if len(tags) > 10 else ''}")
    
    asyncio.run(run())


if __name__ == "__main__":
    main()


# 🚀✨🎯🍽️