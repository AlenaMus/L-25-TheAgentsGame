"""
Referee Agent Package for Even/Odd League Tournament.

This package implements a referee agent that orchestrates individual
Even/Odd game matches using the MCP protocol.
"""

__version__ = "1.0.0"
__author__ = "AI Development Course"

from .main import main
from .config import Config

__all__ = [
    "main",
    "Config",
]
