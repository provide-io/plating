# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for guide template processing functionality."""

from pathlib import Path

import pytest

from plating.core.guide_processor import (
    GuideProcessingError,
    TemplateFile,
    extract_frontmatter_field,
    parse_frontmatter,
    parse_template_file,
    process_template_file,
    validate_template_output_path,
)


class TestParseFrontmatter:
    """Tests for frontmatter parsing."""

    def test_parse_valid_frontmatter(self):
        """Test parsing content with valid frontmatter."""
        content = """---
title: Test
template_output: index.md
---
# Body content"""
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter.startswith("---")
        assert "template_output: index.md" in frontmatter
        assert body.strip() == "# Body content"

    def test_parse_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "# Just content"
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter == ""
        assert body == content

    def test_parse_incomplete_frontmatter(self):
        """Test parsing content with incomplete frontmatter (no closing delimiter)."""
        content = """---
title: Test
# Body content"""
        frontmatter, body = parse_frontmatter(content)
        assert frontmatter == ""
        assert body == content

    def test_parse_empty_frontmatter(self):
        """Test parsing content with empty frontmatter."""
        content = """---
---
# Body content"""
        frontmatter, body = parse_frontmatter(content)
        assert "---" in frontmatter
        assert body.strip() == "# Body content"


class TestExtractFrontmatterField:
    """Tests for extracting fields from frontmatter."""

    def test_extract_existing_field(self):
        """Test extracting a field that exists."""
        frontmatter = """---
title: Test
template_output: index.md
---"""
        value = extract_frontmatter_field(frontmatter, "template_output")
        assert value == "index.md"

    def test_extract_missing_field(self):
        """Test extracting a field that doesn't exist."""
        frontmatter = """---
title: Test
---"""
        value = extract_frontmatter_field(frontmatter, "template_output")
        assert value is None

    def test_extract_from_empty_frontmatter(self):
        """Test extracting from empty frontmatter."""
        value = extract_frontmatter_field("", "template_output")
        assert value is None

    def test_extract_field_without_delimiters(self):
        """Test extracting field from frontmatter without delimiters."""
        frontmatter = """title: Test
template_output: index.md"""
        value = extract_frontmatter_field(frontmatter, "template_output")
        assert value == "index.md"

    def test_extract_non_string_field(self):
        """Test extracting non-string field values."""
        frontmatter = """---
page_number: 42
enabled: true
---"""
        assert extract_frontmatter_field(frontmatter, "page_number") == "42"
        assert extract_frontmatter_field(frontmatter, "enabled") == "True"


class TestValidateTemplateOutputPath:
    """Tests for template output path validation."""

    def test_validate_valid_path(self):
        """Test validating a valid relative path."""
        path = validate_template_output_path("index.md", Path("test.tmpl.md"))
        assert path == Path("index.md")

    def test_validate_nested_path(self):
        """Test validating a nested relative path."""
        path = validate_template_output_path("resources/index.md", Path("test.tmpl.md"))
        assert path == Path("resources/index.md")

    def test_validate_empty_path(self):
        """Test that empty paths are rejected."""
        with pytest.raises(GuideProcessingError, match="empty"):
            validate_template_output_path("", Path("test.tmpl.md"))

    def test_validate_absolute_path(self):
        """Test that absolute paths are rejected."""
        with pytest.raises(GuideProcessingError, match="absolute"):
            validate_template_output_path("/etc/passwd", Path("test.tmpl.md"))

    def test_validate_path_traversal(self):
        """Test that path traversal attempts are rejected."""
        with pytest.raises(GuideProcessingError, match="traversal"):
            validate_template_output_path("../../../etc/passwd", Path("test.tmpl.md"))

        with pytest.raises(GuideProcessingError, match="traversal"):
            validate_template_output_path("../../secret.md", Path("test.tmpl.md"))

    def test_validate_path_with_parent_refs_within_docs(self):
        """Test paths with parent refs that stay within docs."""
        # This should work - goes up then back down, staying within docs
        path = validate_template_output_path("subdir/../index.md", Path("test.tmpl.md"))
        assert path == Path("subdir/../index.md")

    def test_validate_invalid_characters(self):
        """Test that paths with invalid characters are rejected."""
        invalid_paths = [
            "index<test>.md",
            "index:test.md",
            'index"test.md',
            "index|test.md",
            "index?test.md",
            "index*test.md",
        ]
        for invalid_path in invalid_paths:
            with pytest.raises(GuideProcessingError, match="invalid characters"):
                validate_template_output_path(invalid_path, Path("test.tmpl.md"))

    def test_validate_non_markdown_extension(self):
        """Test that non-.md extensions are rejected."""
        with pytest.raises(GuideProcessingError, match="must end with .md"):
            validate_template_output_path("index.html", Path("test.tmpl.md"))

        with pytest.raises(GuideProcessingError, match="must end with .md"):
            validate_template_output_path("README.txt", Path("test.tmpl.md"))


