"""
Build management routes.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from lego_architect.core.data_structures import (
    BuildState,
    StudCoordinate,
    Rotation,
    PartDimensions,
)

router = APIRouter()

# In-memory build storage (single build for simplicity)
_current_build: BuildState = BuildState(name="My LEGO Build")


# Pydantic models for API
class PartPlacement(BaseModel):
    part_id: str
    part_name: str
    color: int
    x: int
    z: int
    y: int
    rotation: int = 0
    width: int
    length: int
    height: int


class PartResponse(BaseModel):
    id: int
    part_id: str
    part_name: str
    color: int
    x: int
    z: int
    y: int
    rotation: int
    width: int
    length: int
    height: int


class BuildResponse(BaseModel):
    name: str
    description: str
    part_count: int
    dimensions: tuple[int, int, int]
    parts: List[PartResponse]


class BuildMetadata(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


def _part_to_response(part) -> PartResponse:
    """Convert PlacedPart to API response."""
    min_c, max_c = part.get_bounding_box()
    return PartResponse(
        id=part.id,
        part_id=part.part_id,
        part_name=part.part_name,
        color=part.color,
        x=part.position.stud_x,
        z=part.position.stud_z,
        y=part.position.plate_y,
        rotation=part.rotation.degrees,
        width=part.dimensions.studs_width,
        length=part.dimensions.studs_length,
        height=part.dimensions.plates_height,
    )


@router.get("", response_model=BuildResponse)
async def get_build():
    """Get current build state."""
    return BuildResponse(
        name=_current_build.name,
        description=_current_build.description,
        part_count=len(_current_build.parts),
        dimensions=_current_build.get_dimensions(),
        parts=[_part_to_response(p) for p in _current_build.parts],
    )


@router.post("/clear")
async def clear_build():
    """Clear all parts from build."""
    global _current_build
    _current_build = BuildState(name=_current_build.name)
    return {"message": "Build cleared", "part_count": 0}


@router.patch("/metadata")
async def update_metadata(metadata: BuildMetadata):
    """Update build metadata."""
    if metadata.name is not None:
        _current_build.name = metadata.name
    if metadata.description is not None:
        _current_build.description = metadata.description
    return {"name": _current_build.name, "description": _current_build.description}


@router.post("/parts", response_model=PartResponse)
async def add_part(part: PartPlacement):
    """Add a part to the build."""
    if part.rotation not in [0, 90, 180, 270]:
        raise HTTPException(status_code=400, detail="Rotation must be 0, 90, 180, or 270")

    placed = _current_build.add_part(
        part_id=part.part_id,
        part_name=part.part_name,
        color=part.color,
        position=StudCoordinate(part.x, part.z, part.y),
        rotation=Rotation(part.rotation),
        dimensions=PartDimensions(part.width, part.length, part.height),
    )

    return _part_to_response(placed)


@router.delete("/parts/{part_id}")
async def remove_part(part_id: int):
    """Remove a part from the build."""
    if _current_build.remove_part(part_id):
        return {"message": f"Part {part_id} removed", "part_count": len(_current_build.parts)}
    raise HTTPException(status_code=404, detail=f"Part {part_id} not found")


@router.get("/parts/{part_id}", response_model=PartResponse)
async def get_part(part_id: int):
    """Get a specific part by ID."""
    part = _current_build.get_part_by_id(part_id)
    if part is None:
        raise HTTPException(status_code=404, detail=f"Part {part_id} not found")
    return _part_to_response(part)


# Expose build state for other routes
def get_current_build() -> BuildState:
    """Get the current build state."""
    return _current_build
