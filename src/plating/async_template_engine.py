#
# plating/async_template_engine.py  
#
"""Modern async template engine with foundation integration."""

import asyncio
from pathlib import Path

from jinja2 import DictLoader, Environment, select_autoescape
from provide.foundation import logger

from .decorators import with_metrics, with_timing, plating_metrics
from .plating import PlatingBundle
from .types import PlatingContext


class AsyncTemplateEngine:
    """Async-first template engine with foundation integration."""
    
    def __init__(self):
        self._jinja_env = None
        self._template_cache: dict[str, str] = {}
    
    def _get_jinja_env(self, templates: dict[str, str]) -> Environment:
        """Get or create Jinja2 environment with templates."""
        env = Environment(
            loader=DictLoader(templates),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=True  # Enable async template rendering
        )
        
        # Add custom template functions
        env.globals.update({
            "schema": lambda: "",  # Will be overridden per template
            "example": self._format_example,
            "include": lambda filename: templates.get(filename, ""),
        })
        
        return env
    
    @with_timing
    @with_metrics("template_render")
    async def render(
        self, 
        bundle: PlatingBundle,
        context: PlatingContext
    ) -> str:
        """Render template with context and partials.
        
        Args:
            bundle: PlatingBundle containing template and assets
            context: Type-safe context for rendering
            
        Returns:
            Rendered template string
        """
        # Load template and partials concurrently
        template_task = asyncio.create_task(self._load_template(bundle))
        partials_task = asyncio.create_task(self._load_partials(bundle))
        
        template_content, partials = await asyncio.gather(template_task, partials_task)
        
        if not template_content:
            logger.debug(f"No template found for {bundle.name}, skipping")
            return ""
        
        # Prepare templates dict
        templates = {"main.tmpl": template_content}
        templates.update(partials)
        
        # Create Jinja environment
        env = self._get_jinja_env(templates)
        
        # Convert context to dict
        context_dict = context.to_dict()
        
        # Override schema function to return actual schema
        if context.schema:
            env.globals["schema"] = lambda: context.schema.to_markdown()
        
        # Render template asynchronously
        template = env.get_template("main.tmpl")
        
        async with plating_metrics.track_operation("template_render", bundle=bundle.name):
            return await template.render_async(**context_dict)
    
    async def render_batch(
        self, 
        items: list[tuple[PlatingBundle, PlatingContext]]
    ) -> list[str]:
        """Render multiple templates in parallel.
        
        Args:
            items: List of (bundle, context) tuples to render
            
        Returns:
            List of rendered template strings
        """
        tasks = [
            asyncio.create_task(self.render(bundle, context))
            for bundle, context in items
        ]
        
        async with plating_metrics.track_operation("batch_render", count=len(items)):
            return await asyncio.gather(*tasks)
    
    async def _load_template(self, bundle: PlatingBundle) -> str:
        """Load main template from bundle."""
        cache_key = f"{bundle.plating_dir}:main"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        # Run in thread pool since file I/O is blocking
        template_content = await asyncio.get_event_loop().run_in_executor(
            None, bundle.load_main_template
        )
        
        self._template_cache[cache_key] = template_content
        return template_content
    
    async def _load_partials(self, bundle: PlatingBundle) -> dict[str, str]:
        """Load partial templates from bundle."""
        cache_key = f"{bundle.plating_dir}:partials"
        if cache_key in self._template_cache:
            return eval(self._template_cache[cache_key])  # Stored as string repr
        
        # Run in thread pool since file I/O is blocking
        partials = await asyncio.get_event_loop().run_in_executor(
            None, bundle.load_partials
        )
        
        self._template_cache[cache_key] = repr(partials)
        return partials
    
    def _format_example(self, example_code: str) -> str:
        """Format example code for display."""
        if not example_code:
            return ""
        return f"```terraform\n{example_code}\n```"
    
    def clear_cache(self):
        """Clear template cache."""
        self._template_cache.clear()


# Global template engine instance
template_engine = AsyncTemplateEngine()


# 🍲⚡🎨📝