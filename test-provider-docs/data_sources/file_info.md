---
page_title: "Data Source: pyvider_file_info"
description: |-
  Provides detailed information about files and directories
---

# pyvider_file_info (Data Source)

> Read comprehensive metadata about files and directories without managing them

The `pyvider_file_info` data source allows you to inspect files and directories on the local filesystem. It provides detailed metadata including size, timestamps, permissions, and file type information without creating or managing the files.

## When to Use This

- **Conditional resource creation**: Check if files exist before creating resources
- **File system validation**: Verify expected files are present with correct properties
- **Deployment checks**: Validate configuration files before deployment
- **Backup verification**: Check file sizes and modification times
- **Permission auditing**: Inspect file and directory permissions

**Anti-patterns (when NOT to use):**
- Managing file content (use `pyvider_file_content` resource instead)
- Creating or modifying files (this is read-only)
- Complex file operations (use external tools)

## Quick Start

```terraform
# Check if a configuration file exists
data "pyvider_file_info" "config" {
  path = "/etc/myapp/config.yaml"
}

# Conditionally create backup based on file existence
resource "pyvider_file_content" "backup" {
  count = data.pyvider_file_info.config.exists ? 1 : 0

  filename = "/backup/config.yaml.bak"
  content  = "Backup created at ${timestamp()}"
}
```

## Examples

### Basic Usage

