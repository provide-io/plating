---
page_title: "Resource: pyvider_local_directory"
description: |-
  Manages directories on the local filesystem with permissions and metadata tracking
---

# pyvider_local_directory (Resource)

> Creates and manages directories with optional permission control and file counting

The `pyvider_local_directory` resource allows you to create, manage, and monitor directories on the local filesystem. It automatically tracks directory metadata including file counts and provides fine-grained permission control.

## When to Use This

- **Project structure**: Create consistent directory layouts for applications
- **Permission management**: Ensure directories have correct access permissions
- **Workspace initialization**: Set up development or deployment environments
- **Directory monitoring**: Track changes in directory contents

**Anti-patterns (when NOT to use):**
- Temporary directories that don't need state tracking
- Directories where you only need to check existence (use `pyvider_file_info` instead)
- Complex recursive operations (handle those with external tools)

## Quick Start

```terraform
# Create a simple directory
resource "pyvider_local_directory" "app_logs" {
  path = "/tmp/app/logs"
}

# Create a directory with specific permissions
resource "pyvider_local_directory" "secure_config" {
  path        = "/tmp/app/config"
  permissions = "0o750"  # rwxr-x---
}

# Access computed attributes
output "log_dir_info" {
  value = {
    id         = pyvider_local_directory.app_logs.id
    file_count = pyvider_local_directory.app_logs.file_count
  }
}
```

## Examples

### Basic Usage

```terraform
# Basic directory creation and management

# Create a simple directory
resource "pyvider_local_directory" "basic_dir" {
  path = "/tmp/pyvider_basic"
}

# Create a directory with specific permissions
resource "pyvider_local_directory" "secure_dir" {
  path        = "/tmp/pyvider_secure"
  permissions = "0o700"  # Only owner can read/write/execute
}

# Create multiple related directories
resource "pyvider_local_directory" "app_root" {
  path = "/tmp/myapp"
}

resource "pyvider_local_directory" "app_logs" {
  path        = "/tmp/myapp/logs"
  permissions = "0o755"

  depends_on = [pyvider_local_directory.app_root]
}

resource "pyvider_local_directory" "app_data" {
  path        = "/tmp/myapp/data"
  permissions = "0o750"  # More restrictive for data directory

  depends_on = [pyvider_local_directory.app_root]
}

# Add some files to demonstrate file counting
resource "pyvider_file_content" "log_file" {
  filename = "${pyvider_local_directory.app_logs.path}/app.log"
  content  = "Application started at ${timestamp()}"

  depends_on = [pyvider_local_directory.app_logs]
}

resource "pyvider_file_content" "config_file" {
  filename = "${pyvider_local_directory.app_root.path}/config.ini"
  content = join("\n", [
    "[database]",
    "host=localhost",
    "port=5432",
    "",
    "[logging]",
    "level=INFO",
    "file=${pyvider_local_directory.app_logs.path}/app.log"
  ])

  depends_on = [pyvider_local_directory.app_root]
}

output "directory_info" {
  description = "Information about created directories"
  value = {
    basic = {
      path       = pyvider_local_directory.basic_dir.path
      id         = pyvider_local_directory.basic_dir.id
      file_count = pyvider_local_directory.basic_dir.file_count
    }
    secure = {
      path        = pyvider_local_directory.secure_dir.path
      permissions = pyvider_local_directory.secure_dir.permissions
      file_count  = pyvider_local_directory.secure_dir.file_count
    }
    app_structure = {
      root = {
        path       = pyvider_local_directory.app_root.path
        file_count = pyvider_local_directory.app_root.file_count  # Should show 1 (config.ini)
      }
      logs = {
        path       = pyvider_local_directory.app_logs.path
        file_count = pyvider_local_directory.app_logs.file_count  # Should show 1 (app.log)
        permissions = pyvider_local_directory.app_logs.permissions
      }
      data = {
        path        = pyvider_local_directory.app_data.path
        file_count  = pyvider_local_directory.app_data.file_count  # Should show 0
        permissions = pyvider_local_directory.app_data.permissions
      }
    }
  }
}
```

