---
page_title: "Data Source: pyvider_env_variables"
description: |-
  Provides access to environment variables with filtering and transformation capabilities
---

# pyvider_env_variables (Data Source)

> Read and filter environment variables with powerful transformation options

The `pyvider_env_variables` data source allows you to access environment variables from the system where Terraform is running. It provides flexible filtering by keys, prefixes, or regex patterns, plus built-in transformations for keys and values.

## When to Use This

- **Configuration management**: Read environment-specific settings
- **Multi-environment deployments**: Access different configs per environment
- **Secrets injection**: Pull sensitive values from environment variables
- **Dynamic configuration**: Use environment state to influence resource creation
- **CI/CD integration**: Access build/deployment variables

**Anti-patterns (when NOT to use):**
- Hardcoded secrets (use proper secret management instead)
- Large amounts of configuration data (use config files)
- Complex data structures (environment variables are strings only)

## Quick Start

```terraform
# Read specific environment variables
data "pyvider_env_variables" "app_config" {
  keys = ["DATABASE_URL", "API_KEY", "DEBUG"]
}

# Access the values
resource "pyvider_file_content" "config" {
  filename = "/tmp/app.conf"
  content = "DATABASE_URL=${lookup(data.pyvider_env_variables.app_config.values, "DATABASE_URL", "localhost")}"
}
```

## Examples

### Basic Usage

```terraform
# Basic environment variable access examples

# Read specific environment variables
data "pyvider_env_variables" "system_info" {
  keys = ["USER", "HOME", "PATH", "SHELL"]
}

# Read all variables with a specific prefix
data "pyvider_env_variables" "terraform_vars" {
  prefix = "TF_"
}

# Read variables using regex pattern
data "pyvider_env_variables" "path_vars" {
  regex = ".*PATH.*"  # Matches PATH, LD_LIBRARY_PATH, etc.
}

# Create a system info file using environment variables
resource "pyvider_file_content" "system_info" {
  filename = "/tmp/system_info.txt"
  content = join("\n", [
    "=== System Information ===",
    "User: ${lookup(data.pyvider_env_variables.system_info.values, "USER", "unknown")}",
    "Home: ${lookup(data.pyvider_env_variables.system_info.values, "HOME", "/tmp")}",
    "Shell: ${lookup(data.pyvider_env_variables.system_info.values, "SHELL", "/bin/sh")}",
    "",
    "=== Environment Variables ===",
    "Total system variables found: ${length(data.pyvider_env_variables.system_info.all_environment)}",
    "Terraform variables found: ${length(data.pyvider_env_variables.terraform_vars.values)}",
    "PATH-related variables found: ${length(data.pyvider_env_variables.path_vars.values)}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

# Example with default values for missing variables
data "pyvider_env_variables" "optional_config" {
  keys = ["DATABASE_URL", "REDIS_URL", "LOG_LEVEL", "DEBUG"]
}

locals {
  # Provide sensible defaults for missing environment variables
  config = {
    database_url = lookup(data.pyvider_env_variables.optional_config.values, "DATABASE_URL", "sqlite:///tmp/app.db")
    redis_url    = lookup(data.pyvider_env_variables.optional_config.values, "REDIS_URL", "redis://localhost:6379")
    log_level    = lookup(data.pyvider_env_variables.optional_config.values, "LOG_LEVEL", "INFO")
    debug_mode   = lookup(data.pyvider_env_variables.optional_config.values, "DEBUG", "false") == "true"
  }
}

# Create application configuration file
resource "pyvider_file_content" "app_config" {
  filename = "/tmp/application.conf"
  content = join("\n", [
    "# Application Configuration",
    "# Generated from environment variables with defaults",
    "",
    "[database]",
    "url = ${local.config.database_url}",
    "",
    "[cache]",
    "url = ${local.config.redis_url}",
    "",
    "[logging]",
    "level = ${local.config.log_level}",
    "debug = ${local.config.debug_mode}",
    "",
    "# Available environment variables:",
    "${join("\n", [for key in keys(data.pyvider_env_variables.optional_config.all_environment) : "# ${key}"])}",
    "",
    "# Configuration last updated: ${timestamp()}"
  ])
}

# Example using lookup with complex logic
locals {
  # Determine if we're in a CI environment
  is_ci = anytrue([
    lookup(data.pyvider_env_variables.system_info.all_environment, "CI", "") == "true",
    lookup(data.pyvider_env_variables.system_info.all_environment, "GITHUB_ACTIONS", "") == "true",
    lookup(data.pyvider_env_variables.system_info.all_environment, "GITLAB_CI", "") == "true",
    lookup(data.pyvider_env_variables.system_info.all_environment, "JENKINS_URL", "") != ""
  ])

  # Get user preference or default
  preferred_editor = lookup(
    data.pyvider_env_variables.system_info.values,
    "EDITOR",
    lookup(data.pyvider_env_variables.system_info.values, "VISUAL", "nano")
  )
}

resource "pyvider_file_content" "environment_analysis" {
  filename = "/tmp/env_analysis.json"
  content = jsonencode({
    environment_type = local.is_ci ? "ci" : "development"
    user_info = {
      username        = lookup(data.pyvider_env_variables.system_info.values, "USER", "unknown")
      home_directory  = lookup(data.pyvider_env_variables.system_info.values, "HOME", "/tmp")
      preferred_shell = lookup(data.pyvider_env_variables.system_info.values, "SHELL", "/bin/sh")
      preferred_editor = local.preferred_editor
    }
    system_info = {
      total_env_vars    = length(data.pyvider_env_variables.system_info.all_environment)
      terraform_vars    = length(data.pyvider_env_variables.terraform_vars.values)
      path_related_vars = length(data.pyvider_env_variables.path_vars.values)
      is_ci_environment = local.is_ci
    }
    application_config = local.config
    timestamp = timestamp()
  })
}

output "basic_examples" {
  description = "Basic environment variable usage examples"
  value = {
    user_info = {
      username = lookup(data.pyvider_env_variables.system_info.values, "USER", "unknown")
      home     = lookup(data.pyvider_env_variables.system_info.values, "HOME", "/tmp")
    }

    environment_stats = {
      total_variables      = length(data.pyvider_env_variables.system_info.all_environment)
      terraform_variables  = length(data.pyvider_env_variables.terraform_vars.values)
      path_variables      = length(data.pyvider_env_variables.path_vars.values)
    }

    application_config = local.config

    ci_detection = {
      is_ci_environment = local.is_ci
      preferred_editor  = local.preferred_editor
    }

    created_files = [
      pyvider_file_content.system_info.filename,
      pyvider_file_content.app_config.filename,
      pyvider_file_content.environment_analysis.filename
    ]
  }
}
```

