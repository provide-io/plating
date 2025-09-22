---
page_title: "Data Source: pyvider_http_api"
description: |-
  Makes HTTP requests and processes responses for infrastructure automation
---

# pyvider_http_api (Data Source)

> Make HTTP requests to external APIs and process responses in Terraform configurations

The `pyvider_http_api` data source allows you to make HTTP requests to external APIs and use the responses in your Terraform configurations. It supports various HTTP methods, custom headers, and provides detailed response information including status codes, headers, and timing.

## When to Use This

- **API integration**: Fetch configuration data from external APIs
- **Service discovery**: Query service registries or configuration endpoints
- **Health checks**: Verify external services are available before deployment
- **Dynamic configuration**: Pull settings from configuration management systems
- **Webhook validation**: Test webhook endpoints before setting up integrations

**Anti-patterns (when NOT to use):**
- Modifying external state (use proper API resources instead)
- Large file downloads (use specialized download tools)
- Real-time monitoring (use dedicated monitoring solutions)
- Authentication flows requiring multiple requests (handle outside Terraform)

## Quick Start

```terraform
# Simple GET request to fetch configuration
data "pyvider_http_api" "config" {
  url = "https://api.example.com/config"
}

# Use the response in other resources
resource "pyvider_file_content" "downloaded_config" {
  filename = "/tmp/api_config.json"
  content  = data.pyvider_http_api.config.response_body
}
```

## Examples

### Basic Usage

