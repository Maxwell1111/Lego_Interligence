"""
Export routes for BOM and LDraw.
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from lego_architect.web.routes.builds import get_current_build

router = APIRouter()


# LDraw color names mapping
LDRAW_COLORS = {
    0: "Black",
    1: "Blue",
    2: "Green",
    3: "Dark Turquoise",
    4: "Red",
    5: "Dark Pink",
    6: "Brown",
    7: "Light Gray",
    8: "Dark Gray",
    9: "Light Blue",
    10: "Bright Green",
    11: "Light Turquoise",
    12: "Salmon",
    13: "Pink",
    14: "Yellow",
    15: "White",
    17: "Light Green",
    18: "Light Yellow",
    19: "Tan",
    20: "Light Violet",
    22: "Purple",
    23: "Dark Blue Violet",
    25: "Orange",
    26: "Magenta",
    27: "Lime",
    28: "Dark Tan",
    29: "Bright Pink",
    33: "Trans Light Blue",
    34: "Trans Green",
    36: "Trans Red",
    41: "Trans Light Purple",
    42: "Trans Purple",
    46: "Trans Yellow",
    47: "Trans Clear",
    70: "Reddish Brown",
    71: "Light Bluish Gray",
    72: "Dark Bluish Gray",
    78: "Pearl Light Gold",
    85: "Dark Purple",
    484: "Dark Orange",
}


class BomEntry(BaseModel):
    part_id: str
    part_name: str
    color_id: int
    color_name: str
    quantity: int


class BomResponse(BaseModel):
    build_name: str
    total_parts: int
    unique_parts: int
    entries: list[BomEntry]


@router.get("/bom", response_model=BomResponse)
async def get_bom():
    """Get Bill of Materials for the build."""
    build = get_current_build()
    bom = build.get_bom()

    # Group by part_id to get names
    part_names = {}
    for part in build.parts:
        part_names[part.part_id] = part.part_name

    entries = []
    for (part_id, color), quantity in bom.items():
        entries.append(
            BomEntry(
                part_id=part_id,
                part_name=part_names.get(part_id, "Unknown"),
                color_id=color,
                color_name=LDRAW_COLORS.get(color, f"Color {color}"),
                quantity=quantity,
            )
        )

    # Sort by quantity descending
    entries.sort(key=lambda e: e.quantity, reverse=True)

    return BomResponse(
        build_name=build.name,
        total_parts=len(build.parts),
        unique_parts=len(entries),
        entries=entries,
    )


@router.get("/ldraw", response_class=PlainTextResponse)
async def get_ldraw():
    """Export build as LDraw file."""
    build = get_current_build()

    lines = [
        f"0 {build.name}",
        f"0 Name: {build.name}.ldr",
        "0 Author: LEGO Architect",
        f"0 !LDRAW_ORG Unofficial_Model",
        "",
    ]

    # Add all parts
    for part in build.parts:
        lines.append(part.to_ldraw_line())

    lines.append("")
    lines.append("0")

    return "\n".join(lines)


@router.get("/ldraw/download")
async def download_ldraw():
    """Download LDraw file."""
    build = get_current_build()
    content = await get_ldraw()

    filename = f"{build.name.replace(' ', '_')}.ldr"
    return PlainTextResponse(
        content,
        media_type="application/x-ldraw",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
