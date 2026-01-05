"""
Pattern generation routes.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

from lego_architect.patterns.library import PatternLibrary
from lego_architect.web.routes.builds import get_current_build, _part_to_response

router = APIRouter()


class BasePattern(BaseModel):
    start_x: int = 0
    start_z: int = 0
    width: int = 8
    length: int = 8
    color: int = 71  # Light gray


class WallPattern(BaseModel):
    start_x: int = 0
    start_z: int = 0
    start_y: int = 0
    length: int = 8
    height: int = 9  # 3 bricks high
    direction: Literal["x", "z"] = "x"
    color: int = 4  # Red
    style: Literal["solid", "window", "castle"] = "solid"


class ColumnPattern(BaseModel):
    x: int = 0
    z: int = 0
    height: int = 12  # 4 bricks high
    thickness: int = 2
    color: int = 15  # White


class WingPattern(BaseModel):
    start_x: int = 0
    start_z: int = 0
    start_y: int = 0
    length: int = 8
    sweep_angle: int = 15
    thickness: int = 1
    color: int = 1  # Blue


class PatternResponse(BaseModel):
    pattern_type: str
    parts_added: int
    part_ids: list[int]


@router.post("/base", response_model=PatternResponse)
async def create_base(pattern: BasePattern):
    """Create a base plate layer."""
    build = get_current_build()
    parts = PatternLibrary.create_base(
        build_state=build,
        start_x=pattern.start_x,
        start_z=pattern.start_z,
        width=pattern.width,
        length=pattern.length,
        color=pattern.color,
    )

    return PatternResponse(
        pattern_type="base",
        parts_added=len(parts),
        part_ids=[p.id for p in parts],
    )


@router.post("/wall", response_model=PatternResponse)
async def create_wall(pattern: WallPattern):
    """Create a wall structure."""
    build = get_current_build()
    parts = PatternLibrary.create_wall(
        build_state=build,
        start_x=pattern.start_x,
        start_z=pattern.start_z,
        start_y=pattern.start_y,
        length=pattern.length,
        height=pattern.height,
        direction=pattern.direction,
        color=pattern.color,
        style=pattern.style,
    )

    return PatternResponse(
        pattern_type="wall",
        parts_added=len(parts),
        part_ids=[p.id for p in parts],
    )


@router.post("/column", response_model=PatternResponse)
async def create_column(pattern: ColumnPattern):
    """Create a vertical column."""
    build = get_current_build()
    parts = PatternLibrary.create_column(
        build_state=build,
        x=pattern.x,
        z=pattern.z,
        height=pattern.height,
        thickness=pattern.thickness,
        color=pattern.color,
    )

    return PatternResponse(
        pattern_type="column",
        parts_added=len(parts),
        part_ids=[p.id for p in parts],
    )


@router.post("/wing", response_model=PatternResponse)
async def create_wing(pattern: WingPattern):
    """Create a wing structure."""
    build = get_current_build()
    parts = PatternLibrary.create_wing(
        build_state=build,
        start_x=pattern.start_x,
        start_z=pattern.start_z,
        start_y=pattern.start_y,
        length=pattern.length,
        sweep_angle=pattern.sweep_angle,
        thickness=pattern.thickness,
        color=pattern.color,
    )

    return PatternResponse(
        pattern_type="wing",
        parts_added=len(parts),
        part_ids=[p.id for p in parts],
    )
