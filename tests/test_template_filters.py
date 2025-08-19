"""
Tests for template filters.
"""
import pytest
from garnish.template_filters import TemplateFilters


class TestTemplateFilters:
    """Tests for template filters."""

    @pytest.fixture
    def filters(self):
        """Get template filters."""
        return TemplateFilters.get_filters()

    def test_get_filters(self):
        """Test that get_filters returns all expected filters."""
        filters = TemplateFilters.get_filters()
        
        expected_filters = [
            "snake_case", "kebab_case", "pascal_case", "camel_case",
            "upper_snake", "title_case", "singular", "plural",
            "truncate", "wrap", "indent", "markdown_table"
        ]
        
        for filter_name in expected_filters:
            assert filter_name in filters
            assert callable(filters[filter_name])

    def test_snake_case(self, filters):
        """Test snake_case filter."""
        snake_case = filters["snake_case"]
        
        assert snake_case("HelloWorld") == "hello_world"
        assert snake_case("hello-world") == "hello_world"
        assert snake_case("hello world") == "hello_world"
        assert snake_case("HELLO_WORLD") == "hello_world"
        assert snake_case("helloWorld") == "hello_world"

    def test_kebab_case(self, filters):
        """Test kebab_case filter."""
        kebab_case = filters["kebab_case"]
        
        assert kebab_case("HelloWorld") == "hello-world"
        assert kebab_case("hello_world") == "hello-world"
        assert kebab_case("hello world") == "hello-world"
        assert kebab_case("HELLO_WORLD") == "hello-world"

    def test_pascal_case(self, filters):
        """Test pascal_case filter."""
        pascal_case = filters["pascal_case"]
        
        assert pascal_case("hello_world") == "HelloWorld"
        assert pascal_case("hello-world") == "HelloWorld"
        assert pascal_case("hello world") == "HelloWorld"
        assert pascal_case("helloWorld") == "HelloWorld"

    def test_camel_case(self, filters):
        """Test camel_case filter."""
        camel_case = filters["camel_case"]
        
        assert camel_case("hello_world") == "helloWorld"
        assert camel_case("hello-world") == "helloWorld"
        assert camel_case("hello world") == "helloWorld"
        assert camel_case("HelloWorld") == "helloWorld"

    def test_upper_snake(self, filters):
        """Test upper_snake filter."""
        upper_snake = filters["upper_snake"]
        
        assert upper_snake("hello_world") == "HELLO_WORLD"
        assert upper_snake("hello-world") == "HELLO_WORLD"
        assert upper_snake("HelloWorld") == "HELLO_WORLD"
        assert upper_snake("hello world") == "HELLO_WORLD"

    def test_title_case(self, filters):
        """Test title_case filter."""
        title_case = filters["title_case"]
        
        assert title_case("hello_world") == "Hello World"
        assert title_case("hello-world") == "Hello World"
        assert title_case("HelloWorld") == "Hello World"
        assert title_case("HELLO_WORLD") == "Hello World"

    def test_singular(self, filters):
        """Test singular filter."""
        singular = filters["singular"]
        
        assert singular("users") == "user"
        assert singular("categories") == "category"
        assert singular("boxes") == "box"
        assert singular("user") == "user"  # Already singular
        assert singular("data") == "data"  # Uncountable

    def test_plural(self, filters):
        """Test plural filter."""
        plural = filters["plural"]
        
        assert plural("user") == "users"
        assert plural("category") == "categories"
        assert plural("box") == "boxes"
        assert plural("users") == "users"  # Already plural
        assert plural("data") == "data"  # Uncountable

    def test_truncate(self, filters):
        """Test truncate filter."""
        truncate = filters["truncate"]
        
        short_text = "Short text"
        long_text = "This is a very long text that should be truncated to a specific length"
        
        assert truncate(short_text, 20) == short_text
        assert truncate(long_text, 20) == "This is a very lo..."
        assert truncate(long_text, 30) == "This is a very long text th..."
        assert len(truncate(long_text, 20)) == 20

    def test_wrap(self, filters):
        """Test wrap filter."""
        wrap = filters["wrap"]
        
        text = "This is a long text that should be wrapped to multiple lines when it exceeds the specified width."
        
        wrapped = wrap(text, 30)
        lines = wrapped.split('\n')
        
        for line in lines:
            assert len(line) <= 30
        
        # Test with short text
        short = "Short text"
        assert wrap(short, 30) == short

    def test_indent(self, filters):
        """Test indent filter."""
        indent = filters["indent"]
        
        text = "Line 1\nLine 2\nLine 3"
        
        # Test with 2 spaces
        indented = indent(text, 2)
        expected = "  Line 1\n  Line 2\n  Line 3"
        assert indented == expected
        
        # Test with 4 spaces
        indented = indent(text, 4)
        expected = "    Line 1\n    Line 2\n    Line 3"
        assert indented == expected
        
        # Test with prefix
        indented = indent(text, 0, "> ")
        expected = "> Line 1\n> Line 2\n> Line 3"
        assert indented == expected

    def test_markdown_table(self, filters):
        """Test markdown_table filter."""
        markdown_table = filters["markdown_table"]
        
        data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "London"},
            {"name": "Charlie", "age": 35, "city": "Paris"}
        ]
        
        table = markdown_table(data)
        
        # Check header row
        assert "| name | age | city |" in table
        # Check separator row
        assert "|------|-----|------|" in table
        # Check data rows
        assert "| Alice | 30 | New York |" in table
        assert "| Bob | 25 | London |" in table
        assert "| Charlie | 35 | Paris |" in table
        
        # Test empty data
        assert markdown_table([]) == ""
        
        # Test data with missing keys
        incomplete_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "city": "London"}
        ]
        
        table = markdown_table(incomplete_data)
        assert "| name | age | city |" in table
        assert "| Alice | 30 |  |" in table
        assert "| Bob |  | London |" in table