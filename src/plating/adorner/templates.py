#
# plating/adorner/templates.py
#
"""Template generation for adorned components."""


class TemplateGenerator:
    """Generates templates and examples for components."""

    async def generate_template(
        self, name: str, component_type: str, component_class
    ) -> str:
        """Generate template content based on component type."""
        # Get component description if available
        try:
            doc = component_class.__doc__
            # Check if it's a real docstring (not from Mock or other test objects)
            if doc:
                doc_stripped = doc.strip()
                if not doc_stripped.startswith("Create a new `Mock`"):
                    description = doc_stripped.split("\n")[0]  # First line only
                else:
                    description = (
                        f"Terraform {component_type.replace('_', ' ')} for {name}"
                    )
            else:
                description = f"Terraform {component_type.replace('_', ' ')} for {name}"
        except AttributeError:
            # No docstring attribute
            description = f"Terraform {component_type.replace('_', ' ')} for {name}"

        if component_type == "resource":
            return self._resource_template(name, description)
        elif component_type == "data_source":
            return self._data_source_template(name, description)
        elif component_type == "function":
            return self._function_template(name, description)
        else:
            return self._generic_template(name, description, component_type)

    async def generate_example(self, name: str, component_type: str) -> str:
        """Generate example Terraform content."""
        if component_type == "resource":
            return self._resource_example(name)
        elif component_type == "data_source":
            return self._data_source_example(name)
        elif component_type == "function":
            return self._function_example(name)
        else:
            return self._generic_example(name)

    def _resource_template(self, name: str, description: str) -> str:
        """Generate resource template content."""
        return f"""---
page_title: "Resource: {name}"
description: |-
  {description}
---

# {name} (Resource)

{description}

## Example Usage

{{{{ example("example") }}}}

## Argument Reference

{{{{ schema() }}}}

## Import

```bash
terraform import {name}.example <id>
```
"""

    def _data_source_template(self, name: str, description: str) -> str:
        """Generate data source template content."""
        return f"""---
page_title: "Data Source: {name}"
description: |-
  {description}
---

# {name} (Data Source)

{description}

## Example Usage

{{{{ example("example") }}}}

## Argument Reference

{{{{ schema() }}}}
"""

    def _function_template(self, name: str, description: str) -> str:
        """Generate function template content."""
        return f"""---
page_title: "Function: {name}"
description: |-
  {description}
---

# {name} (Function)

{description}

## Example Usage

{{{{ example("example") }}}}

## Signature

`{{{{ signature_markdown }}}}`

## Arguments

{{{{ arguments_markdown }}}}

{{% if has_variadic %}}
## Variadic Arguments

{{{{ variadic_argument_markdown }}}}
{{% endif %}}
"""

    def _generic_template(
        self, name: str, description: str, component_type: str
    ) -> str:
        """Generate generic template content."""
        return f"""---
page_title: "{component_type.title()}: {name}"
description: |-
  {description}
---

# {name} ({component_type.title()})

{description}

## Example Usage

{{{{ example("example") }}}}

## Schema

{{{{ schema() }}}}
"""

    def _resource_example(self, name: str) -> str:
        """Generate resource example."""
        return f'''resource "{name}" "example" {{
  # Configuration options here
}}

output "example_id" {{
  description = "The ID of the {name} resource"
  value       = {name}.example.id
}}
'''

    def _data_source_example(self, name: str) -> str:
        """Generate data source example."""
        return f'''data "{name}" "example" {{
  # Configuration options here
}}

output "example_data" {{
  description = "Data from {name}"
  value       = data.{name}.example
}}
'''

    def _function_example(self, name: str) -> str:
        """Generate function example."""
        return f"""locals {{
  example_result = {name}(
    # Function arguments here
  )
}}

output "function_result" {{
  description = "Result of {name} function"  
  value       = local.example_result
}}
"""

    def _generic_example(self, name: str) -> str:
        """Generate generic example."""
        return f"""# Example usage for {name}
# Add your Terraform configuration here
"""


# 🍲🥄👗📝🪄