```terraform
# Basic file information examples

# Check a regular file
data "pyvider_file_info" "hosts_file" {
  path = "/etc/hosts"
}

# Check a directory
data "pyvider_file_info" "tmp_dir" {
  path = "/tmp"
}

# Check a potentially non-existent file
data "pyvider_file_info" "config_file" {
  path = "/etc/myapp/config.yaml"
}

# Check current working directory
data "pyvider_file_info" "current_dir" {
  path = "."
}

# Create some files to demonstrate with
resource "pyvider_local_directory" "test_dir" {
  path        = "/tmp/file_info_test"
  permissions = "0755"
}

resource "pyvider_file_content" "sample_text" {
  filename = "${pyvider_local_directory.test_dir.path}/sample.txt"
  content  = "This is a sample text file for testing file_info data source."

  depends_on = [pyvider_local_directory.test_dir]
}

resource "pyvider_file_content" "sample_json" {
  filename = "${pyvider_local_directory.test_dir.path}/config.json"
  content = jsonencode({
    app_name = "file_info_demo"
    version  = "1.0.0"
    settings = {
      debug = true
      port  = 8080
    }
  })

  depends_on = [pyvider_local_directory.test_dir]
}

# Check the files we just created
data "pyvider_file_info" "created_text" {
  path = pyvider_file_content.sample_text.filename

  depends_on = [pyvider_file_content.sample_text]
}

data "pyvider_file_info" "created_json" {
  path = pyvider_file_content.sample_json.filename

  depends_on = [pyvider_file_content.sample_json]
}

data "pyvider_file_info" "created_dir" {
  path = pyvider_local_directory.test_dir.path

  depends_on = [pyvider_local_directory.test_dir]
}

# Create a report of all file information
resource "pyvider_file_content" "file_info_report" {
  filename = "/tmp/file_info_basic_report.txt"
  content = join("\n", [
    "=== File Information Report ===",
    "",
    "=== System Files ===",
    "/etc/hosts:",
    "  Exists: ${data.pyvider_file_info.hosts_file.exists}",
    "  Type: ${data.pyvider_file_info.hosts_file.is_file ? "File" : data.pyvider_file_info.hosts_file.is_dir ? "Directory" : "Other"}",
    "  Size: ${data.pyvider_file_info.hosts_file.size} bytes",
    "  Modified: ${data.pyvider_file_info.hosts_file.modified_time}",
    "  Permissions: ${data.pyvider_file_info.hosts_file.permissions}",
    "  Owner: ${data.pyvider_file_info.hosts_file.owner}",
    "  MIME Type: ${data.pyvider_file_info.hosts_file.mime_type}",
    "",
    "/tmp directory:",
    "  Exists: ${data.pyvider_file_info.tmp_dir.exists}",
    "  Type: ${data.pyvider_file_info.tmp_dir.is_file ? "File" : data.pyvider_file_info.tmp_dir.is_dir ? "Directory" : "Other"}",
    "  Permissions: ${data.pyvider_file_info.tmp_dir.permissions}",
    "  Owner: ${data.pyvider_file_info.tmp_dir.owner}",
    "  Group: ${data.pyvider_file_info.tmp_dir.group}",
    "",
    "=== Application Config ===",
    "/etc/myapp/config.yaml:",
    "  Exists: ${data.pyvider_file_info.config_file.exists}",
    data.pyvider_file_info.config_file.exists ? "  Size: ${data.pyvider_file_info.config_file.size} bytes" : "  (File not found)",
    data.pyvider_file_info.config_file.exists ? "  Modified: ${data.pyvider_file_info.config_file.modified_time}" : "",
    "",
    "=== Current Directory ===",
    "Current working directory (.):",
    "  Exists: ${data.pyvider_file_info.current_dir.exists}",
    "  Type: ${data.pyvider_file_info.current_dir.is_dir ? "Directory" : "Not Directory"}",
    "  Permissions: ${data.pyvider_file_info.current_dir.permissions}",
    "",
    "=== Created Test Files ===",
    "Test directory (${pyvider_local_directory.test_dir.path}):",
    "  Exists: ${data.pyvider_file_info.created_dir.exists}",
    "  Type: Directory",
    "  Permissions: ${data.pyvider_file_info.created_dir.permissions}",
    "",
    "Sample text file:",
    "  Path: ${data.pyvider_file_info.created_text.path}",
    "  Exists: ${data.pyvider_file_info.created_text.exists}",
    "  Size: ${data.pyvider_file_info.created_text.size} bytes",
    "  MIME Type: ${data.pyvider_file_info.created_text.mime_type}",
    "  Modified: ${data.pyvider_file_info.created_text.modified_time}",
    "",
    "Sample JSON file:",
    "  Path: ${data.pyvider_file_info.created_json.path}",
    "  Exists: ${data.pyvider_file_info.created_json.exists}",
    "  Size: ${data.pyvider_file_info.created_json.size} bytes",
    "  MIME Type: ${data.pyvider_file_info.created_json.mime_type}",
    "  Modified: ${data.pyvider_file_info.created_json.modified_time}",
    "",
    "=== File Size Analysis ===",
    "Text file size: ${data.pyvider_file_info.created_text.size} bytes",
    "JSON file size: ${data.pyvider_file_info.created_json.size} bytes",
    "Larger file: ${data.pyvider_file_info.created_text.size > data.pyvider_file_info.created_json.size ? "text" : "json"}",
    "",
    "Report generated at: ${timestamp()}"
  ])

  depends_on = [
    data.pyvider_file_info.created_text,
    data.pyvider_file_info.created_json,
    data.pyvider_file_info.created_dir
  ]
}

# Calculate some basic statistics
locals {
  file_stats = {
    total_files_checked = 6
    existing_files = length([
      for info in [
        data.pyvider_file_info.hosts_file,
        data.pyvider_file_info.tmp_dir,
        data.pyvider_file_info.config_file,
        data.pyvider_file_info.current_dir,
        data.pyvider_file_info.created_text,
        data.pyvider_file_info.created_json
      ] : info if info.exists
    ])

    total_size_bytes = (
      data.pyvider_file_info.hosts_file.size +
      data.pyvider_file_info.created_text.size +
      data.pyvider_file_info.created_json.size
    )

    file_types = {
      regular_files = length([
        for info in [
          data.pyvider_file_info.hosts_file,
          data.pyvider_file_info.created_text,
          data.pyvider_file_info.created_json
        ] : info if info.is_file && info.exists
      ])

      directories = length([
        for info in [
          data.pyvider_file_info.tmp_dir,
          data.pyvider_file_info.current_dir,
          data.pyvider_file_info.created_dir
        ] : info if info.is_dir && info.exists
      ])
    }
  }
}

output "basic_file_info" {
  description = "Basic file information examples"
  value = {
    system_files = {
      hosts_file = {
        exists = data.pyvider_file_info.hosts_file.exists
        size = data.pyvider_file_info.hosts_file.size
        type = data.pyvider_file_info.hosts_file.is_file ? "file" : "other"
        permissions = data.pyvider_file_info.hosts_file.permissions
        mime_type = data.pyvider_file_info.hosts_file.mime_type
      }

      tmp_directory = {
        exists = data.pyvider_file_info.tmp_dir.exists
        is_directory = data.pyvider_file_info.tmp_dir.is_dir
        permissions = data.pyvider_file_info.tmp_dir.permissions
        owner = data.pyvider_file_info.tmp_dir.owner
      }
    }

    application_files = {
      config_exists = data.pyvider_file_info.config_file.exists
      current_dir_accessible = data.pyvider_file_info.current_dir.exists
    }

    created_files = {
      test_directory = {
        path = data.pyvider_file_info.created_dir.path
        exists = data.pyvider_file_info.created_dir.exists
        permissions = data.pyvider_file_info.created_dir.permissions
      }

      text_file = {
        path = data.pyvider_file_info.created_text.path
        exists = data.pyvider_file_info.created_text.exists
        size = data.pyvider_file_info.created_text.size
        mime_type = data.pyvider_file_info.created_text.mime_type
      }

      json_file = {
        path = data.pyvider_file_info.created_json.path
        exists = data.pyvider_file_info.created_json.exists
        size = data.pyvider_file_info.created_json.size
        mime_type = data.pyvider_file_info.created_json.mime_type
      }
    }

    statistics = local.file_stats

    report_file = pyvider_file_content.file_info_report.filename
  }
}
```

### Conditional Logic



### File System Validation



### Permission Checking



## Schema



## Output Attributes

The data source provides comprehensive file information:

### Basic Properties
- **`exists`** - Whether the path exists
- **`size`** - File size in bytes (0 for directories)
- **`is_file`** - True if it's a regular file
- **`is_dir`** - True if it's a directory
- **`is_symlink`** - True if it's a symbolic link

