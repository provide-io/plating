#
# plating/templating/__init__.py
#
"""Template processing and rendering module."""

from plating.templating.engine import AsyncTemplateEngine, template_engine
from plating.templating.filters import schema_to_markdown
from plating.templating.functions import SchemaRenderer
from plating.templating.generator import TemplateGenerator
from plating.templating.metadata import TemplateMetadataExtractor
from plating.templating.processor import TemplateProcessor

__all__ = [
    # Engine
    "AsyncTemplateEngine",
    "template_engine",
    # Processor
    "TemplateProcessor",
    # Generator
    "TemplateGenerator",
    # Metadata
    "TemplateMetadataExtractor",
    # Functions
    "SchemaRenderer",
    # Filters
    "schema_to_markdown",
]
