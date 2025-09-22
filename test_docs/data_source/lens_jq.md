---
page_title: "Data Source: pyvider_lens_jq"
description: |-
  Transforms JSON data using JQ queries with powerful filtering and manipulation
---

# pyvider_lens_jq (Data Source)

> Transform and query JSON data using the powerful JQ language

The `pyvider_lens_jq` data source allows you to transform JSON data using JQ queries. This enables complex data manipulation, filtering, and extraction from JSON sources such as API responses, configuration files, or structured data within your Terraform configurations.

## When to Use This

- **JSON data transformation**: Process complex JSON structures from APIs or files
- **Data extraction**: Pull specific values from nested JSON documents
- **Configuration processing**: Transform configuration formats between systems
- **API response filtering**: Extract relevant data from large API responses
- **Data validation**: Check JSON structure and validate required fields

**Anti-patterns (when NOT to use):**
- Simple field access (use direct Terraform syntax instead)
- Non-JSON data (use string manipulation functions)
- Very large datasets (consider performance implications)
- Real-time data processing (this is for configuration-time transformation)

## Quick Start

```terraform
# Transform JSON configuration data
data "pyvider_lens_jq" "config_transform" {
  json_input = jsonencode({
    users = [
      { name = "Alice", role = "admin", active = true },
      { name = "Bob", role = "user", active = false }
    ]
  })
  query = ".users | map(select(.active)) | map(.name)"
}

# Result will be ["Alice"]
output "active_users" {
  value = data.pyvider_lens_jq.config_transform.result
}
```

## Examples

### Basic Usage

```terraform
# Basic JQ data source transformation examples

# Example 1: Simple field extraction
data "pyvider_lens_jq" "extract_user_name" {
  json_input = jsonencode({
    name = "John Doe"
    age  = 30
    email = "john.doe@example.com"
    address = {
      street = "123 Main St"
      city   = "Anytown"
      state  = "CA"
      zip    = "12345"
    }
  })
  query = ".name"
}

# Example 2: Nested field extraction
data "pyvider_lens_jq" "extract_city" {
  json_input = jsonencode({
    user = {
      profile = {
        address = {
          city = "San Francisco"
          state = "CA"
        }
      }
    }
  })
  query = ".user.profile.address.city"
}

# Example 3: Array operations
data "pyvider_lens_jq" "process_hobbies" {
  json_input = jsonencode({
    hobbies = ["reading", "hiking", "coding", "photography"]
  })
  query = ".hobbies | length"
}

# Example 4: Filter array elements
data "pyvider_lens_jq" "filter_employees" {
  json_input = jsonencode([
    {
      name = "Alice"
      department = "Engineering"
      salary = 95000
      active = true
    },
    {
      name = "Bob"
      department = "Marketing"
      salary = 75000
      active = false
    },
    {
      name = "Carol"
      department = "Engineering"
      salary = 105000
      active = true
    }
  ])
  query = "[.[] | select(.active and .department == \"Engineering\")]"
}

# Example 5: Transform and map
data "pyvider_lens_jq" "user_summary" {
  json_input = jsonencode([
    {
      id = 1
      firstName = "John"
      lastName = "Doe"
      posts = [
        { title = "Hello World", likes = 5 },
        { title = "Getting Started", likes = 12 }
      ]
    },
    {
      id = 2
      firstName = "Jane"
      lastName = "Smith"
      posts = [
        { title = "Advanced Tips", likes = 25 },
        { title = "Best Practices", likes = 18 }
      ]
    }
  ])
  query = "map({
    id,
    full_name: (.firstName + \" \" + .lastName),
    total_likes: [.posts[].likes] | add,
    post_count: (.posts | length)
  })"
}

# Example 6: Statistical operations
data "pyvider_lens_jq" "salary_stats" {
  json_input = jsonencode([
    { name = "Alice", salary = 95000 },
    { name = "Bob", salary = 75000 },
    { name = "Carol", salary = 105000 },
    { name = "Dave", salary = 85000 }
  ])
  query = "{
    total_employees: length,
    total_salary: [.[].salary] | add,
    average_salary: ([.[].salary] | add / length),
    max_salary: [.[].salary] | max,
    min_salary: [.[].salary] | min
  }"
}

# Create summary file with results
resource "pyvider_file_content" "jq_basic_results" {
  filename = "/tmp/jq_basic_results.txt"
  content = join("\n", [
    "=== Basic JQ Transformation Results ===",
    "",
    "User Name: ${data.pyvider_lens_jq.extract_user_name.result}",
    "City: ${data.pyvider_lens_jq.extract_city.result}",
    "Number of Hobbies: ${data.pyvider_lens_jq.process_hobbies.result}",
    "",
    "Active Engineers: ${length(data.pyvider_lens_jq.filter_employees.result)}",
    "User Summaries: ${length(data.pyvider_lens_jq.user_summary.result)}",
    "",
    "Salary Statistics:",
    "- Total Employees: ${jsondecode(data.pyvider_lens_jq.salary_stats.result).total_employees}",
    "- Average Salary: $${jsondecode(data.pyvider_lens_jq.salary_stats.result).average_salary}",
    "- Max Salary: $${jsondecode(data.pyvider_lens_jq.salary_stats.result).max_salary}",
    "- Min Salary: $${jsondecode(data.pyvider_lens_jq.salary_stats.result).min_salary}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "basic_jq_results" {
  description = "Results from basic JQ transformations"
  value = {
    user_name = data.pyvider_lens_jq.extract_user_name.result
    city = data.pyvider_lens_jq.extract_city.result
    hobby_count = data.pyvider_lens_jq.process_hobbies.result
    active_engineers = length(data.pyvider_lens_jq.filter_employees.result)
    user_summaries = length(data.pyvider_lens_jq.user_summary.result)
    salary_stats = jsondecode(data.pyvider_lens_jq.salary_stats.result)
  }
}
```

