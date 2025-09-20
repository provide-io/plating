---
page_title: "Data Source: pyvider_provider_config_reader"
description: |-
  Reads provider configuration settings for dynamic resource management
---

# pyvider_provider_config_reader (Data Source)

> Access provider configuration settings within your Terraform configuration

The `pyvider_provider_config_reader` data source allows you to read the current provider configuration settings. This enables dynamic resource creation based on provider settings and helps create reusable configurations that adapt to different provider configurations.

## When to Use This

- **Dynamic resource configuration**: Adapt resource settings based on provider config
- **Multi-environment deployments**: Use different API endpoints per environment
- **Configuration validation**: Verify provider settings before resource creation
- **Debugging and troubleshooting**: Inspect current provider configuration
- **Conditional logic**: Create resources based on provider capabilities

**Anti-patterns (when NOT to use):**
- Storing sensitive data in outputs (API tokens are marked sensitive)
- Hardcoding provider configuration (defeats the purpose)
- Using for application configuration (use proper config management)

## Quick Start

```terraform
# Read current provider configuration
data "pyvider_provider_config_reader" "current" {}

# Use provider config in resource creation
resource "pyvider_file_content" "config_summary" {
  filename = "/tmp/provider_config.txt"
  content = "API Endpoint: ${data.pyvider_provider_config_reader.current.api_endpoint}"
}
```

## Examples

### Basic Usage

