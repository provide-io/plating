# Troubleshooting Guide

This guide helps you resolve common issues when using Plating.

## Common Issues

### 1. "Module not found" Errors

**Problem:** ImportError when trying to import plating or pyvider packages.

**Solutions:**
```bash
# Ensure plating is installed
uv sync

# Install pyvider dependencies
uv add pyvider-cty provide-foundation
```

### 2. Async/Await Errors

**Problem:** "RuntimeWarning: coroutine was never awaited"

**Solution:** All Plating API methods are async and must be awaited:

```python
# ❌ Wrong
api.adorn()

# ✅ Correct
await api.adorn()

# Or wrap in async function
import asyncio
asyncio.run(main())
```

### 3. No Components Found

**Problem:** Plating doesn't find any components to document.

**Solutions:**

1. **Check package name:**
```python
# Specify the correct package
api = Plating(context, package_name="pyvider.components")
```

2. **Verify component discovery:**
```bash
# Check if components are registered
python -c "from provide.foundation.hub import Hub; hub = Hub(); hub.discover_components('pyvider.components'); print(hub.list_components())"
```

3. **Check component structure:**
- Ensure components are in correct directories (resources/, data_sources/, functions/)
- Verify components have proper naming (e.g., `my_resource.py`)

### 4. Template Rendering Fails

**Problem:** TemplateError during documentation generation.

**Common Causes:**
1. **Syntax error in template:**
   - Check for unmatched `{{` or `}}`
   - Verify Jinja2 syntax

2. **Missing example file:**
   ```jinja2
   {{ example("basic") }}  # Requires examples/basic.tf
   ```

3. **Schema not available:**
   - Ensure component has `get_schema()` method
   - Check schema extraction logs

### 5. File System Errors

**Problem:** FileSystemError when writing documentation.

**Solutions:**
```bash
# Check permissions
ls -la docs/

# Create output directory
mkdir -p docs/resources docs/data-sources docs/functions

# Use --force flag to overwrite
plating plate --force
```

### 6. Provider Name Not Detected

**Problem:** "Could not determine provider name"

**Solutions:**

1. **Specify explicitly:**
```bash
plating adorn --provider-name my_provider
```

2. **Configure in pyproject.toml:**
```toml
[tool.plating]
provider_name = "my_provider"
```

3. **Follow naming convention:**
   - Package name: `terraform-provider-myname`
   - Or: `myname-provider`

### 7. Validation Failures

**Problem:** Documentation validation fails.

**Check:**
1. **Markdown syntax:**
   ```bash
   # Run linter directly
   pymarkdownlnt docs/
   ```

2. **Required sections:**
   - Ensure templates include required Terraform Registry sections
   - Check frontmatter format

3. **Schema formatting:**
   - Verify schema tables are properly formatted
   - Check for special characters in descriptions

### 8. Memory Issues with Large Providers

**Problem:** High memory usage or OOM errors.

**Solutions:**
1. **Process in batches:**
```python
# Process component types separately
await api.adorn(component_types=[ComponentType.RESOURCE])
await api.adorn(component_types=[ComponentType.DATA_SOURCE])
```

2. **Increase memory limit:**
```bash
# Set higher memory limit if needed
ulimit -m 4194304  # 4GB
```

### 9. Circuit Breaker Triggered

**Problem:** "Circuit breaker is open" errors.

**Cause:** Too many consecutive failures triggered the circuit breaker.

**Solution:**
```python
# Wait for circuit to reset (typically 60 seconds)
import time
time.sleep(60)

# Or restart the process
```

### 10. Template Functions Not Working

**Problem:** `{{ schema() }}` or `{{ example() }}` showing empty or error.

**Debug steps:**
1. **Check component has schema:**
```python
component = hub.get_component("resource", "my_resource")
schema = component.get_schema()
print(schema)
```

2. **Verify example file exists:**
```bash
ls my_resource.plating/examples/
```

3. **Check template context:**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Debug Mode

Enable verbose logging to troubleshoot issues:

```python
# Python API
context = PlatingContext(
    provider_name="my_provider",
    log_level="DEBUG",
    verbose=True
)

# CLI
plating plate --verbose --log-level DEBUG
```

## Getting Help

If you encounter issues not covered here:

1. **Check the logs:** Look for error messages and stack traces
2. **Review examples:** Check the test files for usage patterns
3. **File an issue:** https://github.com/provide-io/plating/issues

### Issue Template

When reporting issues, include:
- Plating version (`plating --version`)
- Python version (`python --version`)
- Complete error message and stack trace
- Minimal reproducible example
- Operating system and environment

## Performance Optimization

### Slow Documentation Generation

**Optimize with:**
1. **Parallel processing:**
```python
# Use batch operations
result = await api.plate(component_types=[ComponentType.RESOURCE])
```

2. **Cache schemas:**
- Schemas are cached per session automatically
- Reuse the same Plating instance

3. **Limit scope:**
```bash
# Process specific components
plating plate --component-type resource
```

## Foundation Integration Issues

### Retry Policy Not Working

**Verify retry configuration:**
```python
# Check retry policy is active
api.retry_policy.max_attempts  # Should be 3
api.retry_policy.backoff  # Should be BackoffStrategy.EXPONENTIAL
```

### Metrics Not Collected

**Enable metrics collection:**
```python
from provide.foundation import metrics
metrics.enable()
```

## Environment Variables

Useful environment variables for debugging:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Disable colored output
export NO_COLOR=1

# Set plugin cache (speeds up schema extraction)
export TF_PLUGIN_CACHE_DIR=$HOME/.terraform.d/plugin-cache
```
