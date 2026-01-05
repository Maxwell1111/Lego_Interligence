#!/usr/bin/env python3
"""
Demo script for LEGO Architect.

This demonstrates the core functionality without requiring the LLM:
- Creating builds manually
- Validating physical constraints
- Using pattern library
- Exporting to LDraw format
"""

import sys

from lego_architect.core.data_structures import (
    BuildState,
    PartDimensions,
    Rotation,
    StudCoordinate,
)
from lego_architect.patterns import PatternLibrary
from lego_architect.validation import PhysicalValidator


def safe_input(prompt="Press Enter to continue..."):
    """Safely handle input in both interactive and non-interactive environments."""
    if not sys.stdin.isatty():
        # Non-interactive environment, skip input
        print(f"[Auto-continuing in non-interactive mode]")
        return ""
    try:
        return input(prompt)
    except EOFError:
        print(f"\n[Auto-continuing]")
        return ""


def demo_simple_tower():
    """Demo: Build a simple tower and validate it."""
    print("=" * 70)
    print("DEMO 1: Simple Tower")
    print("=" * 70)

    build = BuildState(name="Simple Tower", description="A 3-brick tall tower")

    # Add three bricks stacked vertically
    print("\n📦 Adding bricks to build...")

    for i in range(3):
        part = build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,  # Red
            position=StudCoordinate(stud_x=0, stud_z=0, plate_y=i * 3),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )
        print(f"  ✓ Added {part.part_name} at {part.position}")

    # Validate
    print("\n🔍 Validating build...")
    validator = PhysicalValidator()
    result = validator.validate_build(build)

    if result.is_valid:
        print(f"  ✅ Build is valid! ({len(build.parts)} parts)")
    else:
        print(f"  ❌ Build has errors:")
        for error in result.errors:
            print(f"     - {error}")

    if result.warnings:
        print(f"  ⚠️  Warnings:")
        for warning in result.warnings:
            print(f"     - {warning}")

    # Show dimensions
    dims = build.get_dimensions()
    print(f"\n📏 Dimensions: {dims[0]}×{dims[1]} studs, {dims[2]} plates tall")

    # Show BOM
    print("\n📦 Bill of Materials:")
    bom = build.get_bom()
    for (part_id, color), quantity in bom.items():
        print(f"  - {quantity}× Part {part_id} (Color {color})")

    # Export to LDraw
    print("\n💾 LDraw export (first 3 lines):")
    for i, part in enumerate(build.parts[:3]):
        print(f"  {part.to_ldraw_line()}")

    print()


def demo_collision_detection():
    """Demo: Show collision detection in action."""
    print("=" * 70)
    print("DEMO 2: Collision Detection")
    print("=" * 70)

    build = BuildState(name="Collision Test")

    # Add first brick
    print("\n📦 Adding first brick...")
    build.add_part(
        part_id="3001",
        part_name="Brick 2×4",
        color=4,
        position=StudCoordinate(0, 0, 0),
        rotation=Rotation(0),
        dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
    )
    print("  ✓ Added Brick 2×4 at (0, 0, 0)")

    # Try to add overlapping brick
    print("\n📦 Adding overlapping brick...")
    build.add_part(
        part_id="3001",
        part_name="Brick 2×4",
        color=1,
        position=StudCoordinate(1, 1, 0),  # Overlaps!
        rotation=Rotation(0),
        dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
    )
    print("  ✓ Added Brick 2×4 at (1, 1, 0) - This overlaps!")

    # Validate
    print("\n🔍 Validating build...")
    validator = PhysicalValidator()
    result = validator.validate_build(build)

    if result.is_valid:
        print("  ✅ Build is valid")
    else:
        print(f"  ❌ Build has {len(result.errors)} error(s):")
        for error in result.errors:
            print(f"     - {error}")

    print()


