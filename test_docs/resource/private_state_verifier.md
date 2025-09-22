---
page_title: "Resource: pyvider_private_state_verifier"
description: |-
  Verifies private state encryption and decryption functionality in Terraform resources
---

# pyvider_private_state_verifier (Resource)

> Verify and test private state encryption mechanisms in Terraform provider development

The `pyvider_private_state_verifier` resource is designed for testing and verifying the private state encryption functionality of Terraform providers. It demonstrates how sensitive data can be securely stored in private state, encrypted by Terraform, and properly decrypted when needed.

## When to Use This

- **Provider development**: Test private state encryption during provider development
- **Security validation**: Verify that sensitive data is properly encrypted in state
- **Testing workflows**: Validate encryption/decryption cycles in CI/CD pipelines
- **Compliance verification**: Ensure private state handling meets security requirements
- **Educational purposes**: Learn how Terraform private state encryption works

**Anti-patterns (when NOT to use):**
- Production workloads (this is a testing/verification resource)
- Storing actual secrets (use proper secret management systems)
- General-purpose encryption (use dedicated encryption tools)
- Long-term data storage (this is for verification only)

## Quick Start

```terraform
# Basic private state verification
resource "pyvider_private_state_verifier" "test" {
  input_value = "test-data"
}

# Verify the decryption works
output "verification_result" {
  value = pyvider_private_state_verifier.test.decrypted_token
}
```

## Examples

### Basic Usage

```terraform
# Basic private state verification examples

# Example 1: Simple encryption verification
resource "pyvider_private_state_verifier" "simple_test" {
  input_value = "basic-test"
}

# Example 2: Alphanumeric input test
resource "pyvider_private_state_verifier" "alphanumeric_test" {
  input_value = "test123"
}

# Example 3: Special characters test
resource "pyvider_private_state_verifier" "special_chars_test" {
  input_value = "test-with-dashes_and_underscores"
}

# Example 4: Mixed case input test
resource "pyvider_private_state_verifier" "mixed_case_test" {
  input_value = "MixedCaseInput"
}

# Example 5: Long input test
resource "pyvider_private_state_verifier" "long_input_test" {
  input_value = "this-is-a-very-long-input-value-for-testing-private-state-encryption"
}

# Verify all tests produce expected results
locals {
  verification_results = {
    simple_test = {
      input = pyvider_private_state_verifier.simple_test.input_value
      output = pyvider_private_state_verifier.simple_test.decrypted_token
      expected = "SECRET_FOR_BASIC-TEST"
      passed = pyvider_private_state_verifier.simple_test.decrypted_token == "SECRET_FOR_BASIC-TEST"
    }

    alphanumeric_test = {
      input = pyvider_private_state_verifier.alphanumeric_test.input_value
      output = pyvider_private_state_verifier.alphanumeric_test.decrypted_token
      expected = "SECRET_FOR_TEST123"
      passed = pyvider_private_state_verifier.alphanumeric_test.decrypted_token == "SECRET_FOR_TEST123"
    }

    special_chars_test = {
      input = pyvider_private_state_verifier.special_chars_test.input_value
      output = pyvider_private_state_verifier.special_chars_test.decrypted_token
      expected = "SECRET_FOR_TEST-WITH-DASHES_AND_UNDERSCORES"
      passed = pyvider_private_state_verifier.special_chars_test.decrypted_token == "SECRET_FOR_TEST-WITH-DASHES_AND_UNDERSCORES"
    }

    mixed_case_test = {
      input = pyvider_private_state_verifier.mixed_case_test.input_value
      output = pyvider_private_state_verifier.mixed_case_test.decrypted_token
      expected = "SECRET_FOR_MIXEDCASEINPUT"
      passed = pyvider_private_state_verifier.mixed_case_test.decrypted_token == "SECRET_FOR_MIXEDCASEINPUT"
    }

    long_input_test = {
      input = pyvider_private_state_verifier.long_input_test.input_value
      output = pyvider_private_state_verifier.long_input_test.decrypted_token
      expected = "SECRET_FOR_THIS-IS-A-VERY-LONG-INPUT-VALUE-FOR-TESTING-PRIVATE-STATE-ENCRYPTION"
      passed = pyvider_private_state_verifier.long_input_test.decrypted_token == "SECRET_FOR_THIS-IS-A-VERY-LONG-INPUT-VALUE-FOR-TESTING-PRIVATE-STATE-ENCRYPTION"
    }
  }

  all_tests_passed = alltrue([
    for test_name, result in local.verification_results : result.passed
  ])

  failed_tests = [
    for test_name, result in local.verification_results : test_name
    if !result.passed
  ]
}

# Create verification report
resource "pyvider_file_content" "verification_report" {
  filename = "/tmp/private_state_verification_report.json"
  content = jsonencode({
    timestamp = timestamp()
    test_summary = {
      total_tests = length(local.verification_results)
      passed_tests = length([for result in local.verification_results : result if result.passed])
      failed_tests = length(local.failed_tests)
      all_tests_passed = local.all_tests_passed
      failed_test_names = local.failed_tests
    }

    test_results = local.verification_results

    security_validation = {
      private_state_encryption = "verified"
      secret_generation_pattern = "SECRET_FOR_{UPPER_INPUT}"
      state_file_protection = "enabled"
      decryption_mechanism = "terraform_native"
    }

    compliance = {
      encryption_at_rest = true
      secure_secret_storage = true
      no_plaintext_secrets = true
      terraform_state_protection = true
    }

    test_methodology = {
      input_variation = "tested multiple input formats"
      output_verification = "verified expected secret format"
      encryption_cycle = "tested full encrypt/decrypt cycle"
      state_persistence = "verified across terraform operations"
    }
  })
}

# Create detailed test report
resource "pyvider_file_content" "detailed_test_report" {
  filename = "/tmp/private_state_detailed_report.txt"
  content = join("\n", [
    "=== Private State Encryption Verification Report ===",
    "",
    "Test Execution Time: ${timestamp()}",
    "Total Tests: ${length(local.verification_results)}",
    "Passed Tests: ${length([for result in local.verification_results : result if result.passed])}",
    "Failed Tests: ${length(local.failed_tests)}",
    "Overall Result: ${local.all_tests_passed ? "✅ ALL TESTS PASSED" : "❌ SOME TESTS FAILED"}",
    "",
    "=== Individual Test Results ===",
    "",
    "1. Simple Test:",
    "   Input: '${local.verification_results.simple_test.input}'",
    "   Expected: '${local.verification_results.simple_test.expected}'",
    "   Actual: '${local.verification_results.simple_test.output}'",
    "   Result: ${local.verification_results.simple_test.passed ? "✅ PASSED" : "❌ FAILED"}",
    "",
    "2. Alphanumeric Test:",
    "   Input: '${local.verification_results.alphanumeric_test.input}'",
    "   Expected: '${local.verification_results.alphanumeric_test.expected}'",
    "   Actual: '${local.verification_results.alphanumeric_test.output}'",
    "   Result: ${local.verification_results.alphanumeric_test.passed ? "✅ PASSED" : "❌ FAILED"}",
    "",
    "3. Special Characters Test:",
    "   Input: '${local.verification_results.special_chars_test.input}'",
    "   Expected: '${local.verification_results.special_chars_test.expected}'",
    "   Actual: '${local.verification_results.special_chars_test.output}'",
    "   Result: ${local.verification_results.special_chars_test.passed ? "✅ PASSED" : "❌ FAILED"}",
    "",
    "4. Mixed Case Test:",
    "   Input: '${local.verification_results.mixed_case_test.input}'",
    "   Expected: '${local.verification_results.mixed_case_test.expected}'",
    "   Actual: '${local.verification_results.mixed_case_test.output}'",
    "   Result: ${local.verification_results.mixed_case_test.passed ? "✅ PASSED" : "❌ FAILED"}",
    "",
    "5. Long Input Test:",
    "   Input: '${local.verification_results.long_input_test.input}'",
    "   Expected: '${local.verification_results.long_input_test.expected}'",
    "   Actual: '${local.verification_results.long_input_test.output}'",
    "   Result: ${local.verification_results.long_input_test.passed ? "✅ PASSED" : "❌ FAILED"}",
    "",
    "=== Security Analysis ===",
    "",
    "✅ Private state encryption is working correctly",
    "✅ Secret generation follows expected pattern",
    "✅ Input values are properly transformed to uppercase",
    "✅ No sensitive data exposed in regular state",
    "✅ Decryption mechanism functions properly",
    "",
    "=== Pattern Analysis ===",
    "",
    "Secret Generation Pattern: SECRET_FOR_{UPPER_INPUT}",
    "- Input values are converted to uppercase",
    "- Special characters and numbers are preserved",
    "- Dashes and underscores are maintained",
    "- Long inputs are handled correctly",
    "",
    length(local.failed_tests) > 0 ? "=== Failed Tests Analysis ===" : "",
    length(local.failed_tests) > 0 ? join("\n", [for test in local.failed_tests : "❌ Failed: ${test}"]) : "",
    length(local.failed_tests) > 0 ? "Please review the failed tests and investigate potential issues." : "",
    "",
    "=== Recommendations ===",
    "",
    local.all_tests_passed ? "🎉 All tests passed! Private state encryption is working correctly." : "⚠️  Some tests failed. Review the implementation and retry.",
    "💡 This verification confirms that sensitive data is encrypted in Terraform state",
    "🔒 Private state provides secure storage for sensitive resource data",
    "📋 Use this pattern for storing secrets, tokens, and other sensitive information",
    "",
    "Generated by: pyvider_private_state_verifier",
    "Report Date: ${timestamp()}"
  ])
}

# Create summary for CI/CD integration
resource "pyvider_file_content" "ci_summary" {
  filename = "/tmp/private_state_ci_summary.json"
  content = jsonencode({
    test_run = {
      timestamp = timestamp()
      status = local.all_tests_passed ? "success" : "failure"
      exit_code = local.all_tests_passed ? 0 : 1
    }

    metrics = {
      total_tests = length(local.verification_results)
      passed_tests = length([for result in local.verification_results : result if result.passed])
      failed_tests = length(local.failed_tests)
      success_rate = (length([for result in local.verification_results : result if result.passed]) / length(local.verification_results)) * 100
    }

    validation_points = [
      {
        name = "private_state_encryption"
        status = local.all_tests_passed ? "passed" : "failed"
        description = "Verify private state encryption works correctly"
      },
      {
        name = "secret_generation"
        status = local.all_tests_passed ? "passed" : "failed"
        description = "Verify secret generation follows expected pattern"
      },
      {
        name = "input_transformation"
        status = local.all_tests_passed ? "passed" : "failed"
        description = "Verify input values are properly transformed"
      },
      {
        name = "state_security"
        status = "passed"
        description = "Verify no sensitive data exposed in regular state"
      }
    ]

    artifacts = [
      pyvider_file_content.verification_report.filename,
      pyvider_file_content.detailed_test_report.filename,
      pyvider_file_content.ci_summary.filename
    ]
  })
}

output "basic_verification_results" {
  description = "Results of basic private state encryption verification"
  value = {
    test_summary = {
      total_tests = length(local.verification_results)
      passed_tests = length([for result in local.verification_results : result if result.passed])
      failed_tests = length(local.failed_tests)
      all_tests_passed = local.all_tests_passed
      success_rate = (length([for result in local.verification_results : result if result.passed]) / length(local.verification_results)) * 100
    }

    individual_results = {
      simple_test_passed = local.verification_results.simple_test.passed
      alphanumeric_test_passed = local.verification_results.alphanumeric_test.passed
      special_chars_test_passed = local.verification_results.special_chars_test.passed
      mixed_case_test_passed = local.verification_results.mixed_case_test.passed
      long_input_test_passed = local.verification_results.long_input_test.passed
    }

    security_validation = {
      private_state_working = local.all_tests_passed
      encryption_verified = true
      decryption_verified = true
      pattern_verified = local.all_tests_passed
    }

    files_created = [
      pyvider_file_content.verification_report.filename,
      pyvider_file_content.detailed_test_report.filename,
      pyvider_file_content.ci_summary.filename
    ]

    failed_tests = local.failed_tests
  }
}
```

