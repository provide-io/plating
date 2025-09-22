---
page_title: "Resource: pyvider_file_content"
description: |-
  Manages the content of a file on the local filesystem
---

# pyvider_file_content (Resource)

> Manages file content with atomic writes and content tracking

The `pyvider_file_content` resource allows you to create, read, update, and delete files on the local filesystem. It automatically tracks content changes using SHA256 hashing and provides atomic write operations to ensure file integrity.

## When to Use This

- **Configuration files**: Create and manage application config files
- **Template rendering**: Generate files from dynamic content
- **Atomic file operations**: Ensure file writes are safe and complete
- **Content tracking**: Monitor file changes with automatic hash calculation

**Anti-patterns (when NOT to use):**
- Large binary files (use file operations instead)
- Temporary files that don't need state tracking
- Files requiring special permissions (use `local_directory` for permission management)

## Quick Start

```terraform
# Create a simple configuration file
resource "pyvider_file_content" "app_config" {
  filename = "/tmp/app.conf"
  content  = "DATABASE_URL=localhost:5432"
}

# Access the computed attributes
output "config_exists" {
  value = pyvider_file_content.app_config.exists
}

output "config_hash" {
  value = pyvider_file_content.app_config.content_hash
}
```

## Examples

### Basic Usage

```terraform
# Basic file creation and management
resource "pyvider_file_content" "readme" {
  filename = "/tmp/pyvider_readme.txt"
  content  = "Welcome to Pyvider Components!\n\nThis file was created by Terraform."
}

# Show the computed attributes
output "file_details" {
  description = "Details about the created file"
  value = {
    filename     = pyvider_file_content.readme.filename
    exists       = pyvider_file_content.readme.exists
    content_hash = pyvider_file_content.readme.content_hash
    content_size = length(pyvider_file_content.readme.content)
  }
}

# Create a simple JSON configuration file
resource "pyvider_file_content" "json_config" {
  filename = "/tmp/app_config.json"
  content = jsonencode({
    app_name = "my-terraform-app"
    version  = "1.0.0"
    debug    = false
    database = {
      host = "localhost"
      port = 5432
    }
  })
}

output "json_config_hash" {
  description = "Hash of the JSON configuration file"
  value       = pyvider_file_content.json_config.content_hash
}
```

### Template-Based Configuration

```terraform
# Template-based configuration with dynamic content

# Read environment variables for the template
data "pyvider_env_variables" "app_vars" {
  keys = ["USER", "HOME", "HOSTNAME"]
}

# Create a configuration file using template functions
resource "pyvider_file_content" "app_properties" {
  filename = "/tmp/application.properties"
  content = join("\n", [
    "# Application Configuration",
    "# Generated on ${timestamp()}",
    "",
    "app.user=${lookup(data.pyvider_env_variables.app_vars.values, "USER", "unknown")}",
    "app.home=${lookup(data.pyvider_env_variables.app_vars.values, "HOME", "/tmp")}",
    "app.hostname=${lookup(data.pyvider_env_variables.app_vars.values, "HOSTNAME", "localhost")}",
    "",
    "# Database Configuration",
    "database.url=jdbc:postgresql://localhost:5432/myapp",
    "database.username=app_user",
    "database.pool.size=10",
    "",
    "# Feature Flags",
    "features.new_ui=true",
    "features.analytics=false"
  ])
}

# Create a shell script with executable content
resource "pyvider_file_content" "deploy_script" {
  filename = "/tmp/deploy.sh"
  content = templatefile("${path.module}/deploy.sh.tpl", {
    app_name = "my-terraform-app"
    version  = "1.0.0"
    user     = lookup(data.pyvider_env_variables.app_vars.values, "USER", "deploy")
  })
}

# Example template file content (this would be a separate .tpl file)
# #!/bin/bash
# set -e
#
# APP_NAME="${app_name}"
# VERSION="${version}"
# USER="${user}"
#
# echo "Deploying $APP_NAME version $VERSION as user $USER"
# echo "Timestamp: $(date)"
#
# # Add your deployment logic here
# echo "Deployment complete!"

output "template_outputs" {
  description = "Information about template-generated files"
  value = {
    properties_file = {
      path = pyvider_file_content.app_properties.filename
      hash = pyvider_file_content.app_properties.content_hash
    }
    deploy_script = {
      path = pyvider_file_content.deploy_script.filename
      hash = pyvider_file_content.deploy_script.content_hash
    }
  }
}
```

### Multi-Line Content

