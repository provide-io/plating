---
page_title: "Resource: pyvider_timed_token"
description: |-
  Generates time-limited authentication tokens with automatic expiration management
---

# pyvider_timed_token (Resource)

> Generate secure, time-limited tokens for authentication and authorization workflows

The `pyvider_timed_token` resource creates time-limited authentication tokens that automatically expire after a specified duration. This is useful for generating temporary access credentials, API keys, or session tokens with built-in security through automatic expiration.

## When to Use This

- **Temporary API access**: Generate short-lived tokens for external integrations
- **Session management**: Create time-limited session tokens for applications
- **Secure automation**: Provide temporary credentials for CI/CD pipelines
- **Token rotation**: Implement automatic token refresh workflows
- **Testing and development**: Generate test tokens with predictable expiration

**Anti-patterns (when NOT to use):**
- Long-term authentication (use proper credential management instead)
- Storing tokens in version control (tokens are sensitive)
- Client-side token generation (generate server-side for security)
- Permanent access tokens (defeats the purpose of time-limited security)

## Quick Start

```terraform
# Generate a simple timed token
resource "pyvider_timed_token" "api_access" {
  name = "temporary-api-token"
}

# Use the token in other resources
resource "pyvider_file_content" "api_config" {
  filename = "/tmp/api_config.json"
  content = jsonencode({
    api_token = pyvider_timed_token.api_access.token
    expires_at = pyvider_timed_token.api_access.expires_at
  })
}
```

## Examples

### Basic Usage

```terraform
# Basic timed token examples

# Example 1: Simple token generation
resource "pyvider_timed_token" "simple" {
  name = "basic-example-token"
}

# Example 2: Token for API integration
resource "pyvider_timed_token" "api_auth" {
  name = "api-integration-token"
}

# Create configuration file with token
resource "pyvider_file_content" "api_config" {
  filename = "/tmp/api_config.json"
  content = jsonencode({
    authentication = {
      token_id = pyvider_timed_token.api_auth.id
      token_name = pyvider_timed_token.api_auth.name
      expires_at = pyvider_timed_token.api_auth.expires_at
      # Note: token value is sensitive and not included in config file
      token_available = pyvider_timed_token.api_auth.token != null
    }
    api_endpoint = "https://api.example.com/v1"
    timeout_seconds = 30
    retry_attempts = 3
  })
}

# Example 3: Token for service authentication
resource "pyvider_timed_token" "service_auth" {
  name = "background-service-token"
}

# Create service configuration
resource "pyvider_file_content" "service_config" {
  filename = "/tmp/service_config.yaml"
  content = yamlencode({
    service = {
      name = "background-processor"
      authentication = {
        method = "bearer_token"
        token_name = pyvider_timed_token.service_auth.name
        token_id = pyvider_timed_token.service_auth.id
        expires_at = pyvider_timed_token.service_auth.expires_at
      }
      endpoints = {
        health_check = "/health"
        metrics = "/metrics"
        ready = "/ready"
      }
    }
  })
}

# Example 4: Multiple tokens for different purposes
resource "pyvider_timed_token" "read_token" {
  name = "readonly-access-token"
}

resource "pyvider_timed_token" "write_token" {
  name = "write-access-token"
}

# Create access control configuration
resource "pyvider_file_content" "access_control" {
  filename = "/tmp/access_control.json"
  content = jsonencode({
    access_tokens = {
      readonly = {
        token_id = pyvider_timed_token.read_token.id
        name = pyvider_timed_token.read_token.name
        expires_at = pyvider_timed_token.read_token.expires_at
        permissions = ["read", "list"]
        scope = "user_data"
      }
      readwrite = {
        token_id = pyvider_timed_token.write_token.id
        name = pyvider_timed_token.write_token.name
        expires_at = pyvider_timed_token.write_token.expires_at
        permissions = ["read", "write", "delete", "list"]
        scope = "user_data"
      }
    }
    token_validation = {
      check_expiration = true
      require_https = true
      audience = "api.example.com"
    }
  })
}

# Example 5: Token with monitoring configuration
resource "pyvider_timed_token" "monitored_token" {
  name = "production-api-token"
}

# Create monitoring and alerting configuration
resource "pyvider_file_content" "token_monitoring" {
  filename = "/tmp/token_monitoring.json"
  content = jsonencode({
    token_monitoring = {
      token_id = pyvider_timed_token.monitored_token.id
      token_name = pyvider_timed_token.monitored_token.name
      expires_at = pyvider_timed_token.monitored_token.expires_at

      alerts = {
        expiration_warning = {
          enabled = true
          warn_before_minutes = 15
          notification_channels = ["email", "slack"]
        }
        usage_monitoring = {
          enabled = true
          track_requests = true
          alert_on_unusual_activity = true
        }
      }

      rotation_policy = {
        automatic = false
        manual_approval_required = true
        advance_notice_hours = 4
      }
    }

    metadata = {
      environment = "production"
      service = "api-gateway"
      owner = "platform-team"
      created_at = timestamp()
    }
  })
}

# Create token registry for tracking
resource "pyvider_file_content" "token_registry" {
  filename = "/tmp/token_registry.txt"
  content = join("\n", [
    "=== Token Registry ===",
    "",
    "Basic Token:",
    "  Name: ${pyvider_timed_token.simple.name}",
    "  ID: ${pyvider_timed_token.simple.id}",
    "  Expires: ${pyvider_timed_token.simple.expires_at}",
    "",
    "API Authentication Token:",
    "  Name: ${pyvider_timed_token.api_auth.name}",
    "  ID: ${pyvider_timed_token.api_auth.id}",
    "  Expires: ${pyvider_timed_token.api_auth.expires_at}",
    "",
    "Service Authentication Token:",
    "  Name: ${pyvider_timed_token.service_auth.name}",
    "  ID: ${pyvider_timed_token.service_auth.id}",
    "  Expires: ${pyvider_timed_token.service_auth.expires_at}",
    "",
    "Access Control Tokens:",
    "  Read Token: ${pyvider_timed_token.read_token.name} (${pyvider_timed_token.read_token.id})",
    "  Write Token: ${pyvider_timed_token.write_token.name} (${pyvider_timed_token.write_token.id})",
    "",
    "Monitored Production Token:",
    "  Name: ${pyvider_timed_token.monitored_token.name}",
    "  ID: ${pyvider_timed_token.monitored_token.id}",
    "  Expires: ${pyvider_timed_token.monitored_token.expires_at}",
    "",
    "⚠️  All tokens are time-limited and will expire automatically.",
    "⚠️  Token values are sensitive and stored securely.",
    "⚠️  Plan for token rotation before expiration.",
    "",
    "Registry generated at: ${timestamp()}"
  ])
}

output "basic_token_examples" {
  description = "Information about created tokens (sensitive values excluded)"
  value = {
    tokens_created = {
      simple = {
        name = pyvider_timed_token.simple.name
        id = pyvider_timed_token.simple.id
        expires_at = pyvider_timed_token.simple.expires_at
        token_available = pyvider_timed_token.simple.token != null
      }

      api_auth = {
        name = pyvider_timed_token.api_auth.name
        id = pyvider_timed_token.api_auth.id
        expires_at = pyvider_timed_token.api_auth.expires_at
        token_available = pyvider_timed_token.api_auth.token != null
      }

      service_auth = {
        name = pyvider_timed_token.service_auth.name
        id = pyvider_timed_token.service_auth.id
        expires_at = pyvider_timed_token.service_auth.expires_at
        token_available = pyvider_timed_token.service_auth.token != null
      }

      read_access = {
        name = pyvider_timed_token.read_token.name
        id = pyvider_timed_token.read_token.id
        expires_at = pyvider_timed_token.read_token.expires_at
        token_available = pyvider_timed_token.read_token.token != null
      }

      write_access = {
        name = pyvider_timed_token.write_token.name
        id = pyvider_timed_token.write_token.id
        expires_at = pyvider_timed_token.write_token.expires_at
        token_available = pyvider_timed_token.write_token.token != null
      }

      monitored = {
        name = pyvider_timed_token.monitored_token.name
        id = pyvider_timed_token.monitored_token.id
        expires_at = pyvider_timed_token.monitored_token.expires_at
        token_available = pyvider_timed_token.monitored_token.token != null
      }
    }

    summary = {
      total_tokens = 6
      all_tokens_valid = (
        pyvider_timed_token.simple.token != null &&
        pyvider_timed_token.api_auth.token != null &&
        pyvider_timed_token.service_auth.token != null &&
        pyvider_timed_token.read_token.token != null &&
        pyvider_timed_token.write_token.token != null &&
        pyvider_timed_token.monitored_token.token != null
      )
    }

    files_created = [
      pyvider_file_content.api_config.filename,
      pyvider_file_content.service_config.filename,
      pyvider_file_content.access_control.filename,
      pyvider_file_content.token_monitoring.filename,
      pyvider_file_content.token_registry.filename
    ]
  }
}
```