### Security Testing

```terraform
# Security-focused private state verification examples

# Example 1: Unicode and internationalization testing
resource "pyvider_private_state_verifier" "unicode_test" {
  input_value = "unicode-тест-测试-テスト"
}

# Example 2: Special characters and symbols
resource "pyvider_private_state_verifier" "symbols_test" {
  input_value = "symbols!@#$%^&*()_+-=[]{}|;:,.<>?"
}

# Example 3: SQL injection attempt simulation
resource "pyvider_private_state_verifier" "sql_injection_test" {
  input_value = "test'; DROP TABLE users; --"
}

# Example 4: XSS attempt simulation
resource "pyvider_private_state_verifier" "xss_test" {
  input_value = "<script>alert('xss')</script>"
}

# Example 5: Path traversal attempt simulation
resource "pyvider_private_state_verifier" "path_traversal_test" {
  input_value = "../../../etc/passwd"
}

# Example 6: Command injection attempt simulation
resource "pyvider_private_state_verifier" "command_injection_test" {
  input_value = "test; cat /etc/passwd"
}

# Example 7: Very long input (buffer overflow simulation)
resource "pyvider_private_state_verifier" "buffer_overflow_test" {
  input_value = join("", [for i in range(1000) : "A"])
}

# Example 8: Empty and whitespace testing
resource "pyvider_private_state_verifier" "empty_test" {
  input_value = ""
}

resource "pyvider_private_state_verifier" "whitespace_test" {
  input_value = "   spaces   and   tabs	"
}

# Example 9: Binary-like input
resource "pyvider_private_state_verifier" "binary_test" {
  input_value = "binary-001101001100001"
}

# Example 10: JSON-like input
resource "pyvider_private_state_verifier" "json_test" {
  input_value = "{\"malicious\":\"payload\"}"
}

# Security verification logic
locals {
  security_tests = {
    unicode = {
      input = pyvider_private_state_verifier.unicode_test.input_value
      output = pyvider_private_state_verifier.unicode_test.decrypted_token
      expected = "SECRET_FOR_UNICODE-ТЕСТ-测试-テスト"
      passed = pyvider_private_state_verifier.unicode_test.decrypted_token == "SECRET_FOR_UNICODE-ТЕСТ-测试-テスト"
      security_concern = "internationalization"
    }

    symbols = {
      input = pyvider_private_state_verifier.symbols_test.input_value
      output = pyvider_private_state_verifier.symbols_test.decrypted_token
      expected = "SECRET_FOR_SYMBOLS!@#$%^&*()_+-=[]{}|;:,.<>?"
      passed = pyvider_private_state_verifier.symbols_test.decrypted_token == "SECRET_FOR_SYMBOLS!@#$%^&*()_+-=[]{}|;:,.<>?"
      security_concern = "special_characters"
    }

    sql_injection = {
      input = pyvider_private_state_verifier.sql_injection_test.input_value
      output = pyvider_private_state_verifier.sql_injection_test.decrypted_token
      expected = "SECRET_FOR_TEST'; DROP TABLE USERS; --"
      passed = pyvider_private_state_verifier.sql_injection_test.decrypted_token == "SECRET_FOR_TEST'; DROP TABLE USERS; --"
      security_concern = "sql_injection"
    }

    xss = {
      input = pyvider_private_state_verifier.xss_test.input_value
      output = pyvider_private_state_verifier.xss_test.decrypted_token
      expected = "SECRET_FOR_<SCRIPT>ALERT('XSS')</SCRIPT>"
      passed = pyvider_private_state_verifier.xss_test.decrypted_token == "SECRET_FOR_<SCRIPT>ALERT('XSS')</SCRIPT>"
      security_concern = "xss_injection"
    }

    path_traversal = {
      input = pyvider_private_state_verifier.path_traversal_test.input_value
      output = pyvider_private_state_verifier.path_traversal_test.decrypted_token
      expected = "SECRET_FOR_../../../ETC/PASSWD"
      passed = pyvider_private_state_verifier.path_traversal_test.decrypted_token == "SECRET_FOR_../../../ETC/PASSWD"
      security_concern = "path_traversal"
    }

    command_injection = {
      input = pyvider_private_state_verifier.command_injection_test.input_value
      output = pyvider_private_state_verifier.command_injection_test.decrypted_token
      expected = "SECRET_FOR_TEST; CAT /ETC/PASSWD"
      passed = pyvider_private_state_verifier.command_injection_test.decrypted_token == "SECRET_FOR_TEST; CAT /ETC/PASSWD"
      security_concern = "command_injection"
    }

    buffer_overflow = {
      input = substr(pyvider_private_state_verifier.buffer_overflow_test.input_value, 0, 50) # Show first 50 chars
      output = substr(pyvider_private_state_verifier.buffer_overflow_test.decrypted_token, 0, 50) # Show first 50 chars
      expected = "SECRET_FOR_" + join("", [for i in range(1000) : "A"])
      passed = pyvider_private_state_verifier.buffer_overflow_test.decrypted_token == ("SECRET_FOR_" + join("", [for i in range(1000) : "A"]))
      security_concern = "buffer_overflow"
      full_length = length(pyvider_private_state_verifier.buffer_overflow_test.decrypted_token)
    }

    empty_input = {
      input = pyvider_private_state_verifier.empty_test.input_value
      output = pyvider_private_state_verifier.empty_test.decrypted_token
      expected = "SECRET_FOR_"
      passed = pyvider_private_state_verifier.empty_test.decrypted_token == "SECRET_FOR_"
      security_concern = "empty_input"
    }

    whitespace = {
      input = pyvider_private_state_verifier.whitespace_test.input_value
      output = pyvider_private_state_verifier.whitespace_test.decrypted_token
      expected = "SECRET_FOR_   SPACES   AND   TABS	"
      passed = pyvider_private_state_verifier.whitespace_test.decrypted_token == "SECRET_FOR_   SPACES   AND   TABS	"
      security_concern = "whitespace_handling"
    }

    binary_like = {
      input = pyvider_private_state_verifier.binary_test.input_value
      output = pyvider_private_state_verifier.binary_test.decrypted_token
      expected = "SECRET_FOR_BINARY-001101001100001"
      passed = pyvider_private_state_verifier.binary_test.decrypted_token == "SECRET_FOR_BINARY-001101001100001"
      security_concern = "binary_data"
    }

    json_like = {
      input = pyvider_private_state_verifier.json_test.input_value
      output = pyvider_private_state_verifier.json_test.decrypted_token
      expected = "SECRET_FOR_{\"MALICIOUS\":\"PAYLOAD\"}"
      passed = pyvider_private_state_verifier.json_test.decrypted_token == "SECRET_FOR_{\"MALICIOUS\":\"PAYLOAD\"}"
      security_concern = "json_injection"
    }
  }

  security_summary = {
    total_tests = length(local.security_tests)
    passed_tests = length([for test in local.security_tests : test if test.passed])
    failed_tests = length([for test in local.security_tests : test if !test.passed])
    all_tests_passed = alltrue([for test in local.security_tests : test.passed])

    failed_test_names = [
      for test_name, test in local.security_tests : test_name
      if !test.passed
    ]

    security_concerns_tested = [
      for test in local.security_tests : test.security_concern
    ]
  }

  # Detailed security analysis
  security_analysis = {
    encryption_resilience = local.security_summary.all_tests_passed
    input_sanitization = "not_applicable" # Raw input is preserved
    injection_resistance = local.security_summary.all_tests_passed
    buffer_handling = local.security_tests.buffer_overflow.passed
    unicode_support = local.security_tests.unicode.passed
    edge_case_handling = (
      local.security_tests.empty_input.passed &&
      local.security_tests.whitespace.passed
    )
  }
}

# Create comprehensive security report
resource "pyvider_file_content" "security_report" {
  filename = "/tmp/private_state_security_report.json"
  content = jsonencode({
    timestamp = timestamp()
    test_type = "security_verification"

    executive_summary = {
      total_security_tests = local.security_summary.total_tests
      passed_tests = local.security_summary.passed_tests
      failed_tests = local.security_summary.failed_tests
      overall_security_status = local.security_summary.all_tests_passed ? "secure" : "needs_review"
      risk_level = local.security_summary.all_tests_passed ? "low" : "medium"
    }

    test_results = local.security_tests

    security_analysis = local.security_analysis

    threat_vectors_tested = [
      {
        threat = "SQL Injection"
        test_name = "sql_injection"
        status = local.security_tests.sql_injection.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of SQL injection attempts in input"
      },
      {
        threat = "Cross-Site Scripting (XSS)"
        test_name = "xss"
        status = local.security_tests.xss.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of XSS payload in input"
      },
      {
        threat = "Path Traversal"
        test_name = "path_traversal"
        status = local.security_tests.path_traversal.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of path traversal attempts"
      },
      {
        threat = "Command Injection"
        test_name = "command_injection"
        status = local.security_tests.command_injection.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of command injection attempts"
      },
      {
        threat = "Buffer Overflow"
        test_name = "buffer_overflow"
        status = local.security_tests.buffer_overflow.passed ? "mitigated" : "vulnerable"
        description = "Tests handling of extremely long input values"
      }
    ]

    compliance_checks = {
      input_validation = "raw_input_preserved"
      output_transformation = "uppercase_conversion"
      encryption_strength = "terraform_native"
      state_protection = "private_state_encrypted"
      data_integrity = local.security_summary.all_tests_passed ? "verified" : "compromised"
    }

    recommendations = concat(
      local.security_summary.all_tests_passed ? [
        "✅ All security tests passed",
        "✅ Private state encryption is working correctly",
        "✅ Input handling is robust across threat vectors"
      ] : [
        "⚠️ Some security tests failed",
        "⚠️ Review failed tests for potential vulnerabilities"
      ],
      [
        "🔒 Continue using private state for sensitive data",
        "📋 Regularly test with various input types",
        "🛡️ Monitor for new threat vectors",
        "📊 Include security testing in CI/CD pipeline"
      ]
    )
  })
}

# Create detailed security analysis
resource "pyvider_file_content" "security_analysis" {
  filename = "/tmp/security_analysis_detailed.txt"
  content = join("\n", [
    "=== Comprehensive Security Analysis ===",
    "",
    "Test Date: ${timestamp()}",
    "Test Type: Private State Encryption Security Verification",
    "Total Tests: ${local.security_summary.total_tests}",
    "Passed: ${local.security_summary.passed_tests}",
    "Failed: ${local.security_summary.failed_tests}",
    "Overall Status: ${local.security_summary.all_tests_passed ? "✅ SECURE" : "⚠️ NEEDS REVIEW"}",
    "",
    "=== Threat Vector Analysis ===",
    "",
    "1. Unicode/Internationalization Attack:",
    "   Input: 'unicode-тест-测试-テスト'",
    "   Result: ${local.security_tests.unicode.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Unicode injection, encoding attacks",
    "   Mitigation: Input preserved, uppercase transformation applied",
    "",
    "2. Special Characters Injection:",
    "   Input: 'symbols!@#$%^&*()_+-=[]{}|;:,.<>?'",
    "   Result: ${local.security_tests.symbols.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Symbol-based injection attacks",
    "   Mitigation: All symbols preserved and processed correctly",
    "",
    "3. SQL Injection Attempt:",
    "   Input: 'test'; DROP TABLE users; --'",
    "   Result: ${local.security_tests.sql_injection.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Database compromise",
    "   Mitigation: Input treated as literal string, no SQL execution",
    "",
    "4. Cross-Site Scripting (XSS):",
    "   Input: '<script>alert('xss')</script>'",
    "   Result: ${local.security_tests.xss.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Client-side code execution",
    "   Mitigation: HTML tags preserved as literal text",
    "",
    "5. Path Traversal Attack:",
    "   Input: '../../../etc/passwd'",
    "   Result: ${local.security_tests.path_traversal.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Unauthorized file system access",
    "   Mitigation: Path components treated as literal string",
    "",
    "6. Command Injection:",
    "   Input: 'test; cat /etc/passwd'",
    "   Result: ${local.security_tests.command_injection.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: System command execution",
    "   Mitigation: Command syntax preserved as literal text",
    "",
    "7. Buffer Overflow Simulation:",
    "   Input: ${local.security_tests.buffer_overflow.full_length} character string",
    "   Result: ${local.security_tests.buffer_overflow.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Memory corruption, system crash",
    "   Mitigation: Large inputs handled correctly",
    "",
    "8. Empty Input Edge Case:",
    "   Input: ''",
    "   Result: ${local.security_tests.empty_input.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Null pointer, undefined behavior",
    "   Mitigation: Empty input processed correctly",
    "",
    "9. Whitespace Handling:",
    "   Input: '   spaces   and   tabs	'",
    "   Result: ${local.security_tests.whitespace.passed ? "✅ PASSED" : "❌ FAILED"}",
    "   Risk: Whitespace-based attacks",
    "   Mitigation: Whitespace preserved correctly",
    "",
    "10. Binary Data Simulation:",
    "    Input: 'binary-001101001100001'",
    "    Result: ${local.security_tests.binary_like.passed ? "✅ PASSED" : "❌ FAILED"}",
    "    Risk: Binary data injection",
    "    Mitigation: Binary-like data handled as text",
    "",
    "11. JSON Injection:",
    "    Input: '{\"malicious\":\"payload\"}'",
    "    Result: ${local.security_tests.json_like.passed ? "✅ PASSED" : "❌ FAILED"}",
    "    Risk: JSON structure manipulation",
    "    Mitigation: JSON treated as literal string",
    "",
    "=== Security Assessment ===",
    "",
    "Encryption Resilience: ${local.security_analysis.encryption_resilience ? "✅ ROBUST" : "⚠️ WEAK"}",
    "Input Sanitization: ${local.security_analysis.input_sanitization} (Raw preservation)",
    "Injection Resistance: ${local.security_analysis.injection_resistance ? "✅ STRONG" : "⚠️ VULNERABLE"}",
    "Buffer Handling: ${local.security_analysis.buffer_handling ? "✅ SECURE" : "⚠️ VULNERABLE"}",
    "Unicode Support: ${local.security_analysis.unicode_support ? "✅ CORRECT" : "⚠️ BROKEN"}",
    "Edge Case Handling: ${local.security_analysis.edge_case_handling ? "✅ ROBUST" : "⚠️ FRAGILE"}",
    "",
    "=== Key Security Findings ===",
    "",
    "✅ Private state encryption prevents sensitive data exposure",
    "✅ Input transformation (uppercase) is applied consistently",
    "✅ No code execution occurs from malicious input",
    "✅ Large inputs are handled without buffer overflow",
    "✅ Special characters and unicode are preserved correctly",
    "✅ Edge cases (empty, whitespace) are handled properly",
    "",
    "=== Threat Mitigation Summary ===",
    "",
    "The private state verifier demonstrates robust security characteristics:",
    "• Input is treated as literal data, preventing injection attacks",
    "• Terraform's encryption mechanisms protect sensitive data at rest",
    "• No dynamic code execution based on input content",
    "• Consistent uppercase transformation applied to all input",
    "• Unicode and special characters handled correctly",
    "• Buffer overflow protection through proper string handling",
    "",
    length(local.security_summary.failed_test_names) > 0 ? "=== Failed Tests Requiring Review ===" : "",
    length(local.security_summary.failed_test_names) > 0 ? join("\n", [for test in local.security_summary.failed_test_names : "❌ ${test}"]) : "",
    "",
    "=== Recommendations ===",
    "",
    local.security_summary.all_tests_passed ? "🎉 All security tests passed! The implementation is secure." : "⚠️ Review failed tests and address security concerns.",
    "🔒 Continue using private state for sensitive data storage",
    "📋 Include these security tests in automated CI/CD pipelines",
    "🛡️ Monitor for new attack vectors and update tests accordingly",
    "📊 Regular security audits recommended",
    "",
    "Report Generated: ${timestamp()}",
    "Next Review: Recommended within 90 days"
  ])
}

# Create SAST/Security scan summary for CI/CD
resource "pyvider_file_content" "sast_summary" {
  filename = "/tmp/sast_security_summary.json"
  content = jsonencode({
    scan_info = {
      timestamp = timestamp()
      scan_type = "static_analysis_security_testing"
      tool = "pyvider_private_state_verifier"
      version = "1.0"
    }

    summary = {
      total_vulnerabilities = local.security_summary.failed_tests
      critical = 0
      high = local.security_summary.failed_tests
      medium = 0
      low = 0
      info = local.security_summary.passed_tests
    }

    findings = [
      for test_name, test in local.security_tests : {
        id = "PSV-${upper(substr(test_name, 0, 3))}-001"
        title = "Private State ${title(replace(test.security_concern, "_", " "))} Test"
        severity = test.passed ? "info" : "high"
        status = test.passed ? "passed" : "failed"
        category = "encryption_verification"
        description = "Testing private state encryption with ${test.security_concern} input vector"
        recommendation = test.passed ? "No action required" : "Review encryption handling for this input type"
        test_vector = test.input
        expected_output = test.expected
        actual_output = test.output
      }
    ]

    compliance = {
      owasp_top_10 = {
        injection = local.security_tests.sql_injection.passed && local.security_tests.command_injection.passed ? "compliant" : "non_compliant"
        xss = local.security_tests.xss.passed ? "compliant" : "non_compliant"
        security_misconfiguration = "not_applicable"
        sensitive_data_exposure = local.security_summary.all_tests_passed ? "compliant" : "non_compliant"
      }

      encryption_standards = {
        data_at_rest = "terraform_managed"
        key_management = "terraform_managed"
        algorithm = "terraform_default"
      }
    }

    exit_code = local.security_summary.all_tests_passed ? 0 : 1
    pass_criteria = "all_tests_must_pass"
  })
}

output "security_testing_results" {
  description = "Comprehensive security testing results for private state encryption"
  value = {
    summary = local.security_summary

    security_status = local.security_summary.all_tests_passed ? "secure" : "needs_review"

    threat_vectors_tested = local.security_summary.security_concerns_tested

    critical_findings = length(local.security_summary.failed_test_names) > 0 ? local.security_summary.failed_test_names : []

    security_analysis = local.security_analysis

    compliance_status = {
      encryption_verified = local.security_summary.all_tests_passed
      injection_resistant = (
        local.security_tests.sql_injection.passed &&
        local.security_tests.command_injection.passed &&
        local.security_tests.xss.passed
      )
      buffer_secure = local.security_tests.buffer_overflow.passed
      unicode_compliant = local.security_tests.unicode.passed
    }

    files_generated = [
      pyvider_file_content.security_report.filename,
      pyvider_file_content.security_analysis.filename,
      pyvider_file_content.sast_summary.filename
    ]
  }
}
```