### Timestamps
- **`modified_time`** - Last modification time (ISO 8601 format)
- **`access_time`** - Last access time (ISO 8601 format)
- **`creation_time`** - File creation time (ISO 8601 format)

### Security & Ownership
- **`permissions`** - File permissions in octal format (e.g., "0644")
- **`owner`** - File owner username
- **`group`** - File group name

### Content Information
- **`mime_type`** - MIME type of the file (e.g., "text/plain", "application/json")

## Common Patterns

### Conditional Resource Creation
```terraform
data "pyvider_file_info" "ssl_cert" {
  path = "/etc/ssl/certs/app.crt"
}

# Only create certificate if it doesn't exist
resource "pyvider_file_content" "ssl_cert" {
  count = !data.pyvider_file_info.ssl_cert.exists ? 1 : 0

  filename = "/etc/ssl/certs/app.crt"
  content  = var.ssl_certificate_content
}
```

### File Validation
```terraform
data "pyvider_file_info" "config" {
  path = "/app/config.json"
}

locals {
  config_valid = (
    data.pyvider_file_info.config.exists &&
    data.pyvider_file_info.config.is_file &&
    data.pyvider_file_info.config.size > 0 &&
    data.pyvider_file_info.config.mime_type == "application/json"
  )
}
```

### Permission Auditing
```terraform
data "pyvider_file_info" "sensitive_file" {
  path = "/etc/secrets/api_key"
}

locals {
  secure_permissions = data.pyvider_file_info.sensitive_file.permissions == "0600"
  correct_owner = data.pyvider_file_info.sensitive_file.owner == "app"
}
```

### Backup Decision Logic
```terraform
data "pyvider_file_info" "database_dump" {
  path = "/backups/db_dump.sql"
}

# Create new backup if file is older than 24 hours
locals {
  backup_age_hours = (
    parseint(formatdate("YYYYMMDDhhmm", timestamp()), 10) -
    parseint(formatdate("YYYYMMDDhhmm", data.pyvider_file_info.database_dump.modified_time), 10)
  ) / 100  # Rough calculation

  needs_backup = (
    !data.pyvider_file_info.database_dump.exists ||
    local.backup_age_hours > 24
  )
}
```

## File Size Interpretation

The `size` attribute returns bytes. For human-readable sizes:

```terraform
locals {
  file_size_kb = data.pyvider_file_info.large_file.size / 1024
  file_size_mb = data.pyvider_file_info.large_file.size / (1024 * 1024)
  file_size_gb = data.pyvider_file_info.large_file.size / (1024 * 1024 * 1024)
}
```

## Timestamp Formats

All timestamps are returned in ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`):

```terraform
locals {
  # Extract components
  modified_date = split("T", data.pyvider_file_info.example.modified_time)[0]
  modified_time = split("T", data.pyvider_file_info.example.modified_time)[1]

  # Age calculation
  is_recent = timecmp(
    data.pyvider_file_info.example.modified_time,
    timeadd(timestamp(), "-1h")
  ) > 0
}
```

## Permission Format

Permissions are returned in octal format with leading zero:

| Permission | Meaning |
|------------|---------|
| `0644` | rw-r--r-- (owner: read/write, others: read) |
| `0755` | rwxr-xr-x (owner: read/write/execute, others: read/execute) |
| `0600` | rw------- (owner: read/write only) |
| `0700` | rwx------ (owner: read/write/execute only) |

## Common Issues & Solutions

### Error: "Path not found"
This is expected behavior when checking if files exist:

```terraform
# ✅ Correct - handle non-existent files gracefully
data "pyvider_file_info" "optional_file" {
  path = "/optional/config.conf"
}

locals {
  use_defaults = !data.pyvider_file_info.optional_file.exists
}
```

### Symlink Handling
For symbolic links, the data source reports information about the link itself, not the target:

```terraform
data "pyvider_file_info" "symlink" {
  path = "/etc/current-config"  # Points to /etc/configs/v1.2.3/config.yaml
}

# This will be true if it's a symlink, regardless of target validity
output "is_symlink" {
  value = data.pyvider_file_info.symlink.is_symlink
}
```

### Directory vs File Detection
```terraform
data "pyvider_file_info" "path" {
  path = "/var/log"
}

locals {
  path_type = (
    data.pyvider_file_info.path.is_file ? "file" :
    data.pyvider_file_info.path.is_dir ? "directory" :
    data.pyvider_file_info.path.is_symlink ? "symlink" :
    "unknown"
  )
}
```

## Security Considerations

1. **Permission Validation**: Always check file permissions for sensitive files
2. **Owner Verification**: Verify files are owned by expected users
3. **Path Traversal**: Be careful with dynamic paths from user input
4. **Symbolic Links**: Consider if symlinks pose security risks in your use case

## Related Components

- [`pyvider_file_content`](../../resources/file_content.md) - Create and manage file content
- [`pyvider_local_directory`](../../resources/local_directory.md) - Create and manage directories
- [`pyvider_env_variables`](../env_variables.md) - Use environment variables in file paths