```terraform
# Multi-line content examples with proper formatting

# Create a YAML configuration file
resource "pyvider_file_content" "kubernetes_config" {
  filename = "/tmp/k8s-deployment.yaml"
  content = <<-EOF
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
      labels:
        app: my-app
        version: "1.0"
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: my-app
      template:
        metadata:
          labels:
            app: my-app
        spec:
          containers:
          - name: app
            image: my-app:1.0
            ports:
            - containerPort: 8080
            env:
            - name: DATABASE_URL
              value: "postgresql://db:5432/myapp"
            - name: LOG_LEVEL
              value: "INFO"
  EOF
}

# Create a Docker Compose file
resource "pyvider_file_content" "docker_compose" {
  filename = "/tmp/docker-compose.yml"
  content = <<-EOF
    version: '3.8'

    services:
      web:
        image: nginx:alpine
        ports:
          - "80:80"
        volumes:
          - ./nginx.conf:/etc/nginx/nginx.conf:ro
        depends_on:
          - api

      api:
        build: .
        ports:
          - "8080:8080"
        environment:
          - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
          - REDIS_URL=redis://redis:6379
        depends_on:
          - db
          - redis

      db:
        image: postgres:15-alpine
        environment:
          - POSTGRES_DB=myapp
          - POSTGRES_USER=postgres
          - POSTGRES_PASSWORD=password
        volumes:
          - postgres_data:/var/lib/postgresql/data

      redis:
        image: redis:7-alpine
        command: redis-server --appendonly yes
        volumes:
          - redis_data:/data

    volumes:
      postgres_data:
      redis_data:
  EOF
}

# Create a complex configuration with heredoc syntax
resource "pyvider_file_content" "nginx_config" {
  filename = "/tmp/nginx.conf"
  content = <<-NGINX
    user nginx;
    worker_processes auto;
    error_log /var/log/nginx/error.log warn;
    pid /var/run/nginx.pid;

    events {
        worker_connections 1024;
        use epoll;
        multi_accept on;
    }

    http {
        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        # Logging
        log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                        '$status $body_bytes_sent "$http_referer" '
                        '"$http_user_agent" "$http_x_forwarded_for"';

        access_log /var/log/nginx/access.log main;

        # Performance
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        types_hash_max_size 2048;

        # Compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types
            text/plain
            text/css
            text/xml
            text/javascript
            application/javascript
            application/xml+rss
            application/json;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # Default server
        server {
            listen 80 default_server;
            listen [::]:80 default_server;
            server_name _;

            location / {
                proxy_pass http://api:8080;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }

            location /health {
                access_log off;
                return 200 "healthy\n";
                add_header Content-Type text/plain;
            }
        }
    }
  NGINX
}

output "multiline_files" {
  description = "Information about multi-line configuration files"
  value = {
    kubernetes = {
      path         = pyvider_file_content.kubernetes_config.filename
      content_hash = pyvider_file_content.kubernetes_config.content_hash
      content_size = length(pyvider_file_content.kubernetes_config.content)
    }
    docker_compose = {
      path         = pyvider_file_content.docker_compose.filename
      content_hash = pyvider_file_content.docker_compose.content_hash
      content_size = length(pyvider_file_content.docker_compose.content)
    }
    nginx = {
      path         = pyvider_file_content.nginx_config.filename
      content_hash = pyvider_file_content.nginx_config.content_hash
      content_size = length(pyvider_file_content.nginx_config.content)
    }
  }
}
```

### Environment-Specific Files

