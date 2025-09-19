---
page_title: "Resource: pyvider_warning_example"
description: |-
  Demonstrates Terraform warning mechanisms for deprecated attributes and validation
---

# pyvider_warning_example (Resource)

> Demonstrate and test Terraform warning mechanisms for provider development

The `pyvider_warning_example` resource is designed to demonstrate how Terraform providers can issue warnings for deprecated attributes, configuration conflicts, and validation scenarios. This resource is primarily used for testing warning mechanisms during provider development and for educational purposes.

## When to Use This

- **Provider development**: Test warning mechanisms in Terraform providers
- **Educational purposes**: Learn how Terraform warnings work
- **Migration testing**: Test deprecated attribute warnings during API transitions
- **Validation testing**: Test configuration validation and warning scenarios
- **Documentation examples**: Demonstrate warning patterns in provider documentation

**Anti-patterns (when NOT to use):**
- Production workloads (this is a testing/demonstration resource)
- Real resource management (use actual resource types)
- Error handling (use proper error mechanisms instead of warnings)
- Critical validation (use validation rules instead of warnings)

## Quick Start

```terraform
# Basic warning demonstration
resource "pyvider_warning_example" "test" {
  name = "example"
}

# Deprecated attribute warning
resource "pyvider_warning_example" "deprecated" {
  old_name = "legacy-name"  # Will trigger deprecation warning
}
```

## Examples

### Basic Usage



### Deprecation Warnings



### Validation Scenarios



### Migration Examples



## Schema



## Warning Mechanisms

The `pyvider_warning_example` resource demonstrates several types of warnings:

### 1. Deprecated Attribute Warnings
When using the `old_name` attribute, Terraform will issue a deprecation warning:
```
Warning: Attribute 'old_name' is deprecated
Please use the 'name' attribute instead.
```

### 2. Configuration Validation Warnings
The resource validates configuration and issues warnings for:
- Mutually exclusive attributes (`name` and `source_file`)
- Missing required configuration (all attributes empty)

### 3. Migration Path Warnings
Helps demonstrate how to guide users through attribute migrations and API changes.

## Attribute Behavior

### Configuration Logic
- **`name`**: Primary attribute for specifying the resource name
- **`old_name`**: Deprecated attribute that triggers warnings
- **`source_file`**: Alternative configuration method

### Validation Rules
1. `name` and `source_file` are mutually exclusive
2. At least one of `name`, `old_name`, or `source_file` must be specified
3. `old_name` triggers a deprecation warning when used

### Value Resolution
- If `name` is specified: uses `name` value
- If `old_name` is specified: uses `old_name` value (with warning)
- If `source_file` is specified: uses `from_file:{source_file}` format
- Precedence: `name` > `old_name` > `source_file`

## Common Patterns

### Deprecation Warning Testing
```terraform
# Test deprecated attribute usage
resource "pyvider_warning_example" "deprecation_test" {
  old_name = "legacy-configuration"
}

# Verify the warning is issued
# Expected warning: "Attribute 'old_name' is deprecated"
```

### Migration Scenario Testing
```terraform
# Before migration (triggers warning)
resource "pyvider_warning_example" "before_migration" {
  old_name = "old-style-name"
}

# After migration (no warning)
resource "pyvider_warning_example" "after_migration" {
  name = "new-style-name"
}
```

### Validation Error Testing
```terraform
# This will cause a validation error
resource "pyvider_warning_example" "validation_error" {
  name        = "conflicting-name"
  source_file = "conflicting-file.txt"
  # Error: 'name' and 'source_file' are mutually exclusive
}
```

### Configuration Flexibility
```terraform
# Method 1: Direct name
resource "pyvider_warning_example" "direct" {
  name = "direct-configuration"
}

# Method 2: File-based (generates "from_file:" prefix)
resource "pyvider_warning_example" "file_based" {
  source_file = "config.yaml"
}

# Method 3: Legacy (with warning)
resource "pyvider_warning_example" "legacy" {
  old_name = "legacy-style"
}
```

