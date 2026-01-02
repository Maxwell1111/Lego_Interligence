"""
AI-Powered LEGO Architect

A Python-based CLI tool that transforms natural language prompts into complete,
physically valid LEGO builds using Claude AI.
"""

__version__ = "1.0.0"
__author__ = "LEGO Architect Team"

from lego_architect.core.data_structures import (
    BuildState,
    PlacedPart,
    StudCoordinate,
    Rotation,
    PartDimensions,
    ValidationResult,
)

__all__ = [
    "BuildState",
    "PlacedPart",
    "StudCoordinate",
    "Rotation",
    "PartDimensions",
    "ValidationResult",
]
