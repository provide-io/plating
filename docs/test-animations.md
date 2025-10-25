# Terminal Animation Test

This page tests that the Termynal terminal simulator is working correctly.

## Test 1: Basic Commands

<div class="termy">

```console
$ echo "Hello World"
Hello World

$ ls -la
total 24
drwxr-xr-x  4 user staff  128 Oct 24 12:00 .
drwxr-xr-x 15 user staff  480 Oct 24 11:59 ..
-rw-r--r--  1 user staff  123 Oct 24 12:00 README.md
```

</div>

## Test 2: With Comments

<div class="termy">

```console
$ plating adorn --component-type resource
// Adorning components...
// Generating templates...
✓ Created example_resource.plating/
✓ Generated docs/resource.tmpl.md
✓ Generated examples/basic.tf

$ ls example_resource.plating/
docs/
examples/
```

</div>

## Test 3: With Progress Bar

<div class="termy">

```console
$ plating plate --output-dir docs/
// Plating documentation...
---> 100%
✓ Generated 15 files
✓ Documentation complete!
```

</div>

## Test 4: Multi-Step Process

<div class="termy">

```console
$ uv sync
// Installing dependencies...
Resolved 24 packages in 1.2s

$ uv run pytest
// Running test suite...
======================== 15 passed in 0.82s ========================

$ uv run plating --help
Usage: plating [OPTIONS] COMMAND [ARGS]...

  Plating documentation generator

Options:
  --help  Show this message and exit.
```

</div>

## Verification Checklist

If terminal animations are working correctly, you should see:

- ✅ Commands typing out with animation
- ✅ Comments showing with 💬 emoji
- ✅ Progress bars animating from 0% to 100%
- ✅ Output appearing instantly after commands
- ✅ Restart (↻) and Fast Forward (→) buttons
- ✅ Smooth transitions and timing

If you see static code blocks instead, check:

1. Browser console for JavaScript errors
2. Network tab for 404s on theme files
3. Verify `.shared-theme/` directory exists in `docs/`
4. Verify `mkdocs.yml` has correct paths