```terraform
# Basic provider configuration reader examples

# Example 1: Read current provider configuration
data "pyvider_provider_config_reader" "current" {}

# Example 2: Use provider configuration in file creation
resource "pyvider_file_content" "provider_summary" {
  filename = "/tmp/provider_config_summary.txt"
  content = join("\n", [
    "=== Provider Configuration Summary ===",
    "",
    "API Endpoint: ${data.pyvider_provider_config_reader.current.api_endpoint != null ? data.pyvider_provider_config_reader.current.api_endpoint : "Not configured"}",
    "API Timeout: ${data.pyvider_provider_config_reader.current.api_timeout != null ? "${data.pyvider_provider_config_reader.current.api_timeout} seconds" : "Default"}",
    "API Retries: ${data.pyvider_provider_config_reader.current.api_retries != null ? data.pyvider_provider_config_reader.current.api_retries : "Default"}",
    "TLS Verification: ${data.pyvider_provider_config_reader.current.api_insecure_skip_verify != null ? (data.pyvider_provider_config_reader.current.api_insecure_skip_verify ? "DISABLED" : "ENABLED") : "Default (enabled)"}",
    "Authentication: ${data.pyvider_provider_config_reader.current.api_token != null ? "Token configured" : "No authentication"}",
    "Custom Headers: ${data.pyvider_provider_config_reader.current.api_headers != null ? length(data.pyvider_provider_config_reader.current.api_headers) : 0} headers",
    "",
    "Generated at: ${timestamp()}"
  ])
}

# Example 3: Create environment detection based on provider config
locals {
  # Determine environment from API endpoint
  detected_environment = (
    data.pyvider_provider_config_reader.current.api_endpoint != null ? (
      can(regex("localhost|127\\.0\\.0\\.1", data.pyvider_provider_config_reader.current.api_endpoint)) ? "local" :
      can(regex("dev|development", data.pyvider_provider_config_reader.current.api_endpoint)) ? "development" :
      can(regex("test|testing", data.pyvider_provider_config_reader.current.api_endpoint)) ? "testing" :
      can(regex("staging|stage", data.pyvider_provider_config_reader.current.api_endpoint)) ? "staging" :
      can(regex("prod|production", data.pyvider_provider_config_reader.current.api_endpoint)) ? "production" :
      "unknown"
    ) : "unconfigured"
  )

  # Configuration analysis
  config_analysis = {
    endpoint_configured = data.pyvider_provider_config_reader.current.api_endpoint != null
    auth_configured     = data.pyvider_provider_config_reader.current.api_token != null
    has_custom_headers  = data.pyvider_provider_config_reader.current.api_headers != null && length(data.pyvider_provider_config_reader.current.api_headers) > 0
    tls_secure         = data.pyvider_provider_config_reader.current.api_insecure_skip_verify != true

    timeout_configured = data.pyvider_provider_config_reader.current.api_timeout != null
    timeout_value     = data.pyvider_provider_config_reader.current.api_timeout
    timeout_category  = (
      data.pyvider_provider_config_reader.current.api_timeout == null ? "default" :
      data.pyvider_provider_config_reader.current.api_timeout <= 10 ? "fast" :
      data.pyvider_provider_config_reader.current.api_timeout <= 60 ? "normal" :
      data.pyvider_provider_config_reader.current.api_timeout <= 300 ? "slow" :
      "very_slow"
    )

    retries_configured = data.pyvider_provider_config_reader.current.api_retries != null
    retries_value     = data.pyvider_provider_config_reader.current.api_retries
    retries_category  = (
      data.pyvider_provider_config_reader.current.api_retries == null ? "default" :
      data.pyvider_provider_config_reader.current.api_retries == 0 ? "no_retries" :
      data.pyvider_provider_config_reader.current.api_retries <= 3 ? "conservative" :
      data.pyvider_provider_config_reader.current.api_retries <= 10 ? "aggressive" :
      "very_aggressive"
    )
  }

  # Configuration recommendations
  config_recommendations = concat(
    !local.config_analysis.endpoint_configured ? ["Configure api_endpoint in provider block"] : [],
    !local.config_analysis.auth_configured ? ["Consider configuring api_token for authentication"] : [],
    !local.config_analysis.tls_secure ? ["WARNING: TLS verification is disabled - security risk"] : [],
    local.config_analysis.timeout_category == "very_slow" ? ["Consider reducing api_timeout for better performance"] : [],
    local.config_analysis.retries_category == "very_aggressive" ? ["High retry count may cause long delays on failures"] : []
  )

  # Security assessment
  security_score = (
    (local.config_analysis.endpoint_configured && can(regex("^https://", data.pyvider_provider_config_reader.current.api_endpoint)) ? 25 : 0) +
    (local.config_analysis.auth_configured ? 25 : 0) +
    (local.config_analysis.tls_secure ? 25 : 0) +
    (!local.config_analysis.has_custom_headers || length(data.pyvider_provider_config_reader.current.api_headers) <= 5 ? 25 : 0)
  )
}

# Example 4: Create environment-specific configuration file
resource "pyvider_file_content" "environment_config" {
  filename = "/tmp/environment_config.json"
  content = jsonencode({
    detected_environment = local.detected_environment

    provider_config = {
      endpoint_url = data.pyvider_provider_config_reader.current.api_endpoint
      timeout_seconds = data.pyvider_provider_config_reader.current.api_timeout
      retry_count = data.pyvider_provider_config_reader.current.api_retries
      tls_verification = !data.pyvider_provider_config_reader.current.api_insecure_skip_verify
      authentication_enabled = data.pyvider_provider_config_reader.current.api_token != null
      custom_headers_count = data.pyvider_provider_config_reader.current.api_headers != null ? length(data.pyvider_provider_config_reader.current.api_headers) : 0
    }

    analysis = local.config_analysis

    security = {
      score = local.security_score
      level = (
        local.security_score >= 75 ? "high" :
        local.security_score >= 50 ? "medium" :
        local.security_score >= 25 ? "low" :
        "very_low"
      )
    }

    recommendations = local.config_recommendations

    timestamp = timestamp()
  })
}

# Example 5: Conditional resource creation based on provider config
resource "pyvider_file_content" "debug_info" {
  count = local.detected_environment == "development" || local.detected_environment == "local" ? 1 : 0

  filename = "/tmp/debug_info.txt"
  content = join("\n", [
    "=== DEBUG MODE ENABLED ===",
    "Environment: ${local.detected_environment}",
    "Provider endpoint: ${data.pyvider_provider_config_reader.current.api_endpoint}",
    "Timeout configuration: ${local.config_analysis.timeout_category}",
    "Retry configuration: ${local.config_analysis.retries_category}",
    "Security score: ${local.security_score}/100",
    "",
    "This file is only created in development/local environments.",
    "Generated at: ${timestamp()}"
  ])
}

resource "pyvider_file_content" "production_config" {
  count = local.detected_environment == "production" ? 1 : 0

  filename = "/tmp/production_config.txt"
  content = join("\n", [
    "=== PRODUCTION ENVIRONMENT DETECTED ===",
    "Security level: ${local.security_score >= 75 ? "ACCEPTABLE" : "NEEDS IMPROVEMENT"}",
    "TLS verification: ${local.config_analysis.tls_secure ? "ENABLED" : "DISABLED - SECURITY RISK"}",
    "Authentication: ${local.config_analysis.auth_configured ? "CONFIGURED" : "NOT CONFIGURED"}",
    "",
    length(local.config_recommendations) > 0 ? "RECOMMENDATIONS:" : "Configuration looks good!",
    join("\n", [for rec in local.config_recommendations : "- ${rec}"]),
    "",
    "Generated at: ${timestamp()}"
  ])
}

# Example 6: Create API client configuration file
resource "pyvider_file_content" "api_client_config" {
  filename = "/tmp/api_client_config.yaml"
  content = yamlencode({
    api_client = {
      base_url = data.pyvider_provider_config_reader.current.api_endpoint != null ? data.pyvider_provider_config_reader.current.api_endpoint : "http://localhost:8080"

      timeout = {
        seconds = data.pyvider_provider_config_reader.current.api_timeout != null ? data.pyvider_provider_config_reader.current.api_timeout : 30
        category = local.config_analysis.timeout_category
      }

      retry_policy = {
        max_attempts = data.pyvider_provider_config_reader.current.api_retries != null ? data.pyvider_provider_config_reader.current.api_retries + 1 : 4
        strategy = local.config_analysis.retries_category
      }

      security = {
        verify_tls = !data.pyvider_provider_config_reader.current.api_insecure_skip_verify
        auth_required = data.pyvider_provider_config_reader.current.api_token != null
      }

      headers = data.pyvider_provider_config_reader.current.api_headers != null ? data.pyvider_provider_config_reader.current.api_headers : {}
    }

    metadata = {
      environment = local.detected_environment
      security_score = local.security_score
      config_source = "terraform_provider"
      generated_at = timestamp()
    }
  })
}

output "provider_config_analysis" {
  description = "Analysis of current provider configuration"
  value = {
    detected_environment = local.detected_environment

    configuration = {
      endpoint_configured = local.config_analysis.endpoint_configured
      auth_configured = local.config_analysis.auth_configured
      tls_secure = local.config_analysis.tls_secure
      timeout_category = local.config_analysis.timeout_category
      retries_category = local.config_analysis.retries_category
    }

    security = {
      score = local.security_score
      level = (
        local.security_score >= 75 ? "high" :
        local.security_score >= 50 ? "medium" :
        local.security_score >= 25 ? "low" :
        "very_low"
      )
    }

    recommendations_count = length(local.config_recommendations)

    files_created = concat(
      [
        pyvider_file_content.provider_summary.filename,
        pyvider_file_content.environment_config.filename,
        pyvider_file_content.api_client_config.filename
      ],
      local.detected_environment == "development" || local.detected_environment == "local" ? [
        pyvider_file_content.debug_info[0].filename
      ] : [],
      local.detected_environment == "production" ? [
        pyvider_file_content.production_config[0].filename
      ] : []
    )
  }
}
```