### Filtering and Transformations

```terraform
# Advanced filtering and transformation examples

# Filter by prefix with case-sensitive matching
data "pyvider_env_variables" "app_config_sensitive" {
  prefix = "MYAPP_"
  case_sensitive = true
}

# Filter by prefix with case-insensitive matching
data "pyvider_env_variables" "app_config_insensitive" {
  prefix = "myapp_"
  case_sensitive = false  # Matches MYAPP_, MyApp_, myapp_, etc.
}

# Apply transformations to keys and values
data "pyvider_env_variables" "transformed_vars" {
  prefix = "CONFIG_"
  transform_keys = "lower"    # CONFIG_DATABASE_URL becomes config_database_url
  transform_values = "upper"  # Transform all values to uppercase
}

# Complex regex patterns
data "pyvider_env_variables" "url_vars" {
  regex = ".*_URL$"  # Matches any variable ending in _URL
}

data "pyvider_env_variables" "port_vars" {
  regex = ".*PORT.*"  # Matches variables containing PORT anywhere
}

data "pyvider_env_variables" "credential_vars" {
  regex = ".*(KEY|SECRET|TOKEN|PASSWORD).*"  # Security-related variables
}

# Include empty variables
data "pyvider_env_variables" "with_empty" {
  prefix = "OPTIONAL_"
  exclude_empty = false  # Include variables that exist but are empty
}

# Exclude empty variables (default behavior)
data "pyvider_env_variables" "without_empty" {
  prefix = "OPTIONAL_"
  exclude_empty = true
}

# Multiple filtering approaches combined
locals {
  # Combine different filtering results
  all_urls = merge(
    data.pyvider_env_variables.url_vars.values,
    {for k, v in data.pyvider_env_variables.app_config_sensitive.values : k => v if can(regex(".*_URL$", k))}
  )

  # Transform app config variables to a more usable format
  app_config = {
    for key, value in data.pyvider_env_variables.transformed_vars.values :
    replace(replace(key, "config_", ""), "_", ".") => lower(value)
  }

  # Categorize variables by type
  variable_categories = {
    urls = {
      for k, v in data.pyvider_env_variables.url_vars.values : k => v
    }
    ports = {
      for k, v in data.pyvider_env_variables.port_vars.values : k => {
        value = v
        parsed_port = can(tonumber(v)) ? tonumber(v) : null
        is_valid_port = can(tonumber(v)) && tonumber(v) > 0 && tonumber(v) <= 65535
      }
    }
    credentials = {
      for k, v in data.pyvider_env_variables.credential_vars.values : k => {
        length = length(v)
        has_value = v != ""
      }
    }
  }
}

# Create configuration files using filtered variables
resource "pyvider_file_content" "network_config" {
  filename = "/tmp/network_config.yaml"
  content = yamlencode({
    services = {
      for url_key, url_value in local.all_urls :
      replace(lower(url_key), "_url", "") => {
        url = url_value
        type = can(regex("^https?://", url_value)) ? "http" : (
          can(regex("^postgresql://", url_value)) ? "database" : (
            can(regex("^redis://", url_value)) ? "cache" : "unknown"
          )
        )
      }
    }
    ports = {
      for port_key, port_data in local.variable_categories.ports :
      lower(port_key) => {
        value = port_data.value
        number = port_data.parsed_port
        valid = port_data.is_valid_port
      }
    }
    generated_at = timestamp()
  })
}

resource "pyvider_file_content" "app_settings" {
  filename = "/tmp/app_settings.ini"
  content = join("\n", concat(
    ["# Application Settings from Environment Variables", ""],
    [for key, value in local.app_config : "${key} = ${value}"],
    ["", "# Transformation applied:", "# - Keys: lowercased, CONFIG_ prefix removed, underscores to dots", "# - Values: lowercased"]
  ))
}

# Create a summary of filtering results
resource "pyvider_file_content" "filtering_report" {
  filename = "/tmp/filtering_report.md"
  content = templatefile("${path.module}/filtering_report.md.tpl", {
    case_sensitive_count = length(data.pyvider_env_variables.app_config_sensitive.values)
    case_insensitive_count = length(data.pyvider_env_variables.app_config_insensitive.values)
    transformed_count = length(data.pyvider_env_variables.transformed_vars.values)
    url_vars_count = length(data.pyvider_env_variables.url_vars.values)
    port_vars_count = length(data.pyvider_env_variables.port_vars.values)
    credential_vars_count = length(data.pyvider_env_variables.credential_vars.values)
    with_empty_count = length(data.pyvider_env_variables.with_empty.values)
    without_empty_count = length(data.pyvider_env_variables.without_empty.values)

    case_sensitive_vars = keys(data.pyvider_env_variables.app_config_sensitive.values)
    case_insensitive_vars = keys(data.pyvider_env_variables.app_config_insensitive.values)
    url_vars = keys(data.pyvider_env_variables.url_vars.values)
    port_vars = keys(data.pyvider_env_variables.port_vars.values)
    credential_vars = keys(data.pyvider_env_variables.credential_vars.values)

    app_config = local.app_config
    variable_categories = local.variable_categories
  })
}

# Alternative approach without external template file
resource "pyvider_file_content" "filtering_summary" {
  filename = "/tmp/filtering_summary.json"
  content = jsonencode({
    filtering_results = {
      case_sensitive = {
        pattern = "MYAPP_"
        count = length(data.pyvider_env_variables.app_config_sensitive.values)
        variables = keys(data.pyvider_env_variables.app_config_sensitive.values)
      }
      case_insensitive = {
        pattern = "myapp_"
        count = length(data.pyvider_env_variables.app_config_insensitive.values)
        variables = keys(data.pyvider_env_variables.app_config_insensitive.values)
      }
      regex_filters = {
        urls = {
          pattern = ".*_URL$"
          count = length(data.pyvider_env_variables.url_vars.values)
          variables = keys(data.pyvider_env_variables.url_vars.values)
        }
        ports = {
          pattern = ".*PORT.*"
          count = length(data.pyvider_env_variables.port_vars.values)
          variables = keys(data.pyvider_env_variables.port_vars.values)
        }
        credentials = {
          pattern = ".*(KEY|SECRET|TOKEN|PASSWORD).*"
          count = length(data.pyvider_env_variables.credential_vars.values)
          variables = keys(data.pyvider_env_variables.credential_vars.values)
        }
      }
      transformations = {
        keys_lowercased = keys(data.pyvider_env_variables.transformed_vars.values)
        processed_config = local.app_config
      }
      empty_handling = {
        with_empty = length(data.pyvider_env_variables.with_empty.values)
        without_empty = length(data.pyvider_env_variables.without_empty.values)
      }
    }
    categorized_variables = local.variable_categories
    timestamp = timestamp()
  })
}

output "filtering_results" {
  description = "Results of various filtering and transformation approaches"
  value = {
    case_sensitivity = {
      sensitive_match = length(data.pyvider_env_variables.app_config_sensitive.values)
      insensitive_match = length(data.pyvider_env_variables.app_config_insensitive.values)
    }

    regex_patterns = {
      url_matches = length(data.pyvider_env_variables.url_vars.values)
      port_matches = length(data.pyvider_env_variables.port_vars.values)
      credential_matches = length(data.pyvider_env_variables.credential_vars.values)
    }

    transformations = {
      transformed_variables = length(data.pyvider_env_variables.transformed_vars.values)
      processed_config_keys = length(local.app_config)
    }

    empty_variable_handling = {
      including_empty = length(data.pyvider_env_variables.with_empty.values)
      excluding_empty = length(data.pyvider_env_variables.without_empty.values)
    }

    categorized_data = {
      total_urls = length(local.all_urls)
      valid_ports = length([for k, v in local.variable_categories.ports : k if v.is_valid_port])
      credentials_with_values = length([for k, v in local.variable_categories.credentials : k if v.has_value])
    }

    generated_files = [
      pyvider_file_content.network_config.filename,
      pyvider_file_content.app_settings.filename,
      pyvider_file_content.filtering_summary.filename
    ]
  }
}
```