class TestParseTemplateFile:
    """Tests for parsing template files."""

    def test_parse_valid_template(self, tmp_path):
        """Test parsing a valid template file."""
        tmpl_file = tmp_path / "test.tmpl.md"
        tmpl_file.write_text("""---
page_title: Test
template_output: index.md
---
# Test Content""")

        template = parse_template_file(tmpl_file)
        assert template.source_path == tmpl_file
        assert template.template_output == "index.md"
        assert "page_title: Test" in template.frontmatter
        assert "# Test Content" in template.content

    def test_parse_template_without_frontmatter(self, tmp_path):
        """Test that templates without frontmatter are rejected."""
        tmpl_file = tmp_path / "test.tmpl.md"
        tmpl_file.write_text("# Just content")

        with pytest.raises(GuideProcessingError, match="must have YAML frontmatter"):
            parse_template_file(tmpl_file)

    def test_parse_template_without_template_output(self, tmp_path):
        """Test that templates without template_output are rejected."""
        tmpl_file = tmp_path / "test.tmpl.md"
        tmpl_file.write_text("""---
page_title: Test
---
# Content""")

        with pytest.raises(GuideProcessingError, match="must have 'template_output' field"):
            parse_template_file(tmpl_file)

    def test_parse_template_with_invalid_path(self, tmp_path):
        """Test that templates with invalid paths are rejected."""
        tmpl_file = tmp_path / "test.tmpl.md"
        tmpl_file.write_text("""---
page_title: Test
template_output: ../../../etc/passwd
---
# Content""")

        with pytest.raises(GuideProcessingError, match="traversal"):
            parse_template_file(tmpl_file)

    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing a file that doesn't exist.

        Note: safe_read_text returns empty string for nonexistent files,
        so this tests that empty content triggers frontmatter error.
        """
        tmpl_file = tmp_path / "nonexistent.tmpl.md"

        with pytest.raises(GuideProcessingError, match="must have YAML frontmatter"):
            parse_template_file(tmpl_file)

    def test_parse_template_with_nested_output(self, tmp_path):
        """Test parsing template with nested output path."""
        tmpl_file = tmp_path / "test.tmpl.md"
        tmpl_file.write_text("""---
page_title: Test
template_output: resources/index.md
---
# Resource Index""")

        template = parse_template_file(tmpl_file)
        assert template.template_output == "resources/index.md"


class TestProcessTemplateFile:
    """Tests for processing template files."""

    def test_process_template_to_index(self, tmp_path):
        """Test processing a template to index.md."""
        source_file = tmp_path / "source" / "test.tmpl.md"
        source_file.parent.mkdir()
        source_file.write_text("""---
page_title: Test
template_output: index.md
---
# Test Content""")

        template = parse_template_file(source_file)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result_path = process_template_file(template, output_dir)
        assert result_path == output_dir / "index.md"
        assert result_path.exists()
        assert "# Test Content" in result_path.read_text()

    def test_process_template_to_nested_path(self, tmp_path):
        """Test processing a template to a nested path."""
        source_file = tmp_path / "source" / "test.tmpl.md"
        source_file.parent.mkdir()
        source_file.write_text("""---
page_title: Test
template_output: resources/index.md
---
# Resource Index""")

        template = parse_template_file(source_file)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result_path = process_template_file(template, output_dir)
        assert result_path == output_dir / "resources" / "index.md"
        assert result_path.exists()
        assert result_path.parent.exists()

    def test_process_template_preserves_frontmatter(self, tmp_path):
        """Test that processing preserves frontmatter in output."""
        source_file = tmp_path / "source" / "test.tmpl.md"
        source_file.parent.mkdir()
        content = """---
page_title: Test Provider
description: A test
template_output: index.md
---
# Provider Content"""
        source_file.write_text(content)

        template = parse_template_file(source_file)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result_path = process_template_file(template, output_dir)
        output_content = result_path.read_text()
        assert "page_title: Test Provider" in output_content
        assert "template_output: index.md" in output_content
        assert "# Provider Content" in output_content

    def test_process_template_creates_parent_dirs(self, tmp_path):
        """Test that parent directories are created automatically."""
        source_file = tmp_path / "source" / "test.tmpl.md"
        source_file.parent.mkdir()
        source_file.write_text("""---
template_output: deeply/nested/path/index.md
---
# Content""")

        template = parse_template_file(source_file)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result_path = process_template_file(template, output_dir)
        assert result_path.exists()
        assert result_path.parent.name == "path"
        assert result_path.parent.parent.name == "nested"


class TestGuideProcessingError:
    """Tests for GuideProcessingError."""

    def test_error_without_file_path(self):
        """Test error message without file path."""
        error = GuideProcessingError("Test error")
        assert error.to_user_message() == "Test error"

    def test_error_with_file_path(self):
        """Test error message with file path."""
        error = GuideProcessingError("Test error", file_path=Path("test.tmpl.md"))
        message = error.to_user_message()
        assert "Test error" in message
        assert "test.tmpl.md" in message


class TestTemplateFile:
    """Tests for TemplateFile namedtuple."""

    def test_template_file_creation(self):
        """Test creating a TemplateFile."""
        template = TemplateFile(
            source_path=Path("test.tmpl.md"),
            template_output="index.md",
            frontmatter="---\ntitle: Test\n---",
            content="Full content",
        )
        assert template.source_path == Path("test.tmpl.md")
        assert template.template_output == "index.md"
        assert template.frontmatter == "---\ntitle: Test\n---"
        assert template.content == "Full content"