### Complex Transformations

```terraform
# Complex JQ transformations for advanced data processing

# Example 1: Multi-level data processing
data "pyvider_lens_jq" "company_analysis" {
  json_input = jsonencode({
    company = "TechCorp"
    departments = [
      {
        name = "Engineering"
        budget = 2500000
        employees = [
          { name = "Alice", role = "Senior Engineer", salary = 120000, skills = ["Python", "Go", "Kubernetes"] },
          { name = "Bob", role = "Engineer", salary = 95000, skills = ["JavaScript", "React", "Node.js"] },
          { name = "Carol", role = "Tech Lead", salary = 140000, skills = ["Python", "AWS", "Docker"] }
        ]
      },
      {
        name = "Marketing"
        budget = 1200000
        employees = [
          { name = "Dave", role = "Marketing Manager", salary = 85000, skills = ["SEO", "Analytics", "Content"] },
          { name = "Eve", role = "Content Creator", salary = 65000, skills = ["Writing", "Design", "Social Media"] }
        ]
      },
      {
        name = "Sales"
        budget = 1800000
        employees = [
          { name = "Frank", role = "Sales Director", salary = 110000, skills = ["B2B Sales", "CRM", "Negotiation"] },
          { name = "Grace", role = "Account Manager", salary = 75000, skills = ["Customer Relations", "Salesforce"] }
        ]
      }
    ]
  })
  query = ".departments | map({
    department: .name,
    employee_count: (.employees | length),
    total_salary_cost: ([.employees[].salary] | add),
    avg_salary: (([.employees[].salary] | add) / (.employees | length)),
    budget_utilization: ((([.employees[].salary] | add) / .budget) * 100),
    skill_diversity: ([.employees[].skills[]] | unique | length),
    senior_roles: ([.employees[] | select(.role | contains(\"Senior\") or contains(\"Lead\") or contains(\"Director\") or contains(\"Manager\"))] | length)
  })"
}

# Example 2: Time series data processing
data "pyvider_lens_jq" "metrics_analysis" {
  json_input = jsonencode({
    metrics = [
      { timestamp = "2024-01-01T00:00:00Z", cpu_usage = 45.2, memory_usage = 67.8, requests = 1250 },
      { timestamp = "2024-01-01T01:00:00Z", cpu_usage = 52.1, memory_usage = 72.1, requests = 1380 },
      { timestamp = "2024-01-01T02:00:00Z", cpu_usage = 38.9, memory_usage = 65.2, requests = 1100 },
      { timestamp = "2024-01-01T03:00:00Z", cpu_usage = 61.7, memory_usage = 78.9, requests = 1520 },
      { timestamp = "2024-01-01T04:00:00Z", cpu_usage = 44.3, memory_usage = 69.4, requests = 1290 }
    ]
  })
  query = "{
    total_hours: (.metrics | length),
    cpu_stats: {
      average: (([.metrics[].cpu_usage] | add) / (.metrics | length)),
      max: ([.metrics[].cpu_usage] | max),
      min: ([.metrics[].cpu_usage] | min),
      above_50: ([.metrics[] | select(.cpu_usage > 50)] | length)
    },
    memory_stats: {
      average: (([.metrics[].memory_usage] | add) / (.metrics | length)),
      max: ([.metrics[].memory_usage] | max),
      min: ([.metrics[].memory_usage] | min),
      above_75: ([.metrics[] | select(.memory_usage > 75)] | length)
    },
    request_stats: {
      total: ([.metrics[].requests] | add),
      average: (([.metrics[].requests] | add) / (.metrics | length)),
      peak_hour: (.metrics | max_by(.requests) | .timestamp),
      low_hour: (.metrics | min_by(.requests) | .timestamp)
    },
    alerts: [
      (.metrics[] | select(.cpu_usage > 60) | \"High CPU at \" + .timestamp),
      (.metrics[] | select(.memory_usage > 75) | \"High Memory at \" + .timestamp)
    ]
  }"
}

# Example 3: Configuration transformation and validation
data "pyvider_lens_jq" "config_processor" {
  json_input = jsonencode({
    environments = {
      development = {
        api_endpoint = "https://dev-api.example.com"
        database_url = "postgres://dev-db:5432/app"
        redis_url = "redis://dev-cache:6379"
        log_level = "debug"
        replicas = 1
        resources = {
          cpu = "100m"
          memory = "256Mi"
        }
      }
      staging = {
        api_endpoint = "https://staging-api.example.com"
        database_url = "postgres://staging-db:5432/app"
        redis_url = "redis://staging-cache:6379"
        log_level = "info"
        replicas = 2
        resources = {
          cpu = "500m"
          memory = "512Mi"
        }
      }
      production = {
        api_endpoint = "https://api.example.com"
        database_url = "postgres://prod-db:5432/app"
        redis_url = "redis://prod-cache:6379"
        log_level = "warn"
        replicas = 5
        resources = {
          cpu = "1000m"
          memory = "1Gi"
        }
      }
    }
  })
  query = ".environments | to_entries | map({
    environment: .key,
    config: .value,
    security_score: (
      (if (.value.api_endpoint | startswith(\"https://\")) then 25 else 0 end) +
      (if (.value.database_url | contains(\"ssl\")) then 25 else 10 end) +
      (if (.value.log_level == \"warn\" or .value.log_level == \"error\") then 25 else 0 end) +
      (if (.value.replicas > 1) then 25 else 0 end)
    ),
    resource_tier: (
      if (.value.resources.memory | test(\"Gi\")) then \"high\"
      elif (.value.resources.memory | test(\"512Mi\")) then \"medium\"
      else \"low\"
      end
    ),
    recommendations: [
      (if (.value.log_level == \"debug\" and .key != \"development\") then \"Consider changing log level from debug\" else empty end),
      (if (.value.replicas < 2 and .key == \"production\") then \"Production should have multiple replicas\" else empty end),
      (if (.value.api_endpoint | startswith(\"http://\")) then \"Use HTTPS for secure communication\" else empty end)
    ]
  })"
}

# Example 4: Data aggregation and grouping
data "pyvider_lens_jq" "transaction_analysis" {
  json_input = jsonencode([
    { id = "tx1", amount = 150.50, currency = "USD", category = "food", date = "2024-01-15", user_id = "user1" },
    { id = "tx2", amount = 75.25, currency = "USD", category = "transport", date = "2024-01-15", user_id = "user2" },
    { id = "tx3", amount = 200.00, currency = "EUR", category = "food", date = "2024-01-16", user_id = "user1" },
    { id = "tx4", amount = 50.75, currency = "USD", category = "entertainment", date = "2024-01-16", user_id = "user3" },
    { id = "tx5", amount = 120.30, currency = "EUR", category = "food", date = "2024-01-17", user_id = "user2" },
    { id = "tx6", amount = 90.45, currency = "USD", category = "transport", date = "2024-01-17", user_id = "user1" }
  ])
  query = "{
    by_category: (
      group_by(.category) | map({
        category: .[0].category,
        total_transactions: length,
        total_amount_usd: ([.[] | select(.currency == \"USD\") | .amount] | add // 0),
        total_amount_eur: ([.[] | select(.currency == \"EUR\") | .amount] | add // 0),
        avg_amount: (([.[].amount] | add) / length),
        users: ([.[].user_id] | unique)
      })
    ),
    by_currency: (
      group_by(.currency) | map({
        currency: .[0].currency,
        transaction_count: length,
        total_amount: ([.[].amount] | add),
        avg_amount: (([.[].amount] | add) / length),
        categories: ([.[].category] | unique)
      })
    ),
    by_date: (
      group_by(.date) | map({
        date: .[0].date,
        transaction_count: length,
        daily_total: ([.[].amount] | add),
        unique_users: ([.[].user_id] | unique | length)
      })
    ),
    summary: {
      total_transactions: length,
      unique_users: ([.[].user_id] | unique | length),
      date_range: {
        first: (map(.date) | sort | first),
        last: (map(.date) | sort | last)
      },
      largest_transaction: (max_by(.amount) | {id, amount, category}),
      most_active_user: (
        group_by(.user_id) | map({user: .[0].user_id, count: length}) | max_by(.count) | .user
      )
    }
  }"
}

# Create detailed analysis files
resource "pyvider_file_content" "company_analysis_report" {
  filename = "/tmp/company_analysis.json"
  content = jsonencode({
    timestamp = timestamp()
    analysis = jsondecode(data.pyvider_lens_jq.company_analysis.result)
    summary = {
      total_departments = length(jsondecode(data.pyvider_lens_jq.company_analysis.result))
      highest_budget_utilization = max([
        for dept in jsondecode(data.pyvider_lens_jq.company_analysis.result) :
        dept.budget_utilization
      ]...)
      most_diverse_skills = max([
        for dept in jsondecode(data.pyvider_lens_jq.company_analysis.result) :
        dept.skill_diversity
      ]...)
    }
  })
}

resource "pyvider_file_content" "metrics_dashboard" {
  filename = "/tmp/metrics_dashboard.txt"
  content = join("\n", [
    "=== System Metrics Dashboard ===",
    "",
    "Monitoring Period: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).total_hours} hours",
    "",
    "CPU Performance:",
    "- Average: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).cpu_stats.average}%",
    "- Peak: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).cpu_stats.max}%",
    "- High Usage Hours: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).cpu_stats.above_50}",
    "",
    "Memory Performance:",
    "- Average: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).memory_stats.average}%",
    "- Peak: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).memory_stats.max}%",
    "- Critical Hours: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).memory_stats.above_75}",
    "",
    "Request Statistics:",
    "- Total Requests: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).request_stats.total}",
    "- Average per Hour: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).request_stats.average}",
    "- Peak Hour: ${jsondecode(data.pyvider_lens_jq.metrics_analysis.result).request_stats.peak_hour}",
    "",
    "Alerts Generated: ${length(jsondecode(data.pyvider_lens_jq.metrics_analysis.result).alerts)}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

# Output comprehensive results
output "complex_jq_analysis" {
  description = "Complex JQ transformation results"
  value = {
    company_analysis = {
      departments_analyzed = length(jsondecode(data.pyvider_lens_jq.company_analysis.result))
      total_employees = sum([
        for dept in jsondecode(data.pyvider_lens_jq.company_analysis.result) :
        dept.employee_count
      ])
    }

    metrics_summary = {
      monitoring_hours = jsondecode(data.pyvider_lens_jq.metrics_analysis.result).total_hours
      cpu_avg = jsondecode(data.pyvider_lens_jq.metrics_analysis.result).cpu_stats.average
      memory_avg = jsondecode(data.pyvider_lens_jq.metrics_analysis.result).memory_stats.average
      total_requests = jsondecode(data.pyvider_lens_jq.metrics_analysis.result).request_stats.total
      alerts_generated = length(jsondecode(data.pyvider_lens_jq.metrics_analysis.result).alerts)
    }

    config_environments = length(jsondecode(data.pyvider_lens_jq.config_processor.result))

    transaction_summary = {
      total_transactions = jsondecode(data.pyvider_lens_jq.transaction_analysis.result).summary.total_transactions
      unique_users = jsondecode(data.pyvider_lens_jq.transaction_analysis.result).summary.unique_users
      categories_found = length(jsondecode(data.pyvider_lens_jq.transaction_analysis.result).by_category)
      currencies_found = length(jsondecode(data.pyvider_lens_jq.transaction_analysis.result).by_currency)
    }

    files_created = [
      pyvider_file_content.company_analysis_report.filename,
      pyvider_file_content.metrics_dashboard.filename
    ]
  }
}
```