```terraform
# Basic HTTP API usage examples

# Example 1: Simple GET request
data "pyvider_http_api" "simple_get" {
  url = "https://httpbin.org/get"
}

# Example 2: GET request with query parameters in URL
data "pyvider_http_api" "with_params" {
  url = "https://httpbin.org/get?param1=value1&param2=value2"
}

# Example 3: GET request with custom headers
data "pyvider_http_api" "with_headers" {
  url = "https://httpbin.org/headers"
  headers = {
    "User-Agent"    = "Terraform-Pyvider/1.0"
    "Accept"        = "application/json"
    "Custom-Header" = "custom-value"
  }
}

# Example 4: Request with custom timeout
data "pyvider_http_api" "with_timeout" {
  url     = "https://httpbin.org/delay/2"
  timeout = 10  # 10 seconds
}

# Example 5: HEAD request to check resource existence
data "pyvider_http_api" "head_check" {
  url    = "https://httpbin.org/status/200"
  method = "HEAD"
}

# Example 6: Real-world example - GitHub API
data "pyvider_http_api" "github_user" {
  url = "https://api.github.com/users/octocat"
  headers = {
    "Accept"     = "application/vnd.github.v3+json"
    "User-Agent" = "Terraform-Provider-Example"
  }
}

# Example 7: JSONPlaceholder API for testing
data "pyvider_http_api" "json_placeholder" {
  url = "https://jsonplaceholder.typicode.com/posts/1"
  headers = {
    "Accept" = "application/json"
  }
}

# Process API responses
locals {
  # Parse JSON responses
  github_user = can(jsondecode(data.pyvider_http_api.github_user.response_body)) ?
    jsondecode(data.pyvider_http_api.github_user.response_body) : {}

  json_post = can(jsondecode(data.pyvider_http_api.json_placeholder.response_body)) ?
    jsondecode(data.pyvider_http_api.json_placeholder.response_body) : {}

  # Extract specific information
  user_info = {
    name         = lookup(local.github_user, "name", "Unknown")
    public_repos = lookup(local.github_user, "public_repos", 0)
    followers    = lookup(local.github_user, "followers", 0)
    company      = lookup(local.github_user, "company", "None")
  }

  post_info = {
    title  = lookup(local.json_post, "title", "No title")
    body   = lookup(local.json_post, "body", "No content")
    userId = lookup(local.json_post, "userId", 0)
  }

  # Check response success
  requests_status = {
    simple_get = {
      success       = data.pyvider_http_api.simple_get.status_code == 200
      response_time = data.pyvider_http_api.simple_get.response_time_ms
      content_type  = data.pyvider_http_api.simple_get.content_type
    }

    github_api = {
      success       = data.pyvider_http_api.github_user.status_code == 200
      response_time = data.pyvider_http_api.github_user.response_time_ms
      headers_count = data.pyvider_http_api.github_user.header_count
    }

    head_request = {
      success       = data.pyvider_http_api.head_check.status_code == 200
      response_time = data.pyvider_http_api.head_check.response_time_ms
      has_body      = data.pyvider_http_api.head_check.response_body != null
    }
  }
}

# Create files with API responses
resource "pyvider_file_content" "api_responses" {
  filename = "/tmp/http_api_basic_responses.json"
  content = jsonencode({
    timestamp = timestamp()

    responses = {
      simple_get = {
        url         = data.pyvider_http_api.simple_get.url
        status_code = data.pyvider_http_api.simple_get.status_code
        success     = local.requests_status.simple_get.success
        response_time_ms = data.pyvider_http_api.simple_get.response_time_ms
        content_type = data.pyvider_http_api.simple_get.content_type
      }

      with_headers = {
        url           = data.pyvider_http_api.with_headers.url
        status_code   = data.pyvider_http_api.with_headers.status_code
        headers_count = data.pyvider_http_api.with_headers.header_count
      }

      timeout_test = {
        url           = data.pyvider_http_api.with_timeout.url
        status_code   = data.pyvider_http_api.with_timeout.status_code
        response_time = data.pyvider_http_api.with_timeout.response_time_ms
        configured_timeout = 10
      }

      head_request = {
        url         = data.pyvider_http_api.head_check.url
        method      = data.pyvider_http_api.head_check.method
        status_code = data.pyvider_http_api.head_check.status_code
        has_body    = local.requests_status.head_request.has_body
      }
    }

    parsed_data = {
      github_user = local.user_info
      sample_post = local.post_info
    }

    performance_summary = {
      total_requests = 7
      successful_requests = length([
        for status in values(local.requests_status) : status
        if status.success
      ])
      average_response_time = (
        data.pyvider_http_api.simple_get.response_time_ms +
        data.pyvider_http_api.github_user.response_time_ms +
        data.pyvider_http_api.head_check.response_time_ms
      ) / 3
    }
  })
}

# Create a simple text report
resource "pyvider_file_content" "api_report" {
  filename = "/tmp/http_api_basic_report.txt"
  content = join("\n", [
    "=== HTTP API Basic Examples Report ===",
    "",
    "=== Request Status Summary ===",
    "Simple GET: ${local.requests_status.simple_get.success ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.simple_get.status_code}) - ${data.pyvider_http_api.simple_get.response_time_ms}ms",
    "With Headers: ${data.pyvider_http_api.with_headers.status_code == 200 ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.with_headers.status_code}) - ${data.pyvider_http_api.with_headers.header_count} headers",
    "Timeout Test: ${local.requests_status.simple_get.success ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.with_timeout.status_code}) - ${data.pyvider_http_api.with_timeout.response_time_ms}ms",
    "HEAD Request: ${local.requests_status.head_request.success ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.head_check.status_code}) - No body: ${!local.requests_status.head_request.has_body}",
    "GitHub API: ${local.requests_status.github_api.success ? "SUCCESS" : "FAILED"} (${data.pyvider_http_api.github_user.status_code}) - ${data.pyvider_http_api.github_user.response_time_ms}ms",
    "",
    "=== GitHub User Information ===",
    "Name: ${local.user_info.name}",
    "Public Repos: ${local.user_info.public_repos}",
    "Followers: ${local.user_info.followers}",
    "Company: ${local.user_info.company}",
    "",
    "=== Sample Post Information ===",
    "Title: ${local.post_info.title}",
    "User ID: ${local.post_info.userId}",
    "Content Length: ${length(local.post_info.body)} characters",
    "",
    "=== Performance Metrics ===",
    "Fastest Response: ${min(data.pyvider_http_api.simple_get.response_time_ms, data.pyvider_http_api.github_user.response_time_ms, data.pyvider_http_api.head_check.response_time_ms)}ms",
    "Slowest Response: ${max(data.pyvider_http_api.simple_get.response_time_ms, data.pyvider_http_api.github_user.response_time_ms, data.pyvider_http_api.head_check.response_time_ms)}ms",
    "",
    "Report generated at: ${timestamp()}"
  ])
}

output "basic_http_api_results" {
  description = "Results from basic HTTP API calls"
  value = {
    request_summary = {
      total_requests = 7
      successful_requests = length([
        for req in [
          data.pyvider_http_api.simple_get,
          data.pyvider_http_api.with_headers,
          data.pyvider_http_api.with_timeout,
          data.pyvider_http_api.head_check,
          data.pyvider_http_api.github_user,
          data.pyvider_http_api.json_placeholder
        ] : req if req.status_code == 200
      ])
    }

    response_times = {
      simple_get   = data.pyvider_http_api.simple_get.response_time_ms
      github_api   = data.pyvider_http_api.github_user.response_time_ms
      head_request = data.pyvider_http_api.head_check.response_time_ms
    }

    parsed_data = {
      github_user = local.user_info
      sample_post = local.post_info
    }

    content_types = {
      simple_get    = data.pyvider_http_api.simple_get.content_type
      github_api    = data.pyvider_http_api.github_user.content_type
      json_placeholder = data.pyvider_http_api.json_placeholder.content_type
    }

    generated_files = [
      pyvider_file_content.api_responses.filename,
      pyvider_file_content.api_report.filename
    ]
  }
}
```