### Project Structure Creation

```terraform
# Create a complete project directory structure

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "my-terraform-project"
}

variable "base_path" {
  description = "Base path for project creation"
  type        = string
  default     = "/tmp"
}

locals {
  project_root = "${var.base_path}/${var.project_name}"
}

# Create project root directory
resource "pyvider_local_directory" "project_root" {
  path        = local.project_root
  permissions = "0o755"
}

# Source code directories
resource "pyvider_local_directory" "src" {
  path = "${local.project_root}/src"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "src_components" {
  path = "${local.project_root}/src/components"
  depends_on = [pyvider_local_directory.src]
}

resource "pyvider_local_directory" "src_utils" {
  path = "${local.project_root}/src/utils"
  depends_on = [pyvider_local_directory.src]
}

# Test directories
resource "pyvider_local_directory" "tests" {
  path = "${local.project_root}/tests"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "tests_unit" {
  path = "${local.project_root}/tests/unit"
  depends_on = [pyvider_local_directory.tests]
}

resource "pyvider_local_directory" "tests_integration" {
  path = "${local.project_root}/tests/integration"
  depends_on = [pyvider_local_directory.tests]
}

# Documentation directories
resource "pyvider_local_directory" "docs" {
  path        = "${local.project_root}/docs"
  permissions = "0o755"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "docs_api" {
  path = "${local.project_root}/docs/api"
  depends_on = [pyvider_local_directory.docs]
}

# Configuration directories
resource "pyvider_local_directory" "config" {
  path        = "${local.project_root}/config"
  permissions = "0o750"  # More restrictive for config
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "config_environments" {
  path = "${local.project_root}/config/environments"
  depends_on = [pyvider_local_directory.config]
}

# Runtime directories
resource "pyvider_local_directory" "logs" {
  path        = "${local.project_root}/logs"
  permissions = "0o755"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "tmp" {
  path        = "${local.project_root}/tmp"
  permissions = "0o777"  # World writable for temp files
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "data" {
  path        = "${local.project_root}/data"
  permissions = "0o750"  # Restrictive for data
  depends_on = [pyvider_local_directory.project_root]
}

# Development-specific directories
resource "pyvider_local_directory" "scripts" {
  path = "${local.project_root}/scripts"
  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_local_directory" "tools" {
  path = "${local.project_root}/tools"
  depends_on = [pyvider_local_directory.project_root]
}

# Create essential project files
resource "pyvider_file_content" "readme" {
  filename = "${pyvider_local_directory.project_root.path}/README.md"
  content = <<-EOF
    # ${var.project_name}

    A project created with Terraform and Pyvider Components.

    ## Directory Structure

    ```
    ${var.project_name}/
    ├── src/                 # Source code
    │   ├── components/      # Reusable components
    │   └── utils/          # Utility functions
    ├── tests/              # Test files
    │   ├── unit/           # Unit tests
    │   └── integration/    # Integration tests
    ├── docs/               # Documentation
    │   └── api/            # API documentation
    ├── config/             # Configuration files
    │   └── environments/   # Environment-specific configs
    ├── logs/               # Log files
    ├── tmp/                # Temporary files
    ├── data/               # Application data
    ├── scripts/            # Build/deployment scripts
    └── tools/              # Development tools
    ```

    ## Getting Started

    1. Navigate to the project directory:
       ```bash
       cd ${local.project_root}
       ```

    2. Start development!

    Generated on: ${timestamp()}
  EOF

  depends_on = [pyvider_local_directory.project_root]
}

resource "pyvider_file_content" "gitignore" {
  filename = "${pyvider_local_directory.project_root.path}/.gitignore"
  content = <<-EOF
    # Logs
    logs/
    *.log

    # Temporary files
    tmp/
    *.tmp
    *.temp

    # OS generated files
    .DS_Store
    .DS_Store?
    ._*
    .Spotlight-V100
    .Trashes
    ehthumbs.db
    Thumbs.db

    # IDE files
    .vscode/
    .idea/
    *.swp
    *.swo

    # Environment files
    .env
    .env.local
    .env.*.local

    # Dependency directories
    node_modules/
    __pycache__/
    .pytest_cache/
  EOF

  depends_on = [pyvider_local_directory.project_root]
}

# Create environment configuration files
resource "pyvider_file_content" "env_development" {
  filename = "${pyvider_local_directory.config_environments.path}/development.conf"
  content = <<-EOF
    # Development Environment Configuration
    DEBUG=true
    LOG_LEVEL=debug
    DATABASE_URL=sqlite:///tmp/dev.db
    CACHE_ENABLED=false
  EOF

  depends_on = [pyvider_local_directory.config_environments]
}

resource "pyvider_file_content" "env_production" {
  filename = "${pyvider_local_directory.config_environments.path}/production.conf"
  content = <<-EOF
    # Production Environment Configuration
    DEBUG=false
    LOG_LEVEL=info
    DATABASE_URL=postgresql://localhost:5432/app_prod
    CACHE_ENABLED=true
    CACHE_TTL=3600
  EOF

  depends_on = [pyvider_local_directory.config_environments]
}

output "project_structure" {
  description = "Complete project directory structure"
  value = {
    project_name = var.project_name
    project_root = pyvider_local_directory.project_root.path

    directories = {
      source = {
        path       = pyvider_local_directory.src.path
        components = pyvider_local_directory.src_components.path
        utils      = pyvider_local_directory.src_utils.path
      }
      tests = {
        path        = pyvider_local_directory.tests.path
        unit        = pyvider_local_directory.tests_unit.path
        integration = pyvider_local_directory.tests_integration.path
      }
      docs = {
        path = pyvider_local_directory.docs.path
        api  = pyvider_local_directory.docs_api.path
      }
      config = {
        path         = pyvider_local_directory.config.path
        permissions  = pyvider_local_directory.config.permissions
        environments = pyvider_local_directory.config_environments.path
      }
      runtime = {
        logs = {
          path        = pyvider_local_directory.logs.path
          permissions = pyvider_local_directory.logs.permissions
        }
        tmp = {
          path        = pyvider_local_directory.tmp.path
          permissions = pyvider_local_directory.tmp.permissions
        }
        data = {
          path        = pyvider_local_directory.data.path
          permissions = pyvider_local_directory.data.permissions
        }
      }
      development = {
        scripts = pyvider_local_directory.scripts.path
        tools   = pyvider_local_directory.tools.path
      }
    }

    file_counts = {
      root   = pyvider_local_directory.project_root.file_count
      config = pyvider_local_directory.config_environments.file_count
      src    = pyvider_local_directory.src.file_count
      tests  = pyvider_local_directory.tests.file_count
    }
  }
}
```

