"""
League Manager Package for Even/Odd Tournament.

This package implements the top-level tournament orchestrator that manages
player and referee registration, scheduling, standings, and match coordination.
"""

__version__ = "1.0.0"
__author__ = "AI Development Course"

from .main import main
from .config import Config

__all__ = [
    "main",
    "Config",
]