### Conditional Resource Creation



### Multi-Provider Setup



## Schema



## Provider Configuration Attributes

The data source exposes the following provider configuration settings:

### Connection Settings
- **`api_endpoint`** - The API endpoint URL configured for the provider
- **`api_timeout`** - Request timeout in seconds
- **`api_retries`** - Number of retry attempts for failed requests

### Authentication
- **`api_token`** - API authentication token (marked as sensitive)
- **`api_headers`** - Custom headers sent with API requests

### Security Settings
- **`api_insecure_skip_verify`** - Whether TLS certificate verification is disabled

## Common Patterns

### Environment-Aware Configuration
```terraform
data "pyvider_provider_config_reader" "config" {}

locals {
  # Determine environment based on API endpoint
  environment = (
    can(regex("staging", data.pyvider_provider_config_reader.config.api_endpoint)) ? "staging" :
    can(regex("prod", data.pyvider_provider_config_reader.config.api_endpoint)) ? "production" :
    "development"
  )

  # Adjust settings based on environment
  replica_count = local.environment == "production" ? 3 : 1
  debug_enabled = local.environment == "development"
}
```

### Configuration Validation
```terraform
data "pyvider_provider_config_reader" "config" {}

locals {
  # Validate provider configuration
  config_valid = (
    data.pyvider_provider_config_reader.config.api_endpoint != null &&
    data.pyvider_provider_config_reader.config.api_timeout > 0 &&
    data.pyvider_provider_config_reader.config.api_retries >= 0
  )

  # Configuration warnings
  config_warnings = concat(
    data.pyvider_provider_config_reader.config.api_insecure_skip_verify ? ["TLS verification disabled"] : [],
    data.pyvider_provider_config_reader.config.api_timeout > 300 ? ["Very long timeout configured"] : [],
    data.pyvider_provider_config_reader.config.api_retries > 10 ? ["High retry count may cause delays"] : []
  )
}
```

