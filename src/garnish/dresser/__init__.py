#
# garnish/dresser/__init__.py
#
"""Dressing system for adding .garnish directories to components."""

from garnish.dresser.api import dress_components, dress_missing_components
from garnish.dresser.dresser import GarnishDresser

__all__ = [
    "GarnishDresser",
    "dress_components",
    "dress_missing_components",
]


# 🍲🥄👗🪄