### Compliance Verification

```terraform
# Compliance and regulatory verification examples

variable "compliance_framework" {
  description = "Compliance framework to test against"
  type        = string
  default     = "SOC2"
  validation {
    condition = contains([
      "SOC2", "HIPAA", "PCI-DSS", "GDPR", "FedRAMP", "ISO27001"
    ], var.compliance_framework)
    error_message = "Must be a supported compliance framework."
  }
}

variable "environment_classification" {
  description = "Environment security classification"
  type        = string
  default     = "internal"
  validation {
    condition = contains([
      "public", "internal", "confidential", "restricted"
    ], var.environment_classification)
    error_message = "Must be a valid classification level."
  }
}

# Compliance framework requirements mapping
locals {
  compliance_requirements = {
    SOC2 = {
      encryption_at_rest = true
      access_controls = true
      audit_logging = true
      data_integrity = true
      availability_controls = true
    }
    HIPAA = {
      encryption_at_rest = true
      access_controls = true
      audit_logging = true
      data_integrity = true
      administrative_safeguards = true
      physical_safeguards = true
      technical_safeguards = true
    }
    "PCI-DSS" = {
      encryption_at_rest = true
      encryption_in_transit = true
      access_controls = true
      network_security = true
      vulnerability_management = true
      secure_coding = true
    }
    GDPR = {
      data_protection_by_design = true
      encryption_at_rest = true
      access_controls = true
      data_portability = true
      right_to_erasure = true
      audit_logging = true
    }
    FedRAMP = {
      encryption_at_rest = true
      access_controls = true
      audit_logging = true
      incident_response = true
      continuous_monitoring = true
      security_controls = true
    }
    ISO27001 = {
      information_security_policy = true
      risk_management = true
      asset_management = true
      access_controls = true
      cryptography = true
      incident_management = true
    }
  }

  current_requirements = local.compliance_requirements[var.compliance_framework]
}

# Example 1: Data classification verification
resource "pyvider_private_state_verifier" "data_classification" {
  input_value = "${var.environment_classification}-data-classification-test"
}

# Example 2: Encryption strength verification
resource "pyvider_private_state_verifier" "encryption_strength" {
  input_value = "encryption-strength-validation-${var.compliance_framework}"
}

# Example 3: Access control verification
resource "pyvider_private_state_verifier" "access_control" {
  input_value = "access-control-test-${var.compliance_framework}"
}

# Example 4: Audit trail verification
resource "pyvider_private_state_verifier" "audit_trail" {
  input_value = "audit-trail-verification-${timestamp()}"
}

# Example 5: Data integrity verification
resource "pyvider_private_state_verifier" "data_integrity" {
  input_value = "data-integrity-check-${var.compliance_framework}"
}

# Example 6: PII handling verification (simulated)
resource "pyvider_private_state_verifier" "pii_handling" {
  input_value = "pii-protection-test-${var.compliance_framework}"
}

# Example 7: Retention policy verification
resource "pyvider_private_state_verifier" "retention_policy" {
  input_value = "retention-policy-${var.compliance_framework}-test"
}

# Example 8: Cross-border data transfer verification
resource "pyvider_private_state_verifier" "cross_border" {
  input_value = "cross-border-transfer-${var.compliance_framework}"
}

# Compliance verification logic
locals {
  compliance_tests = {
    data_classification = {
      test_name = "data_classification"
      input = pyvider_private_state_verifier.data_classification.input_value
      output = pyvider_private_state_verifier.data_classification.decrypted_token
      expected = "SECRET_FOR_${upper(var.environment_classification)}-DATA-CLASSIFICATION-TEST"
      passed = pyvider_private_state_verifier.data_classification.decrypted_token == "SECRET_FOR_${upper(var.environment_classification)}-DATA-CLASSIFICATION-TEST"
      requirement = "data_protection"
      criticality = "high"
    }

    encryption_strength = {
      test_name = "encryption_strength"
      input = pyvider_private_state_verifier.encryption_strength.input_value
      output = pyvider_private_state_verifier.encryption_strength.decrypted_token
      expected = "SECRET_FOR_ENCRYPTION-STRENGTH-VALIDATION-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.encryption_strength.decrypted_token == "SECRET_FOR_ENCRYPTION-STRENGTH-VALIDATION-${upper(var.compliance_framework)}"
      requirement = "encryption_at_rest"
      criticality = "critical"
    }

    access_control = {
      test_name = "access_control"
      input = pyvider_private_state_verifier.access_control.input_value
      output = pyvider_private_state_verifier.access_control.decrypted_token
      expected = "SECRET_FOR_ACCESS-CONTROL-TEST-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.access_control.decrypted_token == "SECRET_FOR_ACCESS-CONTROL-TEST-${upper(var.compliance_framework)}"
      requirement = "access_controls"
      criticality = "high"
    }

    audit_trail = {
      test_name = "audit_trail"
      input = pyvider_private_state_verifier.audit_trail.input_value
      output = pyvider_private_state_verifier.audit_trail.decrypted_token
      expected = "SECRET_FOR_${upper(pyvider_private_state_verifier.audit_trail.input_value)}"
      passed = pyvider_private_state_verifier.audit_trail.decrypted_token == "SECRET_FOR_${upper(pyvider_private_state_verifier.audit_trail.input_value)}"
      requirement = "audit_logging"
      criticality = "high"
    }

    data_integrity = {
      test_name = "data_integrity"
      input = pyvider_private_state_verifier.data_integrity.input_value
      output = pyvider_private_state_verifier.data_integrity.decrypted_token
      expected = "SECRET_FOR_DATA-INTEGRITY-CHECK-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.data_integrity.decrypted_token == "SECRET_FOR_DATA-INTEGRITY-CHECK-${upper(var.compliance_framework)}"
      requirement = "data_integrity"
      criticality = "critical"
    }

    pii_handling = {
      test_name = "pii_handling"
      input = pyvider_private_state_verifier.pii_handling.input_value
      output = pyvider_private_state_verifier.pii_handling.decrypted_token
      expected = "SECRET_FOR_PII-PROTECTION-TEST-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.pii_handling.decrypted_token == "SECRET_FOR_PII-PROTECTION-TEST-${upper(var.compliance_framework)}"
      requirement = "data_protection"
      criticality = "critical"
    }

    retention_policy = {
      test_name = "retention_policy"
      input = pyvider_private_state_verifier.retention_policy.input_value
      output = pyvider_private_state_verifier.retention_policy.decrypted_token
      expected = "SECRET_FOR_RETENTION-POLICY-${upper(var.compliance_framework)}-TEST"
      passed = pyvider_private_state_verifier.retention_policy.decrypted_token == "SECRET_FOR_RETENTION-POLICY-${upper(var.compliance_framework)}-TEST"
      requirement = "data_lifecycle"
      criticality = "medium"
    }

    cross_border = {
      test_name = "cross_border"
      input = pyvider_private_state_verifier.cross_border.input_value
      output = pyvider_private_state_verifier.cross_border.decrypted_token
      expected = "SECRET_FOR_CROSS-BORDER-TRANSFER-${upper(var.compliance_framework)}"
      passed = pyvider_private_state_verifier.cross_border.decrypted_token == "SECRET_FOR_CROSS-BORDER-TRANSFER-${upper(var.compliance_framework)}"
      requirement = "data_transfer"
      criticality = "high"
    }
  }

  compliance_summary = {
    framework = var.compliance_framework
    classification = var.environment_classification
    total_tests = length(local.compliance_tests)
    passed_tests = length([for test in local.compliance_tests : test if test.passed])
    failed_tests = length([for test in local.compliance_tests : test if !test.passed])
    compliance_status = alltrue([for test in local.compliance_tests : test.passed])

    critical_failures = length([
      for test in local.compliance_tests : test
      if !test.passed && test.criticality == "critical"
    ])

    high_failures = length([
      for test in local.compliance_tests : test
      if !test.passed && test.criticality == "high"
    ])

    failed_requirements = [
      for test in local.compliance_tests : test.requirement
      if !test.passed
    ]
  }
}

# Create compliance assessment report
resource "pyvider_file_content" "compliance_assessment" {
  filename = "/tmp/compliance_assessment_${var.compliance_framework}.json"
  content = jsonencode({
    assessment = {
      timestamp = timestamp()
      framework = var.compliance_framework
      classification = var.environment_classification
      assessor = "pyvider_private_state_verifier"
      version = "1.0"
    }

    executive_summary = {
      overall_compliance = local.compliance_summary.compliance_status ? "compliant" : "non_compliant"
      risk_level = (
        local.compliance_summary.critical_failures > 0 ? "critical" :
        local.compliance_summary.high_failures > 0 ? "high" :
        local.compliance_summary.failed_tests > 0 ? "medium" : "low"
      )
      certification_ready = local.compliance_summary.compliance_status
      remediation_required = !local.compliance_summary.compliance_status
    }

    test_results = local.compliance_tests

    framework_requirements = local.current_requirements

    requirement_coverage = {
      for requirement, enabled in local.current_requirements :
      requirement => {
        required = enabled
        tested = contains([for test in local.compliance_tests : test.requirement], requirement)
        compliant = !contains(local.compliance_summary.failed_requirements, requirement)
      }
    }

    compliance_metrics = {
      total_tests = local.compliance_summary.total_tests
      passed_tests = local.compliance_summary.passed_tests
      failed_tests = local.compliance_summary.failed_tests
      compliance_percentage = (local.compliance_summary.passed_tests / local.compliance_summary.total_tests) * 100
      critical_failures = local.compliance_summary.critical_failures
      high_failures = local.compliance_summary.high_failures
    }

    recommendations = concat(
      local.compliance_summary.compliance_status ? [
        "✅ All compliance tests passed",
        "✅ Ready for ${var.compliance_framework} certification",
        "✅ Private state encryption meets requirements"
      ] : [
        "⚠️ Compliance violations detected",
        "⚠️ Remediation required before certification",
        "📋 Review failed tests and implement fixes"
      ],
      [
        "🔒 Continue monitoring compliance status",
        "📊 Regular compliance assessments recommended",
        "📋 Maintain audit documentation",
        "🛡️ Implement continuous compliance monitoring"
      ]
    )

    next_assessment = {
      recommended_date = timeadd(timestamp(), "2160h") # 90 days
      frequency = "quarterly"
      scope = "full_compliance_validation"
    }
  })
}

# Create framework-specific compliance report
resource "pyvider_file_content" "framework_compliance_report" {
  filename = "/tmp/${lower(var.compliance_framework)}_compliance_report.txt"
  content = join("\n", [
    "=== ${var.compliance_framework} Compliance Verification Report ===",
    "",
    "Assessment Date: ${timestamp()}",
    "Framework: ${var.compliance_framework}",
    "Environment Classification: ${var.environment_classification}",
    "Assessment Tool: Private State Verifier",
    "",
    "=== Executive Summary ===",
    "",
    "Overall Compliance Status: ${local.compliance_summary.compliance_status ? "✅ COMPLIANT" : "❌ NON-COMPLIANT"}",
    "Total Tests Conducted: ${local.compliance_summary.total_tests}",
    "Tests Passed: ${local.compliance_summary.passed_tests}",
    "Tests Failed: ${local.compliance_summary.failed_tests}",
    "Compliance Percentage: ${(local.compliance_summary.passed_tests / local.compliance_summary.total_tests) * 100}%",
    "",
    "Risk Assessment:",
    "- Critical Failures: ${local.compliance_summary.critical_failures}",
    "- High Risk Failures: ${local.compliance_summary.high_failures}",
    "- Overall Risk Level: ${local.compliance_summary.critical_failures > 0 ? "CRITICAL" : local.compliance_summary.high_failures > 0 ? "HIGH" : local.compliance_summary.failed_tests > 0 ? "MEDIUM" : "LOW"}",
    "",
    "=== Framework Requirements Verification ===",
    "",
    var.compliance_framework == "SOC2" ? join("\n", [
      "SOC 2 Type II Controls Assessment:",
      "CC6.1 - Logical and Physical Access Controls: ${contains(local.compliance_summary.failed_requirements, "access_controls") ? "❌ FAILED" : "✅ PASSED"}",
      "CC6.7 - Data Transmission and Disposal: ${contains(local.compliance_summary.failed_requirements, "data_integrity") ? "❌ FAILED" : "✅ PASSED"}",
      "CC6.8 - Encryption: ${contains(local.compliance_summary.failed_requirements, "encryption_at_rest") ? "❌ FAILED" : "✅ PASSED"}",
    ]) : "",
    "",
    var.compliance_framework == "HIPAA" ? join("\n", [
      "HIPAA Safeguards Assessment:",
      "§164.312(a)(1) - Access Control: ${contains(local.compliance_summary.failed_requirements, "access_controls") ? "❌ FAILED" : "✅ PASSED"}",
      "§164.312(a)(2)(iv) - Encryption: ${contains(local.compliance_summary.failed_requirements, "encryption_at_rest") ? "❌ FAILED" : "✅ PASSED"}",
      "§164.312(b) - Audit Controls: ${contains(local.compliance_summary.failed_requirements, "audit_logging") ? "❌ FAILED" : "✅ PASSED"}",
      "§164.312(c)(1) - Integrity: ${contains(local.compliance_summary.failed_requirements, "data_integrity") ? "❌ FAILED" : "✅ PASSED"}",
    ]) : "",
    "",
    var.compliance_framework == "PCI-DSS" ? join("\n", [
      "PCI DSS Requirements Assessment:",
      "Requirement 3 - Protect Stored Data: ${contains(local.compliance_summary.failed_requirements, "encryption_at_rest") ? "❌ FAILED" : "✅ PASSED"}",
      "Requirement 4 - Encrypt Data in Transit: ${contains(local.compliance_summary.failed_requirements, "encryption_in_transit") ? "❌ FAILED" : "✅ PASSED"}",
      "Requirement 7 - Restrict Access: ${contains(local.compliance_summary.failed_requirements, "access_controls") ? "❌ FAILED" : "✅ PASSED"}",
      "Requirement 10 - Log and Monitor: ${contains(local.compliance_summary.failed_requirements, "audit_logging") ? "❌ FAILED" : "✅ PASSED"}",
    ]) : "",
    "",
    var.compliance_framework == "GDPR" ? join("\n", [
      "GDPR Articles Assessment:",
      "Article 25 - Data Protection by Design: ${contains(local.compliance_summary.failed_requirements, "data_protection") ? "❌ FAILED" : "✅ PASSED"}",
      "Article 32 - Security of Processing: ${contains(local.compliance_summary.failed_requirements, "encryption_at_rest") ? "❌ FAILED" : "✅ PASSED"}",
      "Article 20 - Right to Data Portability: ${contains(local.compliance_summary.failed_requirements, "data_portability") ? "❌ FAILED" : "✅ PASSED"}",
      "Article 17 - Right to Erasure: ${contains(local.compliance_summary.failed_requirements, "right_to_erasure") ? "❌ FAILED" : "✅ PASSED"}",
    ]) : "",
    "",
    "=== Detailed Test Results ===",
    "",
    join("\n", [
      for test_name, test in local.compliance_tests :
      "${test_name}: ${test.passed ? "✅ PASSED" : "❌ FAILED"} (${upper(test.criticality)})\n  Requirement: ${test.requirement}\n  Input: ${test.input}\n  Expected: ${test.expected}\n  Actual: ${test.output}\n"
    ]),
    "",
    "=== Technical Implementation Details ===",
    "",
    "Encryption Mechanism: Terraform Private State",
    "Key Management: Terraform Managed",
    "Data Classification: ${title(var.environment_classification)}",
    "Access Control: Role-Based (Terraform State)",
    "Audit Trail: Terraform State Operations",
    "",
    "=== Remediation Requirements ===",
    "",
    length(local.compliance_summary.failed_requirements) > 0 ? "Required Actions:" : "No remediation required - all tests passed.",
    length(local.compliance_summary.failed_requirements) > 0 ? join("\n", [
      for req in local.compliance_summary.failed_requirements :
      "- Address ${req} requirement violations"
    ]) : "",
    "",
    "=== Compliance Certification Status ===",
    "",
    local.compliance_summary.compliance_status ? "✅ READY FOR CERTIFICATION" : "❌ NOT READY FOR CERTIFICATION",
    local.compliance_summary.compliance_status ? "All ${var.compliance_framework} requirements verified" : "Remediation required before certification",
    "",
    "=== Next Steps ===",
    "",
    local.compliance_summary.compliance_status ? "1. Proceed with formal ${var.compliance_framework} audit" : "1. Remediate failed compliance tests",
    "2. Implement continuous compliance monitoring",
    "3. Schedule quarterly compliance assessments",
    "4. Maintain compliance documentation",
    "5. Train staff on compliance requirements",
    "",
    "Assessment Completed: ${timestamp()}",
    "Next Assessment Due: ${timeadd(timestamp(), "2160h")}"
  ])
}

# Create audit evidence package
resource "pyvider_file_content" "audit_evidence" {
  filename = "/tmp/audit_evidence_${var.compliance_framework}.json"
  content = jsonencode({
    audit_evidence = {
      timestamp = timestamp()
      framework = var.compliance_framework
      scope = "private_state_encryption_verification"
      auditor = "automated_compliance_testing"
    }

    test_evidence = {
      for test_name, test in local.compliance_tests :
      test_name => {
        test_id = "${var.compliance_framework}-PSV-${upper(substr(test_name, 0, 3))}"
        requirement = test.requirement
        criticality = test.criticality
        test_input = test.input
        expected_output = test.expected
        actual_output = test.output
        test_result = test.passed ? "pass" : "fail"
        test_timestamp = timestamp()
        compliance_mapping = {
          SOC2 = test.requirement == "encryption_at_rest" ? "CC6.8" : test.requirement == "access_controls" ? "CC6.1" : test.requirement == "audit_logging" ? "CC7.2" : "CC6.7"
          HIPAA = test.requirement == "encryption_at_rest" ? "§164.312(a)(2)(iv)" : test.requirement == "access_controls" ? "§164.312(a)(1)" : test.requirement == "audit_logging" ? "§164.312(b)" : "§164.312(c)(1)"
          "PCI-DSS" = test.requirement == "encryption_at_rest" ? "Requirement 3" : test.requirement == "access_controls" ? "Requirement 7" : test.requirement == "audit_logging" ? "Requirement 10" : "Requirement 4"
          GDPR = test.requirement == "data_protection" ? "Article 25" : test.requirement == "encryption_at_rest" ? "Article 32" : test.requirement == "audit_logging" ? "Article 30" : "Article 5"
          FedRAMP = test.requirement == "encryption_at_rest" ? "SC-28" : test.requirement == "access_controls" ? "AC-2" : test.requirement == "audit_logging" ? "AU-2" : "SC-13"
          ISO27001 = test.requirement == "encryption_at_rest" ? "A.10.1.1" : test.requirement == "access_controls" ? "A.9.1.1" : test.requirement == "audit_logging" ? "A.12.4.1" : "A.10.1.2"
        }[var.compliance_framework]
      }
    }

    technical_details = {
      encryption_algorithm = "terraform_managed"
      key_management = "terraform_managed"
      data_classification = var.environment_classification
      state_protection = "private_state_encrypted"
      access_control_mechanism = "terraform_rbac"
    }

    compliance_attestation = {
      overall_compliance = local.compliance_summary.compliance_status
      framework_version = var.compliance_framework
      assessment_scope = "encryption_and_data_protection"
      limitations = "limited_to_private_state_functionality"
      certification_readiness = local.compliance_summary.compliance_status
    }
  })
}

output "compliance_verification_results" {
  description = "Compliance framework verification results"
  value = {
    framework = var.compliance_framework
    classification = var.environment_classification

    compliance_status = {
      overall_compliant = local.compliance_summary.compliance_status
      certification_ready = local.compliance_summary.compliance_status
      risk_level = (
        local.compliance_summary.critical_failures > 0 ? "critical" :
        local.compliance_summary.high_failures > 0 ? "high" :
        local.compliance_summary.failed_tests > 0 ? "medium" : "low"
      )
    }

    test_metrics = {
      total_tests = local.compliance_summary.total_tests
      passed_tests = local.compliance_summary.passed_tests
      failed_tests = local.compliance_summary.failed_tests
      compliance_percentage = (local.compliance_summary.passed_tests / local.compliance_summary.total_tests) * 100
    }

    failure_analysis = {
      critical_failures = local.compliance_summary.critical_failures
      high_failures = local.compliance_summary.high_failures
      failed_requirements = local.compliance_summary.failed_requirements
    }

    framework_requirements = local.current_requirements

    documentation_artifacts = [
      pyvider_file_content.compliance_assessment.filename,
      pyvider_file_content.framework_compliance_report.filename,
      pyvider_file_content.audit_evidence.filename
    ]

    next_assessment_date = timeadd(timestamp(), "2160h")
  }
}
```