### Conditional Resource Creation
```terraform
data "pyvider_provider_config_reader" "config" {}

# Only create certain resources if provider supports them
resource "pyvider_file_content" "debug_config" {
  count = data.pyvider_provider_config_reader.config.api_timeout > 60 ? 1 : 0

  filename = "/tmp/debug_enabled.conf"
  content  = "Debug mode enabled due to high timeout value"
}
```

### API Client Configuration
```terraform
data "pyvider_provider_config_reader" "config" {}

# Configure API client based on provider settings
resource "pyvider_file_content" "api_client_config" {
  filename = "/tmp/api_client.json"
  content = jsonencode({
    endpoint = data.pyvider_provider_config_reader.config.api_endpoint
    timeout  = data.pyvider_provider_config_reader.config.api_timeout
    retries  = data.pyvider_provider_config_reader.config.api_retries
    headers  = data.pyvider_provider_config_reader.config.api_headers

    # Don't expose sensitive token
    auth_configured = data.pyvider_provider_config_reader.config.api_token != null

    security = {
      tls_verify = !data.pyvider_provider_config_reader.config.api_insecure_skip_verify
    }
  })
}
```

## Security Considerations

1. **Sensitive Data**: The `api_token` is marked as sensitive and won't appear in logs
2. **Output Exposure**: Be careful not to expose sensitive configuration in outputs
3. **TLS Verification**: Check `api_insecure_skip_verify` for security implications
4. **Header Inspection**: Custom headers may contain sensitive information

```terraform
# ✅ Safe - doesn't expose sensitive data
output "provider_endpoint" {
  value = data.pyvider_provider_config_reader.config.api_endpoint
}

# ❌ Unsafe - would expose sensitive token
# output "provider_token" {
#   value = data.pyvider_provider_config_reader.config.api_token
# }

# ✅ Safe - checks if token exists without exposing it
output "auth_configured" {
  value = data.pyvider_provider_config_reader.config.api_token != null
}
```

## Multi-Provider Scenarios

When using multiple provider instances, each instance's configuration can be read separately:

```terraform
# Configure multiple provider instances
provider "pyvider" {
  alias        = "staging"
  api_endpoint = "https://staging-api.example.com"
  api_timeout  = 30
}

provider "pyvider" {
  alias        = "production"
  api_endpoint = "https://api.example.com"
  api_timeout  = 60
}

# Read configuration from each provider
data "pyvider_provider_config_reader" "staging" {
  provider = pyvider.staging
}

data "pyvider_provider_config_reader" "production" {
  provider = pyvider.production
}

# Compare configurations
locals {
  staging_timeout    = data.pyvider_provider_config_reader.staging.api_timeout
  production_timeout = data.pyvider_provider_config_reader.production.api_timeout

  timeout_difference = local.production_timeout - local.staging_timeout
}
```

## Troubleshooting

### Common Issues

**Error: "Provider context has not been configured"**
- Ensure the provider block is properly configured
- Check that required provider configuration is present

**Missing Configuration Values**
- Some attributes may be null if not configured in the provider block
- Use conditional logic to handle missing values

**Sensitive Data in Outputs**
- Terraform will prevent sensitive values from being displayed
- Use conditional checks instead of direct value access

### Debugging Provider Configuration
```terraform
data "pyvider_provider_config_reader" "debug" {}

resource "pyvider_file_content" "provider_debug" {
  filename = "/tmp/provider_debug.txt"
  content = join("\n", [
    "Provider Configuration Debug Info:",
    "================================",
    "Endpoint configured: ${data.pyvider_provider_config_reader.debug.api_endpoint != null}",
    "Timeout value: ${data.pyvider_provider_config_reader.debug.api_timeout}",
    "Retries configured: ${data.pyvider_provider_config_reader.debug.api_retries}",
    "TLS verification: ${!data.pyvider_provider_config_reader.debug.api_insecure_skip_verify}",
    "Custom headers: ${length(data.pyvider_provider_config_reader.debug.api_headers != null ? data.pyvider_provider_config_reader.debug.api_headers : {})}",
    "Authentication: ${data.pyvider_provider_config_reader.debug.api_token != null ? "Configured" : "Not configured"}",
  ])
}
```

## Related Components

- [`pyvider_env_variables`](../env_variables.md) - Read environment variables used in provider configuration
- [`pyvider_http_api`](../http_api.md) - Make requests using provider's configured endpoint
- [`pyvider_file_content`](../../resources/file_content.md) - Create configuration files based on provider settings