### Sensitive Variable Handling

```terraform
# Sensitive variable handling examples

# Read a mix of sensitive and non-sensitive variables
data "pyvider_env_variables" "app_credentials" {
  keys = [
    "DATABASE_URL",     # Sensitive - contains credentials
    "API_SECRET_KEY",   # Sensitive - secret key
    "JWT_SIGNING_KEY",  # Sensitive - cryptographic key
    "APP_NAME",         # Not sensitive - application name
    "APP_VERSION",      # Not sensitive - version info
    "LOG_LEVEL"         # Not sensitive - logging configuration
  ]

  # Mark which variables should be treated as sensitive
  sensitive_keys = [
    "DATABASE_URL",
    "API_SECRET_KEY",
    "JWT_SIGNING_KEY"
  ]
}

# Read environment variables with prefix filtering for secrets
data "pyvider_env_variables" "secrets" {
  prefix = "SECRET_"
  # All variables with SECRET_ prefix are treated as sensitive
  sensitive_keys = [for k in keys(data.pyvider_env_variables.secrets.all_environment) : k if can(regex("^SECRET_", k))]
}

# Read configuration with selective sensitivity
data "pyvider_env_variables" "oauth_config" {
  prefix = "OAUTH_"
  sensitive_keys = [
    "OAUTH_CLIENT_SECRET",
    "OAUTH_PRIVATE_KEY"
    # OAUTH_CLIENT_ID and OAUTH_REDIRECT_URI are not sensitive
  ]
}

# Example of safely using sensitive variables
locals {
  # Non-sensitive configuration can be used directly
  app_metadata = {
    name     = lookup(data.pyvider_env_variables.app_credentials.values, "APP_NAME", "unknown-app")
    version  = lookup(data.pyvider_env_variables.app_credentials.values, "APP_VERSION", "0.0.0")
    log_level = lookup(data.pyvider_env_variables.app_credentials.values, "LOG_LEVEL", "INFO")
  }

  # For sensitive data, we need to be careful about how we use it
  # We can't directly interpolate sensitive values into strings
  has_database_url = contains(keys(data.pyvider_env_variables.app_credentials.sensitive_values), "DATABASE_URL")
  has_api_key = contains(keys(data.pyvider_env_variables.app_credentials.sensitive_values), "API_SECRET_KEY")

  # OAuth configuration (mixed sensitive/non-sensitive)
  oauth_public_config = {
    client_id = lookup(data.pyvider_env_variables.oauth_config.values, "OAUTH_CLIENT_ID", "")
    redirect_uri = lookup(data.pyvider_env_variables.oauth_config.values, "OAUTH_REDIRECT_URI", "")
    enabled = lookup(data.pyvider_env_variables.oauth_config.values, "OAUTH_ENABLED", "false") == "true"
  }
}

# Create a non-sensitive configuration file
resource "pyvider_file_content" "public_config" {
  filename = "/tmp/public_config.yaml"
  content = yamlencode({
    application = local.app_metadata
    oauth = local.oauth_public_config
    security = {
      has_database_credentials = local.has_database_url
      has_api_key = local.has_api_key
      total_secrets = length(data.pyvider_env_variables.app_credentials.sensitive_values)
    }
    generated_at = timestamp()
  })
}

# Create a template file that references sensitive variables
# Note: The actual sensitive values won't be exposed in the file content
resource "pyvider_file_content" "app_config_template" {
  filename = "/tmp/app_config_template.env"
  content = join("\n", [
    "# Application Configuration Template",
    "# This file shows which environment variables are expected",
    "",
    "# Application Metadata",
    "APP_NAME=${local.app_metadata.name}",
    "APP_VERSION=${local.app_metadata.version}",
    "LOG_LEVEL=${local.app_metadata.log_level}",
    "",
    "# Sensitive Variables (values not shown)",
    "# These must be set in the environment:",
    local.has_database_url ? "# DATABASE_URL=<configured>" : "# DATABASE_URL=<not configured>",
    local.has_api_key ? "# API_SECRET_KEY=<configured>" : "# API_SECRET_KEY=<not configured>",
    "",
    "# OAuth Configuration",
    "OAUTH_CLIENT_ID=${local.oauth_public_config.client_id}",
    "OAUTH_REDIRECT_URI=${local.oauth_public_config.redirect_uri}",
    "OAUTH_ENABLED=${local.oauth_public_config.enabled}",
    "# OAUTH_CLIENT_SECRET=<sensitive>",
    "# OAUTH_PRIVATE_KEY=<sensitive>",
    "",
    "# Configuration generated at: ${timestamp()}"
  ])
}

# Example of secure credential validation
locals {
  # Check if required sensitive variables are present
  required_secrets = ["DATABASE_URL", "API_SECRET_KEY"]
  missing_secrets = [
    for secret in local.required_secrets :
    secret if !contains(keys(data.pyvider_env_variables.app_credentials.sensitive_values), secret)
  ]

  # Validate credential formats (without exposing values)
  credential_validation = {
    database_url_format_valid = local.has_database_url ? (
      can(regex("^(postgresql|mysql|sqlite)://",
        data.pyvider_env_variables.app_credentials.sensitive_values["DATABASE_URL"]
      ))
    ) : false

    api_key_length_valid = local.has_api_key ? (
      length(data.pyvider_env_variables.app_credentials.sensitive_values["API_SECRET_KEY"]) >= 32
    ) : false
  }
}

# Create a security report (without exposing sensitive values)
resource "pyvider_file_content" "security_report" {
  filename = "/tmp/security_report.json"
  content = jsonencode({
    security_assessment = {
      total_variables_checked = length(data.pyvider_env_variables.app_credentials.keys)
      sensitive_variables_found = length(data.pyvider_env_variables.app_credentials.sensitive_values)
      non_sensitive_variables = length(data.pyvider_env_variables.app_credentials.values)

      required_secrets = {
        expected = local.required_secrets
        missing = local.missing_secrets
        all_present = length(local.missing_secrets) == 0
      }

      credential_validation = local.credential_validation

      oauth_config = {
        public_settings = local.oauth_public_config
        sensitive_keys_present = {
          client_secret = contains(keys(data.pyvider_env_variables.oauth_config.sensitive_values), "OAUTH_CLIENT_SECRET")
          private_key = contains(keys(data.pyvider_env_variables.oauth_config.sensitive_values), "OAUTH_PRIVATE_KEY")
        }
      }

      recommendations = concat(
        length(local.missing_secrets) > 0 ? ["Set missing environment variables: ${join(", ", local.missing_secrets)}"] : [],
        !local.credential_validation.database_url_format_valid ? ["Check DATABASE_URL format"] : [],
        !local.credential_validation.api_key_length_valid ? ["API_SECRET_KEY should be at least 32 characters"] : []
      )
    }
    generated_at = timestamp()
  })
}

# Example of conditional resource creation based on sensitive variables
resource "pyvider_file_content" "database_status" {
  count = local.has_database_url ? 1 : 0

  filename = "/tmp/database_available.txt"
  content = join("\n", [
    "Database configuration detected",
    "Application: ${local.app_metadata.name}",
    "Version: ${local.app_metadata.version}",
    "Database URL is configured and available",
    "URL format validation: ${local.credential_validation.database_url_format_valid ? "PASSED" : "FAILED"}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

resource "pyvider_file_content" "no_database_warning" {
  count = !local.has_database_url ? 1 : 0

  filename = "/tmp/no_database_warning.txt"
  content = join("\n", [
    "WARNING: No database configuration found",
    "Application: ${local.app_metadata.name}",
    "Please set the DATABASE_URL environment variable",
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "sensitive_variable_handling" {
  description = "Example of handling sensitive environment variables"
  value = {
    application_info = local.app_metadata

    security_status = {
      total_secrets_configured = length(data.pyvider_env_variables.app_credentials.sensitive_values)
      required_secrets_present = length(local.missing_secrets) == 0
      missing_secrets_count = length(local.missing_secrets)
      # Note: We don't expose the actual missing secret names in output
    }

    oauth_status = {
      public_config = local.oauth_public_config
      has_client_secret = contains(keys(data.pyvider_env_variables.oauth_config.sensitive_values), "OAUTH_CLIENT_SECRET")
      has_private_key = contains(keys(data.pyvider_env_variables.oauth_config.sensitive_values), "OAUTH_PRIVATE_KEY")
    }

    validation_results = local.credential_validation

    files_created = {
      public_config = pyvider_file_content.public_config.filename
      template = pyvider_file_content.app_config_template.filename
      security_report = pyvider_file_content.security_report.filename
      database_status = local.has_database_url ? pyvider_file_content.database_status[0].filename : null
      no_database_warning = !local.has_database_url ? pyvider_file_content.no_database_warning[0].filename : null
    }
  }

  # Mark this output as sensitive since it contains information about sensitive variables
  sensitive = true
}
```

