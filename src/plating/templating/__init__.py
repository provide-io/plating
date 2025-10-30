#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Template processing and rendering module."""

from plating.templating.engine import AsyncTemplateEngine, template_engine
from plating.templating.filters import schema_to_markdown
from plating.templating.functions import SchemaRenderer
from plating.templating.generator import TemplateGenerator
from plating.templating.metadata import TemplateMetadataExtractor
from plating.templating.processor import TemplateProcessor

__all__ = [
    "AsyncTemplateEngine",
    "SchemaRenderer",
    "TemplateGenerator",
    "TemplateMetadataExtractor",
    "TemplateProcessor",
    "schema_to_markdown",
    "template_engine",
]

# 🍽️📖🔚
