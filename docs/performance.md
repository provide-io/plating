# Performance Guide

Optimize Plating performance for large providers and complex documentation workflows.

## Key Performance Features

- **Async Operations**: All I/O operations are asynchronous
- **Parallel Processing**: Templates render concurrently
- **Lazy Loading**: Bundles load on-demand
- **Schema Caching**: Schemas cached per session
- **Retry Policies**: Automatic retries with exponential backoff
- **Circuit Breakers**: Prevent cascading failures

## Optimization Strategies

### 1. Package-Specific Discovery

Always specify the package name to avoid searching all installed packages:

```python
# ✅ Fast - searches one package
api = Plating(context, package_name="pyvider.aws")

# ❌ Slow - searches all packages
api = Plating(context)
```

### 2. Component Type Filtering

Process specific component types to reduce scope:

```python
# Process only resources
result = await api.adorn(component_types=[ComponentType.RESOURCE])

# Process only what you need
await api.plate(component_types=[ComponentType.RESOURCE, ComponentType.DATA_SOURCE])
```

### 3. Parallel Template Rendering

Plating automatically renders templates in parallel:

```python
# Templates are rendered concurrently
result = await api.plate()  # All templates render in parallel

# Internal implementation uses asyncio.gather()
# for maximum concurrency
```

### 4. Batch Processing

For multiple providers, process them efficiently:

```python
import asyncio
from plating import Plating, PlatingContext

async def process_provider(provider_name: str):
    context = PlatingContext(provider_name=provider_name)
    api = Plating(context, package_name=f"pyvider.{provider_name}")
    return await api.plate()

async def process_all_providers():
    providers = ["aws", "azure", "gcp"]

    # Process providers in parallel
    results = await asyncio.gather(*[
        process_provider(p) for p in providers
    ])

    return results

asyncio.run(process_all_providers())
```

### 5. Memory Optimization

For providers with hundreds of components:

```python
async def process_large_provider():
    context = PlatingContext(provider_name="aws")
    api = Plating(context, package_name="pyvider.aws")

    # Process in chunks to manage memory
    component_types = [
        ComponentType.RESOURCE,
        ComponentType.DATA_SOURCE,
        ComponentType.FUNCTION
    ]

    for comp_type in component_types:
        # Process one type at a time
        await api.plate(component_types=[comp_type])

        # Let Python garbage collect between batches
        import gc
        gc.collect()
```

## Caching Strategies

### Schema Caching

Schemas are automatically cached per Plating instance:

```python
# Reuse the same api instance for multiple operations
api = Plating(context)

# Schema extracted once, reused for all operations
await api.adorn()   # Uses cached schema
await api.plate()   # Uses cached schema
await api.validate() # Uses cached schema
```

### Template Compilation Caching

Jinja2 templates are compiled and cached:

```python
# Templates compiled once per session
engine = AsyncTemplateEngine()

# Subsequent renders use compiled templates
await engine.render(bundle1, context1)  # Compiles template
await engine.render(bundle1, context2)  # Uses cached compilation
```

### Terraform Plugin Cache

Speed up schema extraction with plugin caching:

```bash
# Set plugin cache directory
export TF_PLUGIN_CACHE_DIR=$HOME/.terraform.d/plugin-cache

# Plating will reuse cached provider binaries
plating adorn
```

## Performance Monitoring

### Enable Metrics

Monitor operation performance:

```python
from provide.foundation import metrics

# Enable metrics collection
metrics.enable()

context = PlatingContext(
    provider_name="my_provider",
    log_level="INFO"
)

# Operations are automatically tracked
api = Plating(context)
result = await api.plate()

# Metrics available for:
# - adorn operations
# - plate operations
# - validate operations
# - template rendering
# - schema extraction
```

### Timing Operations

```python
import time

async def timed_operation():
    start = time.perf_counter()

    result = await api.plate()

    duration = time.perf_counter() - start
    print(f"Documentation generated in {duration:.2f}s")
    print(f"Files/second: {result.files_generated / duration:.1f}")
```

## Resilience Patterns

### Retry Policies

Built-in retry with exponential backoff:

```python
# Automatic retry configuration
retry_policy = RetryPolicy(
    max_attempts=3,
    backoff=BackoffStrategy.EXPONENTIAL,
    base_delay=0.5,
    max_delay=10.0
)

# Applied automatically to:
# - File I/O operations
# - Schema extraction
# - Network operations
```

### Circuit Breaker

Prevents cascading failures:

```python
# Circuit breaker opens after consecutive failures
# Prevents system overload
# Automatically resets after cooldown period
```

## Benchmarks

Typical performance metrics:

| Operation | Small Provider (10 components) | Medium (50 components) | Large (200+ components) |
|-----------|--------------------------------|------------------------|-------------------------|
| Discovery | < 0.5s | 1-2s | 3-5s |
| Adorn | < 1s | 2-3s | 5-10s |
| Plate | < 2s | 5-10s | 15-30s |
| Validate | < 1s | 2-3s | 5-10s |

## Performance Tuning

### 1. Optimize Template Complexity

Keep templates simple for faster rendering:

```jinja2
{# ✅ Fast - simple schema function #}
{{ schema() }}

{# ❌ Slow - complex nested loops #}
{% for item in items %}
  {% for subitem in item.subitems %}
    {% include complex_partial %}
  {% endfor %}
{% endfor %}
```

### 2. Minimize File I/O

```python
# ✅ Batch operations
result = await api.plate()  # Single batch operation

# ❌ Individual operations
for component in components:
    await process_component(component)  # Many small I/O operations
```

### 3. Use Appropriate Concurrency

```python
# Control concurrency level
import asyncio

# Limit concurrent tasks for resource-constrained environments
semaphore = asyncio.Semaphore(10)

async def limited_task(item):
    async with semaphore:
        return await process_item(item)

results = await asyncio.gather(*[
    limited_task(item) for item in items
])
```

## Troubleshooting Performance

### Slow Discovery

```python
# Enable debug logging to see what's being searched
context = PlatingContext(
    provider_name="my_provider",
    log_level="DEBUG"
)

# Check which packages are being scanned
api = Plating(context)  # Watch debug output
```

### Template Rendering Bottlenecks

```python
# Profile template rendering
import cProfile
import pstats

async def profile_templates():
    profiler = cProfile.Profile()
    profiler.enable()

    await api.plate()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 time consumers
```

### Memory Usage

```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Run operations
await api.plate()

# Get memory snapshot
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

# Print top memory consumers
for stat in top_stats[:10]:
    print(stat)
```

## Best Practices

1. **Specify package names** - Always provide package_name parameter
2. **Reuse API instances** - Create once, use multiple times
3. **Process by type** - Handle component types separately for large providers
4. **Enable plugin cache** - Set TF_PLUGIN_CACHE_DIR environment variable
5. **Monitor metrics** - Use foundation metrics for production
6. **Batch operations** - Use bulk operations over individual processing
7. **Profile first** - Measure before optimizing

## Environment Variables

Optimize with environment variables:

```bash
# Terraform plugin cache (speeds up schema extraction)
export TF_PLUGIN_CACHE_DIR=$HOME/.terraform.d/plugin-cache

# Python optimizations
export PYTHONOPTIMIZE=1

# Asyncio debug mode (development only)
export PYTHONASYNCIODEBUG=0  # Disable in production

# Memory limits (if needed)
ulimit -m 4194304  # 4GB memory limit
```