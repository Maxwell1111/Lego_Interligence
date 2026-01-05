"""
Configuration management for LEGO Architect.

Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    """Application configuration."""

    # Anthropic API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Rebrickable API (for Global Build Library)
    REBRICKABLE_API_KEY: str = os.getenv("REBRICKABLE_API_KEY", "")
    REBRICKABLE_BASE_URL: str = "https://rebrickable.com/api/v3"

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "lego_architect")

    # LDraw
    LDRAW_PATH: Optional[Path] = (
        Path(os.getenv("LDRAW_PATH")) if os.getenv("LDRAW_PATH") else None
    )

    # Generation Settings
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "claude-opus-4-5-20251101")
    REFINEMENT_MODEL: str = os.getenv("REFINEMENT_MODEL", "claude-haiku-3-5-20241022")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "8192"))

    # Cost Optimization
    ENABLE_PROMPT_CACHING: bool = os.getenv("ENABLE_PROMPT_CACHING", "true").lower() == "true"
    CACHE_TTL_MINUTES: int = int(os.getenv("CACHE_TTL_MINUTES", "30"))

    # Feature Flags
    ENABLE_AI_FEATURES: bool = os.getenv("ENABLE_AI_FEATURES", "true").lower() == "true"

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if cls.ENABLE_AI_FEATURES and not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Please set it in .env file or environment variable, "
                "or set ENABLE_AI_FEATURES=false to disable AI features."
            )

    @classmethod
    def is_ai_available(cls) -> bool:
        """Check if AI features are available and properly configured."""
        return cls.ENABLE_AI_FEATURES and bool(cls.ANTHROPIC_API_KEY)

    @classmethod
    def is_library_available(cls) -> bool:
        """Check if library features are available and properly configured."""
        return bool(cls.REBRICKABLE_API_KEY)


# Global config instance
config = Config()