### Multi-Environment Configuration

```terraform
# Multi-environment configuration management with environment variables

variable "environment" {
  description = "Target environment for deployment"
  type        = string
  default     = "development"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

# Read environment-specific variables with prefix
data "pyvider_env_variables" "env_config" {
  prefix = "${upper(var.environment)}_"
  case_sensitive = true
}

# Read common application variables
data "pyvider_env_variables" "app_common" {
  prefix = "APP_"
  sensitive_keys = ["APP_SECRET_KEY", "APP_DATABASE_PASSWORD"]
}

# Read environment-agnostic system variables
data "pyvider_env_variables" "system_config" {
  keys = ["HOSTNAME", "USER", "DEPLOYMENT_ID"]
}

# Read feature flags with environment awareness
data "pyvider_env_variables" "feature_flags" {
  regex = "^(FEATURE_|${upper(var.environment)}_FEATURE_).*"
  transform_keys = "lower"
}

locals {
  # Environment-specific configuration with fallbacks
  env_config = {
    # Database configuration
    database_url = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_DATABASE_URL",
      lookup(data.pyvider_env_variables.app_common.values, "APP_DATABASE_URL", "sqlite:///tmp/${var.environment}.db")
    )

    # Redis configuration
    redis_url = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_REDIS_URL",
      lookup(data.pyvider_env_variables.app_common.values, "APP_REDIS_URL", "redis://localhost:6379/${var.environment == "production" ? "0" : "1"}")
    )

    # API configuration
    api_base_url = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_API_BASE_URL",
      var.environment == "production" ? "https://api.example.com" : "http://localhost:3000"
    )

    # Performance settings
    worker_processes = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_WORKERS",
      var.environment == "production" ? "4" : "2"
    )

    # Security settings
    debug_enabled = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_DEBUG",
      var.environment == "development" ? "true" : "false"
    ) == "true"

    # Logging configuration
    log_level = lookup(
      data.pyvider_env_variables.env_config.values,
      "${upper(var.environment)}_LOG_LEVEL",
      var.environment == "production" ? "ERROR" : (var.environment == "staging" ? "WARN" : "DEBUG")
    )
  }

  # Process feature flags
  feature_flags = {
    for key, value in data.pyvider_env_variables.feature_flags.values :
    replace(replace(key, "feature_", ""), "${var.environment}_feature_", "") => value == "true"
  }

  # Environment-specific defaults
  environment_defaults = {
    development = {
      cache_ttl = "60"
      rate_limit = "1000"
      enable_cors = "true"
      ssl_required = "false"
    }
    staging = {
      cache_ttl = "300"
      rate_limit = "500"
      enable_cors = "true"
      ssl_required = "true"
    }
    production = {
      cache_ttl = "3600"
      rate_limit = "100"
      enable_cors = "false"
      ssl_required = "true"
    }
  }

  # Merge environment-specific settings
  runtime_config = merge(
    local.environment_defaults[var.environment],
    {
      for key, value in data.pyvider_env_variables.env_config.values :
      lower(replace(key, "${upper(var.environment)}_", "")) => value
    }
  )

  # System information
  system_info = {
    hostname = lookup(data.pyvider_env_variables.system_config.values, "HOSTNAME", "unknown")
    user = lookup(data.pyvider_env_variables.system_config.values, "USER", "unknown")
    deployment_id = lookup(data.pyvider_env_variables.system_config.values, "DEPLOYMENT_ID", "local-${formatdate("YYYYMMDD-hhmmss", timestamp())}")
  }
}

# Create environment-specific application configuration
resource "pyvider_file_content" "app_config" {
  filename = "/tmp/config-${var.environment}.yaml"
  content = yamlencode({
    environment = var.environment

    application = {
      name = lookup(data.pyvider_env_variables.app_common.values, "APP_NAME", "my-application")
      version = lookup(data.pyvider_env_variables.app_common.values, "APP_VERSION", "1.0.0")
      debug = local.env_config.debug_enabled
    }

    database = {
      url = local.env_config.database_url
      pool_size = tonumber(local.runtime_config.cache_ttl) / 60  # Derive pool size from cache TTL
    }

    cache = {
      url = local.env_config.redis_url
      ttl = tonumber(local.runtime_config.cache_ttl)
    }

    api = {
      base_url = local.env_config.api_base_url
      rate_limit = tonumber(local.runtime_config.rate_limit)
      cors_enabled = local.runtime_config.enable_cors == "true"
    }

    security = {
      ssl_required = local.runtime_config.ssl_required == "true"
      debug_enabled = local.env_config.debug_enabled
    }

    logging = {
      level = local.env_config.log_level
      structured = var.environment == "production"
    }

    features = local.feature_flags

    performance = {
      worker_processes = tonumber(local.env_config.worker_processes)
      cache_ttl = tonumber(local.runtime_config.cache_ttl)
    }

    deployment = {
      environment = var.environment
      hostname = local.system_info.hostname
      user = local.system_info.user
      deployment_id = local.system_info.deployment_id
      timestamp = timestamp()
    }
  })
}

# Create environment-specific Docker environment file
resource "pyvider_file_content" "docker_env" {
  filename = "/tmp/.env.${var.environment}"
  content = join("\n", concat(
    [
      "# Docker Environment for ${upper(var.environment)}",
      "# Generated at ${timestamp()}",
      "",
      "# Application"
    ],
    [for key, value in data.pyvider_env_variables.app_common.values : "${key}=${value}"],
    [
      "",
      "# Environment-specific configuration"
    ],
    [for key, value in data.pyvider_env_variables.env_config.values : "${key}=${value}"],
    [
      "",
      "# Runtime configuration"
    ],
    [for key, value in local.runtime_config : "${upper(key)}=${value}"],
    [
      "",
      "# Feature flags"
    ],
    [for key, value in local.feature_flags : "FEATURE_${upper(key)}=${value}"],
    [
      "",
      "# System information",
      "HOSTNAME=${local.system_info.hostname}",
      "DEPLOYMENT_USER=${local.system_info.user}",
      "DEPLOYMENT_ID=${local.system_info.deployment_id}",
      "TARGET_ENVIRONMENT=${var.environment}"
    ]
  ))
}

# Create environment comparison report
resource "pyvider_file_content" "environment_comparison" {
  filename = "/tmp/environment-comparison.json"
  content = jsonencode({
    current_environment = var.environment

    configurations = {
      for env in ["development", "staging", "production"] :
      env => merge(
        local.environment_defaults[env],
        {
          expected_variables = [
            "${upper(env)}_DATABASE_URL",
            "${upper(env)}_REDIS_URL",
            "${upper(env)}_API_BASE_URL",
            "${upper(env)}_LOG_LEVEL"
          ]
        }
      )
    }

    current_config = {
      environment_variables = length(data.pyvider_env_variables.env_config.values)
      app_variables = length(data.pyvider_env_variables.app_common.values)
      feature_flags = length(local.feature_flags)
      sensitive_variables = length(data.pyvider_env_variables.app_common.sensitive_values)
    }

    validation = {
      has_database = contains(keys(data.pyvider_env_variables.env_config.values), "${upper(var.environment)}_DATABASE_URL") ||
                    contains(keys(data.pyvider_env_variables.app_common.values), "APP_DATABASE_URL")

      has_api_config = contains(keys(data.pyvider_env_variables.env_config.values), "${upper(var.environment)}_API_BASE_URL")

      has_required_secrets = contains(keys(data.pyvider_env_variables.app_common.sensitive_values), "APP_SECRET_KEY")

      environment_specific_vars = [
        for key in keys(data.pyvider_env_variables.env_config.values) :
        key if can(regex("^${upper(var.environment)}_", key))
      ]
    }

    recommendations = concat(
      !contains(keys(data.pyvider_env_variables.env_config.values), "${upper(var.environment)}_DATABASE_URL") &&
      !contains(keys(data.pyvider_env_variables.app_common.values), "APP_DATABASE_URL") ?
      ["Set ${upper(var.environment)}_DATABASE_URL or APP_DATABASE_URL"] : [],

      !contains(keys(data.pyvider_env_variables.app_common.sensitive_values), "APP_SECRET_KEY") ?
      ["Set APP_SECRET_KEY for encryption"] : [],

      var.environment == "production" && local.env_config.debug_enabled ?
      ["Disable debug mode in production"] : [],

      var.environment == "production" && local.runtime_config.enable_cors == "true" ?
      ["Consider disabling CORS in production"] : []
    )

    generated_at = timestamp()
  })
}

# Environment-specific validation
locals {
  validation_errors = concat(
    # Production-specific validations
    var.environment == "production" ? [
      for condition, message in {
        "debug_enabled" = "Debug mode should be disabled in production"
        "cors_enabled" = "CORS should be restricted in production"
        "weak_rate_limit" = "Rate limit should be restrictive in production"
      } : message if (
        condition == "debug_enabled" && local.env_config.debug_enabled
      ) || (
        condition == "cors_enabled" && local.runtime_config.enable_cors == "true"
      ) || (
        condition == "weak_rate_limit" && tonumber(local.runtime_config.rate_limit) > 200
      )
    ] : [],

    # General validations
    [
      for condition, message in {
        "missing_database" = "Database URL is required"
        "missing_secret" = "Application secret key is required"
      } : message if (
        condition == "missing_database" && !contains(keys(data.pyvider_env_variables.env_config.values), "${upper(var.environment)}_DATABASE_URL") && !contains(keys(data.pyvider_env_variables.app_common.values), "APP_DATABASE_URL")
      ) || (
        condition == "missing_secret" && !contains(keys(data.pyvider_env_variables.app_common.sensitive_values), "APP_SECRET_KEY")
      )
    ]
  )
}

# Create validation report
resource "pyvider_file_content" "validation_report" {
  filename = "/tmp/validation-${var.environment}.txt"
  content = join("\n", concat(
    [
      "Environment Validation Report",
      "============================",
      "Environment: ${var.environment}",
      "Generated: ${timestamp()}",
      ""
    ],
    length(local.validation_errors) == 0 ? [
      "✓ All validations passed",
      "Environment is properly configured"
    ] : [
      "❌ Validation Issues Found:",
      ""
    ],
    [for error in local.validation_errors : "  - ${error}"],
    length(local.validation_errors) > 0 ? ["", "Please address these issues before deployment."] : []
  ))
}

output "multi_environment_config" {
  description = "Multi-environment configuration management results"
  value = {
    environment = var.environment

    configuration_summary = {
      environment_vars = length(data.pyvider_env_variables.env_config.values)
      app_vars = length(data.pyvider_env_variables.app_common.values)
      feature_flags = length(local.feature_flags)
      sensitive_vars = length(data.pyvider_env_variables.app_common.sensitive_values)
    }

    environment_config = {
      database_configured = local.env_config.database_url != ""
      redis_configured = local.env_config.redis_url != ""
      api_configured = local.env_config.api_base_url != ""
      debug_enabled = local.env_config.debug_enabled
      log_level = local.env_config.log_level
    }

    feature_flags_enabled = [
      for flag, enabled in local.feature_flags : flag if enabled
    ]

    validation = {
      passed = length(local.validation_errors) == 0
      error_count = length(local.validation_errors)
      # Don't expose actual errors in output for security
    }

    generated_files = [
      pyvider_file_content.app_config.filename,
      pyvider_file_content.docker_env.filename,
      pyvider_file_content.environment_comparison.filename,
      pyvider_file_content.validation_report.filename
    ]

    system_info = local.system_info
  }
}
```