### Advanced HTTP Operations

```terraform
# Advanced HTTP API usage examples

# Example 1: POST request with JSON content type
data "pyvider_http_api" "post_json" {
  url    = "https://httpbin.org/post"
  method = "POST"
  headers = {
    "Content-Type" = "application/json"
    "Accept"       = "application/json"
    "User-Agent"   = "Terraform-Pyvider-Advanced/1.0"
  }
}

# Example 2: PUT request for updates
data "pyvider_http_api" "put_request" {
  url    = "https://httpbin.org/put"
  method = "PUT"
  headers = {
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer fake-token-for-example"
    "X-Request-ID"  = "req-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  }
}

# Example 3: DELETE request
data "pyvider_http_api" "delete_request" {
  url    = "https://httpbin.org/delete"
  method = "DELETE"
  headers = {
    "Authorization" = "Bearer fake-token-for-example"
    "X-Reason"      = "cleanup-operation"
  }
}

# Example 4: PATCH request for partial updates
data "pyvider_http_api" "patch_request" {
  url    = "https://httpbin.org/patch"
  method = "PATCH"
  headers = {
    "Content-Type" = "application/json-patch+json"
    "If-Match"     = "etag-example"
  }
}

# Example 5: OPTIONS request to check allowed methods
data "pyvider_http_api" "options_request" {
  url    = "https://httpbin.org/get"
  method = "OPTIONS"
}

# Example 6: Request with custom timeout for slow APIs
data "pyvider_http_api" "slow_api" {
  url     = "https://httpbin.org/delay/3"
  timeout = 10
  headers = {
    "Accept-Encoding" = "gzip, deflate"
    "Cache-Control"   = "no-cache"
  }
}

# Example 7: Complex headers for API authentication
data "pyvider_http_api" "authenticated_api" {
  url = "https://httpbin.org/bearer"
  headers = {
    "Authorization"     = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example"
    "X-API-Version"     = "2023-01-01"
    "X-Client-Version"  = "terraform-provider-pyvider/1.0"
    "Accept"            = "application/vnd.api+json"
    "Content-Type"      = "application/vnd.api+json"
    "X-Request-Timeout" = "30"
  }
}

# Example 8: Multiple related API calls
data "pyvider_http_api" "user_profile" {
  url = "https://jsonplaceholder.typicode.com/users/1"
}

# Get posts for the user (using data from first call)
locals {
  user_data = can(jsondecode(data.pyvider_http_api.user_profile.response_body)) ?
    jsondecode(data.pyvider_http_api.user_profile.response_body) : { id = 1 }
}

data "pyvider_http_api" "user_posts" {
  url = "https://jsonplaceholder.typicode.com/posts?userId=${local.user_data.id}"
}

# Example 9: Error status code handling
data "pyvider_http_api" "not_found" {
  url = "https://httpbin.org/status/404"
}

data "pyvider_http_api" "server_error" {
  url = "https://httpbin.org/status/500"
}

data "pyvider_http_api" "unauthorized" {
  url = "https://httpbin.org/status/401"
}

# Process responses and handle different scenarios
locals {
  # Parse successful responses
  post_response = can(jsondecode(data.pyvider_http_api.post_json.response_body)) ?
    jsondecode(data.pyvider_http_api.post_json.response_body) : {}

  user_posts = can(jsondecode(data.pyvider_http_api.user_posts.response_body)) ?
    jsondecode(data.pyvider_http_api.user_posts.response_body) : []

  # Analyze response characteristics
  response_analysis = {
    post_request = {
      status_code   = data.pyvider_http_api.post_json.status_code
      response_time = data.pyvider_http_api.post_json.response_time_ms
      content_type  = data.pyvider_http_api.post_json.content_type
      headers_count = data.pyvider_http_api.post_json.header_count
      success       = data.pyvider_http_api.post_json.status_code >= 200 && data.pyvider_http_api.post_json.status_code < 300
    }

    put_request = {
      status_code   = data.pyvider_http_api.put_request.status_code
      response_time = data.pyvider_http_api.put_request.response_time_ms
      success       = data.pyvider_http_api.put_request.status_code >= 200 && data.pyvider_http_api.put_request.status_code < 300
    }

    delete_request = {
      status_code   = data.pyvider_http_api.delete_request.status_code
      response_time = data.pyvider_http_api.delete_request.response_time_ms
      success       = data.pyvider_http_api.delete_request.status_code >= 200 && data.pyvider_http_api.delete_request.status_code < 300
    }

    patch_request = {
      status_code   = data.pyvider_http_api.patch_request.status_code
      response_time = data.pyvider_http_api.patch_request.response_time_ms
      success       = data.pyvider_http_api.patch_request.status_code >= 200 && data.pyvider_http_api.patch_request.status_code < 300
    }

    options_request = {
      status_code   = data.pyvider_http_api.options_request.status_code
      response_time = data.pyvider_http_api.options_request.response_time_ms
      success       = data.pyvider_http_api.options_request.status_code == 200
    }

    slow_api = {
      status_code   = data.pyvider_http_api.slow_api.status_code
      response_time = data.pyvider_http_api.slow_api.response_time_ms
      timeout_ok    = data.pyvider_http_api.slow_api.response_time_ms <= 10000
      success       = data.pyvider_http_api.slow_api.status_code == 200
    }
  }

  # Error handling examples
  error_scenarios = {
    not_found = {
      status_code = data.pyvider_http_api.not_found.status_code
      is_404      = data.pyvider_http_api.not_found.status_code == 404
      has_error   = data.pyvider_http_api.not_found.error_message != null
    }

    server_error = {
      status_code = data.pyvider_http_api.server_error.status_code
      is_5xx      = data.pyvider_http_api.server_error.status_code >= 500
      has_error   = data.pyvider_http_api.server_error.error_message != null
    }

    unauthorized = {
      status_code = data.pyvider_http_api.unauthorized.status_code
      is_401      = data.pyvider_http_api.unauthorized.status_code == 401
      has_error   = data.pyvider_http_api.unauthorized.error_message != null
    }
  }

  # Performance metrics
  performance_metrics = {
    fastest_response = min([
      for analysis in values(local.response_analysis) :
      analysis.response_time if analysis.response_time != null
    ]...)

    slowest_response = max([
      for analysis in values(local.response_analysis) :
      analysis.response_time if analysis.response_time != null
    ]...)

    average_response_time = sum([
      for analysis in values(local.response_analysis) :
      analysis.response_time if analysis.response_time != null
    ]) / length([
      for analysis in values(local.response_analysis) :
      analysis.response_time if analysis.response_time != null
    ])

    success_rate = (length([
      for analysis in values(local.response_analysis) :
      analysis if analysis.success
    ]) / length(values(local.response_analysis))) * 100
  }
}

# Create comprehensive analysis file
resource "pyvider_file_content" "advanced_api_analysis" {
  filename = "/tmp/http_api_advanced_analysis.json"
  content = jsonencode({
    timestamp = timestamp()

    http_methods_tested = [
      "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"
    ]

    response_analysis = local.response_analysis
    error_scenarios   = local.error_scenarios
    performance_metrics = local.performance_metrics

    user_data_example = {
      user_profile = local.user_data
      posts_count  = length(local.user_posts)
      first_post_title = length(local.user_posts) > 0 ? local.user_posts[0].title : null
    }

    api_patterns = {
      authentication_tested = true
      error_handling_tested = true
      timeout_handling_tested = true
      multiple_methods_tested = true
      json_responses_parsed = true
    }

    recommendations = [
      local.performance_metrics.success_rate < 100 ? "Some requests failed - check error handling" : null,
      local.performance_metrics.slowest_response > 5000 ? "Consider optimizing slow requests" : null,
      "Always implement proper error handling for production use",
      "Use environment variables for sensitive authentication tokens",
      "Consider implementing retry logic for critical API calls"
    ]
  })
}

# Create a detailed report
resource "pyvider_file_content" "advanced_api_report" {
  filename = "/tmp/http_api_advanced_report.txt"
  content = join("\n", [
    "=== Advanced HTTP API Examples Report ===",
    "",
    "=== HTTP Methods Test Results ===",
    "POST Request: ${local.response_analysis.post_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.post_request.status_code}) - ${local.response_analysis.post_request.response_time}ms",
    "PUT Request: ${local.response_analysis.put_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.put_request.status_code}) - ${local.response_analysis.put_request.response_time}ms",
    "DELETE Request: ${local.response_analysis.delete_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.delete_request.status_code}) - ${local.response_analysis.delete_request.response_time}ms",
    "PATCH Request: ${local.response_analysis.patch_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.patch_request.status_code}) - ${local.response_analysis.patch_request.response_time}ms",
    "OPTIONS Request: ${local.response_analysis.options_request.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.options_request.status_code}) - ${local.response_analysis.options_request.response_time}ms",
    "",
    "=== Timeout and Performance ===",
    "Slow API (3s delay): ${local.response_analysis.slow_api.success ? "SUCCESS" : "FAILED"} (${local.response_analysis.slow_api.status_code}) - ${local.response_analysis.slow_api.response_time}ms",
    "Timeout handled correctly: ${local.response_analysis.slow_api.timeout_ok ? "YES" : "NO"}",
    "",
    "=== Error Handling Tests ===",
    "404 Not Found: Status ${local.error_scenarios.not_found.status_code} - Is 404: ${local.error_scenarios.not_found.is_404}",
    "500 Server Error: Status ${local.error_scenarios.server_error.status_code} - Is 5xx: ${local.error_scenarios.server_error.is_5xx}",
    "401 Unauthorized: Status ${local.error_scenarios.unauthorized.status_code} - Is 401: ${local.error_scenarios.unauthorized.is_401}",
    "",
    "=== Performance Summary ===",
    "Success Rate: ${local.performance_metrics.success_rate}%",
    "Fastest Response: ${local.performance_metrics.fastest_response}ms",
    "Slowest Response: ${local.performance_metrics.slowest_response}ms",
    "Average Response Time: ${local.performance_metrics.average_response_time}ms",
    "",
    "=== User Data Example ===",
    "User Name: ${lookup(local.user_data, "name", "Unknown")}",
    "User Email: ${lookup(local.user_data, "email", "Unknown")}",
    "Posts Count: ${length(local.user_posts)}",
    length(local.user_posts) > 0 ? "First Post: ${local.user_posts[0].title}" : "No posts found",
    "",
    "=== Content Types Observed ===",
    "POST Response: ${local.response_analysis.post_request.content_type}",
    "Headers Count (POST): ${local.response_analysis.post_request.headers_count}",
    "",
    "Report generated at: ${timestamp()}"
  ])
}

output "advanced_http_api_results" {
  description = "Results from advanced HTTP API operations"
  value = {
    methods_tested = {
      post    = local.response_analysis.post_request.success
      put     = local.response_analysis.put_request.success
      delete  = local.response_analysis.delete_request.success
      patch   = local.response_analysis.patch_request.success
      options = local.response_analysis.options_request.success
    }

    performance_summary = local.performance_metrics

    error_handling = {
      handled_404 = local.error_scenarios.not_found.is_404
      handled_500 = local.error_scenarios.server_error.is_5xx
      handled_401 = local.error_scenarios.unauthorized.is_401
    }

    data_processing = {
      user_profile_parsed = contains(keys(local.user_data), "name")
      posts_retrieved     = length(local.user_posts)
      json_parsing_works  = length(local.post_response) > 0
    }

    files_created = [
      pyvider_file_content.advanced_api_analysis.filename,
      pyvider_file_content.advanced_api_report.filename
    ]
  }
}
```

