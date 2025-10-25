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
-   **Use Template Functions**: The boilerplate will already contain `{{ example("example") }}` and `{{ schema() }}`. These are essential and should be kept.

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
