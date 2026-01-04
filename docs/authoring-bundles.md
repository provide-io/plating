# Guide: Authoring Plating Bundles

This guide provides a practical walkthrough for developers on how to create and maintain documentation, examples, and tests for their components using the `.plating` system.

## Step 1: Adorn Components with Templates

When you create a new component (e.g., a resource named `my_resource.py`), the first step is to create its documentation bundle using the `adorn` command.

Run the `adorn` command:
```bash
plating adorn --component-type resource
```
This command will find `my_resource.py` and, seeing it has no documentation template, create the following structure:
```
src/pyvider/components/resources/
├── my_resource.py
└── my_resource.plating/          # <-- Created
    ├── docs/
    │   └── my_resource.tmpl.md     # <-- Created
    └── examples/
        └── basic.tf                # <-- Created
```
The created files will contain standard boilerplate to get you started.

## Step 2: Populate the Documentation Template

Open the main template file, `my_resource.plating/docs/my_resource.tmpl.md`. This is where you write the primary documentation for your component.

-   **Update the Frontmatter**: Edit the `page_title` and `description` fields.
-   **Write the Introduction**: Add a clear, high-level description of what your component does.
-   **Use Template Functions**: The boilerplate will already contain `{{ example("basic") }}` and `{{ schema() }}`. These are essential and should be kept.

## Step 3: Write Meaningful Examples

Open `my_resource.plating/examples/basic.tf` and replace the placeholder content with a realistic, working example of your component. For components with multiple use cases, you can add more files (e.g., `advanced.tf`) and include them by name with `{{ example("advanced") }}`.

## Step 4: Plate and Verify Documentation

Once you have authored your documentation template and examples, run the `plate` command to generate the final documentation.

```bash
plating plate --output-dir docs/
```
This will create the final Markdown file (e.g., `docs/resources/my_resource.md`). Always review the generated file to ensure it looks correct.

## Step 5: Validate Documentation

After generating documentation, validate it for markdown quality:

```bash
plating validate --output-dir docs/
```

This will check your documentation for:
- Markdown linting errors
- Broken links
- Formatting issues
- Schema consistency

## Advanced: Grouped Examples

For comprehensive examples that demonstrate multiple components working together, you can create grouped examples:

### Creating Grouped Examples

Create subdirectories within your `examples/` folder:

```
my_resource.plating/examples/
├── basic.tf              # Simple flat example
└── full_stack/          # Grouped example directory
    └── main.tf          # Required entry point
```

### How Grouped Examples Work

1. **Discovery**: Plating finds all directories with `main.tf` files
2. **Compilation**: Examples from multiple components are combined
3. **Generation**: Creates:
   - `provider.tf` with required_providers block
   - Component-specific `.tf` files
   - `README.md` with terraform commands
4. **Fixtures**: Any fixtures in `fixtures/` are copied to the output

### Example Structure

```bash
# Multiple components contribute to the same group
resource1.plating/examples/full_stack/main.tf
resource2.plating/examples/full_stack/main.tf
data_source1.plating/examples/full_stack/main.tf

# Compiles to:
examples/full_stack/
├── provider.tf           # Auto-generated
├── resource1.tf          # From resource1
├── resource2.tf          # From resource2
├── data_source1.tf       # From data_source1
└── README.md            # Auto-generated with instructions
```

### Best Practices for Grouped Examples

1. **Use meaningful group names**: `full_stack`, `minimal`, `advanced`
2. **Always include main.tf**: Required for group discovery
3. **Add fixtures if needed**: Place test data in `fixtures/` directory
4. **Avoid filename conflicts**: Each component's files should be uniquely named

## Bundle Structure Reference

Each component has a `.plating` bundle with a standardized directory structure:

```
my_resource.plating/
├── docs/
│   ├── my_resource.tmpl.md    # Main template
│   └── _partial.md             # Reusable partials (optional)
├── examples/
│   ├── basic.tf                # Example configurations
│   ├── advanced.tf             # (optional)
│   └── full_stack/             # Grouped examples (optional)
│       └── main.tf             # Required entry point
└── fixtures/                   # Test fixtures (optional)
    └── data.json               # Test data files
```

### Directory Details

**docs/** - Documentation templates
- `*.tmpl.md` - Jinja2 templates that render to final markdown
- `_partial.md` - Reusable template fragments (use with `include()` or `render()`)

**examples/** - Terraform/Python examples
- `.tf` files for resources/data sources (flat examples)
- `.py` files for Python API examples
- Subdirectories with `main.tf` for grouped examples that combine multiple components

**fixtures/** - Test data (optional)
- JSON, YAML, or other data files used in examples or tests

## Template Functions Reference

Plating provides powerful template functions you can use in your `.tmpl.md` files:

### `{{ schema() }}`
Renders the component's schema as a formatted markdown table with attributes, types, and descriptions.

**Example:**
```markdown
## Schema

{{ schema() }}
```

### `{{ example('name') }}`
Includes an example file from the `examples/` directory in a terraform code block.

**Example:**
```markdown
## Example Usage

{{ example('basic') }}

## Advanced Example

{{ example('advanced') }}
```

### `{{ include('filename') }}`
Includes a static partial file from the `docs/` directory without rendering.

**Example:**
```markdown
{{ include('_partial.md') }}
```

### `{{ render('filename') }}`
Renders a dynamic template partial with the current context (variables, functions).

**Example:**
```markdown
{{ render('_partial.md') }}
```

**When to use `include()` vs `render()`:**
- Use `include()` for static markdown content
- Use `render()` when partials need access to template functions or variables