### API Integration Patterns



### Error Handling



## Schema



## HTTP Methods

The data source supports all standard HTTP methods:

- **GET** (default) - Retrieve data
- **POST** - Send data to the server
- **PUT** - Update existing resources
- **PATCH** - Partial updates
- **DELETE** - Remove resources
- **HEAD** - Get headers only
- **OPTIONS** - Check allowed methods

```terraform
data "pyvider_http_api" "post_example" {
  url    = "https://api.example.com/users"
  method = "POST"
  headers = {
    "Content-Type" = "application/json"
    "Accept"       = "application/json"
  }
}
```

## Request Headers

Custom headers can be added for authentication, content type specification, and API requirements:

```terraform
data "pyvider_http_api" "authenticated" {
  url = "https://api.example.com/protected"
  headers = {
    "Authorization" = "Bearer ${var.api_token}"
    "User-Agent"    = "Terraform/pyvider-components"
    "Accept"        = "application/json"
    "Content-Type"  = "application/json"
  }
  timeout = 60
}
```

## Response Information

The data source provides comprehensive response details:

### Status and Content
- **`status_code`** - HTTP status code (200, 404, 500, etc.)
- **`response_body`** - Full response body as string
- **`content_type`** - Content-Type header value

### Performance Metrics
- **`response_time_ms`** - Response time in milliseconds
- **`response_headers`** - All response headers as a map
- **`header_count`** - Number of response headers