### Permission Management

```terraform
# Permission management examples with different security levels

# Public directory - world readable/executable
resource "pyvider_local_directory" "public_files" {
  path        = "/tmp/public"
  permissions = "0o755"  # rwxr-xr-x
}

# Private user directory - only owner access
resource "pyvider_local_directory" "private_user" {
  path        = "/tmp/private_user"
  permissions = "0o700"  # rwx------
}

# Group shared directory - owner and group access
resource "pyvider_local_directory" "group_shared" {
  path        = "/tmp/group_shared"
  permissions = "0o750"  # rwxr-x---
}

# Read-only shared directory - owner write, others read
resource "pyvider_local_directory" "readonly_shared" {
  path        = "/tmp/readonly_shared"
  permissions = "0o744"  # rwxr--r--
}

# Secure configuration directory - restrictive permissions
resource "pyvider_local_directory" "secure_config" {
  path        = "/tmp/secure_config"
  permissions = "0o700"  # rwx------
}

# Web server directory - appropriate for web content
resource "pyvider_local_directory" "web_content" {
  path        = "/tmp/web"
  permissions = "0o755"  # rwxr-xr-x
}

# Log directory - allowing group write for log rotation
resource "pyvider_local_directory" "logs_group_write" {
  path        = "/tmp/logs_shared"
  permissions = "0o775"  # rwxrwxr-x
}

# Temporary directory - world writable (use with caution)
resource "pyvider_local_directory" "temp_world" {
  path        = "/tmp/temp_world"
  permissions = "0o777"  # rwxrwxrwx
}

# Create files with different permissions to demonstrate
resource "pyvider_file_content" "public_readme" {
  filename = "${pyvider_local_directory.public_files.path}/README.txt"
  content  = "This is a public file that anyone can read."

  depends_on = [pyvider_local_directory.public_files]
}

resource "pyvider_file_content" "private_secret" {
  filename = "${pyvider_local_directory.private_user.path}/secret.txt"
  content  = "This is a private file only the owner can access."

  depends_on = [pyvider_local_directory.private_user]
}

resource "pyvider_file_content" "group_config" {
  filename = "${pyvider_local_directory.group_shared.path}/team_config.yml"
  content = <<-EOF
    # Team Configuration
    team_name: "DevOps Team"
    members:
      - alice
      - bob
      - charlie

    shared_resources:
      - database: "team_db"
      - cache: "redis_cluster"

    permissions:
      read: ["team_members", "managers"]
      write: ["team_leads", "managers"]
  EOF

  depends_on = [pyvider_local_directory.group_shared]
}

resource "pyvider_file_content" "web_index" {
  filename = "${pyvider_local_directory.web_content.path}/index.html"
  content = <<-EOF
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample Web Page</title>
    </head>
    <body>
        <h1>Welcome to the Sample Site</h1>
        <p>This directory has web-appropriate permissions (0o755).</p>
        <p>Generated at: ${timestamp()}</p>
    </body>
    </html>
  EOF

  depends_on = [pyvider_local_directory.web_content]
}

resource "pyvider_file_content" "secure_credentials" {
  filename = "${pyvider_local_directory.secure_config.path}/credentials.json"
  content = jsonencode({
    database = {
      username = "app_user"
      password = "secure_password_here"
      host     = "db.internal.example.com"
    }
    api_keys = {
      third_party_service = "api_key_12345"
      payment_gateway     = "pk_live_abcdef123456"
    }
    encryption = {
      secret_key = "very_secret_encryption_key"
      salt       = "random_salt_value"
    }
  })

  depends_on = [pyvider_local_directory.secure_config]
}

# Demonstrate permission checking with a simple script
resource "pyvider_file_content" "permission_checker" {
  filename = "${pyvider_local_directory.public_files.path}/check_permissions.sh"
  content = <<-EOF
    #!/bin/bash

    echo "=== Directory Permission Check ==="
    echo

    for dir in "/tmp/public" "/tmp/private_user" "/tmp/group_shared" "/tmp/secure_config"; do
        if [ -d "$dir" ]; then
            echo "Directory: $dir"
            ls -ld "$dir"
            echo "Permissions: $(stat -c '%a' "$dir" 2>/dev/null || stat -f '%A' "$dir" 2>/dev/null)"
            echo
        fi
    done

    echo "=== File Permission Check ==="
    echo

    find /tmp -maxdepth 2 -name "*.txt" -o -name "*.json" -o -name "*.yml" 2>/dev/null | while read file; do
        if [ -f "$file" ]; then
            echo "File: $file"
            ls -l "$file"
            echo
        fi
    done
  EOF

  depends_on = [pyvider_local_directory.public_files]
}

output "permission_examples" {
  description = "Directory permission examples and their meanings"
  value = {
    directories = {
      public = {
        path        = pyvider_local_directory.public_files.path
        permissions = pyvider_local_directory.public_files.permissions
        meaning     = "rwxr-xr-x - Owner: read/write/execute, Group/Others: read/execute"
        use_case    = "Public files, documentation, web content"
      }
      private_user = {
        path        = pyvider_local_directory.private_user.path
        permissions = pyvider_local_directory.private_user.permissions
        meaning     = "rwx------ - Owner: read/write/execute, Others: no access"
        use_case    = "Personal files, private keys, user-specific config"
      }
      group_shared = {
        path        = pyvider_local_directory.group_shared.path
        permissions = pyvider_local_directory.group_shared.permissions
        meaning     = "rwxr-x--- - Owner: read/write/execute, Group: read/execute, Others: no access"
        use_case    = "Team shared files, project directories"
      }
      secure_config = {
        path        = pyvider_local_directory.secure_config.path
        permissions = pyvider_local_directory.secure_config.permissions
        meaning     = "rwx------ - Owner only access"
        use_case    = "Credentials, secrets, sensitive configuration"
      }
      web_content = {
        path        = pyvider_local_directory.web_content.path
        permissions = pyvider_local_directory.web_content.permissions
        meaning     = "rwxr-xr-x - Standard web server permissions"
        use_case    = "Web server document root, static assets"
      }
      logs_group_write = {
        path        = pyvider_local_directory.logs_group_write.path
        permissions = pyvider_local_directory.logs_group_write.permissions
        meaning     = "rwxrwxr-x - Owner/Group: read/write/execute, Others: read/execute"
        use_case    = "Shared log directories with log rotation"
      }
      temp_world = {
        path        = pyvider_local_directory.temp_world.path
        permissions = pyvider_local_directory.temp_world.permissions
        meaning     = "rwxrwxrwx - World writable (use with extreme caution)"
        use_case    = "Temporary directories for inter-process communication"
      }
    }

    security_best_practices = {
      principle_of_least_privilege = "Grant only the minimum permissions necessary"
      avoid_world_writable         = "0o777 permissions are dangerous and should be avoided"
      separate_config_and_data     = "Use different permission levels for config vs data directories"
      regular_audits              = "Periodically review directory permissions"
    }

    permission_guide = {
      "0o700" = "Private - Owner only"
      "0o750" = "Group shared - Owner full, Group read/execute"
      "0o755" = "Public read - Standard directory permissions"
      "0o775" = "Group writable - Shared write access"
      "0o777" = "World writable - Dangerous, avoid in production"
    }
  }
}
```

