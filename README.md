# 🍲 Garnish

> Beautiful documentation generation for Terraform/OpenTofu providers

## What is Garnish?

Garnish is a modern documentation generation system specifically designed for Terraform and OpenTofu providers. It transforms your provider code into comprehensive, well-structured documentation with minimal effort.

## Value Proposition

**Problem:** Provider documentation is often incomplete, inconsistent, or outdated. Existing tools require significant manual effort and don't integrate well with modern development workflows.

**Solution:** Garnish automates documentation generation while giving developers full control over presentation. It discovers your provider components, generates smart templates, and renders beautiful documentation that stays in sync with your code.

## Key Features

- **🎯 Automatic Discovery** - Finds all resources, data sources, and functions in your provider
- **📝 Smart Templates** - Generates Jinja2 templates with examples and schemas
- **🍽️ Beautiful Output** - Renders Terraform Registry-compliant documentation
- **🧪 Built-in Testing** - Validates examples and documentation integrity
- **📦 Bundle System** - Co-locates docs, examples, and tests with components

## Comparison with Other Tools

### vs tfplugindocs
- **tfplugindocs:** Official HashiCorp tool, rigid structure, limited customization
- **Garnish:** Flexible templating, smart defaults, richer formatting options

### vs terraform-docs
- **terraform-docs:** Module documentation only, not for providers
- **Garnish:** Provider-focused, understands schemas and component types

### vs Manual Documentation
- **Manual:** Time-consuming, prone to drift, inconsistent formatting
- **Garnish:** Automated generation, stays in sync, enforces consistency

## Quick Example

```bash
# Install garnish
pip install garnish

# Generate documentation templates
garnish dress

# Customize templates as needed
# Then render final documentation
garnish plate
```

## Learn More

Full documentation and source code available in the `develop` branch.

## License

Apache 2.0

---

*Garnish - Making provider documentation as delightful as a well-plated dish* 🍽️