### CI/CD Pipeline Tokens

```terraform
# CI/CD pipeline token examples

# Example 1: GitHub Actions deployment token
resource "pyvider_timed_token" "github_deploy" {
  name = "github-actions-deployment"
}

# Create GitHub Actions configuration
resource "pyvider_file_content" "github_actions_config" {
  filename = "/tmp/github_actions_config.yaml"
  content = yamlencode({
    deployment = {
      token_info = {
        name = pyvider_timed_token.github_deploy.name
        id = pyvider_timed_token.github_deploy.id
        expires_at = pyvider_timed_token.github_deploy.expires_at
        token_available = pyvider_timed_token.github_deploy.token != null
      }
      environment = "production"
      deployment_strategy = "rolling"
      timeout_minutes = 30
    }

    workflow = {
      name = "Deploy to Production"
      on = {
        push = {
          branches = ["main"]
        }
      }
      jobs = {
        deploy = {
          "runs-on" = "ubuntu-latest"
          steps = [
            {
              name = "Checkout code"
              uses = "actions/checkout@v3"
            },
            {
              name = "Deploy with temporary token"
              run = "deploy.sh"
              env = {
                DEPLOY_TOKEN_ID = pyvider_timed_token.github_deploy.id
                DEPLOY_TOKEN_EXPIRES = pyvider_timed_token.github_deploy.expires_at
              }
            }
          ]
        }
      }
    }
  })
}

# Example 2: Jenkins pipeline token
resource "pyvider_timed_token" "jenkins_build" {
  name = "jenkins-build-pipeline"
}

# Create Jenkins pipeline configuration
resource "pyvider_file_content" "jenkins_config" {
  filename = "/tmp/Jenkinsfile.config"
  content = join("\n", [
    "// Jenkins Pipeline Configuration",
    "// Generated with temporary token: ${pyvider_timed_token.jenkins_build.id}",
    "",
    "pipeline {",
    "    agent any",
    "    ",
    "    environment {",
    "        BUILD_TOKEN_ID = '${pyvider_timed_token.jenkins_build.id}'",
    "        BUILD_TOKEN_NAME = '${pyvider_timed_token.jenkins_build.name}'",
    "        TOKEN_EXPIRES_AT = '${pyvider_timed_token.jenkins_build.expires_at}'",
    "    }",
    "    ",
    "    stages {",
    "        stage('Validate Token') {",
    "            steps {",
    "                script {",
    "                    echo \"Using token: ${pyvider_timed_token.jenkins_build.name}\"",
    "                    echo \"Token ID: ${pyvider_timed_token.jenkins_build.id}\"",
    "                    echo \"Expires at: ${pyvider_timed_token.jenkins_build.expires_at}\"",
    "                    ",
    "                    // Validate token is available",
    "                    if (!env.BUILD_TOKEN_ID) {",
    "                        error('Build token is not available')",
    "                    }",
    "                }",
    "            }",
    "        }",
    "        ",
    "        stage('Build') {",
    "            steps {",
    "                echo 'Building application with temporary credentials...'",
    "                // Build steps would use the temporary token",
    "            }",
    "        }",
    "        ",
    "        stage('Test') {",
    "            steps {",
    "                echo 'Running tests with build token...'",
    "                // Test steps with token authentication",
    "            }",
    "        }",
    "        ",
    "        stage('Deploy') {",
    "            when {",
    "                branch 'main'",
    "            }",
    "            steps {",
    "                echo 'Deploying with temporary deployment token...'",
    "                // Deployment steps using the token",
    "            }",
    "        }",
    "    }",
    "    ",
    "    post {",
    "        always {",
    "            echo 'Pipeline completed. Token will expire automatically.'",
    "        }",
    "        failure {",
    "            echo 'Pipeline failed. Check token validity and expiration.'",
    "        }",
    "    }",
    "}"
  ])
}

# Example 3: GitLab CI/CD token
resource "pyvider_timed_token" "gitlab_ci" {
  name = "gitlab-ci-deployment"
}

# Create GitLab CI configuration
resource "pyvider_file_content" "gitlab_ci_config" {
  filename = "/tmp/gitlab-ci.yml"
  content = yamlencode({
    stages = ["build", "test", "deploy"]

    variables = {
      CI_TOKEN_NAME = pyvider_timed_token.gitlab_ci.name
      CI_TOKEN_ID = pyvider_timed_token.gitlab_ci.id
      TOKEN_EXPIRES_AT = pyvider_timed_token.gitlab_ci.expires_at
    }

    before_script = [
      "echo \"Using CI token: $CI_TOKEN_NAME\"",
      "echo \"Token expires at: $TOKEN_EXPIRES_AT\"",
      "# Token validation would happen here"
    ]

    build = {
      stage = "build"
      script = [
        "echo \"Building with token ID: $CI_TOKEN_ID\"",
        "# Build commands using the temporary token"
      ]
      artifacts = {
        paths = ["dist/"]
        expire_in = "1 hour"
      }
    }

    test = {
      stage = "test"
      script = [
        "echo \"Testing with temporary credentials\"",
        "# Test commands with token authentication"
      ]
      dependencies = ["build"]
    }

    deploy = {
      stage = "deploy"
      script = [
        "echo \"Deploying with token: $CI_TOKEN_NAME\"",
        "echo \"Deployment token expires: $TOKEN_EXPIRES_AT\"",
        "# Deployment commands using the token"
      ]
      only = ["main"]
      when = "manual"
    }
  })
}

# Example 4: Azure DevOps pipeline token
resource "pyvider_timed_token" "azure_devops" {
  name = "azure-devops-build"
}

# Create Azure DevOps pipeline configuration
resource "pyvider_file_content" "azure_pipeline_config" {
  filename = "/tmp/azure-pipelines.yml"
  content = join("\n", [
    "# Azure DevOps Pipeline",
    "# Token: ${pyvider_timed_token.azure_devops.name}",
    "# Token ID: ${pyvider_timed_token.azure_devops.id}",
    "# Expires: ${pyvider_timed_token.azure_devops.expires_at}",
    "",
    "trigger:",
    "  branches:",
    "    include:",
    "      - main",
    "      - develop",
    "",
    "variables:",
    "  buildTokenId: '${pyvider_timed_token.azure_devops.id}'",
    "  buildTokenName: '${pyvider_timed_token.azure_devops.name}'",
    "  tokenExpiresAt: '${pyvider_timed_token.azure_devops.expires_at}'",
    "",
    "stages:",
    "  - stage: Build",
    "    displayName: 'Build Application'",
    "    jobs:",
    "      - job: BuildJob",
    "        displayName: 'Build with Temporary Token'",
    "        pool:",
    "          vmImage: 'ubuntu-latest'",
    "        steps:",
    "          - script: |",
    "              echo \"Using build token: $(buildTokenName)\"",
    "              echo \"Token ID: $(buildTokenId)\"",
    "              echo \"Token expires: $(tokenExpiresAt)\"",
    "              # Build commands would use the temporary token",
    "            displayName: 'Build Application'",
    "",
    "  - stage: Test",
    "    displayName: 'Run Tests'",
    "    dependsOn: Build",
    "    jobs:",
    "      - job: TestJob",
    "        displayName: 'Test with Token Authentication'",
    "        pool:",
    "          vmImage: 'ubuntu-latest'",
    "        steps:",
    "          - script: |",
    "              echo \"Running tests with token: $(buildTokenName)\"",
    "              # Test commands with token authentication",
    "            displayName: 'Run Tests'",
    "",
    "  - stage: Deploy",
    "    displayName: 'Deploy to Production'",
    "    dependsOn: Test",
    "    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))",
    "    jobs:",
    "      - deployment: DeployJob",
    "        displayName: 'Deploy with Temporary Credentials'",
    "        environment: 'production'",
    "        strategy:",
    "          runOnce:",
    "            deploy:",
    "              steps:",
    "                - script: |",
    "                    echo \"Deploying with token: $(buildTokenName)\"",
    "                    echo \"Token expires at: $(tokenExpiresAt)\"",
    "                    # Deployment commands using the token",
    "                  displayName: 'Deploy Application'"
  ])
}

# Example 5: CircleCI configuration token
resource "pyvider_timed_token" "circleci" {
  name = "circleci-workflow"
}

# Create CircleCI configuration
resource "pyvider_file_content" "circleci_config" {
  filename = "/tmp/circleci_config.yml"
  content = yamlencode({
    version = "2.1"

    executors = {
      default = {
        docker = [
          {
            image = "cimg/node:18.0"
          }
        ]
        environment = {
          CI_TOKEN_NAME = pyvider_timed_token.circleci.name
          CI_TOKEN_ID = pyvider_timed_token.circleci.id
          TOKEN_EXPIRES_AT = pyvider_timed_token.circleci.expires_at
        }
      }
    }

    jobs = {
      build = {
        executor = "default"
        steps = [
          "checkout",
          {
            run = {
              name = "Validate Token"
              command = join("\n", [
                "echo \"Using CircleCI token: $CI_TOKEN_NAME\"",
                "echo \"Token ID: $CI_TOKEN_ID\"",
                "echo \"Expires at: $TOKEN_EXPIRES_AT\"",
                "# Token validation logic here"
              ])
            }
          },
          {
            run = {
              name = "Build Application"
              command = join("\n", [
                "echo \"Building with temporary token\"",
                "# Build commands using the token"
              ])
            }
          }
        ]
      }

      test = {
        executor = "default"
        steps = [
          "checkout",
          {
            run = {
              name = "Run Tests"
              command = join("\n", [
                "echo \"Testing with token: $CI_TOKEN_NAME\"",
                "# Test commands with token authentication"
              ])
            }
          }
        ]
      }

      deploy = {
        executor = "default"
        steps = [
          "checkout",
          {
            run = {
              name = "Deploy to Production"
              command = join("\n", [
                "echo \"Deploying with token: $CI_TOKEN_NAME\"",
                "echo \"Token expires: $TOKEN_EXPIRES_AT\"",
                "# Deployment commands using the token"
              ])
            }
          }
        ]
      }
    }

    workflows = {
      build_test_deploy = {
        jobs = [
          "build",
          {
            test = {
              requires = ["build"]
            }
          },
          {
            deploy = {
              requires = ["test"]
              filters = {
                branches = {
                  only = ["main"]
                }
              }
            }
          }
        ]
      }
    }
  })
}

# Create CI/CD token management summary
resource "pyvider_file_content" "cicd_token_summary" {
  filename = "/tmp/cicd_token_summary.json"
  content = jsonencode({
    timestamp = timestamp()

    ci_cd_tokens = {
      github_actions = {
        token_name = pyvider_timed_token.github_deploy.name
        token_id = pyvider_timed_token.github_deploy.id
        expires_at = pyvider_timed_token.github_deploy.expires_at
        platform = "GitHub Actions"
        use_case = "Production deployment"
      }

      jenkins = {
        token_name = pyvider_timed_token.jenkins_build.name
        token_id = pyvider_timed_token.jenkins_build.id
        expires_at = pyvider_timed_token.jenkins_build.expires_at
        platform = "Jenkins"
        use_case = "Build pipeline"
      }

      gitlab_ci = {
        token_name = pyvider_timed_token.gitlab_ci.name
        token_id = pyvider_timed_token.gitlab_ci.id
        expires_at = pyvider_timed_token.gitlab_ci.expires_at
        platform = "GitLab CI/CD"
        use_case = "CI/CD deployment"
      }

      azure_devops = {
        token_name = pyvider_timed_token.azure_devops.name
        token_id = pyvider_timed_token.azure_devops.id
        expires_at = pyvider_timed_token.azure_devops.expires_at
        platform = "Azure DevOps"
        use_case = "Build and deployment"
      }

      circleci = {
        token_name = pyvider_timed_token.circleci.name
        token_id = pyvider_timed_token.circleci.id
        expires_at = pyvider_timed_token.circleci.expires_at
        platform = "CircleCI"
        use_case = "Workflow automation"
      }
    }

    security_features = {
      automatic_expiration = true
      sensitive_data_protection = true
      platform_agnostic = true
      no_permanent_credentials = true
    }

    best_practices = [
      "Use environment variables for token IDs",
      "Validate token availability before use",
      "Monitor token expiration times",
      "Plan for token rotation",
      "Never commit actual token values to repository",
      "Use tokens only for the duration needed"
    ]

    recommendations = {
      token_rotation = "Implement automated token rotation for production workloads"
      monitoring = "Set up alerts before token expiration"
      security = "Audit token usage and access patterns"
      documentation = "Document token lifecycle and responsibilities"
    }
  })
}

output "cicd_token_configurations" {
  description = "CI/CD platform token configurations"
  value = {
    platforms_configured = ["GitHub Actions", "Jenkins", "GitLab CI/CD", "Azure DevOps", "CircleCI"]

    tokens_created = {
      github_actions = {
        name = pyvider_timed_token.github_deploy.name
        id = pyvider_timed_token.github_deploy.id
        expires_at = pyvider_timed_token.github_deploy.expires_at
      }
      jenkins = {
        name = pyvider_timed_token.jenkins_build.name
        id = pyvider_timed_token.jenkins_build.id
        expires_at = pyvider_timed_token.jenkins_build.expires_at
      }
      gitlab_ci = {
        name = pyvider_timed_token.gitlab_ci.name
        id = pyvider_timed_token.gitlab_ci.id
        expires_at = pyvider_timed_token.gitlab_ci.expires_at
      }
      azure_devops = {
        name = pyvider_timed_token.azure_devops.name
        id = pyvider_timed_token.azure_devops.id
        expires_at = pyvider_timed_token.azure_devops.expires_at
      }
      circleci = {
        name = pyvider_timed_token.circleci.name
        id = pyvider_timed_token.circleci.id
        expires_at = pyvider_timed_token.circleci.expires_at
      }
    }

    configuration_files = [
      pyvider_file_content.github_actions_config.filename,
      pyvider_file_content.jenkins_config.filename,
      pyvider_file_content.gitlab_ci_config.filename,
      pyvider_file_content.azure_pipeline_config.filename,
      pyvider_file_content.circleci_config.filename,
      pyvider_file_content.cicd_token_summary.filename
    ]

    security_summary = {
      total_tokens = 5
      all_tokens_time_limited = true
      sensitive_values_protected = true
      automatic_expiration = true
    }
  }
}
```

