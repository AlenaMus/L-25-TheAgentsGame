"""
Game Orchestrator Package for Even/Odd League Tournament.

This package implements the master controller for managing the complete
tournament lifecycle including agent startup, health monitoring, and
tournament flow execution.
"""

__version__ = "1.0.0"
__author__ = "AI Development Course"

from .cli import main

__all__ = [
    "main",
]