### Error Information
- **`error_message`** - Error description if request failed

## Timeout Configuration

Configure request timeouts to handle slow APIs:

```terraform
data "pyvider_http_api" "slow_api" {
  url     = "https://slow-api.example.com/data"
  timeout = 120  # 2 minutes
}
```

## Common Patterns

### Configuration Management
```terraform
# Fetch environment-specific configuration
data "pyvider_http_api" "env_config" {
  url = "https://config.example.com/environments/${var.environment}"
  headers = {
    "Authorization" = "Bearer ${var.config_api_token}"
  }
}

locals {
  config = jsondecode(data.pyvider_http_api.env_config.response_body)
}
```

### Service Discovery
```terraform
# Discover available services
data "pyvider_http_api" "service_registry" {
  url = "https://consul.example.com/v1/catalog/services"
}

locals {
  services = jsondecode(data.pyvider_http_api.service_registry.response_body)
  has_database = contains(keys(local.services), "database")
}
```

### Health Check Validation
```terraform
# Check if external service is healthy before proceeding
data "pyvider_http_api" "health_check" {
  url = "https://api.example.com/health"
}

locals {
  service_healthy = (
    data.pyvider_http_api.health_check.status_code == 200 &&
    jsondecode(data.pyvider_http_api.health_check.response_body).status == "healthy"
  )
}
```

