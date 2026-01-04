# Capability-First Organization

Plating supports organizing documentation by **capability** (subcategory) instead of just by component type. This makes it easier to find related functionality across resource types.

## How It Works

### 1. Add Subcategory to Templates

Add a `subcategory` field to your component template frontmatter:

```markdown
---
page_title: "sqrt Function"
subcategory: "Math"
description: |-
  Calculate square root of a number
---
```

### 2. Automatic Organization

Components are automatically grouped by capability in generated documentation:

```
## Math
### Functions
- add
- subtract
- multiply

## String Utilities
### Functions
- format
- join
- split

## Utilities
### Resources
- pyvider_file_content
### Data Sources
- pyvider_env_variables
```

### 3. MkDocs Navigation

The `mkdocs.yml` navigation is automatically generated with capability-first structure:

```yaml
nav:
  - Overview: index.md
  - Math:
      Functions:
        add: functions/add.md
        subtract: functions/subtract.md
  - String Utilities:
      Functions:
        format: functions/format.md
        join: functions/join.md
  - Utilities:
      Resources:
        file_content: resources/file_content.md
```

## Standard Subcategories

The following standard subcategories are recognized and organized consistently:

- **Math** - Numeric operations (add, subtract, multiply, etc.)
- **String Utilities** - String manipulation (format, join, split, etc.)
- **Collections** - List/map operations (contains, length, lookup)
- **Type Conversion** - Type casting functions
- **Lens** - Data transformation components (JQ integration)
- **Utilities** - General-purpose resources and data sources
- **Test Mode** - Components for testing (always appears last)

## Custom Subcategories

You can use any custom subcategory name. Just add it to your template frontmatter:

```markdown
---
page_title: "Custom Component"
subcategory: "My Custom Category"
---
```

Custom subcategories will appear in alphabetical order alongside standard categories.

## Guide Support

Plating supports provider-level guides that appear in the documentation structure. Add guides in the `.plating/guides/` directory:

```
.plating/
├── guides/
│   ├── getting-started.tmpl.md
│   ├── authentication.tmpl.md
│   └── troubleshooting.tmpl.md
└── docs/
    └── components.tmpl.md
```

### Guide Structure

Guides follow the same template format as component documentation:

```markdown
---
page_title: "Getting Started Guide"
description: |-
  Learn how to get started with this provider
---

# Getting Started

{{ example('basic-setup') }}

## Next Steps

...
```

### Guide Discovery

Guides are automatically:
- Discovered from the `.plating/guides/` directory
- Added to the documentation structure
- Included in navigation with proper ordering
- Rendered with the same template engine as component docs

## Benefits of Capability-First Organization

### For Users
- **Find related functionality faster** - All math functions grouped together
- **Discover cross-component patterns** - See how resources and data sources work together
- **Logical navigation** - Browse by what you want to do, not by component type

### For Maintainers
- **Consistent categorization** - Standard categories across all providers
- **Flexible organization** - Add custom categories as needed
- **Automatic structure** - No manual navigation file maintenance

## Best Practices

1. **Use standard categories when possible** - Helps users familiar with other providers
2. **Be specific with custom categories** - "Database Operations" vs "Misc"
3. **Document category purpose** - Add description in category landing pages
4. **Keep categories focused** - Split large categories into subcategories
5. **Consistent naming** - Use title case for category names