## Testing Warning Mechanisms

### Unit Testing Approach
```terraform
# Test matrix for different warning scenarios
locals {
  warning_test_cases = {
    deprecated_attribute = {
      config = { old_name = "test-deprecated" }
      expected_warning = "Attribute 'old_name' is deprecated"
      expected_result = "test-deprecated"
    }

    modern_attribute = {
      config = { name = "test-modern" }
      expected_warning = null
      expected_result = "test-modern"
    }

    file_based = {
      config = { source_file = "test.conf" }
      expected_warning = null
      expected_result = "from_file:test.conf"
    }
  }
}

# Create test instances
resource "pyvider_warning_example" "test_cases" {
  for_each = local.warning_test_cases

  name        = lookup(each.value.config, "name", null)
  old_name    = lookup(each.value.config, "old_name", null)
  source_file = lookup(each.value.config, "source_file", null)
}
```

### Integration Testing
```terraform
# Test warning integration with other resources
resource "pyvider_warning_example" "integration_test" {
  old_name = "integration-legacy"
}

# Create dependent resource to test warning propagation
resource "pyvider_file_content" "warning_log" {
  filename = "/tmp/warning_test_log.txt"
  content = join("\n", [
    "Warning Integration Test",
    "Resource Name: ${pyvider_warning_example.integration_test.name}",
    "Configuration: legacy (old_name used)",
    "Expected Warning: Deprecation warning should be visible in Terraform output",
    "Test Result: ${pyvider_warning_example.integration_test.name == "integration-legacy" ? "PASS" : "FAIL"}",
    "Timestamp: ${timestamp()}"
  ])
}
```

## Advanced Warning Scenarios

### Conditional Warnings
```terraform
variable "use_legacy_config" {
  description = "Whether to use legacy configuration (triggers warnings)"
  type        = bool
  default     = false
}

resource "pyvider_warning_example" "conditional_warning" {
  name     = var.use_legacy_config ? null : "modern-config"
  old_name = var.use_legacy_config ? "legacy-config" : null
}
```

### Migration Timeline Testing
```terraform
# Simulate different stages of migration
locals {
  migration_stages = {
    stage_1_legacy = {
      old_name = "legacy-only"
      description = "Pure legacy configuration"
    }
    stage_2_hybrid = {
      name = "hybrid-config"
      old_name = "legacy-fallback"
      description = "Hybrid configuration with fallback"
    }
    stage_3_modern = {
      name = "modern-only"
      description = "Pure modern configuration"
    }
  }
}

resource "pyvider_warning_example" "migration_stages" {
  for_each = local.migration_stages

  name     = lookup(each.value, "name", null)
  old_name = lookup(each.value, "old_name", null)
}
```

### Documentation Generation
```terraform
# Generate warning documentation
resource "pyvider_file_content" "warning_documentation" {
  filename = "/tmp/warning_examples_documentation.md"
  content = join("\n", [
    "# Warning Examples Documentation",
    "",
    "## Deprecation Warnings",
    "",
    "### old_name Attribute",
    "- **Status**: Deprecated",
    "- **Replacement**: Use `name` attribute instead",
    "- **Warning Message**: \"Attribute 'old_name' is deprecated\"",
    "- **Migration Path**: Replace `old_name = \"value\"` with `name = \"value\"`",
    "",
    "## Configuration Validation",
    "",
    "### Mutually Exclusive Attributes",
    "- `name` and `source_file` cannot be used together",
    "- **Error Message**: \"'name' and 'source_file' are mutually exclusive\"",
    "",
    "### Required Configuration",
    "- At least one of `name`, `old_name`, or `source_file` must be specified",
    "- **Error Message**: \"One of 'name', 'old_name', or 'source_file' must be specified\"",
    "",
    "## Best Practices",
    "",
    "1. **Use `name` for new configurations**",
    "2. **Migrate away from `old_name` when possible**",
    "3. **Use `source_file` for file-based configurations**",
    "4. **Monitor Terraform output for deprecation warnings**",
    "",
    "Generated: ${timestamp()}"
  ])
}
```

## Error Handling and Validation

### Validation Error Scenarios
```terraform
# Test validation errors (these will fail)
# Uncomment to test error scenarios:

