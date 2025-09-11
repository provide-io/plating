# Template Processing Pipeline for Foundation

## Overview

Plating's async template rendering with Jinja2 integration and partials support could become a general-purpose template processing module in foundation.

## Proposed Foundation Module: `provide.foundation.templates`

### Core Classes

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class TemplateLoader(Protocol):
    """Protocol for template loading strategies."""
    
    async def load_template(self, name: str) -> str:
        """Load template content by name."""
        ...
    
    async def load_partials(self, template_name: str) -> dict[str, str]:
        """Load partial templates related to a template."""
        ...

class AsyncTemplateEngine:
    """Async template processing with partials support."""
    
    def __init__(
        self,
        loader: TemplateLoader,
        engine_type: str = "jinja2",
        global_context: dict[str, Any] = None
    ):
        self.loader = loader
        self.engine_type = engine_type
        self.global_context = global_context or {}
        self._setup_engine()
    
    async def render(
        self, 
        template_name: str, 
        context: dict[str, Any],
        partials: dict[str, str] = None
    ) -> str:
        """Render template with context and partials."""
        # Async implementation with metrics tracking
        
    async def render_batch(
        self, 
        templates: list[tuple[str, dict[str, Any]]]
    ) -> list[str]:
        """Render multiple templates in parallel."""
        # Parallel processing with rate limiting
        
    def add_global_function(self, name: str, func: callable):
        """Add global template function."""
        # Similar to plating's template function registration

class FileTemplateLoader:
    """Load templates from filesystem."""
    
    def __init__(self, template_dirs: list[Path]):
        self.template_dirs = template_dirs
    
    async def load_template(self, name: str) -> str:
        # Find and load template file
        
    async def load_partials(self, template_name: str) -> dict[str, str]:
        # Load related partial templates

class BundleTemplateLoader:
    """Load templates from resource bundles."""
    
    def __init__(self, bundles: list[ResourceBundle]):
        self.bundles = bundles
    
    async def load_template(self, name: str) -> str:
        # Load template from appropriate bundle
        
class CachingTemplateLoader:
    """Wrapper that adds caching to any loader."""
    
    def __init__(self, loader: TemplateLoader, cache_ttl: int = 300):
        self.loader = loader
        self.cache_ttl = cache_ttl
        self._cache = {}
```

### Usage Examples  

```python
# Basic usage
from provide.foundation.templates import AsyncTemplateEngine, FileTemplateLoader

loader = FileTemplateLoader([Path("templates"), Path("partials")])
engine = AsyncTemplateEngine(loader)

# Add custom functions
engine.add_global_function("format_date", lambda d: d.strftime("%Y-%m-%d"))

# Render single template
result = await engine.render("documentation.md", {
    "title": "API Docs",
    "components": components_data
})

# Render multiple templates in parallel
results = await engine.render_batch([
    ("api.md", api_context),
    ("guide.md", guide_context),
    ("reference.md", ref_context)
])

# Using with resource bundles  
from provide.foundation.discovery import ResourceDiscovery

discovery = ResourceDiscovery("*.templates")
bundles = discovery.discover_bundles(resource_type="documentation")

bundle_loader = BundleTemplateLoader(bundles)
cached_loader = CachingTemplateLoader(bundle_loader, cache_ttl=600)
engine = AsyncTemplateEngine(cached_loader)
```

### Features

1. **Async-First**: Built for high-performance parallel rendering
2. **Pluggable Loaders**: Multiple template source strategies
3. **Caching Layer**: Template compilation and content caching
4. **Metrics Integration**: Built-in performance monitoring
5. **Multiple Engines**: Support for Jinja2, Mako, etc.
6. **Partial Support**: Modular template composition
7. **Global Functions**: Extensible template function registry
8. **Rate Limiting**: Controlled resource usage in batch operations

### Advanced Features

```python
# With resilience patterns
from provide.foundation.resilience import RetryExecutor, CircuitBreaker

engine = AsyncTemplateEngine(
    loader=loader,
    retry_executor=RetryExecutor(...),
    circuit_breaker=CircuitBreaker(...)
)

# With streaming for large templates
async for chunk in engine.render_stream("large_template.html", context):
    # Process template chunks as they're rendered
    
# With template inheritance and includes
engine.add_template_path("base_templates/")
result = await engine.render("child_template.html", context)
```

### Benefits

1. **Performance**: Async processing enables high throughput
2. **Flexibility**: Multiple loader strategies for different use cases  
3. **Reliability**: Built-in resilience and caching
4. **Observability**: Metrics and monitoring integration
5. **Reusability**: Generic enough for many template use cases

### Migration Path

1. Extract plating's template logic to foundation
2. Add async capabilities and loader abstractions
3. Update plating to use foundation's template engine
4. Provide compatibility layer for existing template code
5. Add support for additional template engines