### API Integration Tokens

```terraform
# API integration token examples

# Example 1: External API authentication
resource "pyvider_timed_token" "external_api" {
  name = "external-service-integration"
}

# Use token for API authentication
data "pyvider_http_api" "authenticated_request" {
  url = "https://api.example.com/v1/data"
  headers = {
    "Authorization" = "Bearer ${pyvider_timed_token.external_api.token}"
    "Content-Type"  = "application/json"
    "X-API-Version" = "2024-01-01"
    "X-Token-ID"    = pyvider_timed_token.external_api.id
  }
}

# Example 2: Webhook authentication token
resource "pyvider_timed_token" "webhook_auth" {
  name = "webhook-callback-auth"
}

# Configure webhook with temporary authentication
data "pyvider_http_api" "register_webhook" {
  url    = "https://webhooks.example.com/register"
  method = "POST"
  headers = {
    "Authorization" = "Bearer ${pyvider_timed_token.webhook_auth.token}"
    "Content-Type"  = "application/json"
  }
}

# Create webhook configuration file
resource "pyvider_file_content" "webhook_config" {
  filename = "/tmp/webhook_config.json"
  content = jsonencode({
    webhook = {
      endpoint = "https://our-service.example.com/webhook"
      authentication = {
        type = "bearer_token"
        token_id = pyvider_timed_token.webhook_auth.id
        token_name = pyvider_timed_token.webhook_auth.name
        expires_at = pyvider_timed_token.webhook_auth.expires_at
      }
      events = ["user.created", "user.updated", "user.deleted"]
      retry_policy = {
        max_attempts = 3
        backoff_seconds = [1, 5, 15]
      }
    }
    security = {
      verify_signature = true
      allowed_ips = ["192.168.1.0/24", "10.0.0.0/8"]
      rate_limit = {
        requests_per_minute = 100
        burst_limit = 10
      }
    }
  })
}

# Example 3: Database API token
resource "pyvider_timed_token" "database_api" {
  name = "database-service-token"
}

# Create database connection configuration
resource "pyvider_file_content" "database_api_config" {
  filename = "/tmp/database_api_config.json"
  content = jsonencode({
    database_api = {
      connection = {
        base_url = "https://db-api.example.com/v2"
        authentication = {
          method = "api_token"
          token_id = pyvider_timed_token.database_api.id
          token_name = pyvider_timed_token.database_api.name
          expires_at = pyvider_timed_token.database_api.expires_at
        }
        timeout_seconds = 30
        retry_attempts = 3
      }
      endpoints = {
        query = "/query"
        batch = "/batch"
        schema = "/schema"
        health = "/health"
      }
      permissions = {
        read = true
        write = false
        admin = false
      }
    }
    connection_pool = {
      max_connections = 10
      idle_timeout_seconds = 300
      connection_lifetime_hours = 1
    }
  })
}

# Example 4: Multi-service API orchestration
resource "pyvider_timed_token" "service_orchestrator" {
  name = "service-orchestration-token"
}

resource "pyvider_timed_token" "payment_service" {
  name = "payment-service-token"
}

resource "pyvider_timed_token" "notification_service" {
  name = "notification-service-token"
}

# Create service orchestration configuration
resource "pyvider_file_content" "service_orchestration" {
  filename = "/tmp/service_orchestration.json"
  content = jsonencode({
    orchestration = {
      coordinator = {
        token_id = pyvider_timed_token.service_orchestrator.id
        token_name = pyvider_timed_token.service_orchestrator.name
        expires_at = pyvider_timed_token.service_orchestrator.expires_at
      }

      services = {
        payment = {
          base_url = "https://payments.example.com/api/v1"
          token_id = pyvider_timed_token.payment_service.id
          token_name = pyvider_timed_token.payment_service.name
          expires_at = pyvider_timed_token.payment_service.expires_at
          timeout_seconds = 15
          retry_policy = "exponential_backoff"
        }

        notifications = {
          base_url = "https://notify.example.com/api/v1"
          token_id = pyvider_timed_token.notification_service.id
          token_name = pyvider_timed_token.notification_service.name
          expires_at = pyvider_timed_token.notification_service.expires_at
          timeout_seconds = 10
          retry_policy = "immediate_retry"
        }
      }

      workflows = {
        user_registration = {
          steps = [
            {
              service = "payment"
              endpoint = "/customers"
              method = "POST"
              timeout = 15
            },
            {
              service = "notifications"
              endpoint = "/welcome"
              method = "POST"
              timeout = 5
            }
          ]
          rollback_enabled = true
          max_duration_seconds = 60
        }
      }
    }

    monitoring = {
      health_checks = {
        enabled = true
        interval_seconds = 30
        failure_threshold = 3
      }
      token_expiration = {
        warn_before_minutes = 10
        auto_refresh = false
      }
    }
  })
}

# Example 5: GraphQL API integration
resource "pyvider_timed_token" "graphql_api" {
  name = "graphql-service-token"
}

# Create GraphQL client configuration
resource "pyvider_file_content" "graphql_config" {
  filename = "/tmp/graphql_config.json"
  content = jsonencode({
    graphql_client = {
      endpoint = "https://graphql.example.com/api"
      authentication = {
        type = "bearer_token"
        token_id = pyvider_timed_token.graphql_api.id
        token_name = pyvider_timed_token.graphql_api.name
        expires_at = pyvider_timed_token.graphql_api.expires_at
        header_name = "Authorization"
        header_format = "Bearer {token}"
      }

      introspection = {
        enabled = true
        cache_schema = true
        schema_ttl_minutes = 30
      }

      queries = {
        user_profile = {
          query = "query GetUser($id: ID!) { user(id: $id) { id name email profile { avatar bio } } }"
          variables = {
            id = "$USER_ID"
          }
        }
        user_posts = {
          query = "query GetUserPosts($userId: ID!, $limit: Int) { posts(userId: $userId, limit: $limit) { id title content createdAt } }"
          variables = {
            userId = "$USER_ID"
            limit = 10
          }
        }
      }

      mutations = {
        create_post = {
          mutation = "mutation CreatePost($input: PostInput!) { createPost(input: $input) { id title content author { name } } }"
          variables = {
            input = "$POST_INPUT"
          }
        }
      }

      subscriptions = {
        post_updates = {
          subscription = "subscription PostUpdates($userId: ID!) { postUpdated(userId: $userId) { id title content updatedAt } }"
          variables = {
            userId = "$USER_ID"
          }
        }
      }
    }

    client_options = {
      timeout_seconds = 30
      retry_attempts = 3
      batch_requests = true
      persistent_queries = false
    }
  })
}

# Example 6: Token rotation strategy for long-running integrations
resource "pyvider_timed_token" "primary_integration" {
  name = "primary-api-integration"
}

resource "pyvider_timed_token" "backup_integration" {
  name = "backup-api-integration"
}

# Create token rotation configuration
resource "pyvider_file_content" "token_rotation_strategy" {
  filename = "/tmp/token_rotation_strategy.json"
  content = jsonencode({
    token_rotation = {
      strategy = "blue_green"

      primary_token = {
        token_id = pyvider_timed_token.primary_integration.id
        token_name = pyvider_timed_token.primary_integration.name
        expires_at = pyvider_timed_token.primary_integration.expires_at
        status = "active"
        priority = 1
      }

      backup_token = {
        token_id = pyvider_timed_token.backup_integration.id
        token_name = pyvider_timed_token.backup_integration.name
        expires_at = pyvider_timed_token.backup_integration.expires_at
        status = "standby"
        priority = 2
      }

      rotation_policy = {
        trigger_before_expiry_minutes = 15
        overlap_period_minutes = 5
        validation_checks = [
          "token_format",
          "api_connectivity",
          "permission_validation"
        ]
        fallback_enabled = true
        notification_channels = ["email", "slack", "webhook"]
      }

      monitoring = {
        health_endpoint = "/health/tokens"
        check_interval_seconds = 60
        alert_on_failure = true
        metrics = {
          token_usage_rate = true
          api_response_times = true
          error_rates = true
          expiration_warnings = true
        }
      }
    }

    failover = {
      automatic = true
      max_retry_attempts = 3
      circuit_breaker = {
        failure_threshold = 5
        reset_timeout_seconds = 300
      }
    }
  })
}

# Create comprehensive API integration summary
resource "pyvider_file_content" "api_integration_summary" {
  filename = "/tmp/api_integration_summary.txt"
  content = join("\n", [
    "=== API Integration Token Summary ===",
    "",
    "External API Integration:",
    "  Token: ${pyvider_timed_token.external_api.name}",
    "  ID: ${pyvider_timed_token.external_api.id}",
    "  Expires: ${pyvider_timed_token.external_api.expires_at}",
    "  API Status: ${data.pyvider_http_api.authenticated_request.status_code}",
    "",
    "Webhook Authentication:",
    "  Token: ${pyvider_timed_token.webhook_auth.name}",
    "  ID: ${pyvider_timed_token.webhook_auth.id}",
    "  Expires: ${pyvider_timed_token.webhook_auth.expires_at}",
    "  Registration Status: ${data.pyvider_http_api.register_webhook.status_code}",
    "",
    "Database API Integration:",
    "  Token: ${pyvider_timed_token.database_api.name}",
    "  ID: ${pyvider_timed_token.database_api.id}",
    "  Expires: ${pyvider_timed_token.database_api.expires_at}",
    "",
    "Service Orchestration:",
    "  Coordinator: ${pyvider_timed_token.service_orchestrator.name}",
    "  Payment Service: ${pyvider_timed_token.payment_service.name}",
    "  Notification Service: ${pyvider_timed_token.notification_service.name}",
    "",
    "GraphQL Integration:",
    "  Token: ${pyvider_timed_token.graphql_api.name}",
    "  ID: ${pyvider_timed_token.graphql_api.id}",
    "  Expires: ${pyvider_timed_token.graphql_api.expires_at}",
    "",
    "Token Rotation Strategy:",
    "  Primary: ${pyvider_timed_token.primary_integration.name}",
    "  Backup: ${pyvider_timed_token.backup_integration.name}",
    "",
    "Security Features:",
    "  ✅ Time-limited tokens (1 hour expiration)",
    "  ✅ Sensitive data protection",
    "  ✅ Automatic token rotation support",
    "  ✅ Multi-service orchestration",
    "  ✅ Fallback and redundancy",
    "",
    "Integration Patterns Demonstrated:",
    "  - REST API authentication",
    "  - Webhook registration and callbacks",
    "  - Database service integration",
    "  - Multi-service orchestration",
    "  - GraphQL API integration",
    "  - Token rotation strategies",
    "",
    "Generated at: ${timestamp()}"
  ])
}

output "api_integration_results" {
  description = "API integration token configurations and results"
  value = {
    integrations = {
      external_api = {
        token_name = pyvider_timed_token.external_api.name
        token_id = pyvider_timed_token.external_api.id
        expires_at = pyvider_timed_token.external_api.expires_at
        api_status = data.pyvider_http_api.authenticated_request.status_code
        api_success = data.pyvider_http_api.authenticated_request.status_code >= 200 && data.pyvider_http_api.authenticated_request.status_code < 300
      }

      webhook = {
        token_name = pyvider_timed_token.webhook_auth.name
        token_id = pyvider_timed_token.webhook_auth.id
        expires_at = pyvider_timed_token.webhook_auth.expires_at
        registration_status = data.pyvider_http_api.register_webhook.status_code
        registration_success = data.pyvider_http_api.register_webhook.status_code >= 200 && data.pyvider_http_api.register_webhook.status_code < 300
      }

      database_api = {
        token_name = pyvider_timed_token.database_api.name
        token_id = pyvider_timed_token.database_api.id
        expires_at = pyvider_timed_token.database_api.expires_at
      }

      graphql = {
        token_name = pyvider_timed_token.graphql_api.name
        token_id = pyvider_timed_token.graphql_api.id
        expires_at = pyvider_timed_token.graphql_api.expires_at
      }
    }

    service_orchestration = {
      coordinator = pyvider_timed_token.service_orchestrator.name
      payment_service = pyvider_timed_token.payment_service.name
      notification_service = pyvider_timed_token.notification_service.name
      all_services_configured = true
    }

    token_rotation = {
      primary_token = pyvider_timed_token.primary_integration.name
      backup_token = pyvider_timed_token.backup_integration.name
      strategy = "blue_green"
      redundancy_enabled = true
    }

    summary = {
      total_tokens = 8
      integration_types = ["REST API", "Webhook", "Database API", "GraphQL", "Service Orchestration"]
      security_features = ["Time-limited", "Sensitive data protection", "Token rotation", "Failover support"]
    }

    configuration_files = [
      pyvider_file_content.webhook_config.filename,
      pyvider_file_content.database_api_config.filename,
      pyvider_file_content.service_orchestration.filename,
      pyvider_file_content.graphql_config.filename,
      pyvider_file_content.token_rotation_strategy.filename,
      pyvider_file_content.api_integration_summary.filename
    ]
  }
}
```

