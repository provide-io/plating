---
page_title: "Function: divide"
description: |-
  Terraform function for divide
---

# divide (Function)

Terraform function for divide

## Example Usage

```terraform
# Numeric function examples

# Example 1: Basic arithmetic operations
locals {
  base_price = 99.99
  tax_rate = 0.08
  quantity = 3

  # Calculate tax and total
  tax_amount = provider::pyvider::multiply(local.base_price, local.tax_rate)
  subtotal = provider::pyvider::multiply(local.base_price, local.quantity)
  total_with_tax = provider::pyvider::add(local.subtotal, provider::pyvider::multiply(local.subtotal, local.tax_rate))
}

# Example 2: Working with lists of numbers
locals {
  server_response_times = [120, 89, 156, 78, 203, 95, 134]

  total_time = provider::pyvider::sum(local.server_response_times)
  max_response = provider::pyvider::max(local.server_response_times)
  min_response = provider::pyvider::min(local.server_response_times)
  average_response = provider::pyvider::divide(local.total_time, provider::pyvider::length(local.server_response_times))
}

# Example 3: Financial calculations
locals {
  monthly_costs = [1500.50, 2340.75, 987.25, 3456.80, 890.95]

  total_monthly_cost = provider::pyvider::sum(local.monthly_costs)
  highest_month = provider::pyvider::max(local.monthly_costs)
  lowest_month = provider::pyvider::min(local.monthly_costs)
  average_monthly = provider::pyvider::round(
    provider::pyvider::divide(local.total_monthly_cost, provider::pyvider::length(local.monthly_costs))
  )
}

# Example 4: Resource scaling calculations
locals {
  base_cpu_units = 2
  memory_gb = 8
  scaling_factor = 1.5

  # Calculate scaled resources
  scaled_cpu = provider::pyvider::multiply(local.base_cpu_units, local.scaling_factor)
  scaled_memory = provider::pyvider::multiply(local.memory_gb, local.scaling_factor)

  # Calculate cost (CPU: $0.10/unit/hour, Memory: $0.05/GB/hour)
  cpu_cost_per_hour = provider::pyvider::multiply(local.scaled_cpu, 0.10)
  memory_cost_per_hour = provider::pyvider::multiply(local.scaled_memory, 0.05)
  total_hourly_cost = provider::pyvider::add(local.cpu_cost_per_hour, local.memory_cost_per_hour)

  # Monthly cost (assume 730 hours/month)
  monthly_cost = provider::pyvider::round(provider::pyvider::multiply(local.total_hourly_cost, 730))
}

# Example 5: Performance metrics calculation
locals {
  request_counts = [1500, 2300, 1800, 3200, 2700, 1900, 2100]

  peak_requests = provider::pyvider::max(local.request_counts)
  total_requests = provider::pyvider::sum(local.request_counts)
  average_requests = provider::pyvider::round(
    provider::pyvider::divide(local.total_requests, provider::pyvider::length(local.request_counts))
  )

  # Calculate variance from average
  variance_values = [
    for count in local.request_counts :
    provider::pyvider::multiply(
      provider::pyvider::subtract(count, local.average_requests),
      provider::pyvider::subtract(count, local.average_requests)
    )
  ]
  variance = provider::pyvider::divide(provider::pyvider::sum(local.variance_values), provider::pyvider::length(local.variance_values))
}

# Example 6: Complex nested calculations
locals {
  # Calculate compound interest: A = P(1 + r/n)^(nt)
  principal = 10000
  annual_rate = 0.05
  compounds_per_year = 12
  years = 5

  # Break down the calculation step by step
  rate_per_period = provider::pyvider::divide(local.annual_rate, local.compounds_per_year)
  one_plus_rate = provider::pyvider::add(1, local.rate_per_period)
  total_periods = provider::pyvider::multiply(local.compounds_per_year, local.years)

  # For this example, we'll approximate the power calculation
  # In practice, you might use external tools for complex math
  compound_factor = 1.28  # Approximation of (1.004167)^60
  final_amount = provider::pyvider::round(provider::pyvider::multiply(local.principal, local.compound_factor))
  interest_earned = provider::pyvider::subtract(local.final_amount, local.principal)
}

# Create a summary report
resource "pyvider_file_content" "numeric_calculations" {
  filename = "/tmp/numeric_calculations.txt"
  content = join("\n", [
    "=== Numeric Function Examples ===",
    "",
    "=== Shopping Cart Calculation ===",
    "Base price: $${local.base_price}",
    "Quantity: ${local.quantity}",
    "Tax rate: ${local.tax_rate * 100}%",
    "Subtotal: $${local.subtotal}",
    "Tax amount: $${provider::pyvider::round(local.tax_amount)}",
    "Total with tax: $${provider::pyvider::round(local.total_with_tax)}",
    "",
    "=== Server Performance Metrics ===",
    "Response times (ms): ${jsonencode(local.server_response_times)}",
    "Total time: ${local.total_time}ms",
    "Average response: ${provider::pyvider::round(local.average_response)}ms",
    "Min response: ${local.min_response}ms",
    "Max response: ${local.max_response}ms",
    "",
    "=== Monthly Cost Analysis ===",
    "Monthly costs: ${jsonencode(local.monthly_costs)}",
    "Total: $${local.total_monthly_cost}",
    "Average: $${local.average_monthly}",
    "Highest month: $${local.highest_month}",
    "Lowest month: $${local.lowest_month}",
    "",
    "=== Resource Scaling ===",
    "Base CPU: ${local.base_cpu_units} units",
    "Base Memory: ${local.memory_gb} GB",
    "Scaling factor: ${local.scaling_factor}x",
    "Scaled CPU: ${local.scaled_cpu} units",
    "Scaled Memory: ${local.scaled_memory} GB",
    "Hourly cost: $${provider::pyvider::round(local.total_hourly_cost)}",
    "Monthly cost: $${local.monthly_cost}",
    "",
    "=== Request Analytics ===",
    "Request counts: ${jsonencode(local.request_counts)}",
    "Total requests: ${local.total_requests}",
    "Average requests: ${local.average_requests}",
    "Peak requests: ${local.peak_requests}",
    "Variance: ${provider::pyvider::round(local.variance)}",
    "",
    "=== Investment Calculation ===",
    "Principal: $${local.principal}",
    "Annual rate: ${local.annual_rate * 100}%",
    "Compounding: ${local.compounds_per_year}x per year",
    "Years: ${local.years}",
    "Final amount: $${local.final_amount}",
    "Interest earned: $${local.interest_earned}",
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "numeric_function_results" {
  description = "Results of various numeric calculations"
  value = {
    shopping_cart = {
      subtotal = local.subtotal
      tax_amount = provider::pyvider::round(local.tax_amount)
      total = provider::pyvider::round(local.total_with_tax)
    }

    performance_metrics = {
      total_time = local.total_time
      average_response = provider::pyvider::round(local.average_response)
      min_response = local.min_response
      max_response = local.max_response
    }

    cost_analysis = {
      total_monthly = local.total_monthly_cost
      average_monthly = local.average_monthly
      highest_month = local.highest_month
      lowest_month = local.lowest_month
    }

    resource_scaling = {
      scaled_cpu = local.scaled_cpu
      scaled_memory = local.scaled_memory
      hourly_cost = provider::pyvider::round(local.total_hourly_cost)
      monthly_cost = local.monthly_cost
    }

    request_analytics = {
      total_requests = local.total_requests
      average_requests = local.average_requests
      peak_requests = local.peak_requests
      variance = provider::pyvider::round(local.variance)
    }

    investment = {
      final_amount = local.final_amount
      interest_earned = local.interest_earned
    }

    calculations_file = pyvider_file_content.numeric_calculations.filename
  }
}

```

## Signature

``round(number, precision)``

## Arguments