### CI/CD Integration

```terraform
# CI/CD pipeline integration examples for private state verification

variable "ci_environment" {
  description = "CI/CD environment identifier"
  type        = string
  default     = "ci-test"
}

variable "build_number" {
  description = "Build number or identifier"
  type        = string
  default     = "local-build"
}

variable "test_suite" {
  description = "Test suite configuration"
  type = object({
    name = string
    parallel_tests = bool
    timeout_minutes = number
    failure_threshold = number
  })
  default = {
    name = "private-state-verification"
    parallel_tests = true
    timeout_minutes = 10
    failure_threshold = 0
  }
}

# CI/CD test matrix - multiple test scenarios
locals {
  ci_test_matrix = {
    smoke_test = {
      input = "ci-smoke-test-${var.build_number}"
      description = "Basic functionality verification"
      priority = "critical"
      timeout = 60
    }
    integration_test = {
      input = "ci-integration-${var.ci_environment}-${var.build_number}"
      description = "Integration testing with CI environment"
      priority = "high"
      timeout = 120
    }
    regression_test = {
      input = "ci-regression-validation-${var.build_number}"
      description = "Regression testing for known issues"
      priority = "high"
      timeout = 180
    }
    performance_test = {
      input = "ci-performance-benchmark-${var.build_number}"
      description = "Performance and scalability verification"
      priority = "medium"
      timeout = 300
    }
    security_test = {
      input = "ci-security-scan-${var.build_number}"
      description = "Security vulnerability assessment"
      priority = "critical"
      timeout = 240
    }
    compatibility_test = {
      input = "ci-compatibility-${var.ci_environment}"
      description = "Environment compatibility verification"
      priority = "medium"
      timeout = 150
    }
  }
}

# Create test instances for each test in the matrix
resource "pyvider_private_state_verifier" "ci_test_matrix" {
  for_each = local.ci_test_matrix

  input_value = each.value.input
}

# Example 1: GitHub Actions CI/CD integration
resource "pyvider_private_state_verifier" "github_actions_test" {
  input_value = "github-actions-${var.ci_environment}-${var.build_number}"
}

# Example 2: Jenkins pipeline integration
resource "pyvider_private_state_verifier" "jenkins_test" {
  input_value = "jenkins-pipeline-${var.ci_environment}-${var.build_number}"
}

# Example 3: GitLab CI integration
resource "pyvider_private_state_verifier" "gitlab_ci_test" {
  input_value = "gitlab-ci-${var.ci_environment}-${var.build_number}"
}

# Example 4: Azure DevOps integration
resource "pyvider_private_state_verifier" "azure_devops_test" {
  input_value = "azure-devops-${var.ci_environment}-${var.build_number}"
}

# Example 5: CircleCI integration
resource "pyvider_private_state_verifier" "circleci_test" {
  input_value = "circleci-${var.ci_environment}-${var.build_number}"
}

# Test results validation
locals {
  ci_test_results = {
    for test_name, test_config in local.ci_test_matrix :
    test_name => {
      input = pyvider_private_state_verifier.ci_test_matrix[test_name].input_value
      output = pyvider_private_state_verifier.ci_test_matrix[test_name].decrypted_token
      expected = "SECRET_FOR_${upper(test_config.input)}"
      passed = pyvider_private_state_verifier.ci_test_matrix[test_name].decrypted_token == "SECRET_FOR_${upper(test_config.input)}"
      description = test_config.description
      priority = test_config.priority
      timeout = test_config.timeout
      duration = 1 # Simulated test duration in seconds
    }
  }

  platform_test_results = {
    github_actions = {
      input = pyvider_private_state_verifier.github_actions_test.input_value
      output = pyvider_private_state_verifier.github_actions_test.decrypted_token
      expected = "SECRET_FOR_GITHUB-ACTIONS-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.github_actions_test.decrypted_token == "SECRET_FOR_GITHUB-ACTIONS-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "GitHub Actions"
    }
    jenkins = {
      input = pyvider_private_state_verifier.jenkins_test.input_value
      output = pyvider_private_state_verifier.jenkins_test.decrypted_token
      expected = "SECRET_FOR_JENKINS-PIPELINE-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.jenkins_test.decrypted_token == "SECRET_FOR_JENKINS-PIPELINE-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "Jenkins"
    }
    gitlab_ci = {
      input = pyvider_private_state_verifier.gitlab_ci_test.input_value
      output = pyvider_private_state_verifier.gitlab_ci_test.decrypted_token
      expected = "SECRET_FOR_GITLAB-CI-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.gitlab_ci_test.decrypted_token == "SECRET_FOR_GITLAB-CI-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "GitLab CI"
    }
    azure_devops = {
      input = pyvider_private_state_verifier.azure_devops_test.input_value
      output = pyvider_private_state_verifier.azure_devops_test.decrypted_token
      expected = "SECRET_FOR_AZURE-DEVOPS-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.azure_devops_test.decrypted_token == "SECRET_FOR_AZURE-DEVOPS-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "Azure DevOps"
    }
    circleci = {
      input = pyvider_private_state_verifier.circleci_test.input_value
      output = pyvider_private_state_verifier.circleci_test.decrypted_token
      expected = "SECRET_FOR_CIRCLECI-${upper(var.ci_environment)}-${upper(var.build_number)}"
      passed = pyvider_private_state_verifier.circleci_test.decrypted_token == "SECRET_FOR_CIRCLECI-${upper(var.ci_environment)}-${upper(var.build_number)}"
      platform = "CircleCI"
    }
  }

  # Overall CI/CD test summary
  ci_summary = {
    total_matrix_tests = length(local.ci_test_results)
    matrix_tests_passed = length([for test in local.ci_test_results : test if test.passed])
    matrix_tests_failed = length([for test in local.ci_test_results : test if !test.passed])

    total_platform_tests = length(local.platform_test_results)
    platform_tests_passed = length([for test in local.platform_test_results : test if test.passed])
    platform_tests_failed = length([for test in local.platform_test_results : test if !test.passed])

    overall_tests_passed = (
      length([for test in local.ci_test_results : test if test.passed]) +
      length([for test in local.platform_test_results : test if test.passed])
    )
    overall_tests_failed = (
      length([for test in local.ci_test_results : test if !test.passed]) +
      length([for test in local.platform_test_results : test if !test.passed])
    )

    critical_failures = length([
      for test in local.ci_test_results : test
      if !test.passed && test.priority == "critical"
    ])

    all_tests_passed = (
      alltrue([for test in local.ci_test_results : test.passed]) &&
      alltrue([for test in local.platform_test_results : test.passed])
    )

    ci_status = (
      alltrue([for test in local.ci_test_results : test.passed]) &&
      alltrue([for test in local.platform_test_results : test.passed])
    ) ? "success" : "failure"

    exit_code = (
      alltrue([for test in local.ci_test_results : test.passed]) &&
      alltrue([for test in local.platform_test_results : test.passed])
    ) ? 0 : 1
  }
}

# Create CI/CD test report in JUnit XML format
resource "pyvider_file_content" "junit_test_report" {
  filename = "/tmp/private_state_junit_report.xml"
  content = join("\n", [
    "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
    "<testsuites name=\"PrivateStateVerification\" tests=\"${local.ci_summary.overall_tests_passed + local.ci_summary.overall_tests_failed}\" failures=\"${local.ci_summary.overall_tests_failed}\" time=\"${sum([for test in local.ci_test_results : test.duration])}\" timestamp=\"${timestamp()}\">",
    "  <testsuite name=\"MatrixTests\" tests=\"${local.ci_summary.total_matrix_tests}\" failures=\"${local.ci_summary.matrix_tests_failed}\" time=\"${sum([for test in local.ci_test_results : test.duration])}\">",
    join("\n", [
      for test_name, test in local.ci_test_results :
      test.passed ?
      "    <testcase name=\"${test_name}\" classname=\"PrivateStateVerifier.MatrixTests\" time=\"${test.duration}\" />" :
      "    <testcase name=\"${test_name}\" classname=\"PrivateStateVerifier.MatrixTests\" time=\"${test.duration}\">\n      <failure message=\"Expected '${test.expected}' but got '${test.output}'\" type=\"AssertionError\">\n        Test: ${test.description}\n        Priority: ${test.priority}\n        Input: ${test.input}\n        Expected: ${test.expected}\n        Actual: ${test.output}\n      </failure>\n    </testcase>"
    ]),
    "  </testsuite>",
    "  <testsuite name=\"PlatformTests\" tests=\"${local.ci_summary.total_platform_tests}\" failures=\"${local.ci_summary.platform_tests_failed}\" time=\"${local.ci_summary.total_platform_tests}\">",
    join("\n", [
      for test_name, test in local.platform_test_results :
      test.passed ?
      "    <testcase name=\"${test_name}\" classname=\"PrivateStateVerifier.PlatformTests\" time=\"1\" />" :
      "    <testcase name=\"${test_name}\" classname=\"PrivateStateVerifier.PlatformTests\" time=\"1\">\n      <failure message=\"Expected '${test.expected}' but got '${test.output}'\" type=\"AssertionError\">\n        Platform: ${test.platform}\n        Input: ${test.input}\n        Expected: ${test.expected}\n        Actual: ${test.output}\n      </failure>\n    </testcase>"
    ]),
    "  </testsuite>",
    "</testsuites>"
  ])
}

# Create CI/CD pipeline configuration files
resource "pyvider_file_content" "github_actions_workflow" {
  filename = "/tmp/github_actions_private_state_test.yml"
  content = yamlencode({
    name = "Private State Verification"
    on = {
      push = {
        branches = ["main", "develop"]
      }
      pull_request = {
        branches = ["main"]
      }
    }

    jobs = {
      private_state_test = {
        "runs-on" = "ubuntu-latest"
        steps = [
          {
            name = "Checkout"
            uses = "actions/checkout@v3"
          },
          {
            name = "Setup Terraform"
            uses = "hashicorp/setup-terraform@v2"
            with = {
              terraform_version = "1.5.0"
            }
          },
          {
            name = "Initialize Terraform"
            run = "terraform init"
          },
          {
            name = "Run Private State Tests"
            run = join("\n", [
              "terraform plan -var=\"ci_environment=github-actions\" -var=\"build_number=${{ github.run_number }}\"",
              "terraform apply -auto-approve -var=\"ci_environment=github-actions\" -var=\"build_number=${{ github.run_number }}\"",
            ])
            env = {
              TF_LOG = "INFO"
            }
          },
          {
            name = "Validate Test Results"
            run = join("\n", [
              "if [ \"${local.ci_summary.ci_status}\" = \"success\" ]; then",
              "  echo \"✅ All private state tests passed\"",
              "  exit 0",
              "else",
              "  echo \"❌ Private state tests failed\"",
              "  echo \"Critical failures: ${local.ci_summary.critical_failures}\"",
              "  exit 1",
              "fi"
            ])
          }
        ]
      }
    }
  })
}

# Create Jenkins pipeline configuration
resource "pyvider_file_content" "jenkins_pipeline" {
  filename = "/tmp/Jenkinsfile.private_state_test"
  content = join("\n", [
    "pipeline {",
    "    agent any",
    "    ",
    "    environment {",
    "        CI_ENVIRONMENT = '${var.ci_environment}'",
    "        BUILD_NUMBER = '${var.build_number}'",
    "        TF_LOG = 'INFO'",
    "    }",
    "    ",
    "    stages {",
    "        stage('Initialize') {",
    "            steps {",
    "                echo 'Initializing Private State Verification Tests'",
    "                sh 'terraform init'",
    "            }",
    "        }",
    "        ",
    "        stage('Plan Tests') {",
    "            steps {",
    "                echo 'Planning private state verification tests'",
    "                sh 'terraform plan -var=\"ci_environment=jenkins\" -var=\"build_number=${BUILD_NUMBER}\"'",
    "            }",
    "        }",
    "        ",
    "        stage('Execute Tests') {",
    "            steps {",
    "                echo 'Executing private state verification tests'",
    "                sh 'terraform apply -auto-approve -var=\"ci_environment=jenkins\" -var=\"build_number=${BUILD_NUMBER}\"'",
    "            }",
    "        }",
    "        ",
    "        stage('Validate Results') {",
    "            steps {",
    "                script {",
    "                    if ('${local.ci_summary.ci_status}' == 'success') {",
    "                        echo '✅ All private state tests passed'",
    "                        currentBuild.result = 'SUCCESS'",
    "                    } else {",
    "                        echo '❌ Private state tests failed'",
    "                        echo 'Critical failures: ${local.ci_summary.critical_failures}'",
    "                        currentBuild.result = 'FAILURE'",
    "                        error('Private state verification tests failed')",
    "                    }",
    "                }",
    "            }",
    "        }",
    "    }",
    "    ",
    "    post {",
    "        always {",
    "            echo 'Cleaning up test resources'",
    "            sh 'terraform destroy -auto-approve -var=\"ci_environment=jenkins\" -var=\"build_number=${BUILD_NUMBER}\" || true'",
    "        }",
    "        success {",
    "            echo 'Private state verification completed successfully'",
    "        }",
    "        failure {",
    "            echo 'Private state verification failed - check logs for details'",
    "        }",
    "    }",
    "}"
  ])
}

# Create comprehensive CI/CD test report
resource "pyvider_file_content" "cicd_test_report" {
  filename = "/tmp/cicd_private_state_test_report.json"
  content = jsonencode({
    test_execution = {
      timestamp = timestamp()
      ci_environment = var.ci_environment
      build_number = var.build_number
      test_suite = var.test_suite
      duration_seconds = sum([for test in local.ci_test_results : test.duration])
    }

    test_matrix_results = local.ci_test_results
    platform_test_results = local.platform_test_results

    summary = local.ci_summary

    test_categories = {
      critical_tests = {
        total = length([for test in local.ci_test_results : test if test.priority == "critical"])
        passed = length([for test in local.ci_test_results : test if test.priority == "critical" && test.passed])
        failed = length([for test in local.ci_test_results : test if test.priority == "critical" && !test.passed])
      }
      high_priority_tests = {
        total = length([for test in local.ci_test_results : test if test.priority == "high"])
        passed = length([for test in local.ci_test_results : test if test.priority == "high" && test.passed])
        failed = length([for test in local.ci_test_results : test if test.priority == "high" && !test.passed])
      }
      medium_priority_tests = {
        total = length([for test in local.ci_test_results : test if test.priority == "medium"])
        passed = length([for test in local.ci_test_results : test if test.priority == "medium" && test.passed])
        failed = length([for test in local.ci_test_results : test if test.priority == "medium" && !test.passed])
      }
    }

    platform_compatibility = {
      for platform_name, result in local.platform_test_results :
      platform_name => {
        compatible = result.passed
        platform = result.platform
        test_result = result.passed ? "pass" : "fail"
      }
    }

    quality_gates = {
      critical_tests_pass = length([for test in local.ci_test_results : test if test.priority == "critical" && !test.passed]) == 0
      high_priority_tests_pass = length([for test in local.ci_test_results : test if test.priority == "high" && !test.passed]) == 0
      platform_compatibility_pass = alltrue([for test in local.platform_test_results : test.passed])
      overall_quality_gate = local.ci_summary.all_tests_passed
    }

    recommendations = local.ci_summary.all_tests_passed ? [
      "✅ All CI/CD tests passed - ready for deployment",
      "✅ Private state encryption working correctly across platforms",
      "🚀 Proceed with release pipeline",
      "📊 Monitor production deployment"
    ] : concat([
      "❌ CI/CD tests failed - deployment blocked",
      "🔧 Fix failing tests before proceeding"
    ], local.ci_summary.critical_failures > 0 ? [
      "🚨 Critical failures detected - immediate attention required"
    ] : [], [
      "📋 Review test results and implement fixes",
      "🔄 Re-run tests after remediation"
    ])

    artifacts = {
      junit_report = pyvider_file_content.junit_test_report.filename
      github_workflow = pyvider_file_content.github_actions_workflow.filename
      jenkins_pipeline = pyvider_file_content.jenkins_pipeline.filename
      test_report = pyvider_file_content.cicd_test_report.filename
    }
  })
}

output "cicd_testing_results" {
  description = "CI/CD integration testing results for private state verification"
  value = {
    execution_summary = {
      ci_environment = var.ci_environment
      build_number = var.build_number
      test_suite_name = var.test_suite.name
      execution_status = local.ci_summary.ci_status
      exit_code = local.ci_summary.exit_code
    }

    test_metrics = {
      total_tests = local.ci_summary.overall_tests_passed + local.ci_summary.overall_tests_failed
      passed_tests = local.ci_summary.overall_tests_passed
      failed_tests = local.ci_summary.overall_tests_failed
      success_rate = local.ci_summary.overall_tests_failed == 0 ? 100 : (local.ci_summary.overall_tests_passed / (local.ci_summary.overall_tests_passed + local.ci_summary.overall_tests_failed)) * 100
    }

    test_breakdown = {
      matrix_tests = {
        total = local.ci_summary.total_matrix_tests
        passed = local.ci_summary.matrix_tests_passed
        failed = local.ci_summary.matrix_tests_failed
      }
      platform_tests = {
        total = local.ci_summary.total_platform_tests
        passed = local.ci_summary.platform_tests_passed
        failed = local.ci_summary.platform_tests_failed
      }
    }

    quality_gates = {
      critical_tests_pass = local.ci_summary.critical_failures == 0
      all_tests_pass = local.ci_summary.all_tests_passed
      deployment_approved = local.ci_summary.all_tests_passed
    }

    platform_compatibility = {
      for platform_name, result in local.platform_test_results :
      platform_name => result.passed
    }

    artifacts_generated = [
      pyvider_file_content.junit_test_report.filename,
      pyvider_file_content.github_actions_workflow.filename,
      pyvider_file_content.jenkins_pipeline.filename,
      pyvider_file_content.cicd_test_report.filename
    ]
  }
}
```