## Schema



## Filtering Options

The data source provides multiple ways to filter environment variables:

### By Specific Keys
```terraform
data "pyvider_env_variables" "specific" {
  keys = ["PATH", "HOME", "USER"]
}
```

### By Prefix
```terraform
data "pyvider_env_variables" "app_vars" {
  prefix = "MYAPP_"  # Matches MYAPP_DATABASE_URL, MYAPP_DEBUG, etc.
}
```

### By Regex Pattern
```terraform
data "pyvider_env_variables" "pattern_match" {
  regex = ".*_URL$"  # Matches any variable ending in _URL
}
```

## Transformations

### Key Transformations
Transform variable names before returning:

- `"lower"` - Convert to lowercase
- `"upper"` - Convert to uppercase

### Value Transformations
Transform variable values:

- `"lower"` - Convert values to lowercase
- `"upper"` - Convert values to uppercase

### Case Sensitivity
Control case-sensitive matching:

```terraform
data "pyvider_env_variables" "case_insensitive" {
  prefix         = "myapp_"
  case_sensitive = false  # Matches MYAPP_, MyApp_, myapp_, etc.
}
```

## Sensitive Variables

Use the `sensitive_keys` parameter to mark certain variables as sensitive:

```terraform
data "pyvider_env_variables" "with_secrets" {
  keys           = ["API_KEY", "DATABASE_PASSWORD", "PUBLIC_CONFIG"]
  sensitive_keys = ["API_KEY", "DATABASE_PASSWORD"]
}

# sensitive_values contains only the sensitive ones
# values contains only the non-sensitive ones
# all_values contains everything (marked as sensitive)
```