### Workspace Setup

```terraform
# Complete workspace setup for different development scenarios

variable "workspace_name" {
  description = "Name of the workspace to create"
  type        = string
  default     = "dev-workspace"
}

variable "workspace_type" {
  description = "Type of workspace: web, api, data, or fullstack"
  type        = string
  default     = "fullstack"
  validation {
    condition     = contains(["web", "api", "data", "fullstack"], var.workspace_type)
    error_message = "Workspace type must be one of: web, api, data, fullstack."
  }
}

data "pyvider_env_variables" "user_info" {
  keys = ["USER", "HOME"]
}

locals {
  workspace_root = "/tmp/workspaces/${var.workspace_name}"
  username = lookup(data.pyvider_env_variables.user_info.values, "USER", "developer")

  # Define workspace structures based on type
  workspace_configs = {
    web = {
      directories = ["src", "public", "assets", "styles", "scripts", "tests", "dist", "docs"]
      files = {
        "package.json" = {
          name         = var.workspace_name
          version      = "1.0.0"
          main         = "src/index.js"
          scripts = {
            start = "npm run dev"
            dev   = "webpack serve --mode development"
            build = "webpack --mode production"
            test  = "jest"
          }
        }
        "webpack.config.js" = "// Webpack configuration for ${var.workspace_name}"
        ".gitignore" = join("\n", [
          "node_modules/", "dist/", "*.log", ".env*", ".DS_Store"
        ])
      }
    }
    api = {
      directories = ["src", "controllers", "models", "routes", "middleware", "tests", "docs", "config", "logs"]
      files = {
        "package.json" = {
          name    = var.workspace_name
          version = "1.0.0"
          main    = "src/server.js"
          scripts = {
            start = "node src/server.js"
            dev   = "nodemon src/server.js"
            test  = "jest"
          }
        }
        "src/server.js" = "// Express server for ${var.workspace_name}"
        ".env.example" = join("\n", [
          "PORT=3000", "DATABASE_URL=postgresql://localhost:5432/${var.workspace_name}",
          "JWT_SECRET=your-secret-key", "NODE_ENV=development"
        ])
      }
    }
    data = {
      directories = ["notebooks", "data/raw", "data/processed", "data/external", "models", "reports", "scripts", "tests"]
      files = {
        "requirements.txt" = join("\n", [
          "pandas>=1.5.0", "numpy>=1.24.0", "matplotlib>=3.6.0",
          "seaborn>=0.12.0", "scikit-learn>=1.2.0", "jupyter>=1.0.0"
        ])
        "README.md" = "# ${var.workspace_name}\n\nData science workspace created with Terraform."
        ".gitignore" = join("\n", [
          "*.csv", "*.parquet", "__pycache__/", ".ipynb_checkpoints/",
          "data/raw/*", "!data/raw/.gitkeep", "models/*.pkl"
        ])
      }
    }
    fullstack = {
      directories = [
        "frontend/src", "frontend/public", "frontend/tests",
        "backend/src", "backend/tests", "backend/config",
        "database/migrations", "database/seeds",
        "docs", "scripts", "docker", "k8s"
      ]
      files = {
        "docker-compose.yml" = "# Docker Compose for ${var.workspace_name}"
        "README.md" = "# ${var.workspace_name}\n\nFullstack application workspace."
        ".env.example" = join("\n", [
          "# Frontend", "REACT_APP_API_URL=http://localhost:3001",
          "# Backend", "PORT=3001", "DATABASE_URL=postgresql://localhost:5432/${var.workspace_name}",
          "# Docker", "POSTGRES_DB=${var.workspace_name}", "POSTGRES_USER=dev", "POSTGRES_PASSWORD=devpass"
        ])
      }
    }
  }

  config = local.workspace_configs[var.workspace_type]
}

# Create workspace root
resource "pyvider_local_directory" "workspace_root" {
  path        = local.workspace_root
  permissions = "0o755"
}

# Create all directories for the workspace type
resource "pyvider_local_directory" "workspace_dirs" {
  for_each = toset(local.config.directories)

  path = "${local.workspace_root}/${each.value}"
  depends_on = [pyvider_local_directory.workspace_root]
}

# Create workspace-specific configuration files
resource "pyvider_file_content" "workspace_files" {
  for_each = local.config.files

  filename = "${pyvider_local_directory.workspace_root.path}/${each.key}"
  content = can(jsondecode(jsonencode(each.value))) && length(regexall("\\{|\\[", jsonencode(each.value))) > 0 ?
    jsonencode(each.value) : each.value

  depends_on = [pyvider_local_directory.workspace_root]
}

# Create common development files
resource "pyvider_file_content" "workspace_readme" {
  filename = "${pyvider_local_directory.workspace_root.path}/WORKSPACE_INFO.md"
  content = <<-EOF
    # ${var.workspace_name}

    **Type:** ${var.workspace_type}
    **Created:** ${timestamp()}
    **Owner:** ${local.username}

    ## Workspace Structure

    This ${var.workspace_type} workspace includes the following directories:

    ${join("\n", [for dir in local.config.directories : "- `${dir}/`"])}

    ## Getting Started

    1. Navigate to the workspace:
       ```bash
       cd ${local.workspace_root}
       ```

    2. Follow the setup instructions for your workspace type.

    ## Workspace Type: ${upper(var.workspace_type)}

    ${var.workspace_type == "web" ? "This is a frontend web development workspace with webpack configuration." : ""}
    ${var.workspace_type == "api" ? "This is a backend API development workspace with Express.js setup." : ""}
    ${var.workspace_type == "data" ? "This is a data science workspace with Python and Jupyter setup." : ""}
    ${var.workspace_type == "fullstack" ? "This is a fullstack development workspace with frontend, backend, and database components." : ""}

    ## Directory Permissions

    ${join("\n", [for dir_name, dir_resource in pyvider_local_directory.workspace_dirs :
      "- `${dir_name}`: ${dir_resource.permissions != null ? dir_resource.permissions : "default (0o755)"}"
    ])}

    ## File Count Monitoring

    ${join("\n", [for dir_name, dir_resource in pyvider_local_directory.workspace_dirs :
      "- `${dir_name}`: ${dir_resource.file_count} items"
    ])}
  EOF

  depends_on = [pyvider_local_directory.workspace_dirs]
}

# Create development helper scripts
resource "pyvider_local_directory" "scripts_dir" {
  path = "${local.workspace_root}/scripts"
  depends_on = [pyvider_local_directory.workspace_root]
}

resource "pyvider_file_content" "setup_script" {
  filename = "${pyvider_local_directory.scripts_dir.path}/setup.sh"
  content = <<-EOF
    #!/bin/bash
    set -e

    echo "Setting up ${var.workspace_name} (${var.workspace_type}) workspace..."

    # Navigate to workspace root
    cd "${local.workspace_root}"

    ${var.workspace_type == "web" || var.workspace_type == "fullstack" ? "echo 'Installing Node.js dependencies...'\nif [ -f package.json ]; then\n    npm install\nfi" : ""}

    ${var.workspace_type == "data" ? "echo 'Setting up Python environment...'\nif [ -f requirements.txt ]; then\n    pip install -r requirements.txt\nfi" : ""}

    ${var.workspace_type == "api" || var.workspace_type == "fullstack" ? "echo 'Setting up API environment...'\nif [ -f .env.example ]; then\n    cp .env.example .env\n    echo 'Created .env file from example'\nfi" : ""}

    echo "Workspace setup complete!"
    echo "Workspace location: ${local.workspace_root}"
    echo "Type: ${var.workspace_type}"
    echo "Created by: ${local.username}"
  EOF

  depends_on = [pyvider_local_directory.scripts_dir]
}

resource "pyvider_file_content" "cleanup_script" {
  filename = "${pyvider_local_directory.scripts_dir.path}/cleanup.sh"
  content = <<-EOF
    #!/bin/bash

    echo "Cleaning up ${var.workspace_name} workspace..."

    # Navigate to workspace root
    cd "${local.workspace_root}"

    # Clean common temporary files
    find . -name "*.log" -delete
    find . -name "*.tmp" -delete
    find . -name ".DS_Store" -delete

    ${var.workspace_type == "web" || var.workspace_type == "fullstack" ? "# Clean Node.js artifacts\nrm -rf node_modules/\nrm -rf dist/\nrm -rf build/" : ""}

    ${var.workspace_type == "data" ? "# Clean Python artifacts\nfind . -name '__pycache__' -type d -exec rm -rf {} +\nfind . -name '*.pyc' -delete\nrm -rf .ipynb_checkpoints/" : ""}

    ${var.workspace_type == "api" || var.workspace_type == "fullstack" ? "# Clean API artifacts\nrm -rf logs/*.log\nrm -f .env" : ""}

    echo "Cleanup complete!"
  EOF

  depends_on = [pyvider_local_directory.scripts_dir]
}

output "workspace_setup" {
  description = "Complete workspace setup information"
  value = {
    workspace_name = var.workspace_name
    workspace_type = var.workspace_type
    workspace_root = pyvider_local_directory.workspace_root.path
    created_by     = local.username

    structure = {
      directories = {
        for dir_name, dir_resource in pyvider_local_directory.workspace_dirs :
        dir_name => {
          path        = dir_resource.path
          file_count  = dir_resource.file_count
          permissions = dir_resource.permissions
        }
      }
      root_file_count = pyvider_local_directory.workspace_root.file_count
    }

    created_files = [for filename in keys(local.config.files) : filename]

    quick_start = {
      setup_command   = "cd ${local.workspace_root} && bash scripts/setup.sh"
      cleanup_command = "cd ${local.workspace_root} && bash scripts/cleanup.sh"
      workspace_info  = "${local.workspace_root}/WORKSPACE_INFO.md"
    }

    type_specific_info = {
      web = var.workspace_type == "web" ? {
        main_directory = "${local.workspace_root}/src"
        public_assets  = "${local.workspace_root}/public"
        build_output   = "${local.workspace_root}/dist"
      } : null

      api = var.workspace_type == "api" ? {
        server_file    = "${local.workspace_root}/src/server.js"
        routes_dir     = "${local.workspace_root}/routes"
        config_dir     = "${local.workspace_root}/config"
      } : null

      data = var.workspace_type == "data" ? {
        notebooks_dir  = "${local.workspace_root}/notebooks"
        raw_data_dir   = "${local.workspace_root}/data/raw"
        processed_dir  = "${local.workspace_root}/data/processed"
      } : null

      fullstack = var.workspace_type == "fullstack" ? {
        frontend_dir = "${local.workspace_root}/frontend"
        backend_dir  = "${local.workspace_root}/backend"
        database_dir = "${local.workspace_root}/database"
      } : null
    }
  }
}
```