### API Response Processing

```terraform
# API response processing with JQ transformations

# Example 1: GitHub API response processing
data "pyvider_http_api" "github_user" {
  url = "https://api.github.com/users/octocat"
  headers = {
    "Accept" = "application/vnd.github.v3+json"
    "User-Agent" = "Terraform-Pyvider-Example"
  }
}

data "pyvider_http_api" "github_repos" {
  url = "https://api.github.com/users/octocat/repos"
  headers = {
    "Accept" = "application/vnd.github.v3+json"
    "User-Agent" = "Terraform-Pyvider-Example"
  }
}

# Transform GitHub user profile
data "pyvider_lens_jq" "github_profile" {
  json_input = data.pyvider_http_api.github_user.response_body
  query = "{
    username: .login,
    display_name: (.name // .login),
    profile: {
      bio: .bio,
      location: .location,
      company: .company,
      blog: .blog,
      avatar_url: .avatar_url
    },
    stats: {
      public_repos: .public_repos,
      public_gists: .public_gists,
      followers: .followers,
      following: .following
    },
    account_info: {
      created_at: .created_at,
      updated_at: .updated_at,
      account_type: .type,
      is_hireable: (.hireable // false)
    }
  }"
}

# Process repository data
data "pyvider_lens_jq" "github_repo_analysis" {
  json_input = data.pyvider_http_api.github_repos.response_body
  query = "{
    repository_summary: {
      total_repos: length,
      public_repos: [.[] | select(.private == false)] | length,
      private_repos: [.[] | select(.private == true)] | length,
      fork_count: [.[] | select(.fork == true)] | length,
      original_repos: [.[] | select(.fork == false)] | length
    },
    language_stats: (
      [.[].language] | map(select(. != null)) |
      group_by(.) | map({language: .[0], count: length}) |
      sort_by(.count) | reverse
    ),
    popularity_metrics: {
      total_stars: ([.[].stargazers_count] | add),
      total_forks: ([.[].forks_count] | add),
      total_watchers: ([.[].watchers_count] | add),
      most_starred: (max_by(.stargazers_count) | {name, stars: .stargazers_count, url: .html_url}),
      most_forked: (max_by(.forks_count) | {name, forks: .forks_count, url: .html_url})
    },
    recent_activity: {
      recently_updated: ([.[] | select(.updated_at > \"2023-01-01\")] | length),
      last_update: ([.[].updated_at] | max),
      repos_with_issues: ([.[] | select(.has_issues == true)] | length),
      repos_with_wiki: ([.[] | select(.has_wiki == true)] | length)
    },
    top_repositories: (
      sort_by(.stargazers_count) | reverse | .[0:5] | map({
        name,
        description: (.description // \"No description\"),
        language,
        stars: .stargazers_count,
        forks: .forks_count,
        url: .html_url,
        last_updated: .updated_at
      })
    )
  }"
}

# Example 2: REST API data processing
data "pyvider_http_api" "jsonplaceholder_posts" {
  url = "https://jsonplaceholder.typicode.com/posts"
}

data "pyvider_http_api" "jsonplaceholder_users" {
  url = "https://jsonplaceholder.typicode.com/users"
}

data "pyvider_http_api" "jsonplaceholder_comments" {
  url = "https://jsonplaceholder.typicode.com/comments"
}

# Combine and analyze blog data
data "pyvider_lens_jq" "blog_analysis" {
  json_input = jsonencode({
    posts = jsondecode(data.pyvider_http_api.jsonplaceholder_posts.response_body)
    users = jsondecode(data.pyvider_http_api.jsonplaceholder_users.response_body)
    comments = jsondecode(data.pyvider_http_api.jsonplaceholder_comments.response_body)
  })
  query = "{
    content_statistics: {
      total_posts: (.posts | length),
      total_users: (.users | length),
      total_comments: (.comments | length),
      avg_comments_per_post: ((.comments | length) / (.posts | length)),
      posts_per_user: ((.posts | length) / (.users | length))
    },
    user_activity: (
      .users | map({
        id,
        name,
        username,
        email,
        website: .website,
        company: .company.name,
        posts_count: ([.id as $uid | .posts[] | select(.userId == $uid)] | length),
        comments_made: ([.id as $uid | .comments[] | select(.email == .email)] | length)
      }) | sort_by(.posts_count) | reverse
    ),
    content_engagement: (
      .posts | map({
        id,
        title,
        author_id: .userId,
        author_name: ([.userId as $uid | .users[] | select(.id == $uid) | .name][0]),
        word_count: (.body | split(\" \") | length),
        comment_count: ([.id as $pid | .comments[] | select(.postId == $pid)] | length),
        engagement_score: ([.id as $pid | .comments[] | select(.postId == $pid)] | length) * 10 + (.body | split(\" \") | length)
      }) | sort_by(.engagement_score) | reverse | .[0:10]
    ),
    domain_analysis: {
      companies: ([.users[].company.name] | unique),
      domains: ([.users[].website | select(. != null) | split(\".\")[-1]] | unique),
      email_domains: ([.users[].email | split(\"@\")[1]] | group_by(.) | map({domain: .[0], count: length}) | sort_by(.count) | reverse)
    }
  }"
}

# Example 3: Weather API processing
data "pyvider_http_api" "weather_data" {
  url = "https://api.openweathermap.org/data/2.5/forecast?q=London&appid=demo_key&units=metric"
}

# Process weather forecast (handling potential API failures gracefully)
data "pyvider_lens_jq" "weather_forecast" {
  json_input = can(jsondecode(data.pyvider_http_api.weather_data.response_body)) ?
    data.pyvider_http_api.weather_data.response_body :
    jsonencode({
      cod = "401"
      message = "API key required"
      list = []
      city = {name = "Demo", country = "XX"}
    })

  query = "if .cod == \"200\" then {
    location: {
      city: .city.name,
      country: .city.country,
      coordinates: {lat: .city.coord.lat, lon: .city.coord.lon}
    },
    forecast_summary: {
      total_forecasts: (.list | length),
      forecast_days: ((.list | length) / 8),
      temperature_range: {
        min: ([.list[].main.temp_min] | min),
        max: ([.list[].main.temp_max] | max),
        avg: (([.list[].main.temp] | add) / (.list | length))
      },
      weather_conditions: ([.list[].weather[0].main] | group_by(.) | map({condition: .[0], occurrences: length}) | sort_by(.occurrences) | reverse),
      humidity_stats: {
        avg: (([.list[].main.humidity] | add) / (.list | length)),
        max: ([.list[].main.humidity] | max),
        min: ([.list[].main.humidity] | min)
      }
    },
    daily_forecasts: (
      .list | group_by(.dt_txt | split(\" \")[0]) | map({
        date: .[0].dt_txt | split(\" \")[0],
        temp_high: ([.[].main.temp_max] | max),
        temp_low: ([.[].main.temp_min] | min),
        conditions: ([.[].weather[0].main] | unique),
        avg_humidity: (([.[].main.humidity] | add) / length),
        readings_count: length
      })
    )
  } else {
    error: \"Weather API request failed\",
    error_code: .cod,
    error_message: .message,
    mock_data: {
      location: {city: \"Demo City\", country: \"XX\"},
      forecast_summary: {note: \"This is mock data due to API failure\"}
    }
  } end"
}

# Create comprehensive API processing report
resource "pyvider_file_content" "api_processing_report" {
  filename = "/tmp/api_processing_report.json"
  content = jsonencode({
    timestamp = timestamp()

    github_analysis = data.pyvider_http_api.github_user.status_code == 200 ? {
      profile = jsondecode(data.pyvider_lens_jq.github_profile.result)
      repository_analysis = jsondecode(data.pyvider_lens_jq.github_repo_analysis.result)
      api_status = "success"
    } : {
      api_status = "failed"
      status_code = data.pyvider_http_api.github_user.status_code
    }

    blog_analysis = data.pyvider_http_api.jsonplaceholder_posts.status_code == 200 ? {
      analysis = jsondecode(data.pyvider_lens_jq.blog_analysis.result)
      api_status = "success"
    } : {
      api_status = "failed"
      status_code = data.pyvider_http_api.jsonplaceholder_posts.status_code
    }

    weather_analysis = {
      forecast = jsondecode(data.pyvider_lens_jq.weather_forecast.result)
      api_status = data.pyvider_http_api.weather_data.status_code == 200 ? "success" : "failed"
      status_code = data.pyvider_http_api.weather_data.status_code
    }

    processing_summary = {
      apis_called = 6
      successful_calls = sum([
        data.pyvider_http_api.github_user.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.github_repos.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.jsonplaceholder_posts.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.jsonplaceholder_users.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.jsonplaceholder_comments.status_code == 200 ? 1 : 0,
        data.pyvider_http_api.weather_data.status_code == 200 ? 1 : 0
      ])
      jq_transformations = 4
    }
  })
}

resource "pyvider_file_content" "github_report" {
  count = data.pyvider_http_api.github_user.status_code == 200 ? 1 : 0

  filename = "/tmp/github_analysis_report.txt"
  content = join("\n", [
    "=== GitHub Profile Analysis ===",
    "",
    "Profile Information:",
    "- Username: ${jsondecode(data.pyvider_lens_jq.github_profile.result).username}",
    "- Display Name: ${jsondecode(data.pyvider_lens_jq.github_profile.result).display_name}",
    "- Location: ${lookup(jsondecode(data.pyvider_lens_jq.github_profile.result).profile, "location", "Not specified")}",
    "- Company: ${lookup(jsondecode(data.pyvider_lens_jq.github_profile.result).profile, "company", "Not specified")}",
    "",
    "Repository Statistics:",
    "- Total Repositories: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.total_repos}",
    "- Public Repositories: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.public_repos}",
    "- Forked Repositories: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.fork_count}",
    "- Original Repositories: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.original_repos}",
    "",
    "Popularity Metrics:",
    "- Total Stars: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.total_stars}",
    "- Total Forks: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.total_forks}",
    "- Most Starred: ${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.most_starred.name} (${jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.most_starred.stars} stars)",
    "",
    "Programming Languages:",
    join("\n", [for lang in jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).language_stats : "- ${lang.language}: ${lang.count} repositories"]),
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "api_processing_results" {
  description = "Results from API data processing with JQ"
  value = {
    github_success = data.pyvider_http_api.github_user.status_code == 200
    blog_success = data.pyvider_http_api.jsonplaceholder_posts.status_code == 200
    weather_success = data.pyvider_http_api.weather_data.status_code == 200

    github_stats = data.pyvider_http_api.github_user.status_code == 200 ? {
      username = jsondecode(data.pyvider_lens_jq.github_profile.result).username
      total_repos = jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).repository_summary.total_repos
      total_stars = jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).popularity_metrics.total_stars
      languages = length(jsondecode(data.pyvider_lens_jq.github_repo_analysis.result).language_stats)
    } : null

    blog_stats = data.pyvider_http_api.jsonplaceholder_posts.status_code == 200 ? {
      total_posts = jsondecode(data.pyvider_lens_jq.blog_analysis.result).content_statistics.total_posts
      total_users = jsondecode(data.pyvider_lens_jq.blog_analysis.result).content_statistics.total_users
      total_comments = jsondecode(data.pyvider_lens_jq.blog_analysis.result).content_statistics.total_comments
      top_engaged_posts = length(jsondecode(data.pyvider_lens_jq.blog_analysis.result).content_engagement)
    } : null

    files_created = concat([
      pyvider_file_content.api_processing_report.filename
    ], data.pyvider_http_api.github_user.status_code == 200 ? [
      pyvider_file_content.github_report[0].filename
    ] : [])
  }
}
```