# resource "pyvider_warning_example" "mutual_exclusion_error" {
#   name        = "conflict-name"
#   source_file = "conflict-file"
#   # Error: 'name' and 'source_file' are mutually exclusive
# }

# resource "pyvider_warning_example" "missing_config_error" {
#   # Error: One of 'name', 'old_name', or 'source_file' must be specified
# }
```

### Warning vs. Error Distinction
```terraform
# Warning scenario (configuration works, but issues warning)
resource "pyvider_warning_example" "warning_scenario" {
  old_name = "deprecated-value"  # ⚠️ Warning issued
}

# Valid scenario (no warnings or errors)
resource "pyvider_warning_example" "valid_scenario" {
  name = "modern-value"  # ✅ No issues
}
```

## Best Practices

### 1. Warning-Aware Configuration
```terraform
# ✅ Good - modern configuration
resource "pyvider_warning_example" "modern" {
  name = "production-service"
}

# ⚠️ Acceptable for testing - deprecated configuration
resource "pyvider_warning_example" "testing_deprecated" {
  old_name = "test-legacy"
}

# ❌ Bad - conflicting configuration
# resource "pyvider_warning_example" "conflict" {
#   name        = "conflict"
#   source_file = "conflict.txt"
# }
```

### 2. Migration Strategy
```terraform
# Step 1: Identify deprecated usage
# Step 2: Plan migration timeline
# Step 3: Update configurations gradually
# Step 4: Remove deprecated attributes

# Example migration
resource "pyvider_warning_example" "migrating" {
  # Phase 1: Use deprecated attribute (with warning)
  # old_name = "legacy-service"

  # Phase 2: Migrate to modern attribute
  name = "modern-service"
}
```

### 3. Testing Integration
```terraform
# Include warning tests in CI/CD
resource "pyvider_warning_example" "ci_warning_test" {
  old_name = "ci-deprecated-test"
}

# Document expected warnings
resource "pyvider_file_content" "ci_warning_expectations" {
  filename = "/tmp/expected_warnings.txt"
  content = join("\n", [
    "Expected Warnings from CI Tests:",
    "- Warning: Attribute 'old_name' is deprecated",
    "  Resource: pyvider_warning_example.ci_warning_test",
    "  Recommendation: Use 'name' attribute instead",
    "",
    "These warnings are expected and part of the testing process."
  ])
}
```

## Troubleshooting

### Common Issues

**Issue**: No warning appears when using `old_name`
**Cause**: Terraform warnings may be suppressed or not visible in output
**Solution**: Check Terraform output verbosity and warning settings

**Issue**: Validation errors instead of warnings
**Cause**: Configuration violates validation rules
**Solution**: Fix configuration conflicts (mutual exclusion, missing values)

**Issue**: Unexpected resource behavior
**Cause**: Misunderstanding of attribute precedence
**Solution**: Review value resolution logic (name > old_name > source_file)

### Debugging Warning Mechanisms
```terraform
# Debug configuration
resource "pyvider_warning_example" "debug" {
  old_name = "debug-test"
}

# Check output values
output "debug_info" {
  value = {
    name_result = pyvider_warning_example.debug.name
    old_name_input = pyvider_warning_example.debug.old_name
    source_file_input = pyvider_warning_example.debug.source_file
    warning_expected = pyvider_warning_example.debug.old_name != null
  }
}
```

## Related Components

- [`pyvider_private_state_verifier`](../private_state_verifier.md) - Testing and verification patterns
- [`pyvider_timed_token`](../timed_token.md) - Resource lifecycle examples
- [`pyvider_file_content`](../file_content.md) - Create warning documentation and logs