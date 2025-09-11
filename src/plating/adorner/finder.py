#
# plating/adorner/finder.py
#
"""Component source file finding utilities."""

import inspect
from pathlib import Path
from typing import Any


class ComponentFinder:
    """Finds source files for components."""

    async def find_source(self, component_class: Any) -> Path | None:
        """Find the source file for a component class."""
        try:
            source_file = inspect.getfile(component_class)
            return Path(source_file)
        except Exception:
            return None


# 🍲🥄🔍🪄