## Schema



## JQ Query Language

The data source uses the JQ query language for JSON processing. Here are key patterns:

### Basic Operations
- **`.field`** - Extract a field
- **`.nested.field`** - Extract nested field
- **`.[0]`** - Get first array element
- **`.[]`** - Iterate over array/object values

### Array Operations
- **`map(expression)`** - Transform each array element
- **`select(condition)`** - Filter elements
- **`length`** - Get array/object length
- **`sort_by(.field)`** - Sort by field value

### Filtering and Conditions
- **`select(.field == "value")`** - Filter by exact match
- **`select(.field > 10)`** - Numeric comparisons
- **`select(.field | test("pattern"))`** - Regex matching

### Data Manipulation
- **`{new_key: .old_key}`** - Reshape objects
- **`add`** - Sum array of numbers
- **`group_by(.field)`** - Group elements
- **`unique`** - Remove duplicates

## Common Patterns

### Extract Specific Fields
```terraform
data "pyvider_lens_jq" "extract_names" {
  json_input = jsonencode(var.users)
  query = ".[] | .name"
}
```

### Filter and Transform
```terraform
data "pyvider_lens_jq" "active_admins" {
  json_input = jsonencode(var.users)
  query = ".[] | select(.active and .role == \"admin\") | {name, email}"
}
```

