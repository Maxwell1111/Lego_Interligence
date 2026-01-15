"""
Library routes for browsing and importing LEGO sets from Rebrickable.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from lego_architect.config import Config
from lego_architect.services.lego_library_service import (
    LegoLibraryService,
    SetNotFoundError,
    RateLimitError,
    LibraryServiceError,
    get_part_info,
    map_color,
)
from lego_architect.web.routes.builds import get_current_build
from lego_architect.core.data_structures import (
    StudCoordinate,
    Rotation,
    PartDimensions,
)

router = APIRouter()


# Pydantic models for API
class LibraryStatusResponse(BaseModel):
    """Response for library status check."""
    library_available: bool
    message: str


class SetInfoResponse(BaseModel):
    """Set information for search results."""
    set_num: str
    name: str
    year: int
    theme_id: int
    num_parts: int
    img_url: Optional[str] = None


class SetSearchParams(BaseModel):
    """Parameters for set search."""
    search: Optional[str] = None
    theme_id: Optional[int] = None
    min_year: Optional[int] = Field(None, ge=1949, le=2030)
    max_year: Optional[int] = Field(None, ge=1949, le=2030)
    min_parts: Optional[int] = Field(None, ge=0)
    max_parts: Optional[int] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class SetSearchResponse(BaseModel):
    """Response for set search."""
    success: bool
    sets: List[SetInfoResponse] = []
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False
    error: Optional[str] = None


class SetDetailResponse(BaseModel):
    """Detailed set information."""
    success: bool
    set_num: str = ""
    name: str = ""
    year: int = 0
    theme_id: int = 0
    num_parts: int = 0
    img_url: Optional[str] = None
    set_url: Optional[str] = None
    error: Optional[str] = None


class PartInfoResponse(BaseModel):
    """Part information from inventory."""
    part_num: str
    part_name: str
    color_id: int
    color_name: str
    color_rgb: str
    quantity: int
    img_url: Optional[str] = None
    is_spare: bool = False
    is_mappable: bool = False  # True if we can import this part


class SetInventoryResponse(BaseModel):
    """Response for set inventory."""
    success: bool
    set_num: str = ""
    parts: List[PartInfoResponse] = []
    total_parts: int = 0
    unique_parts: int = 0
    mappable_parts: int = 0  # Parts we can import
    error: Optional[str] = None


class ThemeResponse(BaseModel):
    """Theme information."""
    id: int
    name: str
    parent_id: Optional[int] = None


class ThemeListResponse(BaseModel):
    """Response for themes list."""
    success: bool
    themes: List[ThemeResponse] = []
    error: Optional[str] = None


class ImportResponse(BaseModel):
    """Response for import operation."""
    success: bool
    message: str
    build_name: str = ""
    parts_imported: int = 0
    parts_skipped: int = 0
    warnings: List[str] = []


@router.get("/status", response_model=LibraryStatusResponse)
async def get_library_status():
    """Check if library features are available."""
    available = Config.is_library_available()

    if available:
        return LibraryStatusResponse(
            library_available=True,
            message="Library features are available.",
        )
    else:
        return LibraryStatusResponse(
            library_available=False,
            message="Library features require REBRICKABLE_API_KEY. Add it to your .env file.",
        )


@router.post("/search", response_model=SetSearchResponse)
async def search_sets(params: SetSearchParams):
    """Search LEGO sets with filters."""
    if not Config.is_library_available():
        return SetSearchResponse(
            success=False,
            error="Library features not available. Configure REBRICKABLE_API_KEY.",
        )

    service = LegoLibraryService()
    try:
        sets, total_count = await service.search_sets(
            search=params.search,
            theme_id=params.theme_id,
            min_year=params.min_year,
            max_year=params.max_year,
            min_parts=params.min_parts,
            max_parts=params.max_parts,
            page=params.page,
            page_size=params.page_size,
        )

        return SetSearchResponse(
            success=True,
            sets=[
                SetInfoResponse(
                    set_num=s.set_num,
                    name=s.name,
                    year=s.year,
                    theme_id=s.theme_id,
                    num_parts=s.num_parts,
                    img_url=s.img_url,
                )
                for s in sets
            ],
            total_count=total_count,
            page=params.page,
            page_size=params.page_size,
            has_more=(params.page * params.page_size) < total_count,
        )

    except RateLimitError:
        return SetSearchResponse(
            success=False,
            error="API rate limit exceeded. Please wait and try again.",
        )
    except LibraryServiceError as e:
        return SetSearchResponse(
            success=False,
            error=str(e),
        )
    finally:
        await service.close()


@router.get("/sets/{set_num}", response_model=SetDetailResponse)
async def get_set_detail(set_num: str):
    """Get detailed information for a specific set."""
    if not Config.is_library_available():
        return SetDetailResponse(
            success=False,
            error="Library features not available.",
        )

    service = LegoLibraryService()
    try:
        detail = await service.get_set_details(set_num)

        return SetDetailResponse(
            success=True,
            set_num=detail.set_num,
            name=detail.name,
            year=detail.year,
            theme_id=detail.theme_id,
            num_parts=detail.num_parts,
            img_url=detail.img_url,
            set_url=detail.set_url,
        )

    except SetNotFoundError:
        return SetDetailResponse(
            success=False,
            error=f"Set {set_num} not found.",
        )
    except LibraryServiceError as e:
        return SetDetailResponse(
            success=False,
            error=str(e),
        )
    finally:
        await service.close()


@router.get("/sets/{set_num}/inventory", response_model=SetInventoryResponse)
async def get_set_inventory(set_num: str):
    """Get parts inventory for a set."""
    if not Config.is_library_available():
        return SetInventoryResponse(
            success=False,
            error="Library features not available.",
        )

    service = LegoLibraryService()
    try:
        inventory = await service.get_set_inventory(set_num)

        mappable_count = 0
        parts = []
        for p in inventory.parts:
            is_mappable = get_part_info(p.part_num, p.part_name) is not None
            if is_mappable:
                mappable_count += p.quantity

            parts.append(PartInfoResponse(
                part_num=p.part_num,
                part_name=p.part_name,
                color_id=p.color_id,
                color_name=p.color_name,
                color_rgb=p.color_rgb,
                quantity=p.quantity,
                img_url=p.img_url,
                is_spare=p.is_spare,
                is_mappable=is_mappable,
            ))

        return SetInventoryResponse(
            success=True,
            set_num=inventory.set_num,
            parts=parts,
            total_parts=inventory.total_parts,
            unique_parts=inventory.unique_parts,
            mappable_parts=mappable_count,
        )

    except SetNotFoundError:
        return SetInventoryResponse(
            success=False,
            error=f"Set {set_num} not found.",
        )
    except LibraryServiceError as e:
        return SetInventoryResponse(
            success=False,
            error=str(e),
        )
    finally:
        await service.close()


@router.get("/themes", response_model=ThemeListResponse)
async def get_themes():
    """Get list of LEGO themes for filtering."""
    if not Config.is_library_available():
        return ThemeListResponse(
            success=False,
            error="Library features not available.",
        )

    service = LegoLibraryService()
    try:
        themes = await service.get_themes()

        return ThemeListResponse(
            success=True,
            themes=[
                ThemeResponse(
                    id=t.id,
                    name=t.name,
                    parent_id=t.parent_id,
                )
                for t in themes
            ],
        )

    except LibraryServiceError as e:
        return ThemeListResponse(
            success=False,
            error=str(e),
        )
    finally:
        await service.close()


@router.post("/sets/{set_num}/import", response_model=ImportResponse)
async def import_set(set_num: str):
    """Import a set's parts as a new build, replacing current build."""
    if not Config.is_library_available():
        return ImportResponse(
            success=False,
            message="Library features not available.",
        )

    service = LegoLibraryService()
    try:
        # Get set details and inventory
        detail = await service.get_set_details(set_num)
        inventory = await service.get_set_inventory(set_num)

        # Clear current build
        build_state = get_current_build()
        build_state.parts.clear()
        build_state._next_id = 1
        build_state.name = f"{detail.name} ({set_num})"
        build_state.description = f"Imported from Rebrickable - {detail.num_parts} parts"

        # Import parts - organize by part type then color for better visualization
        parts_imported = 0
        parts_skipped = 0
        warnings = []

        # First, collect all importable parts grouped by part_id and color
        grouped_parts = {}
        for part_entry in inventory.parts:
            # Skip spare parts
            if part_entry.is_spare:
                continue

            # Get part mapping (with fallback inference)
            part_info = get_part_info(part_entry.part_num, part_entry.part_name)

            if part_info is None:
                parts_skipped += part_entry.quantity
                if len(warnings) < 20:
                    warnings.append(
                        f"Unknown part: {part_entry.part_num} ({part_entry.part_name}) x{part_entry.quantity}"
                    )
                continue

            # Note if part was inferred
            if part_info.get("is_inferred") and len(warnings) < 20:
                warnings.append(
                    f"Approximated: {part_entry.part_name} (dimensions inferred from name)"
                )

            # Group key: (ldraw_id, color)
            ldraw_color = map_color(part_entry.color_id)
            key = (part_info["ldraw_id"], ldraw_color)

            if key not in grouped_parts:
                grouped_parts[key] = {
                    "part_info": part_info,
                    "color": ldraw_color,
                    "quantity": 0,
                }
            grouped_parts[key]["quantity"] += part_entry.quantity

        # Sort groups by part size (larger first) then by color
        sorted_groups = sorted(
            grouped_parts.values(),
            key=lambda g: (
                -(g["part_info"]["width"] * g["part_info"]["length"]),  # Larger first
                g["color"],
            )
        )

        # Place parts in organized rows - each part type gets its own row
        # ALL parts placed on ground layer (plate_y = 0) to avoid validation errors
        current_z = 0
        max_x = 50  # Wider grid to accommodate more parts on single layer

        for group in sorted_groups:
            part_info = group["part_info"]
            ldraw_color = group["color"]
            quantity = group["quantity"]

            dimensions = PartDimensions(
                studs_width=part_info["width"],
                studs_length=part_info["length"],
                plates_height=part_info["height"],
            )

            # Start new row for this part type
            grid_x = 0

            for _ in range(quantity):
                # Check if we need to wrap to next row
                if grid_x + dimensions.studs_width > max_x:
                    grid_x = 0
                    current_z += dimensions.studs_length + 1

                # All parts on ground layer (plate_y = 0) for inventory view
                build_state.add_part(
                    part_id=part_info["ldraw_id"],
                    part_name=part_info["name"],
                    color=ldraw_color,
                    position=StudCoordinate(grid_x, current_z, 0),
                    rotation=Rotation(0),
                    dimensions=dimensions,
                )

                grid_x += dimensions.studs_width + 1
                parts_imported += 1

            # Move to next row after each part type
            current_z += dimensions.studs_length + 2

        # Add summary warning if many parts skipped
        if parts_skipped > 0:
            total_attempted = parts_imported + parts_skipped
            skip_pct = (parts_skipped / total_attempted) * 100
            warnings.insert(0, f"Imported {parts_imported}/{total_attempted} parts ({skip_pct:.0f}% skipped)")

        return ImportResponse(
            success=True,
            message=f"Successfully imported {parts_imported} parts from {detail.name}",
            build_name=build_state.name,
            parts_imported=parts_imported,
            parts_skipped=parts_skipped,
            warnings=warnings[:20],  # Limit warnings
        )

    except SetNotFoundError:
        return ImportResponse(
            success=False,
            message=f"Set {set_num} not found.",
        )
    except LibraryServiceError as e:
        return ImportResponse(
            success=False,
            message=f"Import failed: {str(e)}",
        )
    finally:
        await service.close()