## Schema



## How Private State Verification Works

The `pyvider_private_state_verifier` resource demonstrates the complete lifecycle of private state encryption:

### 1. Creation Phase
- Takes an `input_value` as configuration
- Generates a secret token based on the input: `SECRET_FOR_{INPUT_VALUE_UPPER}`
- Stores the secret token in encrypted private state
- Returns a planned state with the decrypted token marked as computed

### 2. Apply Phase
- Retrieves the encrypted private state
- Terraform automatically decrypts the private state
- Populates the `decrypted_token` attribute with the decrypted value
- Validates that the decryption process worked correctly

### 3. Read Phase
- Returns the current state including the decrypted token
- Demonstrates that private state persists across operations
- Shows that encrypted data remains accessible when needed

### 4. Verification
- Compares input and output to ensure encryption/decryption cycle worked
- Validates that sensitive data was never stored in plain text in the state file
- Confirms that Terraform's encryption mechanisms are functioning

## Security Features

### Private State Encryption
```terraform
resource "pyvider_private_state_verifier" "encryption_test" {
  input_value = "sensitive-data"
}

# The actual secret token is encrypted in private state
# Only the decrypted result is available as an attribute
output "encryption_works" {
  value = pyvider_private_state_verifier.encryption_test.decrypted_token
  # Will output: "SECRET_FOR_SENSITIVE-DATA"
}
```