### Statistical Operations
```terraform
data "pyvider_lens_jq" "user_stats" {
  json_input = jsonencode(var.users)
  query = "{total: length, active: [.[] | select(.active)] | length}"
}
```

### Complex Nested Processing
```terraform
data "pyvider_lens_jq" "department_summary" {
  json_input = jsonencode(var.company_data)
  query = ".departments | map({
    name: .name,
    employee_count: .employees | length,
    avg_salary: (.employees | map(.salary) | add / length)
  })"
}
```

## Integration with HTTP APIs

Transform API responses for use in Terraform:

```terraform
# Fetch data from API
data "pyvider_http_api" "github_repos" {
  url = "https://api.github.com/users/octocat/repos"
}

# Transform the response
data "pyvider_lens_jq" "repo_summary" {
  json_input = data.pyvider_http_api.github_repos.response_body
  query = "map(select(.private == false)) | map({
    name: .name,
    language: .language,
    stars: .stargazers_count
  }) | sort_by(.stars) | reverse"
}
```

## Configuration Management

Process environment-specific configurations:

```terraform
# Read environment variables
data "pyvider_env_variables" "config" {
  prefix = "APP_"
}

# Transform to application config format
data "pyvider_lens_jq" "app_config" {
  json_input = jsonencode(data.pyvider_env_variables.config.values)
  query = "to_entries | map({
    key: (.key | sub(\"APP_\"; \"\") | ascii_downcase),
    value: .value
  }) | from_entries"
}
```