### Multi-Environment Tokens

```terraform
# Multi-environment token management examples

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "development"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "application_name" {
  description = "Name of the application"
  type        = string
  default     = "example-app"
}

# Environment-specific token configuration
locals {
  env_config = {
    development = {
      token_prefix = "dev"
      monitoring_level = "basic"
      rotation_required = false
      alert_channels = ["email"]
      backup_tokens = 1
    }
    staging = {
      token_prefix = "staging"
      monitoring_level = "enhanced"
      rotation_required = true
      alert_channels = ["email", "slack"]
      backup_tokens = 2
    }
    production = {
      token_prefix = "prod"
      monitoring_level = "comprehensive"
      rotation_required = true
      alert_channels = ["email", "slack", "pagerduty"]
      backup_tokens = 3
    }
  }

  current_config = local.env_config[var.environment]
}

# Example 1: Environment-specific application tokens
resource "pyvider_timed_token" "app_primary" {
  name = "${local.current_config.token_prefix}-${var.application_name}-primary"
}

resource "pyvider_timed_token" "app_backup" {
  count = local.current_config.backup_tokens
  name  = "${local.current_config.token_prefix}-${var.application_name}-backup-${count.index + 1}"
}

# Example 2: Database tokens per environment
resource "pyvider_timed_token" "database_read" {
  name = "${local.current_config.token_prefix}-database-readonly"
}

resource "pyvider_timed_token" "database_write" {
  count = var.environment == "production" ? 1 : 0
  name  = "${local.current_config.token_prefix}-database-readwrite"
}

# Example 3: API gateway tokens
resource "pyvider_timed_token" "api_gateway" {
  name = "${local.current_config.token_prefix}-api-gateway"
}

resource "pyvider_timed_token" "api_internal" {
  name = "${local.current_config.token_prefix}-internal-services"
}

# Example 4: Monitoring and observability tokens
resource "pyvider_timed_token" "metrics_collector" {
  name = "${local.current_config.token_prefix}-metrics-collector"
}

resource "pyvider_timed_token" "log_aggregator" {
  name = "${local.current_config.token_prefix}-log-aggregator"
}

resource "pyvider_timed_token" "trace_collector" {
  count = var.environment != "development" ? 1 : 0
  name  = "${local.current_config.token_prefix}-trace-collector"
}

# Create environment-specific token registry
resource "pyvider_file_content" "token_registry" {
  filename = "/tmp/${var.environment}_token_registry.json"
  content = jsonencode({
    environment = var.environment
    application = var.application_name
    timestamp = timestamp()

    configuration = local.current_config

    tokens = {
      application = {
        primary = {
          name = pyvider_timed_token.app_primary.name
          id = pyvider_timed_token.app_primary.id
          expires_at = pyvider_timed_token.app_primary.expires_at
          type = "primary"
        }
        backups = [
          for i, token in pyvider_timed_token.app_backup : {
            name = token.name
            id = token.id
            expires_at = token.expires_at
            type = "backup"
            sequence = i + 1
          }
        ]
      }

      database = {
        readonly = {
          name = pyvider_timed_token.database_read.name
          id = pyvider_timed_token.database_read.id
          expires_at = pyvider_timed_token.database_read.expires_at
          permissions = ["read", "list"]
        }
        readwrite = var.environment == "production" ? {
          name = pyvider_timed_token.database_write[0].name
          id = pyvider_timed_token.database_write[0].id
          expires_at = pyvider_timed_token.database_write[0].expires_at
          permissions = ["read", "write", "list", "delete"]
        } : null
      }

      api_services = {
        gateway = {
          name = pyvider_timed_token.api_gateway.name
          id = pyvider_timed_token.api_gateway.id
          expires_at = pyvider_timed_token.api_gateway.expires_at
          scope = "external"
        }
        internal = {
          name = pyvider_timed_token.api_internal.name
          id = pyvider_timed_token.api_internal.id
          expires_at = pyvider_timed_token.api_internal.expires_at
          scope = "internal"
        }
      }

      observability = {
        metrics = {
          name = pyvider_timed_token.metrics_collector.name
          id = pyvider_timed_token.metrics_collector.id
          expires_at = pyvider_timed_token.metrics_collector.expires_at
          service = "prometheus"
        }
        logs = {
          name = pyvider_timed_token.log_aggregator.name
          id = pyvider_timed_token.log_aggregator.id
          expires_at = pyvider_timed_token.log_aggregator.expires_at
          service = "elasticsearch"
        }
        traces = var.environment != "development" ? {
          name = pyvider_timed_token.trace_collector[0].name
          id = pyvider_timed_token.trace_collector[0].id
          expires_at = pyvider_timed_token.trace_collector[0].expires_at
          service = "jaeger"
        } : null
      }
    }

    security_policy = {
      rotation_required = local.current_config.rotation_required
      monitoring_level = local.current_config.monitoring_level
      backup_strategy = "multiple_tokens"
      alert_channels = local.current_config.alert_channels
    }

    compliance = {
      environment_isolation = true
      token_segregation = true
      principle_of_least_privilege = true
      automatic_expiration = true
    }
  })
}

# Create environment-specific application configuration
resource "pyvider_file_content" "app_config" {
  filename = "/tmp/${var.environment}_app_config.yaml"
  content = yamlencode({
    application = {
      name = var.application_name
      environment = var.environment

      authentication = {
        primary_token = {
          id = pyvider_timed_token.app_primary.id
          name = pyvider_timed_token.app_primary.name
          expires_at = pyvider_timed_token.app_primary.expires_at
        }

        backup_tokens = [
          for token in pyvider_timed_token.app_backup : {
            id = token.id
            name = token.name
            expires_at = token.expires_at
          }
        ]

        rotation_policy = {
          enabled = local.current_config.rotation_required
          warn_before_minutes = var.environment == "production" ? 10 : 30
          fallback_enabled = length(pyvider_timed_token.app_backup) > 0
        }
      }

      database = {
        connections = {
          readonly = {
            token_id = pyvider_timed_token.database_read.id
            token_name = pyvider_timed_token.database_read.name
            expires_at = pyvider_timed_token.database_read.expires_at
            max_connections = var.environment == "production" ? 20 : 5
          }
          readwrite = var.environment == "production" ? {
            token_id = pyvider_timed_token.database_write[0].id
            token_name = pyvider_timed_token.database_write[0].name
            expires_at = pyvider_timed_token.database_write[0].expires_at
            max_connections = 10
          } : null
        }
      }

      apis = {
        gateway = {
          token_id = pyvider_timed_token.api_gateway.id
          token_name = pyvider_timed_token.api_gateway.name
          expires_at = pyvider_timed_token.api_gateway.expires_at
          base_url = "https://${var.environment == "production" ? "api" : "${var.environment}-api"}.example.com"
          timeout_seconds = var.environment == "production" ? 10 : 30
        }
        internal = {
          token_id = pyvider_timed_token.api_internal.id
          token_name = pyvider_timed_token.api_internal.name
          expires_at = pyvider_timed_token.api_internal.expires_at
          base_url = "https://internal-${var.environment}.example.com"
          timeout_seconds = 15
        }
      }

      observability = {
        metrics = {
          enabled = true
          token_id = pyvider_timed_token.metrics_collector.id
          token_name = pyvider_timed_token.metrics_collector.name
          expires_at = pyvider_timed_token.metrics_collector.expires_at
          endpoint = "https://metrics-${var.environment}.example.com"
          interval_seconds = var.environment == "production" ? 15 : 60
        }

        logging = {
          enabled = true
          token_id = pyvider_timed_token.log_aggregator.id
          token_name = pyvider_timed_token.log_aggregator.name
          expires_at = pyvider_timed_token.log_aggregator.expires_at
          endpoint = "https://logs-${var.environment}.example.com"
          level = var.environment == "production" ? "warn" : (var.environment == "staging" ? "info" : "debug")
        }

        tracing = var.environment != "development" ? {
          enabled = true
          token_id = pyvider_timed_token.trace_collector[0].id
          token_name = pyvider_timed_token.trace_collector[0].name
          expires_at = pyvider_timed_token.trace_collector[0].expires_at
          endpoint = "https://traces-${var.environment}.example.com"
          sampling_rate = var.environment == "production" ? 0.1 : 1.0
        } : {
          enabled = false
        }
      }
    }

    environment_metadata = {
      deployment_tier = var.environment
      monitoring_level = local.current_config.monitoring_level
      compliance_required = var.environment == "production"
      backup_tokens_count = local.current_config.backup_tokens
    }
  })
}

# Create monitoring configuration
resource "pyvider_file_content" "monitoring_config" {
  filename = "/tmp/${var.environment}_monitoring.json"
  content = jsonencode({
    monitoring = {
      environment = var.environment
      application = var.application_name
      level = local.current_config.monitoring_level

      token_monitoring = {
        primary_application = {
          token_id = pyvider_timed_token.app_primary.id
          token_name = pyvider_timed_token.app_primary.name
          expires_at = pyvider_timed_token.app_primary.expires_at
          criticality = "high"
          alert_thresholds = {
            expiry_warning_minutes = var.environment == "production" ? 10 : 30
            usage_anomaly_threshold = 2.0
          }
        }

        backup_tokens = [
          for i, token in pyvider_timed_token.app_backup : {
            token_id = token.id
            token_name = token.name
            expires_at = token.expires_at
            criticality = "medium"
            sequence = i + 1
          }
        ]

        infrastructure_tokens = [
          {
            service = "database_readonly"
            token_id = pyvider_timed_token.database_read.id
            token_name = pyvider_timed_token.database_read.name
            expires_at = pyvider_timed_token.database_read.expires_at
            criticality = "high"
          },
          {
            service = "api_gateway"
            token_id = pyvider_timed_token.api_gateway.id
            token_name = pyvider_timed_token.api_gateway.name
            expires_at = pyvider_timed_token.api_gateway.expires_at
            criticality = "high"
          },
          {
            service = "internal_apis"
            token_id = pyvider_timed_token.api_internal.id
            token_name = pyvider_timed_token.api_internal.name
            expires_at = pyvider_timed_token.api_internal.expires_at
            criticality = "medium"
          }
        ]

        observability_tokens = [
          {
            service = "metrics_collection"
            token_id = pyvider_timed_token.metrics_collector.id
            token_name = pyvider_timed_token.metrics_collector.name
            expires_at = pyvider_timed_token.metrics_collector.expires_at
            criticality = "medium"
          },
          {
            service = "log_aggregation"
            token_id = pyvider_timed_token.log_aggregator.id
            token_name = pyvider_timed_token.log_aggregator.name
            expires_at = pyvider_timed_token.log_aggregator.expires_at
            criticality = "medium"
          }
        ]
      }

      alert_configuration = {
        channels = local.current_config.alert_channels
        escalation_policy = {
          immediate = var.environment == "production"
          business_hours_only = var.environment == "development"
          weekend_alerts = var.environment != "development"
        }
        notification_templates = {
          token_expiry = "Token ${var.token_name} (${var.token_id}) expires at ${var.expires_at}"
          token_rotation = "Token rotation required for ${var.environment} environment"
          token_failure = "Token authentication failed for service ${var.service_name}"
        }
      }

      health_checks = {
        enabled = true
        interval_seconds = var.environment == "production" ? 30 : 300
        timeout_seconds = 10
        failure_threshold = var.environment == "production" ? 2 : 5

        endpoints = [
          {
            name = "token_validation"
            url = "https://auth-${var.environment}.example.com/validate"
            method = "POST"
            expected_status = 200
          },
          {
            name = "api_gateway_health"
            url = "https://${var.environment == "production" ? "api" : "${var.environment}-api"}.example.com/health"
            method = "GET"
            expected_status = 200
          }
        ]
      }
    }

    compliance = {
      audit_logging = var.environment == "production"
      token_lifecycle_tracking = true
      access_review_required = var.environment == "production"
      encryption_at_rest = true
      encryption_in_transit = true
    }
  })
}

# Create deployment summary
resource "pyvider_file_content" "deployment_summary" {
  filename = "/tmp/${var.environment}_deployment_summary.txt"
  content = join("\n", [
    "=== ${title(var.environment)} Environment Token Deployment ===",
    "",
    "Application: ${var.application_name}",
    "Environment: ${var.environment}",
    "Configuration Level: ${local.current_config.monitoring_level}",
    "Generated: ${timestamp()}",
    "",
    "=== Application Tokens ===",
    "Primary Token:",
    "  Name: ${pyvider_timed_token.app_primary.name}",
    "  ID: ${pyvider_timed_token.app_primary.id}",
    "  Expires: ${pyvider_timed_token.app_primary.expires_at}",
    "",
    "Backup Tokens (${length(pyvider_timed_token.app_backup)}):",
    join("\n", [
      for i, token in pyvider_timed_token.app_backup :
      "  ${i + 1}. ${token.name} (${token.id}) - Expires: ${token.expires_at}"
    ]),
    "",
    "=== Infrastructure Tokens ===",
    "Database Access:",
    "  Read-Only: ${pyvider_timed_token.database_read.name} (${pyvider_timed_token.database_read.id})",
    var.environment == "production" ? "  Read-Write: ${pyvider_timed_token.database_write[0].name} (${pyvider_timed_token.database_write[0].id})" : "  Read-Write: Not configured for ${var.environment}",
    "",
    "API Services:",
    "  Gateway: ${pyvider_timed_token.api_gateway.name} (${pyvider_timed_token.api_gateway.id})",
    "  Internal: ${pyvider_timed_token.api_internal.name} (${pyvider_timed_token.api_internal.id})",
    "",
    "=== Observability Tokens ===",
    "Metrics: ${pyvider_timed_token.metrics_collector.name} (${pyvider_timed_token.metrics_collector.id})",
    "Logs: ${pyvider_timed_token.log_aggregator.name} (${pyvider_timed_token.log_aggregator.id})",
    var.environment != "development" ? "Traces: ${pyvider_timed_token.trace_collector[0].name} (${pyvider_timed_token.trace_collector[0].id})" : "Traces: Disabled for development",
    "",
    "=== Security Configuration ===",
    "Token Rotation Required: ${local.current_config.rotation_required ? "Yes" : "No"}",
    "Monitoring Level: ${title(local.current_config.monitoring_level)}",
    "Alert Channels: ${join(", ", local.current_config.alert_channels)}",
    "Backup Tokens: ${local.current_config.backup_tokens}",
    "",
    "=== Compliance Features ===",
    "✅ Environment Isolation",
    "✅ Automatic Token Expiration",
    "✅ Sensitive Data Protection",
    "✅ Token Lifecycle Management",
    var.environment == "production" ? "✅ Production Security Controls" : "ℹ️  Development Environment (Relaxed Controls)",
    "",
    "⚠️  All tokens are time-limited and will expire in 1 hour.",
    "⚠️  Monitor expiration times and plan for rotation.",
    var.environment == "production" ? "⚠️  Production environment requires immediate attention for token issues." : "",
    "",
    "Configuration files generated:",
    "- ${pyvider_file_content.token_registry.filename}",
    "- ${pyvider_file_content.app_config.filename}",
    "- ${pyvider_file_content.monitoring_config.filename}",
    "- ${pyvider_file_content.deployment_summary.filename}"
  ])
}

output "multi_environment_deployment" {
  description = "Multi-environment token deployment summary"
  value = {
    environment = var.environment
    application = var.application_name
    configuration = local.current_config

    tokens = {
      application = {
        primary = {
          name = pyvider_timed_token.app_primary.name
          id = pyvider_timed_token.app_primary.id
          expires_at = pyvider_timed_token.app_primary.expires_at
        }
        backup_count = length(pyvider_timed_token.app_backup)
      }

      infrastructure = {
        database_readonly = {
          name = pyvider_timed_token.database_read.name
          id = pyvider_timed_token.database_read.id
        }
        database_readwrite_enabled = var.environment == "production"
        api_gateway = {
          name = pyvider_timed_token.api_gateway.name
          id = pyvider_timed_token.api_gateway.id
        }
        internal_apis = {
          name = pyvider_timed_token.api_internal.name
          id = pyvider_timed_token.api_internal.id
        }
      }

      observability = {
        metrics_enabled = true
        logging_enabled = true
        tracing_enabled = var.environment != "development"
      }
    }

    security = {
      rotation_required = local.current_config.rotation_required
      monitoring_level = local.current_config.monitoring_level
      backup_strategy = local.current_config.backup_tokens > 0
      alert_channels = local.current_config.alert_channels
    }

    files_generated = [
      pyvider_file_content.token_registry.filename,
      pyvider_file_content.app_config.filename,
      pyvider_file_content.monitoring_config.filename,
      pyvider_file_content.deployment_summary.filename
    ]

    total_tokens = (
      1 + # primary
      length(pyvider_timed_token.app_backup) + # backups
      1 + # database read
      (var.environment == "production" ? 1 : 0) + # database write
      2 + # api tokens
      2 + # observability (metrics + logs)
      (var.environment != "development" ? 1 : 0) # tracing
    )
  }
}
```

