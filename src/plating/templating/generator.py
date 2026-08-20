#
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Template generation for adorned components."""

from typing import Any


class TemplateGenerator:
    """Generates templates and examples for components."""

    async def generate_template(self, name: str, component_type: str, component_class: Any) -> str:
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
                    description = f"Terraform {component_type.replace('_', ' ')} for {name}"
            else:
                description = f"Terraform {component_type.replace('_', ' ')} for {name}"
        except AttributeError:
            # No docstring attribute
            description = f"Terraform {component_type.replace('_', ' ')} for {name}"

        # A test-only component is grouped under "Test Mode" in the index, which
        # reads the subcategory from this frontmatter -- not from the component.
        subcategory = "Test Mode" if getattr(component_class, "_is_test_only", False) else None

        builder = {
            "resource": self._resource_template,
            "data_source": self._data_source_template,
            "function": self._function_template,
            "ephemeral_resource": self._ephemeral_resource_template,
            "list_resource": self._list_resource_template,
            "state_store": self._state_store_template,
            "action": self._action_template,
        }.get(component_type)

        if builder is None:
            return self._generic_template(name, description, component_type, subcategory)
        return builder(name, description, subcategory)

    async def generate_example(self, name: str, component_type: str) -> str:
        """Generate example Terraform content."""
        builder = {
            "resource": self._resource_example,
            "data_source": self._data_source_example,
            "function": self._function_example,
            "ephemeral_resource": self._ephemeral_resource_example,
            "list_resource": self._list_resource_example,
            "state_store": self._state_store_example,
            "action": self._action_example,
        }.get(component_type)

        if builder is None:
            return self._generic_example(name)
        return builder(name)

    @staticmethod
    def _subcategory_line(subcategory: str | None) -> str:
        """Render the frontmatter subcategory line, or nothing."""
        return f'subcategory: "{subcategory}"\n' if subcategory else ""

    @staticmethod
    def _provider_of(name: str) -> str:
        """Infer the provider name from a prefixed component name.

        Components are registered as "<provider>_<component>"; the provider
        half is what a state_store or list block has to name explicitly.
        """
        return name.split("_", 1)[0] if "_" in name else name

    def _resource_template(self, name: str, description: str, subcategory: str | None = None) -> str:
        """Generate resource template content."""
        return f"""---
page_title: "Resource: {name}"
{self._subcategory_line(subcategory)}description: |-
  {description}
---

# {name} (Resource)

{description}

## Example Usage

{{{{ example("example") }}}}

{{{{ schema() }}}}

## Import

```bash
terraform import {name}.example <id>
```
"""

    def _data_source_template(self, name: str, description: str, subcategory: str | None = None) -> str:
        """Generate data source template content."""
        return f"""---
page_title: "Data Source: {name}"
{self._subcategory_line(subcategory)}description: |-
  {description}
---

# {name} (Data Source)

{description}

## Example Usage

{{{{ example("example") }}}}

{{{{ schema() }}}}
"""

    def _function_template(self, name: str, description: str, subcategory: str | None = None) -> str:
        """Generate function template content."""
        return f"""---
page_title: "Function: {name}"
{self._subcategory_line(subcategory)}description: |-
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

    def _ephemeral_resource_template(self, name: str, description: str, subcategory: str | None = None) -> str:
        """Generate ephemeral resource template content."""
        return f"""---
page_title: "Ephemeral Resource: {name}"
{self._subcategory_line(subcategory)}description: |-
  {description}
---

# {name} (Ephemeral Resource)

{description}

Ephemeral resources are opened during an operation and closed when it ends.
Their values are never written to state, so they can only be consumed by
write-only attributes, provider configuration, or other ephemeral values.

## Example Usage

{{{{ example("example") }}}}

{{{{ schema() }}}}
"""

    def _list_resource_template(self, name: str, description: str, subcategory: str | None = None) -> str:
        """Generate list resource template content."""
        return f"""---
page_title: "List Resource: {name}"
{self._subcategory_line(subcategory)}description: |-
  {description}
---

# {name} (List Resource)

{description}

List resources are queried with `terraform query` from a `.tfquery.hcl` file
rather than planned or applied. The schema below is the `config` block of the
`list` block, not the schema of the managed resource being listed.

## Example Usage

{{{{ example("example") }}}}

{{{{ schema() }}}}
"""

    def _state_store_template(self, name: str, description: str, subcategory: str | None = None) -> str:
        """Generate state store template content."""
        return f"""---
page_title: "State Store: {name}"
{self._subcategory_line(subcategory)}description: |-
  {description}
---

# {name} (State Store)

{description}

State stores are configured inside the `terraform` block and hold Terraform
state on the provider's behalf. Because the store is loaded before the provider
is configured, its own `provider` block is declared inline.

## Example Usage

{{{{ example("example") }}}}

{{{{ schema() }}}}
"""

    def _action_template(self, name: str, description: str, subcategory: str | None = None) -> str:
        """Generate action template content."""
        return f"""---
page_title: "Action: {name}"
{self._subcategory_line(subcategory)}description: |-
  {description}
---

# {name} (Action)

{description}

Actions run as a side effect of an apply. They are either triggered from a
resource's `lifecycle.action_trigger` block or invoked directly.

## Example Usage

{{{{ example("example") }}}}

{{{{ schema() }}}}
"""

    def _generic_template(
        self, name: str, description: str, component_type: str, subcategory: str | None = None
    ) -> str:
        """Generate generic template content."""
        return f"""---
page_title: "{component_type.title()}: {name}"
{self._subcategory_line(subcategory)}description: |-
  {description}
---

# {name} ({component_type.title()})

{description}

## Example Usage

{{{{ example("example") }}}}

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

    def _ephemeral_resource_example(self, name: str) -> str:
        """Generate ephemeral resource example."""
        return f'''ephemeral "{name}" "example" {{
  # Configuration options here
}}

# Ephemeral values cannot be persisted. Consume them from a write-only
# attribute, a provider block, or another ephemeral resource.
'''

    def _list_resource_example(self, name: str) -> str:
        """Generate list resource example."""
        provider = self._provider_of(name)
        return f'''# Save as example.tfquery.hcl and run `terraform query`.
list "{name}" "example" {{
  provider = {provider}

  config {{
    # Filter options here
  }}
}}
'''

    def _state_store_example(self, name: str) -> str:
        """Generate state store example."""
        provider = self._provider_of(name)
        return f'''terraform {{
  state_store "{name}" {{
    provider "{provider}" {{}}

    # Configuration options here
  }}
}}
'''

    def _action_example(self, name: str) -> str:
        """Generate action example."""
        return f'''action "{name}" "example" {{
  config {{
    # Configuration options here
  }}
}}

# Actions run as a side effect of an apply, triggered from a resource:
#
#   lifecycle {{
#     action_trigger {{
#       events  = [after_create]
#       actions = [action.{name}.example]
#     }}
#   }}
'''

    def _generic_example(self, name: str) -> str:
        """Generate generic example."""
        return f"""# Example usage for {name}
# Add your Terraform configuration here
"""


# 🍽️📖🔚