## Error Handling

Handle malformed JSON or failed queries:

```terraform
data "pyvider_lens_jq" "safe_transform" {
  json_input = var.json_data
  query = "try (.users | map(.name)) catch []"
}

# Check if transformation succeeded
locals {
  transform_success = data.pyvider_lens_jq.safe_transform.result != null
  user_count = local.transform_success ? length(data.pyvider_lens_jq.safe_transform.result) : 0
}
```

## Performance Considerations

1. **Data Size**: JQ is efficient but very large JSON documents may impact performance
2. **Query Complexity**: Complex nested operations are slower than simple extractions
3. **Caching**: Results are cached during Terraform runs
4. **Memory Usage**: Large transformations may use significant memory

## Advanced JQ Patterns

### Grouping and Aggregation
```jq
group_by(.department) | map({
  department: .[0].department,
  count: length,
  avg_salary: (map(.salary) | add / length)
})
```

### Conditional Transformations
```jq
map(if .active then {name, role} else {name, status: "inactive"} end)
```

### Date Processing
```jq
map(.created_at | strptime("%Y-%m-%d") | strftime("%m/%d/%Y"))
```

### Deep Merging
```jq
reduce .[] as $item ({}; . * $item)
```

## Debugging JQ Queries

1. **Start Simple**: Begin with basic field extraction
2. **Use `debug` operator**: Add `| debug` to see intermediate values
3. **Test Incrementally**: Build complex queries step by step
4. **Online JQ Playground**: Test queries at jqplay.org before using