## Schema



## Token Lifecycle

The `pyvider_timed_token` resource manages the complete lifecycle of time-limited tokens:

### 1. Creation
- Generates a unique token ID with UUID format
- Creates a secure token string with `token-{uuid}` format
- Sets expiration time to 1 hour from creation
- Stores sensitive data in encrypted private state

### 2. Reading
- Returns current token and expiration information
- Automatically decrypts private state for access
- Maintains token validity status

### 3. Expiration
- Tokens expire automatically after the specified duration
- No cleanup required - tokens are self-invalidating
- Expiration time is stored in ISO 8601 format

### 4. Deletion
- Removes token from Terraform state
- No additional cleanup required on the provider side

## Security Features

### Sensitive Data Protection
```terraform
resource "pyvider_timed_token" "secure_token" {
  name = "production-api-key"
}

# ✅ Safe - token is marked as sensitive
output "token_available" {
  value = pyvider_timed_token.secure_token.token != null
}

# ❌ Unsafe - would expose sensitive token
# output "actual_token" {
#   value = pyvider_timed_token.secure_token.token
# }
```

### Private State Encryption
The resource uses Terraform's private state encryption to securely store:
- The actual token value
- Expiration timestamp
- Internal token metadata

### Token Format
Tokens follow a predictable but secure format:
- **ID**: `timed-token-id-{uuid}`
- **Token**: `token-{uuid}`
- **Expiration**: ISO 8601 timestamp (UTC)