### API Response Processing
```terraform
# Process JSON API response
data "pyvider_http_api" "user_data" {
  url = "https://jsonplaceholder.typicode.com/users/1"
}

locals {
  user = jsondecode(data.pyvider_http_api.user_data.response_body)
  user_email = local.user.email
  user_company = local.user.company.name
}
```

## Error Handling

Handle different types of errors gracefully:

```terraform
data "pyvider_http_api" "api_call" {
  url = "https://api.example.com/data"
}

locals {
  # Check for various error conditions
  request_succeeded = data.pyvider_http_api.api_call.status_code >= 200 && data.pyvider_http_api.api_call.status_code < 300

  api_response = local.request_succeeded ? jsondecode(data.pyvider_http_api.api_call.response_body) : {}

  fallback_config = {
    default = true
    message = "Using fallback configuration due to API error"
  }

  final_config = local.request_succeeded ? local.api_response : local.fallback_config
}
```

## Security Best Practices

1. **Secure API Keys**: Use variables or environment variables for sensitive tokens
2. **HTTPS Only**: Always use HTTPS URLs for sensitive data
3. **Timeout Limits**: Set reasonable timeouts to prevent hanging
4. **Error Handling**: Don't expose sensitive error details in outputs
5. **Rate Limiting**: Be mindful of API rate limits

```terraform
# Secure API call example
data "pyvider_http_api" "secure_api" {
  url = "https://secure-api.example.com/data"
  headers = {
    "Authorization" = "Bearer ${var.api_token}"  # Use variable, not hardcode
    "User-Agent"    = "MyApp/1.0"
  }
  timeout = 30
}

# Don't expose sensitive data in outputs
output "api_success" {
  value = data.pyvider_http_api.secure_api.status_code == 200
}
```

## Limitations

- **Request Body**: Currently doesn't support request body for POST/PUT requests
- **File Uploads**: Not designed for file upload operations
- **Cookies**: No automatic cookie handling
- **Redirects**: Follows redirects automatically but doesn't expose redirect chain
- **Binary Data**: Response body is treated as text

## Troubleshooting

### Common HTTP Status Codes
- **200 OK** - Success
- **401 Unauthorized** - Check authentication headers
- **403 Forbidden** - Check API permissions
- **404 Not Found** - Verify URL is correct
- **429 Too Many Requests** - API rate limit exceeded
- **500 Internal Server Error** - API server issue

### Connection Issues
```terraform
# Check for connection errors
locals {
  connection_error = data.pyvider_http_api.example.error_message != null
  timeout_occurred = data.pyvider_http_api.example.response_time_ms == null
}
```

## Related Components

- [`pyvider_file_content`](../../resources/file_content.md) - Save API responses to files
- [`pyvider_env_variables`](../env_variables.md) - Use environment variables for API credentials
- [`lens_jq` function](../../functions/lens_jq.md) - Transform API responses with JQ queries