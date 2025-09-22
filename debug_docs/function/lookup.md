---
page_title: "Function: contains"
description: |-
  Terraform function for contains
---

# contains (Function)

Terraform function for contains

## Example Usage

```terraform
# Collection function examples

# Example 1: Working with maps and lookups
locals {
  database_configs = {
    "development" = "localhost:5432"
    "staging"     = "staging-db.example.com:5432"
    "production"  = "prod-db.example.com:5432"
  }

  environment = "staging"

  # Lookup with default value
  db_host = provider::pyvider::lookup(
    local.database_configs,
    local.environment,
    "default.example.com:5432"
  )

  # Lookup for a missing key
  test_db = provider::pyvider::lookup(
    local.database_configs,
    "testing",
    "test.example.com:5432"
  )
}

# Example 2: String and list operations
locals {
  service_names = ["web", "api", "database", "cache", "monitor"]
  log_message = "Error connecting to database service"

  # Check if service exists
  has_database = provider::pyvider::contains(local.service_names, "database")
  has_analytics = provider::pyvider::contains(local.service_names, "analytics")

  # Check if log contains error
  is_error_log = provider::pyvider::contains(local.log_message, "Error")

  # Get collection sizes
  service_count = provider::pyvider::length(local.service_names)
  log_length = provider::pyvider::length(local.log_message)
}

# Example 3: Configuration management with lookups
locals {
  app_settings = {
    "max_connections" = "100"
    "timeout_seconds" = "30"
    "retry_attempts"  = "3"
    "log_level"       = "INFO"
    "cache_enabled"   = "true"
  }

  feature_flags = {
    "new_ui"      = true
    "analytics"   = false
    "dark_mode"   = true
    "beta_features" = false
  }

  # Get configuration values with defaults
  max_conn = provider::pyvider::lookup(local.app_settings, "max_connections", "50")
  timeout = provider::pyvider::lookup(local.app_settings, "timeout_seconds", "60")
  unknown_setting = provider::pyvider::lookup(local.app_settings, "unknown_key", "default_value")

  # Check feature flags
  ui_enabled = provider::pyvider::lookup(local.feature_flags, "new_ui", false)
  missing_feature = provider::pyvider::lookup(local.feature_flags, "missing_feature", false)
}

# Example 4: Complex data processing
data "pyvider_env_variables" "app_vars" {
  prefix = "APP_"
}

locals {
  # Process environment variables
  env_var_names = keys(data.pyvider_env_variables.app_vars.values)
  env_var_count = provider::pyvider::length(local.env_var_names)

  # Check for specific environment variables
  has_database_url = provider::pyvider::contains(local.env_var_names, "APP_DATABASE_URL")
  has_secret_key = provider::pyvider::contains(local.env_var_names, "APP_SECRET_KEY")

  # Get values with fallbacks
  app_name = provider::pyvider::lookup(
    data.pyvider_env_variables.app_vars.values,
    "APP_NAME",
    "DefaultApp"
  )

  app_version = provider::pyvider::lookup(
    data.pyvider_env_variables.app_vars.values,
    "APP_VERSION",
    "1.0.0"
  )
}

# Example 5: Service discovery and validation
locals {
  required_services = ["web", "api", "database"]
  available_services = ["web", "api", "database", "cache", "monitor", "logging"]

  # Check if all required services are available
  service_checks = {
    for service in local.required_services :
    service => provider::pyvider::contains(local.available_services, service)
  }

  # Count available vs required
  required_count = provider::pyvider::length(local.required_services)
  available_count = provider::pyvider::length(local.available_services)

  # Find missing services (this would require more complex logic in real Terraform)
  all_services_available = alltrue([for check in values(local.service_checks) : check])
}

# Example 6: Network configuration with lookups
locals {
  network_configs = {
    "vpc-prod"    = "10.0.0.0/16"
    "vpc-staging" = "10.1.0.0/16"
    "vpc-dev"     = "10.2.0.0/16"
  }

  subnet_configs = {
    "public"  = "/24"
    "private" = "/24"
    "db"      = "/28"
  }

  current_vpc = "vpc-prod"
  subnet_type = "private"

  # Get network configuration
  vpc_cidr = provider::pyvider::lookup(local.network_configs, local.current_vpc, "172.16.0.0/16")
  subnet_mask = provider::pyvider::lookup(local.subnet_configs, local.subnet_type, "/24")

  # Configuration validation
  has_vpc_config = provider::pyvider::contains(keys(local.network_configs), local.current_vpc)
  has_subnet_config = provider::pyvider::contains(keys(local.subnet_configs), local.subnet_type)

  total_vpcs = provider::pyvider::length(local.network_configs)
  total_subnet_types = provider::pyvider::length(local.subnet_configs)
}

# Create a comprehensive report
resource "pyvider_file_content" "collection_examples" {
  filename = "/tmp/collection_function_examples.txt"
  content = join("\n", [
    "=== Collection Function Examples ===",
    "",
    "=== Database Configuration ===",
    "Environment: ${local.environment}",
    "Database host: ${local.db_host}",
    "Test database: ${local.test_db}",
    "",
    "=== Service Management ===",
    "Available services: ${jsonencode(local.service_names)}",
    "Service count: ${local.service_count}",
    "Has database service: ${local.has_database}",
    "Has analytics service: ${local.has_analytics}",
    "",
    "=== Log Analysis ===",
    "Log message: '${local.log_message}'",
    "Message length: ${local.log_length} characters",
    "Is error log: ${local.is_error_log}",
    "",
    "=== Application Settings ===",
    "Max connections: ${local.max_conn}",
    "Timeout: ${local.timeout} seconds",
    "Unknown setting: ${local.unknown_setting}",
    "New UI enabled: ${local.ui_enabled}",
    "",
    "=== Environment Variables ===",
    "App name: ${local.app_name}",
    "App version: ${local.app_version}",
    "Environment variable count: ${local.env_var_count}",
    "Has database URL: ${local.has_database_url}",
    "Has secret key: ${local.has_secret_key}",
    "",
    "=== Service Discovery ===",
    "Required services: ${jsonencode(local.required_services)}",
    "Available services: ${jsonencode(local.available_services)}",
    "Required count: ${local.required_count}",
    "Available count: ${local.available_count}",
    "All services available: ${local.all_services_available}",
    "",
    "=== Network Configuration ===",
    "Current VPC: ${local.current_vpc}",
    "VPC CIDR: ${local.vpc_cidr}",
    "Subnet type: ${local.subnet_type}",
    "Subnet mask: ${local.subnet_mask}",
    "Has VPC config: ${local.has_vpc_config}",
    "Total VPCs configured: ${local.total_vpcs}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "collection_function_results" {
  description = "Results of various collection operations"
  value = {
    database_config = {
      environment = local.environment
      host = local.db_host
      test_host = local.test_db
    }

    service_management = {
      service_count = local.service_count
      has_database = local.has_database
      has_analytics = local.has_analytics
    }

    log_analysis = {
      message_length = local.log_length
      is_error = local.is_error_log
    }

    app_configuration = {
      name = local.app_name
      version = local.app_version
      max_connections = local.max_conn
      timeout = local.timeout
      ui_enabled = local.ui_enabled
    }

    environment_vars = {
      count = local.env_var_count
      has_database_url = local.has_database_url
      has_secret_key = local.has_secret_key
    }

    service_discovery = {
      required_services = local.required_count
      available_services = local.available_count
      all_available = local.all_services_available
      service_checks = local.service_checks
    }

    network_config = {
      vpc_cidr = local.vpc_cidr
      subnet_mask = local.subnet_mask
      has_vpc_config = local.has_vpc_config
      total_vpcs = local.total_vpcs
    }

    examples_file = pyvider_file_content.collection_examples.filename
  }
}

```

## Signature

``lookup(input)``

## Arguments



