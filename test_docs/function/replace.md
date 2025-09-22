---
page_title: "Function: lower"
description: |-
  Terraform function for lower
---

# lower (Function)

Terraform function for lower

## Example Usage

```terraform
# String manipulation function examples

# Example 1: Convert text to uppercase
locals {
  greeting = "hello world!"
  upper_greeting = provider::pyvider::upper(local.greeting)
}

# Example 2: Convert environment variable to lowercase
data "pyvider_env_variables" "user_info" {
  keys = ["USER"]
}

locals {
  username_lower = provider::pyvider::lower(
    lookup(data.pyvider_env_variables.user_info.values, "USER", "unknown")
  )
}

# Example 3: Format strings with placeholders
locals {
  app_name = "MyApp"
  version = "1.2.3"
  formatted_title = provider::pyvider::format(
    "%s v%s - Environment: %s",
    local.app_name,
    local.version,
    "production"
  )
}

# Example 4: Replace text patterns
locals {
  config_template = "database_host=REPLACE_HOST;database_port=REPLACE_PORT"
  database_config = provider::pyvider::replace(
    provider::pyvider::replace(
      local.config_template,
      "REPLACE_HOST",
      "localhost"
    ),
    "REPLACE_PORT",
    "5432"
  )
}

# Example 5: Split and join strings
locals {
  csv_data = "apple,banana,cherry,date"
  fruits = provider::pyvider::split(local.csv_data, ",")
  fruits_with_and = provider::pyvider::join(local.fruits, " and ")
}

# Example 6: Complex string processing pipeline
locals {
  user_input = "  Hello, World!  "
  processed_input = provider::pyvider::upper(
    provider::pyvider::replace(
      provider::pyvider::replace(local.user_input, " ", "_"),
      ",",
      ""
    )
  )
}

# Create a file demonstrating all string functions
resource "pyvider_file_content" "string_examples" {
  filename = "/tmp/string_function_examples.txt"
  content = join("\n", [
    "=== String Manipulation Examples ===",
    "",
    "Original greeting: '${local.greeting}'",
    "Uppercase greeting: '${local.upper_greeting}'",
    "",
    "Username (lowercase): '${local.username_lower}'",
    "",
    "Formatted title: '${local.formatted_title}'",
    "",
    "Database config: '${local.database_config}'",
    "",
    "Original CSV: '${local.csv_data}'",
    "Split into fruits: ${jsonencode(local.fruits)}",
    "Joined with 'and': '${local.fruits_with_and}'",
    "",
    "User input: '${local.user_input}'",
    "Processed: '${local.processed_input}'",
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "string_function_results" {
  description = "Results of various string manipulation functions"
  value = {
    upper_example = local.upper_greeting
    lower_example = local.username_lower
    format_example = local.formatted_title
    replace_example = local.database_config
    split_example = local.fruits
    join_example = local.fruits_with_and
    pipeline_example = local.processed_input
    examples_file = pyvider_file_content.string_examples.filename
  }
}

```

## Signature

``replace(str, old, new)``

## Arguments