## Common Patterns

### Token Rotation Strategy
```terraform
# Create multiple tokens for rotation
resource "pyvider_timed_token" "primary" {
  name = "primary-token"
}

resource "pyvider_timed_token" "backup" {
  name = "backup-token"
}

# Application config with fallback
resource "pyvider_file_content" "app_config" {
  filename = "/app/config/tokens.json"
  content = jsonencode({
    primary_token = {
      value = pyvider_timed_token.primary.token
      expires_at = pyvider_timed_token.primary.expires_at
    }
    backup_token = {
      value = pyvider_timed_token.backup.token
      expires_at = pyvider_timed_token.backup.expires_at
    }
  })
}
```

### Environment-Specific Tokens
```terraform
variable "environment" {
  description = "Deployment environment"
  type        = string
}

resource "pyvider_timed_token" "env_token" {
  name = "${var.environment}-api-token"
}

# Different expiration handling per environment
locals {
  token_config = {
    production = {
      require_rotation = true
      max_age_hours = 1
    }
    staging = {
      require_rotation = false
      max_age_hours = 24
    }
    development = {
      require_rotation = false
      max_age_hours = 168  # 1 week
    }
  }
}
```

### Integration with External Systems
```terraform
resource "pyvider_timed_token" "webhook_token" {
  name = "webhook-authentication"
}

# Configure webhook with temporary token
data "pyvider_http_api" "register_webhook" {
  url    = "https://api.example.com/webhooks"
  method = "POST"
  headers = {
    "Authorization" = "Bearer ${pyvider_timed_token.webhook_token.token}"
    "Content-Type"  = "application/json"
  }
}
```