```terraform
# Environment-specific configuration management

# Define environment variables
variable "environment" {
  description = "The deployment environment"
  type        = string
  default     = "development"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "app_version" {
  description = "Application version"
  type        = string
  default     = "1.0.0"
}

# Environment-specific database configuration
locals {
  database_configs = {
    development = {
      host     = "localhost"
      port     = 5432
      database = "myapp_dev"
      pool_size = 5
    }
    staging = {
      host     = "staging-db.example.com"
      port     = 5432
      database = "myapp_staging"
      pool_size = 10
    }
    production = {
      host     = "prod-db.example.com"
      port     = 5432
      database = "myapp_prod"
      pool_size = 20
    }
  }

  # Get configuration for current environment
  db_config = local.database_configs[var.environment]

  # Environment-specific feature flags
  feature_flags = {
    development = {
      debug_mode    = true
      verbose_logs  = true
      dev_tools     = true
      metrics       = false
    }
    staging = {
      debug_mode    = false
      verbose_logs  = true
      dev_tools     = false
      metrics       = true
    }
    production = {
      debug_mode    = false
      verbose_logs  = false
      dev_tools     = false
      metrics       = true
    }
  }
}

# Create environment-specific application configuration
resource "pyvider_file_content" "app_config_env" {
  filename = "/tmp/config-${var.environment}.properties"
  content = join("\n", [
    "# Application Configuration for ${upper(var.environment)}",
    "# Generated on ${timestamp()}",
    "",
    "# Application Settings",
    "app.name=my-terraform-app",
    "app.version=${var.app_version}",
    "app.environment=${var.environment}",
    "",
    "# Database Configuration",
    "database.host=${local.db_config.host}",
    "database.port=${local.db_config.port}",
    "database.name=${local.db_config.database}",
    "database.pool.size=${local.db_config.pool_size}",
    "",
    "# Feature Flags",
    "features.debug=${local.feature_flags[var.environment].debug_mode}",
    "features.verbose_logs=${local.feature_flags[var.environment].verbose_logs}",
    "features.dev_tools=${local.feature_flags[var.environment].dev_tools}",
    "features.metrics=${local.feature_flags[var.environment].metrics}",
    "",
    "# Security Settings",
    "security.jwt.expiry=${var.environment == "production" ? "15m" : "24h"}",
    "security.cors.enabled=${var.environment != "production"}",
    "security.ssl.required=${var.environment == "production"}"
  ])
}

# Create environment-specific Docker environment file
resource "pyvider_file_content" "docker_env" {
  filename = "/tmp/.env.${var.environment}"
  content = join("\n", [
    "# Docker Environment Variables for ${upper(var.environment)}",
    "",
    "# Application",
    "APP_ENV=${var.environment}",
    "APP_VERSION=${var.app_version}",
    "APP_DEBUG=${local.feature_flags[var.environment].debug_mode}",
    "",
    "# Database",
    "DATABASE_HOST=${local.db_config.host}",
    "DATABASE_PORT=${local.db_config.port}",
    "DATABASE_NAME=${local.db_config.database}",
    "DATABASE_POOL_SIZE=${local.db_config.pool_size}",
    "",
    "# Logging",
    "LOG_LEVEL=${local.feature_flags[var.environment].verbose_logs ? "DEBUG" : "INFO"}",
    "",
    "# Performance",
    "WORKER_PROCESSES=${var.environment == "production" ? "4" : "2"}",
    "CACHE_TTL=${var.environment == "production" ? "3600" : "60"}",
    "",
    "# Monitoring",
    "METRICS_ENABLED=${local.feature_flags[var.environment].metrics}",
    "HEALTH_CHECK_INTERVAL=${var.environment == "production" ? "30" : "60"}"
  ])
}

# Create a conditional configuration file (only for non-production)
resource "pyvider_file_content" "dev_config" {
  count = var.environment != "production" ? 1 : 0

  filename = "/tmp/development-tools.conf"
  content = <<-EOF
    # Development Tools Configuration
    # This file only exists in non-production environments

    [hot_reload]
    enabled = true
    watch_patterns = ["*.py", "*.js", "*.css"]
    ignore_patterns = ["*.pyc", "node_modules/"]

    [debug_toolbar]
    enabled = true
    profiling = true
    sql_debug = true

    [test_data]
    seed_database = true
    create_test_users = true
    mock_external_apis = true

    [development_server]
    auto_restart = true
    debug_mode = true
    verbose_errors = true
  EOF
}

output "environment_configs" {
  description = "Information about environment-specific configuration files"
  value = {
    environment = var.environment
    app_config = {
      path         = pyvider_file_content.app_config_env.filename
      content_hash = pyvider_file_content.app_config_env.content_hash
    }
    docker_env = {
      path         = pyvider_file_content.docker_env.filename
      content_hash = pyvider_file_content.docker_env.content_hash
    }
    dev_config_created = var.environment != "production"
    dev_config = var.environment != "production" ? {
      path         = pyvider_file_content.dev_config[0].filename
      content_hash = pyvider_file_content.dev_config[0].content_hash
    } : null
  }
}
```

## Schema



## Import

Files can be imported into Terraform state using either the CLI or configuration-based import.

### CLI Import

```bash
terraform import pyvider_file_content.example /path/to/existing/file.txt
```

### Configuration Import (Terraform 1.5+)

```terraform
import {
  to = pyvider_file_content.example
  id = "/path/to/existing/file.txt"
}

resource "pyvider_file_content" "example" {
  filename = "/path/to/existing/file.txt"
  content  = "existing content will be read during import"
}
```

### Import Process

During import, the provider will:
1. Read the current file content from the specified path
2. Calculate the SHA256 hash of the content
3. Set the `exists` attribute to `true`
4. Store the content and hash in Terraform state

**Note**: The `content` attribute in your configuration should match the existing file content, or Terraform will detect a drift and attempt to update the file on the next apply.

## Common Issues & Solutions

### Error: "Permission denied"
**Solution**: Ensure the Terraform process has write permissions to the target directory and file.

```bash
# Check permissions
ls -la /path/to/directory
# Fix permissions if needed
chmod 755 /path/to/directory
chmod 644 /path/to/file
```

### Error: "No such file or directory"
**Solution**: Ensure the parent directory exists before creating the file.

```terraform
# Create parent directory first
resource "pyvider_local_directory" "config_dir" {
  path = "/etc/myapp"
}

resource "pyvider_file_content" "config" {
  filename = "${pyvider_local_directory.config_dir.path}/app.conf"
  content  = "key=value"

  depends_on = [pyvider_local_directory.config_dir]
}
```

### Handling Large Files
For files larger than a few MB, consider alternative approaches:

```terraform
# For large static files, use data source instead
data "pyvider_file_info" "large_file" {
  filename = "/path/to/large/file"
}
```

## Related Components

- [`pyvider_local_directory`](../local_directory.md) - Manage directories and permissions
- [`pyvider_file_info`](../../data-sources/file_info.md) - Read file metadata without managing content
- [`format` function](../../functions/string/format.md) - Generate dynamic content for files
- [`env_variables` data source](../../data-sources/env_variables.md) - Include environment variables in file content