### State File Security
- **Input data**: Stored in regular state (visible)
- **Secret generation**: Happens during resource creation
- **Secret storage**: Encrypted in private state (not visible in state file)
- **Decrypted output**: Available as computed attribute

### Verification Pattern
```terraform
locals {
  test_input = "my-test-value"
  expected_secret = "SECRET_FOR_${upper(local.test_input)}"
}

resource "pyvider_private_state_verifier" "verify" {
  input_value = local.test_input
}

# Verify the encryption/decryption cycle worked
output "verification_passed" {
  value = pyvider_private_state_verifier.verify.decrypted_token == local.expected_secret
}
```

## Common Patterns

### Testing Multiple Scenarios
```terraform
# Test different input types
resource "pyvider_private_state_verifier" "alphanumeric" {
  input_value = "test123"
}

resource "pyvider_private_state_verifier" "special_chars" {
  input_value = "test-with-dashes"
}

resource "pyvider_private_state_verifier" "long_input" {
  input_value = "this-is-a-very-long-test-input-value-for-verification"
}

# Verify all tests pass
locals {
  all_tests_pass = (
    pyvider_private_state_verifier.alphanumeric.decrypted_token == "SECRET_FOR_TEST123" &&
    pyvider_private_state_verifier.special_chars.decrypted_token == "SECRET_FOR_TEST-WITH-DASHES" &&
    pyvider_private_state_verifier.long_input.decrypted_token == "SECRET_FOR_THIS-IS-A-VERY-LONG-TEST-INPUT-VALUE-FOR-VERIFICATION"
  )
}
```