### Token Monitoring and Alerts
```terraform
resource "pyvider_timed_token" "monitored_token" {
  name = "critical-service-token"
}

# Create monitoring configuration
resource "pyvider_file_content" "token_monitor" {
  filename = "/monitoring/token_status.json"
  content = jsonencode({
    token_id = pyvider_timed_token.monitored_token.id
    name = pyvider_timed_token.monitored_token.name
    expires_at = pyvider_timed_token.monitored_token.expires_at
    monitoring = {
      alert_before_expiry_minutes = 15
      auto_rotate = true
      notification_webhook = "https://alerts.example.com/webhook"
    }
  })
}
```

## Error Handling

### Token Access Validation
```terraform
resource "pyvider_timed_token" "api_token" {
  name = "service-integration"
}

# Validate token is available before use
locals {
  token_valid = (
    pyvider_timed_token.api_token.token != null &&
    pyvider_timed_token.api_token.expires_at != null
  )
}

# Conditional resource creation
resource "pyvider_file_content" "api_config" {
  count = local.token_valid ? 1 : 0

  filename = "/config/api_credentials.json"
  content = jsonencode({
    token = pyvider_timed_token.api_token.token
    expires_at = pyvider_timed_token.api_token.expires_at
    last_updated = timestamp()
  })
}
```

