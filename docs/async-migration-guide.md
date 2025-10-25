# Async API Migration Guide

This guide helps you migrate from synchronous patterns to Plating's async-first API.

## Why Async?

Plating uses async operations for:
- **Performance**: Parallel template rendering and I/O operations
- **Scalability**: Handle multiple providers and large component sets
- **Foundation Integration**: Leverage async resilience patterns
- **Modern Python**: Follow current best practices

## Basic Migration Pattern

### Old Synchronous Pattern (Not Supported)
```python
# ❌ This doesn't work - Plating is async-only
from plating import Plating

api = Plating(context)
result = api.adorn()  # Error: coroutine not awaited
```

### New Async Pattern
```python
# ✅ Correct async usage
import asyncio
from plating import Plating, PlatingContext

async def main():
    context = PlatingContext(provider_name="my_provider")
    api = Plating(context)
    result = await api.adorn()
    return result

# Run the async function
result = asyncio.run(main())
```

## Common Migration Scenarios

### 1. Script Migration

**Before (Hypothetical Sync):**
```python
#!/usr/bin/env python3

def generate_docs():
    api = create_api()
    api.adorn()
    api.plate()
    print("Done")

if __name__ == "__main__":
    generate_docs()
```

**After (Async):**
```python
#!/usr/bin/env python3
import asyncio
from plating import Plating, PlatingContext

async def generate_docs():
    context = PlatingContext(provider_name="my_provider")
    api = Plating(context)

    await api.adorn()
    await api.plate()
    print("Done")

if __name__ == "__main__":
    asyncio.run(generate_docs())
```

### 2. Class Integration

**Before (Hypothetical Sync):**
```python
class DocGenerator:
    def __init__(self):
        self.api = create_api()

    def generate(self):
        return self.api.plate()
```

**After (Async):**
```python
class DocGenerator:
    def __init__(self):
        self.context = PlatingContext(provider_name="my_provider")
        self.api = Plating(self.context)

    async def generate(self):
        return await self.api.plate()

# Usage
generator = DocGenerator()
result = asyncio.run(generator.generate())
```

### 3. Test Migration

**Before (Hypothetical Sync):**
```python
def test_documentation():
    api = create_api()
    result = api.adorn()
    assert result.templates_generated > 0
```

**After (Async):**
```python
import pytest

@pytest.mark.asyncio
async def test_documentation():
    context = PlatingContext(provider_name="test")
    api = Plating(context)
    result = await api.adorn()
    assert result.templates_generated > 0
```

### 4. Django/Flask Integration

**For Django:**
```python
from asgiref.sync import async_to_sync
from plating import Plating, PlatingContext

def generate_docs_view(request):
    context = PlatingContext(provider_name="my_provider")
    api = Plating(context)

    # Convert async to sync for Django
    result = async_to_sync(api.plate)()
    return JsonResponse({"files": result.files_generated})
```

**For Flask:**
```python
from asyncio import run
from flask import Flask, jsonify
from plating import Plating, PlatingContext

app = Flask(__name__)

@app.route('/generate')
def generate():
    async def _generate():
        context = PlatingContext(provider_name="my_provider")
        api = Plating(context)
        return await api.plate()

    result = run(_generate())
    return jsonify({"files": result.files_generated})
```

### 5. Celery Task Migration

**Celery with Async Support:**
```python
from celery import Celery
import asyncio
from plating import Plating, PlatingContext

app = Celery('tasks')

@app.task
def generate_documentation(provider_name):
    async def _generate():
        context = PlatingContext(provider_name=provider_name)
        api = Plating(context)

        result = await api.plate()
        return result.files_generated

    return asyncio.run(_generate())
```

## Parallel Operations

### Sequential (Slower)
```python
async def process_all():
    context = PlatingContext(provider_name="my_provider")
    api = Plating(context)

    # Sequential - each awaits completion
    await api.adorn()
    await api.plate()
    await api.validate()
```

### Parallel (Faster)
```python
import asyncio

async def process_all():
    context = PlatingContext(provider_name="my_provider")
    api = Plating(context)

    # Parallel - operations that don't depend on each other
    adorn_task = asyncio.create_task(api.adorn())

    # Wait for adorn to complete before plating
    await adorn_task

    # Then run plate and validate in parallel
    plate_task = asyncio.create_task(api.plate())
    validate_task = asyncio.create_task(api.validate())

    plate_result, validate_result = await asyncio.gather(
        plate_task, validate_task
    )

    return plate_result, validate_result
```