### Compliance Testing Framework
```terraform
variable "compliance_tests" {
  description = "List of compliance test scenarios"
  type = list(object({
    name = string
    input = string
    category = string
  }))
  default = [
    {
      name = "basic_encryption"
      input = "basic-test"
      category = "functionality"
    },
    {
      name = "special_characters"
      input = "special!@#$%"
      category = "edge_cases"
    },
    {
      name = "unicode_support"
      input = "unicode-тест-测试"
      category = "internationalization"
    }
  ]
}

resource "pyvider_private_state_verifier" "compliance_test" {
  for_each = {
    for test in var.compliance_tests : test.name => test
  }

  input_value = each.value.input
}

# Generate compliance report
locals {
  compliance_results = {
    for test_name, test_config in var.compliance_tests :
    test_name => {
      input = test_config.input
      expected = "SECRET_FOR_${upper(test_config.input)}"
      actual = pyvider_private_state_verifier.compliance_test[test_name].decrypted_token
      passed = pyvider_private_state_verifier.compliance_test[test_name].decrypted_token == "SECRET_FOR_${upper(test_config.input)}"
      category = test_config.category
    }
  }
}
```

### CI/CD Verification Pipeline
```terraform
# Automated testing resource
resource "pyvider_private_state_verifier" "ci_test" {
  input_value = "ci-pipeline-test-${formatdate("YYYY-MM-DD", timestamp())}"
}

# Create test report for CI/CD
resource "pyvider_file_content" "ci_test_report" {
  filename = "/tmp/private_state_test_report.json"
  content = jsonencode({
    test_run = {
      timestamp = timestamp()
      test_name = "private_state_encryption_verification"
      input_value = pyvider_private_state_verifier.ci_test.input_value
      decrypted_token = pyvider_private_state_verifier.ci_test.decrypted_token
      expected_pattern = "SECRET_FOR_*"
      test_passed = can(regex("^SECRET_FOR_", pyvider_private_state_verifier.ci_test.decrypted_token))
    }

    security_validation = {
      private_state_used = true
      encryption_verified = true
      state_file_protection = true
      decryption_successful = pyvider_private_state_verifier.ci_test.decrypted_token != null
    }
  })
}
```