## Common Issues & Solutions

### Error: "Invalid JSON input"
**Solution**: Ensure `json_input` contains valid JSON string

```terraform
# ❌ Wrong - passing object directly
data "pyvider_lens_jq" "wrong" {
  json_input = var.my_object  # This is an object, not JSON
  query = ".field"
}

# ✅ Correct - encode to JSON first
data "pyvider_lens_jq" "correct" {
  json_input = jsonencode(var.my_object)
  query = ".field"
}
```

### Error: "JQ query failed"
**Solution**: Use `try-catch` for optional operations

```terraform
data "pyvider_lens_jq" "safe" {
  json_input = jsonencode(var.data)
  query = "try .optional_field catch null"
}
```

### Empty Results
**Solution**: Check your filter conditions and data structure

```terraform
# Debug what's in your data
data "pyvider_lens_jq" "debug" {
  json_input = jsonencode(var.data)
  query = "keys"  # Shows top-level keys
}
```

## Related Components

- [`lens_jq` function](../../functions/lens_jq.md) - Use JQ transformations in function calls
- [`pyvider_http_api`](../http_api.md) - Fetch JSON data from APIs for transformation
- [`pyvider_file_content`](../../resources/file_content.md) - Write transformed JSON to files
- [`pyvider_env_variables`](../env_variables.md) - Transform environment variable data