"""
AI generation routes with feature flag support and graceful degradation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from lego_architect.config import Config
from lego_architect.web.routes.builds import get_current_build, _part_to_response

router = APIRouter()


class GenerateRequest(BaseModel):
    """Request model for AI generation."""
    prompt: str
    size: Optional[str] = None  # "small", "medium", "large"
    color_scheme: Optional[str] = None
    style: Optional[str] = None
    clear_existing: bool = True


class GenerateResponse(BaseModel):
    """Response model for AI generation."""
    success: bool
    message: str
    part_count: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    metrics: Optional[Dict[str, Any]] = None


class AIStatusResponse(BaseModel):
    """Response model for AI feature status."""
    ai_enabled: bool
    ai_available: bool
    message: str
    model: Optional[str] = None


@router.get("/status", response_model=AIStatusResponse)
async def get_ai_status():
    """
    Check if AI features are enabled and available.

    Returns the current status of AI features, including whether they're
    enabled in configuration and whether the API key is properly set.
    """
    enabled = Config.ENABLE_AI_FEATURES
    available = Config.is_ai_available()

    if not enabled:
        return AIStatusResponse(
            ai_enabled=False,
            ai_available=False,
            message="AI features are disabled. Set ENABLE_AI_FEATURES=true to enable.",
        )

    if not available:
        return AIStatusResponse(
            ai_enabled=True,
            ai_available=False,
            message="AI features are enabled but ANTHROPIC_API_KEY is not configured.",
        )

    return AIStatusResponse(
        ai_enabled=True,
        ai_available=True,
        message="AI features are available and ready.",
        model=Config.DEFAULT_MODEL,
    )


@router.post("", response_model=GenerateResponse)
async def generate_build(request: GenerateRequest):
    """
    Generate a LEGO build from a natural language prompt using AI.

    This endpoint requires AI features to be enabled and properly configured.
    If AI is unavailable, it returns a graceful error message.
    """
    # Check feature flag first
    if not Config.ENABLE_AI_FEATURES:
        return GenerateResponse(
            success=False,
            message="AI features are currently disabled. Use manual building or pattern tools instead.",
            errors=["AI features disabled via ENABLE_AI_FEATURES=false"],
        )

    # Check if AI is actually available
    if not Config.is_ai_available():
        return GenerateResponse(
            success=False,
            message="AI features are enabled but not configured. Please set ANTHROPIC_API_KEY.",
            errors=["ANTHROPIC_API_KEY not configured"],
        )

    # Import orchestrator only when needed (lazy loading)
    try:
        from lego_architect.orchestrator import BuildOrchestrator
    except ImportError as e:
        return GenerateResponse(
            success=False,
            message="AI generation module not available.",
            errors=[f"Import error: {str(e)}"],
        )

    # Get or create build state
    build_state = get_current_build()

    # Clear existing build if requested
    if request.clear_existing:
        build_state.parts.clear()
        build_state._next_id = 1

    # Build enriched prompt with clarifications
    enriched_prompt = request.prompt
    clarifications = {}

    if request.size:
        clarifications["What size should the build be?"] = request.size
    if request.color_scheme:
        clarifications["What color scheme should be used?"] = request.color_scheme
    if request.style:
        clarifications["What style should it be?"] = request.style

    try:
        # Create orchestrator and generate
        orchestrator = BuildOrchestrator()

        if clarifications:
            enriched_prompt = orchestrator.enrich_prompt(request.prompt, clarifications)

        # Generate the build
        result = orchestrator.generate_build(
            user_prompt=enriched_prompt,
            build_state=build_state,
            max_refinement_iterations=3,
            auto_refine=True,
        )

        # Build metrics response
        metrics = None
        if result.metrics:
            metrics = {
                "duration_seconds": result.metrics.duration_seconds,
                "total_tokens": result.metrics.total_tokens,
                "cached_tokens": result.metrics.cached_tokens,
                "total_cost_usd": result.metrics.total_cost_usd,
                "iterations": result.metrics.total_iterations,
            }

        return GenerateResponse(
            success=result.success,
            message="Build generated successfully!" if result.success else "Build generation completed with issues.",
            part_count=len(build_state.parts),
            errors=result.errors,
            warnings=result.warnings,
            metrics=metrics,
        )

    except Exception as e:
        # Graceful degradation - don't crash, return error response
        return GenerateResponse(
            success=False,
            message=f"AI generation failed: {str(e)}",
            part_count=len(build_state.parts),
            errors=[str(e)],
        )