### Expiration Handling
```terraform
resource "pyvider_timed_token" "time_sensitive" {
  name = "batch-job-token"
}

# Create expiration warning file
resource "pyvider_file_content" "expiration_notice" {
  filename = "/tmp/token_expiration_notice.txt"
  content = join("\n", [
    "Token Expiration Notice",
    "=====================",
    "Token Name: ${pyvider_timed_token.time_sensitive.name}",
    "Token ID: ${pyvider_timed_token.time_sensitive.id}",
    "Expires At: ${pyvider_timed_token.time_sensitive.expires_at}",
    "",
    "⚠️  This token will expire automatically.",
    "⚠️  Plan for token rotation before expiration.",
    "⚠️  Monitor application logs for authentication failures.",
    "",
    "Generated: ${timestamp()}"
  ])
}
```

## Best Practices

### 1. Descriptive Naming
```terraform
# ✅ Good - descriptive names
resource "pyvider_timed_token" "github_actions_deploy" {
  name = "github-actions-deployment-token"
}

resource "pyvider_timed_token" "api_gateway_auth" {
  name = "api-gateway-service-auth"
}

# ❌ Bad - generic names
resource "pyvider_timed_token" "token1" {
  name = "token"
}
```

### 2. Token Scope Documentation
```terraform
resource "pyvider_timed_token" "database_migration" {
  name = "db-migration-readonly-token"

  # Document token purpose in configuration
  lifecycle {
    # This token is used for database migration scripts
    # Scope: Read-only access to production database
    # Duration: 1 hour (automatic expiration)
    # Rotation: Manual, as needed for migrations
    ignore_changes = []
  }
}
```

### 3. Environment Isolation
```terraform
variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

resource "pyvider_timed_token" "env_isolated" {
  name = "${var.environment}-service-token"
}

# Environment-specific handling
locals {
  is_production = var.environment == "prod"

  # Production tokens require additional monitoring
  monitoring_required = local.is_production
}
```

### 4. Token Rotation Planning
```terraform
# Create tokens with rotation metadata
resource "pyvider_timed_token" "rotatable" {
  name = "service-api-token-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
}

# Track token generations
resource "pyvider_file_content" "token_registry" {
  filename = "/registry/token_generations.json"
  content = jsonencode({
    current_generation = {
      token_id = pyvider_timed_token.rotatable.id
      created_at = timestamp()
      expires_at = pyvider_timed_token.rotatable.expires_at
    }
    rotation_policy = {
      automatic = false
      advance_notice_minutes = 30
      fallback_strategy = "maintain_previous_token"
    }
  })
}
```

## Troubleshooting

### Common Issues

**Issue**: Token appears to be null or empty
**Solution**: Check that the resource has been created successfully
```terraform
# Debug token creation
output "token_debug" {
  value = {
    token_exists = pyvider_timed_token.debug.token != null
    id_exists = pyvider_timed_token.debug.id != null
    name = pyvider_timed_token.debug.name
  }
}
```

**Issue**: Cannot access token value in outputs
**Solution**: Token is marked as sensitive; use conditional checks instead
```terraform
# ✅ Correct way to check token
output "token_status" {
  value = {
    available = pyvider_timed_token.example.token != null
    has_expiration = pyvider_timed_token.example.expires_at != null
  }
}
```

**Issue**: Token expiration time format confusion
**Solution**: Expiration is in ISO 8601 format (UTC)
```terraform
# Parse expiration time
locals {
  expires_timestamp = pyvider_timed_token.example.expires_at
  # Format: "2024-01-15T14:30:00.000000+00:00"
}
```

## Related Components

- [`pyvider_private_state_verifier`](../private_state_verifier.md) - Verify private state encryption
- [`pyvider_file_content`](../file_content.md) - Store token configuration files
- [`pyvider_http_api`](../../data_sources/http_api.md) - Use tokens for API authentication
- [`pyvider_env_variables`](../../data_sources/env_variables.md) - Read token configuration from environment