## Error Handling in Async

### Basic Error Handling
```python
async def safe_generate():
    try:
        context = PlatingContext(provider_name="my_provider")
        api = Plating(context)
        result = await api.plate()
        return result
    except TemplateError as e:
        logger.error(f"Template error: {e}")
        return None
    except Exception as e:
        logger.exception("Unexpected error")
        raise
```

### With Retry Logic
```python
async def generate_with_retry(max_attempts=3):
    for attempt in range(max_attempts):
        try:
            context = PlatingContext(provider_name="my_provider")
            api = Plating(context)
            return await api.plate()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Context Managers

### Async Context Manager
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def plating_session(provider_name):
    context = PlatingContext(provider_name=provider_name)
    api = Plating(context)

    try:
        yield api
    finally:
        # Cleanup if needed
        pass

# Usage
async def main():
    async with plating_session("my_provider") as api:
        result = await api.plate()
        print(f"Generated {result.files_generated} files")
```

## Running Async Code

### Method 1: asyncio.run() (Recommended)
```python
import asyncio

async def main():
    # Your async code here
    pass

asyncio.run(main())
```

### Method 2: Event Loop (Advanced)
```python
import asyncio

async def main():
    # Your async code here
    pass

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()
```

### Method 3: In Jupyter/IPython
```python
# Jupyter automatically handles async
async def main():
    context = PlatingContext(provider_name="my_provider")
    api = Plating(context)
    return await api.plate()

# In Jupyter cell:
await main()
```

## Common Pitfalls

### 1. Forgetting await
```python
# ❌ Wrong - creates coroutine but doesn't execute
result = api.plate()

# ✅ Correct
result = await api.plate()
```

### 2. Using async without asyncio.run()
```python
# ❌ Wrong - can't call async function directly
async def main():
    pass

main()  # Error: coroutine not awaited

# ✅ Correct
asyncio.run(main())
```

### 3. Mixing Sync and Async
```python
# ❌ Wrong - can't await in sync function
def generate():
    api = Plating(context)
    await api.plate()  # SyntaxError

# ✅ Correct - make function async
async def generate():
    api = Plating(context)
    await api.plate()
```

### 4. Blocking Operations in Async
```python
# ❌ Wrong - blocks event loop
async def bad_example():
    time.sleep(5)  # Blocks!

# ✅ Correct - use async sleep
async def good_example():
    await asyncio.sleep(5)  # Non-blocking
```

## Performance Tips

1. **Use gather() for parallel operations:**
```python
results = await asyncio.gather(
    api.adorn(),
    api.validate(),
    return_exceptions=True
)
```

2. **Process large sets in batches:**
```python
async def process_in_batches(components, batch_size=10):
    for i in range(0, len(components), batch_size):
        batch = components[i:i + batch_size]
        await asyncio.gather(*[process(c) for c in batch])
```

3. **Use task groups (Python 3.11+):**
```python
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(api.adorn())
    task2 = tg.create_task(api.plate())
# Both tasks complete here
```

## Testing Async Code

### With pytest-asyncio
```python
# Install: pip install pytest-asyncio

import pytest
from plating import Plating, PlatingContext

@pytest.mark.asyncio
async def test_adorn():
    context = PlatingContext(provider_name="test")
    api = Plating(context)
    result = await api.adorn()
    assert result.templates_generated >= 0

@pytest.fixture
async def api():
    context = PlatingContext(provider_name="test")
    return Plating(context)

@pytest.mark.asyncio
async def test_with_fixture(api):
    result = await api.plate()
    assert result is not None
```

## Debugging Async Code

### 1. Enable Debug Mode
```python
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
asyncio.run(main(), debug=True)
```

### 2. Use aiomonitor for Runtime Inspection
```python
# pip install aiomonitor
import aiomonitor

async def main():
    async with aiomonitor.start_monitor():
        # Your code here
        await api.plate()
```

### 3. Trace Async Execution
```python
import sys

def trace_async(frame, event, arg):
    if event == 'call':
        code = frame.f_code
        if asyncio.iscoroutinefunction(eval(code.co_name, frame.f_globals)):
            print(f"Async call: {code.co_filename}:{code.co_name}")
    return trace_async

sys.settrace(trace_async)
```

## Summary

Key points for migration:
1. All Plating operations are async - use `await`
2. Wrap main code in `asyncio.run()`
3. Use `async def` for functions that call Plating
4. Leverage parallel operations with `gather()`
5. Test with `pytest.mark.asyncio`
6. Handle errors with try/except around await