"""
Validation routes.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from lego_architect.validation.validator import PhysicalValidator
from lego_architect.web.routes.builds import get_current_build

router = APIRouter()


class ValidationResponse(BaseModel):
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]
    part_count: int
    dimensions: tuple[int, int, int]


@router.get("", response_model=ValidationResponse)
async def validate_build():
    """Validate the current build."""
    build = get_current_build()
    validator = PhysicalValidator()
    result = validator.validate_build(build)

    return ValidationResponse(
        is_valid=result.is_valid,
        errors=result.errors,
        warnings=result.warnings,
        suggestions=result.suggestions,
        part_count=len(build.parts),
        dimensions=build.get_dimensions(),
    )
