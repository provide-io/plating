#
# plating/dresser/__init__.py
#
"""Dressing system for adding .plating directories to components."""

from plating.dresser.api import dress_components, dress_missing_components
from plating.dresser.dresser import PlatingDresser

__all__ = [
    "PlatingDresser",
    "dress_components",
    "dress_missing_components",
]


# 🍲🥄👗🪄