## Schema



## Import

You can import existing directories into Terraform state:

```bash
terraform import pyvider_local_directory.example /path/to/existing/directory
```

The import will read the current directory state, permissions, and file count.

## Permission Format

The `permissions` attribute uses octal notation with the `0o` prefix:

| Permission | Octal | Description |
|------------|-------|-------------|
| `0o755`    | 755   | rwxr-xr-x (owner: read/write/execute, group/others: read/execute) |
| `0o750`    | 750   | rwxr-x--- (owner: read/write/execute, group: read/execute, others: none) |
| `0o700`    | 700   | rwx------ (owner: read/write/execute, others: none) |
| `0o644`    | 644   | rw-r--r-- (owner: read/write, group/others: read only) |

## Common Issues & Solutions

### Error: "Permission denied"
**Solution**: Ensure the Terraform process has permission to create directories in the target location.

```bash
# Check parent directory permissions
ls -la /path/to/parent
# Fix parent permissions if needed
chmod 755 /path/to/parent
```

### Error: "Invalid permissions format"
**Solution**: Ensure permissions use the correct octal format with `0o` prefix.

```terraform
# ❌ Wrong
resource "pyvider_local_directory" "wrong" {
  path        = "/tmp/test"
  permissions = "755"  # Missing 0o prefix
}

# ✅ Correct
resource "pyvider_local_directory" "correct" {
  path        = "/tmp/test"
  permissions = "0o755"  # Proper octal format
}
```

### Parent Directory Doesn't Exist
**Solution**: Create parent directories first or use depends_on for proper ordering.

```terraform
# Create parent directory first
resource "pyvider_local_directory" "parent" {
  path = "/tmp/app"
}

resource "pyvider_local_directory" "child" {
  path = "/tmp/app/subdirectory"

  depends_on = [pyvider_local_directory.parent]
}
```

### Directory Already Exists with Different Permissions
When importing or managing existing directories, the resource will update permissions to match the configuration.

## File Count Monitoring

The `file_count` attribute provides the number of direct children (files and subdirectories) in the managed directory:

```terraform
resource "pyvider_local_directory" "monitored" {
  path = "/tmp/monitored"
}

# Use file count in conditional logic
resource "pyvider_file_content" "status" {
  filename = "/tmp/status.txt"
  content  = "Directory has ${pyvider_local_directory.monitored.file_count} items"
}
```

## Related Components

- [`pyvider_file_content`](../file_content.md) - Create files within managed directories
- [`pyvider_file_info`](../../data-sources/file_info.md) - Check directory existence without management
- [`env_variables` data source](../../data-sources/env_variables.md) - Use environment variables in directory paths