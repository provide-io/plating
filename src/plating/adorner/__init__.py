#
# plating/adorner/__init__.py
#
"""Adorning system for adding .plating directories to components."""

from plating.adorner.api import adorn_components, adorn_missing_components
from plating.adorner.adorner import PlatingAdorner

__all__ = [
    "PlatingAdorner",
    "adorn_components",
    "adorn_missing_components",
]


# 🍲🥄👗🪄