## Empty Variable Handling

By default, empty environment variables are excluded. Control this with `exclude_empty`:

```terraform
data "pyvider_env_variables" "include_empty" {
  prefix        = "OPTIONAL_"
  exclude_empty = false  # Include variables that exist but are empty
}
```

## Output Attributes

The data source provides several output attributes:

- **`values`** - Non-sensitive variables as a map
- **`sensitive_values`** - Sensitive variables as a map (marked sensitive)
- **`all_values`** - All variables combined (marked sensitive if any are sensitive)
- **`all_environment`** - Complete environment snapshot

## Common Patterns

### Environment-Specific Configuration
```terraform
data "pyvider_env_variables" "env_config" {
  prefix = "${upper(var.environment)}_"
}

locals {
  database_url = lookup(
    data.pyvider_env_variables.env_config.values,
    "${upper(var.environment)}_DATABASE_URL",
    "postgresql://localhost:5432/default"
  )
}
```

### Feature Flag Management
```terraform
data "pyvider_env_variables" "feature_flags" {
  prefix = "FEATURE_"
  transform_keys = "lower"  # FEATURE_NEW_UI becomes feature_new_ui
}

locals {
  features = {
    for key, value in data.pyvider_env_variables.feature_flags.values :
    replace(key, "feature_", "") => value == "true"
  }
}
```