def demo_connection_validation():
    """Demo: Show connection validation."""
    print("=" * 70)
    print("DEMO 3: Connection Validation (Floating Parts)")
    print("=" * 70)

    build = BuildState(name="Connection Test")

    # Add base brick
    print("\n📦 Adding base brick...")
    build.add_part(
        part_id="3001",
        part_name="Brick 2×4",
        color=4,
        position=StudCoordinate(0, 0, 0),
        rotation=Rotation(0),
        dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
    )
    print("  ✓ Added base brick at (0, 0, 0)")

    # Add floating brick
    print("\n📦 Adding floating brick (not connected)...")
    build.add_part(
        part_id="3001",
        part_name="Brick 2×4",
        color=1,
        position=StudCoordinate(10, 10, 3),  # Far away!
        rotation=Rotation(0),
        dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
    )
    print("  ✓ Added brick at (10, 10, 3) - This is floating!")

    # Validate
    print("\n🔍 Validating build...")
    validator = PhysicalValidator()
    result = validator.validate_build(build)

    if result.is_valid:
        print("  ✅ Build is valid")
    else:
        print(f"  ❌ Build has {len(result.errors)} error(s):")
        for error in result.errors:
            print(f"     - {error}")

    if result.suggestions:
        print(f"\n💡 Suggestions:")
        for suggestion in result.suggestions:
            print(f"   - {suggestion}")

    print()


def demo_pattern_library():
    """Demo: Use pattern library to create structures."""
    print("=" * 70)
    print("DEMO 4: Pattern Library")
    print("=" * 70)

    build = BuildState(name="House with Pattern Library")

    # Create base using pattern
    print("\n🏗️  Creating 8×8 base plate...")
    base_parts = PatternLibrary.create_base(
        build_state=build,
        start_x=0,
        start_z=0,
        width=8,
        length=8,
        color=71,  # Light gray
    )
    print(f"  ✓ Created base with {len(base_parts)} plates")

    # Create wall using pattern
    print("\n🏗️  Creating wall (8 studs long, 12 plates high)...")
    wall_parts = PatternLibrary.create_wall(
        build_state=build,
        start_x=0,
        start_z=0,
        start_y=1,  # Start above base
        length=8,
        height=12,
        direction="x",
        color=4,  # Red
        style="solid",
    )
    print(f"  ✓ Created wall with {len(wall_parts)} bricks")

    # Create column using pattern
    print("\n🏗️  Creating corner column...")
    column_parts = PatternLibrary.create_column(
        build_state=build,
        x=0,
        z=0,
        height=12,
        thickness=2,
        color=72,  # Dark gray
    )
    print(f"  ✓ Created column with {len(column_parts)} bricks")

    # Validate entire build
    print("\n🔍 Validating complete build...")
    validator = PhysicalValidator()
    result = validator.validate_build(build)

    if result.is_valid:
        print(f"  ✅ Build is valid! ({len(build.parts)} total parts)")
    else:
        print(f"  ❌ Build has errors:")
        for error in result.errors:
            print(f"     - {error}")

    # Show final stats
    dims = build.get_dimensions()
    print(f"\n📏 Final Dimensions: {dims[0]}×{dims[1]} studs, {dims[2]} plates tall")

    bom = build.get_bom()
    print(f"📦 Unique parts: {len(bom)}")
    print(f"📦 Total pieces: {len(build.parts)}")

    print()


