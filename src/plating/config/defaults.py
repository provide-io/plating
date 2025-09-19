from __future__ import annotations

"""Centralized default values for plating configuration.
All defaults are defined here instead of inline in field definitions.
"""

# =================================
# Template generation defaults
# =================================
DEFAULT_EXAMPLE_PLACEHOLDER = ""  # Empty string when no example is available
DEFAULT_FALLBACK_SIGNATURE_FORMAT = "`{function_name}(input)`"
DEFAULT_FALLBACK_ARGUMENTS_MARKDOWN = "- `input`: The input value to process"

# =================================
# Test execution defaults
# =================================
DEFAULT_TEST_TIMEOUT = 120
DEFAULT_TEST_PARALLEL = 4

# =================================
# Directory defaults
# =================================
DEFAULT_OUTPUT_DIR = "./docs"
DEFAULT_RESOURCES_DIR = "./resources"
DEFAULT_DATA_SOURCES_DIR = "./data_sources"
DEFAULT_FUNCTIONS_DIR = "./functions"

# =================================
# Environment variable names
# =================================
ENV_PLATING_EXAMPLE_PLACEHOLDER = "PLATING_EXAMPLE_PLACEHOLDER"
ENV_PLATING_FALLBACK_SIGNATURE = "PLATING_FALLBACK_SIGNATURE"
ENV_PLATING_FALLBACK_ARGUMENTS = "PLATING_FALLBACK_ARGUMENTS"
ENV_GARNISH_TF_BINARY = "GARNISH_TF_BINARY"
ENV_TF_PLUGIN_CACHE_DIR = "TF_PLUGIN_CACHE_DIR"
ENV_GARNISH_TEST_TIMEOUT = "GARNISH_TEST_TIMEOUT"
ENV_GARNISH_TEST_PARALLEL = "GARNISH_TEST_PARALLEL"
ENV_GARNISH_OUTPUT_DIR = "GARNISH_OUTPUT_DIR"

# =================================
# Package discovery defaults
# =================================
DEFAULT_PACKAGE_NAME = "pyvider.components"

# =================================
# Template metadata constants
# =================================
# Function types for metadata generation
FUNCTION_TYPE_STRING_TRANSFORM = "string_transform"
FUNCTION_TYPE_MATH = "math"
FUNCTION_TYPE_STRING_MANIPULATION = "string_manipulation"
FUNCTION_TYPE_GENERIC = "generic"

# Common function names by category
STRING_TRANSFORM_FUNCTIONS = frozenset({"upper", "lower", "title"})
MATH_FUNCTIONS = frozenset({"add", "subtract", "multiply", "divide"})
STRING_MANIPULATION_FUNCTIONS = frozenset({"join", "split", "replace"})

# =================================
# Template file patterns
# =================================
TEMPLATE_FILE_PATTERN = "*.tmpl.md"
MAIN_TEMPLATE_FILE = "main.md.j2"

# =================================
# Component type constants
# =================================
COMPONENT_TYPE_FUNCTION = "function"
COMPONENT_TYPE_RESOURCE = "resource"
COMPONENT_TYPE_DATA_SOURCE = "data_source"

# =================================
# Jinja2 template engine defaults
# =================================
DEFAULT_JINJA2_TRIM_BLOCKS = True
DEFAULT_JINJA2_LSTRIP_BLOCKS = True
DEFAULT_JINJA2_KEEP_TRAILING_NEWLINE = True