## Common Issues & Solutions

### Error: "Environment variable not found"
**Solution**: Use `lookup()` with default values for optional variables.

```terraform
# ❌ Will fail if OPTIONAL_VAR doesn't exist
locals {
  config = data.pyvider_env_variables.config.values["OPTIONAL_VAR"]
}

# ✅ Provides fallback value
locals {
  config = lookup(data.pyvider_env_variables.config.values, "OPTIONAL_VAR", "default")
}
```

### Handling Multiline Values
Environment variables containing newlines need special handling:

```terraform
data "pyvider_env_variables" "multiline" {
  keys = ["CERTIFICATE_PEM"]
}

resource "pyvider_file_content" "cert" {
  filename = "/tmp/cert.pem"
  content  = data.pyvider_env_variables.multiline.values["CERTIFICATE_PEM"]
}
```

### Boolean Environment Variables
Convert string environment variables to booleans:

```terraform
data "pyvider_env_variables" "flags" {
  prefix = "ENABLE_"
}

locals {
  boolean_flags = {
    for key, value in data.pyvider_env_variables.flags.values :
    key => contains(["true", "1", "yes", "on"], lower(value))
  }
}
```

## Security Best Practices

1. **Use `sensitive_keys`** for any secrets or credentials
2. **Avoid logging** sensitive environment variables
3. **Use least privilege** - only read variables you need
4. **Validate inputs** - environment variables are user-controlled
5. **Use defaults** - handle missing variables gracefully

## Related Components

- [`pyvider_file_content`](../../resources/file_content.md) - Write environment-based configuration files
- [`pyvider_provider_config_reader`](../provider_config_reader.md) - Access provider configuration
- [String functions](../../functions/string/) - Transform environment variable values