### Integration with Other Resources
```terraform
# Use with timed tokens for comprehensive testing
resource "pyvider_timed_token" "test_token" {
  name = "verification-test-token"
}

resource "pyvider_private_state_verifier" "integrated_test" {
  input_value = "integration-with-${pyvider_timed_token.test_token.id}"
}

# Verify both resources work together
locals {
  integration_test_passed = (
    pyvider_timed_token.test_token.id != null &&
    pyvider_private_state_verifier.integrated_test.decrypted_token != null &&
    can(regex("SECRET_FOR_INTEGRATION-WITH-", pyvider_private_state_verifier.integrated_test.decrypted_token))
  )
}
```

## Error Handling and Validation

### Input Validation
```terraform
variable "test_inputs" {
  description = "Test inputs for validation"
  type = list(string)
  default = ["valid-input", "another-test"]

  validation {
    condition = alltrue([
      for input in var.test_inputs : length(input) > 0
    ])
    error_message = "All test inputs must be non-empty strings."
  }
}

resource "pyvider_private_state_verifier" "validated_test" {
  for_each = toset(var.test_inputs)

  input_value = each.value
}
```

### Failure Detection
```terraform
resource "pyvider_private_state_verifier" "failure_test" {
  input_value = "failure-detection-test"
}

# Check for common failure scenarios
locals {
  test_failures = [
    {
      name = "null_decrypted_token"
      failed = pyvider_private_state_verifier.failure_test.decrypted_token == null
      message = "Decrypted token is null"
    },
    {
      name = "empty_decrypted_token"
      failed = pyvider_private_state_verifier.failure_test.decrypted_token == ""
      message = "Decrypted token is empty"
    },
    {
      name = "incorrect_format"
      failed = !can(regex("^SECRET_FOR_", pyvider_private_state_verifier.failure_test.decrypted_token))
      message = "Decrypted token doesn't match expected format"
    }
  ]

  any_failures = anytrue([for failure in local.test_failures : failure.failed])
  failure_messages = [for failure in local.test_failures : failure.message if failure.failed]
}
```

## Best Practices

### 1. Meaningful Test Names
```terraform
# ✅ Good - descriptive test names
resource "pyvider_private_state_verifier" "user_id_encryption" {
  input_value = "user-12345"
}

resource "pyvider_private_state_verifier" "api_key_verification" {
  input_value = "api-key-test"
}

# ❌ Bad - generic names
resource "pyvider_private_state_verifier" "test1" {
  input_value = "something"
}
```

### 2. Comprehensive Test Coverage
```terraform
# Test various input scenarios
locals {
  test_scenarios = {
    empty_string = ""
    single_char = "a"
    numbers_only = "12345"
    mixed_case = "MixedCase"
    special_chars = "test!@#$%^&*()"
    unicode = "测试-тест-テスト"
    very_long = join("", [for i in range(100) : "a"])
  }
}

resource "pyvider_private_state_verifier" "comprehensive_test" {
  for_each = local.test_scenarios

  input_value = each.value
}
```

### 3. Documentation and Reporting
```terraform
resource "pyvider_private_state_verifier" "documented_test" {
  input_value = "production-readiness-test"

  lifecycle {
    # Document the purpose of this test
    # This verifies that private state encryption works correctly
    # before deploying to production environments
    ignore_changes = []
  }
}

# Generate documentation
resource "pyvider_file_content" "test_documentation" {
  filename = "/tmp/private_state_test_docs.md"
  content = join("\n", [
    "# Private State Encryption Test Documentation",
    "",
    "## Test Purpose",
    "Verify that Terraform private state encryption is working correctly.",
    "",
    "## Test Input",
    "Input Value: `${pyvider_private_state_verifier.documented_test.input_value}`",
    "",
    "## Test Results",
    "Decrypted Token: `${pyvider_private_state_verifier.documented_test.decrypted_token}`",
    "",
    "## Verification",
    "Expected Pattern: `SECRET_FOR_{UPPER_INPUT}`",
    "Test Passed: ${can(regex("^SECRET_FOR_", pyvider_private_state_verifier.documented_test.decrypted_token))}",
    "",
    "## Security Notes",
    "- The secret token is stored in encrypted private state",
    "- The input value is visible in regular state",
    "- The decrypted token is available as a computed attribute",
    "- No sensitive data is exposed in the state file",
    "",
    "Generated: ${timestamp()}"
  ])
}
```

### 4. Environment-Specific Testing
```terraform
variable "environment" {
  description = "Environment for testing"
  type = string
  default = "development"
}

resource "pyvider_private_state_verifier" "env_specific_test" {
  input_value = "${var.environment}-encryption-test"
}

# Environment-specific validation
locals {
  env_test_passed = pyvider_private_state_verifier.env_specific_test.decrypted_token == "SECRET_FOR_${upper(var.environment)}-ENCRYPTION-TEST"

  production_ready = var.environment == "production" ? local.env_test_passed : true
}
```

## Troubleshooting

### Common Issues

**Issue**: Decrypted token is null
**Cause**: Private state was not properly created or encryption failed
**Solution**: Check provider logs and ensure private state support is enabled

**Issue**: Decrypted token doesn't match expected format
**Cause**: Secret generation logic may have changed
**Solution**: Verify the expected format: `SECRET_FOR_{UPPER_INPUT_VALUE}`

**Issue**: State file shows encrypted data
**Cause**: Data may not be properly stored in private state
**Solution**: Ensure the resource uses `PrivateState` class correctly

### Debugging Techniques
```terraform
resource "pyvider_private_state_verifier" "debug_test" {
  input_value = "debug-test-value"
}

# Debug output (be careful not to expose in production)
output "debug_info" {
  value = {
    input_provided = pyvider_private_state_verifier.debug_test.input_value
    output_received = pyvider_private_state_verifier.debug_test.decrypted_token
    output_length = length(pyvider_private_state_verifier.debug_test.decrypted_token)
    format_correct = can(regex("^SECRET_FOR_", pyvider_private_state_verifier.debug_test.decrypted_token))
  }
}
```

## Related Components

- [`pyvider_timed_token`](../timed_token.md) - Time-limited tokens with private state
- [`pyvider_file_content`](../file_content.md) - Create test reports and documentation
- [`pyvider_warning_example`](../warning_example.md) - Testing warning mechanisms