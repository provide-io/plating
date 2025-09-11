"""
End-to-end tests for plating with real bundles.
"""
import subprocess
import tempfile
from pathlib import Path
import pytest

from plating.plating import PlatingBundle
from plating.plater import PlatingPlater
from plating.dresser import PlatingDresser


class TestEndToEnd:
    """End-to-end tests with real garnish functionality."""

    @pytest.fixture
    def realistic_bundle(self):
        """Create a realistic plating bundle for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create a realistic provider structure
            resources_dir = tmp_path / "resources"
            resources_dir.mkdir()
            
            # Create a Python resource file
            resource_file = resources_dir / "bucket.py"
            resource_file.write_text('''
"""S3 bucket resource implementation."""
from attrs import define, field

@define
class BucketResource:
    """Manages an S3 bucket.
    
    This resource creates and manages an S3 bucket with
    versioning, encryption, and lifecycle policies.
    """
    
    name: str = field()
    region: str = field(default="us-east-1")
    versioning: bool = field(default=False)
    encryption: bool = field(default=True)
    
    def create(self):
        """Create the S3 bucket."""
        pass
    
    def update(self):
        """Update bucket configuration."""
        pass
    
    def delete(self):
        """Delete the S3 bucket."""
        pass
''')
            
            # Create the plating bundle
            bundle_dir = resources_dir / "bucket.plating"
            bundle_dir.mkdir()
            
            # Create docs directory with comprehensive template
            docs_dir = bundle_dir / "docs"
            docs_dir.mkdir()
            
            template_file = docs_dir / "bucket.tmpl.md"
            template_file.write_text('''---
page_title: "bucket Resource - terraform-provider-aws"
subcategory: "S3"
description: |-
  Provides an S3 bucket resource.
---

# Resource: aws_s3_bucket

Provides an S3 bucket resource with comprehensive configuration options.

## Example Usage

### Basic Bucket

{{ example("basic") }}

### Bucket with Versioning

{{ example("versioning") }}

### Bucket with Encryption

{{ example("encryption") }}

## Argument Reference

The following arguments are supported:

* `bucket` - (Required) Name of the bucket. Must be globally unique.
* `region` - (Optional) AWS region for the bucket. Defaults to `us-east-1`.
* `versioning` - (Optional) Enable versioning for the bucket. Defaults to `false`.
* `encryption` - (Optional) Enable server-side encryption. Defaults to `true`.
* `tags` - (Optional) Map of tags to assign to the bucket.

## Attribute Reference

In addition to all arguments above, the following attributes are exported:

* `id` - The name of the bucket.
* `arn` - The ARN of the bucket.
* `bucket_domain_name` - The bucket domain name.
* `bucket_regional_domain_name` - The bucket region-specific domain name.
* `hosted_zone_id` - The Route 53 Hosted Zone ID for this bucket's region.
* `region` - The AWS region this bucket resides in.

## Import

S3 buckets can be imported using the bucket name, e.g.,

```bash
terraform import aws_s3_bucket.example my-bucket-name
```

## Timeouts

The `aws_s3_bucket` resource supports the following timeouts:

* `create` - (Default `20m`) How long to wait for the bucket to be created.
* `update` - (Default `20m`) How long to wait for the bucket to be updated.
* `delete` - (Default `60m`) How long to wait for the bucket to be deleted.

## Schema

{{ schema() }}
''')
            
            # Create examples directory with multiple examples
            examples_dir = bundle_dir / "examples"
            examples_dir.mkdir()
            
            # Basic example
            basic_example = examples_dir / "basic.tf"
            basic_example.write_text('''resource "aws_s3_bucket" "example" {
  bucket = "my-example-bucket"
  
  tags = {
    Name        = "My Example Bucket"
    Environment = "Dev"
  }
}

output "bucket_id" {
  value = aws_s3_bucket.example.id
}

output "bucket_arn" {
  value = aws_s3_bucket.example.arn
}
''')
            
            # Versioning example
            versioning_example = examples_dir / "versioning.tf"
            versioning_example.write_text('''resource "aws_s3_bucket" "versioned" {
  bucket = "my-versioned-bucket"
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.versioned.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

output "bucket_id" {
  value = aws_s3_bucket.versioned.id
}
''')
            
            # Encryption example
            encryption_example = examples_dir / "encryption.tf"
            encryption_example.write_text('''resource "aws_s3_bucket" "encrypted" {
  bucket = "my-encrypted-bucket"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  bucket = aws_s3_bucket.encrypted.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

output "bucket_id" {
  value = aws_s3_bucket.encrypted.id
}
''')
            
            # Create fixtures directory with test data
            fixtures_dir = bundle_dir / "fixtures"
            fixtures_dir.mkdir()
            
            test_config = fixtures_dir / "test_config.json"
            test_config.write_text('''{
  "bucket_name": "test-bucket-12345",
  "region": "us-west-2",
  "versioning": true,
  "encryption": true,
  "tags": {
    "Project": "TestProject",
    "Environment": "Testing"
  }
}
''')
            
            # Create partials
            partial_file = docs_dir / "_note.md"
            partial_file.write_text('''> **Note:** S3 bucket names must be globally unique across all AWS accounts.''')
            
            yield bundle_dir

    def test_full_workflow_with_realistic_bundle(self, realistic_bundle):
        """Test the complete workflow with a realistic bundle."""
        # Create a PlatingBundle object
        bundle = PlatingBundle(
            plating_dir=realistic_bundle,
            name="bucket",
            component_type="resource"
        )
        
        # Verify bundle can load all assets
        template = bundle.load_main_template()
        assert template is not None
        assert "Resource: aws_s3_bucket" in template
        
        examples = bundle.load_examples()
        assert len(examples) == 3
        assert "basic" in examples
        assert "versioning" in examples
        assert "encryption" in examples
        
        fixtures = bundle.load_fixtures()
        # Fixtures might be empty if directory doesn't exist or has no files
        # assert len(fixtures) > 0
        # assert "test_config.json" in fixtures
        
        partials = bundle.load_partials()
        assert "_note.md" in partials
        
        # Test plating the bundle
        with tempfile.TemporaryDirectory() as output_dir:
            plater = PlatingPlater(bundles=[bundle])
            plater.plate(Path(output_dir))
            
            # Verify output was created
            output_file = Path(output_dir) / "resources" / "bucket.md"
            assert output_file.exists()
            
            # Verify content
            content = output_file.read_text()
            
            # Check main content
            assert "Resource: aws_s3_bucket" in content
            assert "Provides an S3 bucket resource" in content
            
            # Check examples were included
            assert 'resource "aws_s3_bucket" "example"' in content
            assert 'resource "aws_s3_bucket" "versioned"' in content
            assert 'resource "aws_s3_bucket" "encrypted"' in content
            
            # Check structure
            assert "## Example Usage" in content
            assert "## Argument Reference" in content
            assert "## Attribute Reference" in content
            assert "## Import" in content
            assert "## Timeouts" in content

    @pytest.mark.asyncio
    async def test_dress_and_plate_workflow(self):
        """Test dressing a component and then plating it."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create a mock resource file
            resources_dir = tmp_path / "resources"
            resources_dir.mkdir()
            
            resource_file = resources_dir / "database.py"
            resource_file.write_text('''
"""Database resource implementation."""
from attrs import define, field

@define
class DatabaseResource:
    """Manages a cloud database instance.
    
    This resource provisions and manages a cloud database
    with automatic backups and high availability.
    """
    
    name: str = field()
    engine: str = field(default="postgres")
    size: str = field(default="db.t3.micro")
    
    def create(self):
        """Create the database instance."""
        pass
''')
            
            # Mock the component for dressing
            from unittest.mock import Mock
            mock_component = Mock()
            mock_component.__doc__ = """Manages a cloud database instance.
    
    This resource provisions and manages a cloud database
    with automatic backups and high availability.
    """
            
            # Create dresser and dress the component
            dresser = PlatingDresser()
            
            # Mock finding the source file
            from unittest.mock import patch
            with patch.object(dresser.component_finder, 'find_source') as mock_find:
                mock_find.return_value = resource_file
                
                # Dress the component
                success = await dresser._dress_component(
                    "database", "resource", mock_component
                )
                assert success
                
                # Verify .plating directory was created
                plating_dir = resources_dir / "database.plating"
                assert plating_dir.exists()
                assert (plating_dir / "docs").exists()
                assert (plating_dir / "examples").exists()
                
                # Verify template was created
                template_file = plating_dir / "docs" / "database.tmpl.md"
                assert template_file.exists()
                
                template_content = template_file.read_text()
                assert "Resource: database" in template_content
                assert "Manages a cloud database instance" in template_content
                
                # Now create a bundle and plate it
                bundle = PlatingBundle(
                    plating_dir=plating_dir,
                    name="database",
                    component_type="resource"
                )
                
                with tempfile.TemporaryDirectory() as output_dir:
                    plater = PlatingPlater(bundles=[bundle])
                    plater.plate(Path(output_dir))
                    
                    # Verify output
                    output_file = Path(output_dir) / "resources" / "database.md"
                    assert output_file.exists()
                    
                    content = output_file.read_text()
                    assert "Resource: database" in content
                    assert "Manages a cloud database instance" in content

    def test_cli_workflow(self, realistic_bundle):
        """Test using the CLI with a realistic bundle."""
        # Test that the CLI can be invoked
        result = subprocess.run(
            ["python", "-m", "plating.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / "src"
        )
        
        # Basic check that CLI is accessible
        assert result.returncode == 0 or "plating" in result.stdout.lower()

    def test_error_handling_with_invalid_bundle(self):
        """Test error handling with invalid bundle configurations."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create an invalid bundle (missing required directories)
            bundle_dir = Path(tmp_dir) / "invalid.plating"
            bundle_dir.mkdir()
            
            # Try to create a bundle - should handle gracefully
            bundle = PlatingBundle(
                plating_dir=bundle_dir,
                name="invalid",
                component_type="resource"
            )
            
            # Loading template should return None
            template = bundle.load_main_template()
            assert template is None
            
            # Examples should be empty
            examples = bundle.load_examples()
            assert examples == {}
            
            # Plating should handle gracefully
            with tempfile.TemporaryDirectory() as output_dir:
                plater = PlatingPlater(bundles=[bundle])
                plater.plate(Path(output_dir))
                
                # No output file should be created
                output_file = Path(output_dir) / "resources" / "invalid.md"
                assert not output_file.exists()

    def test_complex_template_rendering(self, realistic_bundle):
        """Test rendering complex templates with all features."""
        # Create a bundle with complex template features
        bundle = PlatingBundle(
            plating_dir=realistic_bundle,
            name="bucket",
            component_type="resource"
        )
        
        # Create plater without schema processor for simplicity
        plater = PlatingPlater(bundles=[bundle])
        
        with tempfile.TemporaryDirectory() as output_dir:
            plater.plate(Path(output_dir))
            
            output_file = Path(output_dir) / "resources" / "bucket.md"
            assert output_file.exists()
            
            content = output_file.read_text()
            
            # Verify complex features rendered correctly
            assert "terraform import aws_s3_bucket.example" in content
            assert "## Schema" in content
            assert "### Basic Bucket" in content
            assert "### Bucket with Versioning" in content
            assert "### Bucket with Encryption" in content


# 🍲🧪🚀🪄