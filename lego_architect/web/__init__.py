"""
Web interface for LEGO Architect.

Provides a FastAPI-based REST API and 3D visualization frontend.
"""

from lego_architect.web.app import create_app

__all__ = ["create_app"]
