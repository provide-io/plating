# CLI Auto-Detection

Plating's CLI intelligently auto-detects configuration values to minimize required parameters. This guide explains how auto-detection works and when you need to provide explicit values.

## Provider Name Auto-Detection

The CLI attempts to determine the provider name in this order:

### 1. Explicit Flag (Highest Priority)
```bash
plating adorn --provider-name my_provider
```

### 2. Configuration File
Checks `pyproject.toml` in the current directory:
```toml
[tool.plating]
provider_name = "my_provider"
```

### 3. Package Name Pattern
Extracts from package name if it follows conventions:
- `terraform-provider-{name}` → Provider: `{name}`
- `{name}-provider` → Provider: `{name}`

Example:
```toml
[project]
name = "terraform-provider-aws"  # Auto-detects: aws
```

### 4. Fallback
If none of the above work, you must specify `--provider-name`.

## Package Name Auto-Detection

Determines which package to search for components:

### 1. Explicit Flag (Highest Priority)
```bash
plating adorn --package-name pyvider.components
```

### 2. Current Directory's Package
Reads from `pyproject.toml`:
```toml
[project]
name = "pyvider.components"  # Auto-detected
```

### 3. Fallback Behavior
- If not specified: Searches ALL installed packages
- This can be slow for large environments
- Recommended: Always specify `--package-name` for better performance

## Output Directory Auto-Detection

### For `plating plate` Command

1. **Explicit Flag:**
```bash
plating plate --output-dir ./documentation
```

2. **Auto-Detection Logic:**
```python
# Looks for existing directories in order:
1. ./docs/          # If exists
2. ./documentation/ # If exists
3. ./doc/          # If exists
4. ./docs/         # Created if none exist
```

### For `plating validate` Command

Uses the same logic as `plate` to find where documentation was generated.

## Component Type Auto-Detection

### Default Behavior
If not specified, operations apply to ALL component types:
```bash
plating adorn  # Adorns resources, data_sources, and functions
```

### Explicit Selection
```bash
plating adorn --component-type resource
plating adorn --component-type resource --component-type function
```

## Project Root Auto-Detection

Determines the project root for relative paths:

### Detection Order:
1. **Explicit Flag:**
```bash
plating plate --project-root /path/to/project
```

2. **Git Repository Root:**
```python
# Walks up from current directory to find .git/
/path/to/project/.git/  # Found → project root is /path/to/project/
```

3. **Pyproject.toml Location:**
```python
# Walks up to find pyproject.toml
/path/to/project/pyproject.toml  # Found → project root is /path/to/project/
```

4. **Current Directory:**
```python
Path.cwd()  # Fallback if no indicators found
```

## Examples Directory Auto-Detection

### For Generated Examples
When using `--generate-examples`:

1. **Explicit Flags:**
```bash
plating plate --generate-examples \
  --examples-dir examples/ \
  --grouped-examples-dir examples/integration/
```

2. **Defaults:**
- Flat examples: `./examples/`
- Grouped examples: `./examples/`

## Auto-Detection in Action

### Minimal Command (Maximum Auto-Detection)
```bash
# In a properly configured project directory:
cd terraform-provider-mycloud
plating adorn    # Auto-detects everything
plating plate    # Auto-detects everything
```

### What Gets Auto-Detected:
- ✅ Provider name: `mycloud` (from package name)
- ✅ Package name: From pyproject.toml
- ✅ Output directory: `./docs/` (if exists)
- ✅ Component types: All types
- ✅ Project root: Git repository root

### When to Specify Values

Provide explicit values when:
1. Auto-detection fails or gives wrong results
2. Working outside a project directory
3. Wanting different behavior than defaults
4. Performance optimization (e.g., specific package)

### Full Explicit Command
```bash
plating adorn \
  --provider-name mycloud \
  --package-name pyvider.mycloud \
  --component-type resource \
  --output-dir ./templates/

plating plate \
  --provider-name mycloud \
  --package-name pyvider.mycloud \
  --output-dir ./docs/ \
  --component-type resource \
  --project-root /path/to/project/
```

## Configuration Precedence

From highest to lowest priority:

1. **Command-line flags** (always wins)
2. **Environment variables** (if implemented)
3. **pyproject.toml [tool.plating]** section
4. **Auto-detection** from context
5. **Built-in defaults**

## Debugging Auto-Detection

To see what values are being auto-detected:

```bash
# Verbose mode shows auto-detection process
plating adorn --verbose

# Debug logging for detailed information
plating plate --log-level DEBUG
```

Example output:
```
[DEBUG] Auto-detected provider name: mycloud
[DEBUG] Auto-detected package name: pyvider.mycloud
[DEBUG] Using output directory: ./docs/
[INFO] Starting adorn operation...
```

## Best Practices

### For Projects
1. **Configure in pyproject.toml:**
```toml
[tool.plating]
provider_name = "mycloud"
# Note: Other settings must use CLI flags
```

2. **Follow naming conventions:**
   - Package: `terraform-provider-{name}`
   - Or: `pyvider.{name}`

3. **Use standard directory structure:**
   - Documentation: `docs/`
   - Examples: `examples/`

### For CI/CD
Always use explicit flags in CI/CD to ensure reproducibility:
```yaml
- name: Generate Documentation
  run: |
    plating adorn --provider-name ${{ env.PROVIDER }} --package-name ${{ env.PACKAGE }}
    plating plate --provider-name ${{ env.PROVIDER }} --output-dir docs/
```

### For Development
Use auto-detection for convenience during development:
```bash
# Quick iterations during development
plating adorn && plating plate
```

## Limitations

Currently, only `provider_name` can be configured in `pyproject.toml`. Other settings like `output_dir`, `component_types`, and `package_name` for filtering must be provided as CLI flags.

Future versions may expand configuration file support.