def demo_rotation_and_placement():
    """Demo: Show rotation and precise placement."""
    print("=" * 70)
    print("DEMO 5: Rotation and Placement")
    print("=" * 70)

    build = BuildState(name="Cross Pattern")

    # Create a cross pattern using rotated bricks
    print("\n🏗️  Creating cross pattern with rotated bricks...")

    # Center vertical brick
    build.add_part(
        part_id="3010",  # 1×4 brick
        part_name="Brick 1×4",
        color=4,
        position=StudCoordinate(4, 2, 0),
        rotation=Rotation(0),  # Vertical
        dimensions=PartDimensions(studs_width=1, studs_length=4, plates_height=3),
    )
    print("  ✓ Added vertical brick at (4, 2, 0)")

    # Horizontal brick (rotated 90°)
    build.add_part(
        part_id="3010",  # 1×4 brick
        part_name="Brick 1×4",
        color=1,
        position=StudCoordinate(2, 4, 0),
        rotation=Rotation(90),  # Horizontal
        dimensions=PartDimensions(studs_width=1, studs_length=4, plates_height=3),
    )
    print("  ✓ Added horizontal brick at (2, 4, 0) rotated 90°")

    # Show bounding boxes
    print("\n📦 Bounding boxes:")
    for i, part in enumerate(build.parts):
        min_corner, max_corner = part.get_bounding_box()
        print(f"  Part {i+1}: {min_corner} → {max_corner}")

    # Validate
    print("\n🔍 Validating build...")
    validator = PhysicalValidator()
    result = validator.validate_build(build)

    if result.is_valid:
        print("  ✅ Build is valid!")
    else:
        print(f"  ❌ Build has errors:")
        for error in result.errors:
            print(f"     - {error}")

    print()


def demo_coordinate_conversion():
    """Demo: Show coordinate system conversions."""
    print("=" * 70)
    print("DEMO 6: Coordinate System Conversions")
    print("=" * 70)

    print("\n📐 Stud Grid ↔ LDraw Units (LDU) Conversion:")
    print("-" * 50)

    # Show conversions
    coords = [
        StudCoordinate(0, 0, 0),
        StudCoordinate(4, 2, 3),
        StudCoordinate(10, 5, 6),
    ]

    for coord in coords:
        ldu = coord.to_ldu()
        print(f"\n  Stud Grid: {coord}")
        print(f"  → LDU: ({ldu[0]:.1f}, {ldu[1]:.1f}, {ldu[2]:.1f})")

        # Convert back
        back = StudCoordinate.from_ldu(*ldu)
        print(f"  → Back: {back}")
        print(f"  ✓ Conversion verified: {coord == back}")

    print("\n📐 The 5:6 Plate-to-Brick Ratio:")
    print("-" * 50)
    print("  5 plates = 40 LDU")
    print("  6 plates = 48 LDU = 2 bricks")
    print("  Ratio: 40/48 = 5/6 ✓")
    print("  This ratio is automatically maintained by the LDU system!")

    print()


def main():
    """Run all demos."""
    print("\n" + "█" * 70)
    print(" " * 15 + "LEGO ARCHITECT - DEMO SUITE")
    print("█" * 70 + "\n")

    demos = [
        demo_simple_tower,
        demo_collision_detection,
        demo_connection_validation,
        demo_pattern_library,
        demo_rotation_and_placement,
        demo_coordinate_conversion,
    ]

    for i, demo in enumerate(demos, 1):
        demo()
        if i < len(demos):
            safe_input(f"Press Enter to continue to Demo {i+1}...")
            print()

    print("=" * 70)
    print("✅ All demos completed successfully!")
    print("=" * 70)
    print()
    print("🎉 Core functionality is working!")
    print()

    # Only show AI instructions if AI features are enabled
    from lego_architect.config import Config
    if Config.ENABLE_AI_FEATURES:
        print("Next steps to try AI-powered generation:")
        print("  1. Set up .env file with your Anthropic API key:")
        print("     cp .env.example .env")
        print("     # Then edit .env and add: ANTHROPIC_API_KEY=your_key_here")
        print()
        print("  2. Run AI-powered demos:")
        print("     python3 demo_llm.py")
        print("     python3 demo_orchestrator.py")
        print()
    else:
        print("AI features are disabled. Manual building and patterns are available.")
        print("To enable AI features, set ENABLE_AI_FEATURES=true in your .env file.")
        print()

    print("Run all tests:")
    print("  ./test.sh")
    print("  # or: make test")
    print()


if __name__ == "__main__":
    main()
