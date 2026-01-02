#!/usr/bin/env python3
"""Quick test script to verify core functionality works."""

from lego_architect.core.data_structures import (
    BuildState,
    PartDimensions,
    Rotation,
    StudCoordinate,
)
from lego_architect.patterns import PatternLibrary
from lego_architect.validation import PhysicalValidator


def test_basic_functionality():
    """Test basic build creation and validation."""
    print("Testing basic functionality...")

    # Create a simple build
    build = BuildState(name="Test Tower")

    # Add parts
    for i in range(3):
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, i * 3),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

    assert len(build.parts) == 3, "Should have 3 parts"

    # Validate
    validator = PhysicalValidator()
    result = validator.validate_build(build)

    assert result.is_valid, f"Build should be valid, got errors: {result.errors}"

    print("✅ Basic functionality works!")


def test_collision_detection():
    """Test collision detection."""
    print("Testing collision detection...")

    build = BuildState()

    # Add base brick
    build.add_part(
        part_id="3001",
        part_name="Brick 2×4",
        color=4,
        position=StudCoordinate(0, 0, 0),
        rotation=Rotation(0),
        dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
    )

    # Add overlapping brick
    build.add_part(
        part_id="3001",
        part_name="Brick 2×4",
        color=1,
        position=StudCoordinate(1, 1, 0),  # Overlaps
        rotation=Rotation(0),
        dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
    )

    validator = PhysicalValidator()
    result = validator.validate_build(build)

    assert not result.is_valid, "Build with collision should be invalid"
    assert len(result.errors) > 0, "Should have collision errors"
    assert "collision" in result.errors[0].lower(), "Error should mention collision"

    print("✅ Collision detection works!")


def test_connection_validation():
    """Test connection validation."""
    print("Testing connection validation...")

    build = BuildState()

    # Add base brick
    build.add_part(
        part_id="3001",
        part_name="Brick 2×4",
        color=4,
        position=StudCoordinate(0, 0, 0),
        rotation=Rotation(0),
        dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
    )

    # Add floating brick
    build.add_part(
        part_id="3001",
        part_name="Brick 2×4",
        color=1,
        position=StudCoordinate(10, 10, 3),  # Not connected
        rotation=Rotation(0),
        dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
    )

    validator = PhysicalValidator()
    result = validator.validate_build(build)

    assert not result.is_valid, "Build with floating part should be invalid"
    assert "not connected" in result.errors[0].lower(), "Error should mention connection"

    print("✅ Connection validation works!")


def test_pattern_library():
    """Test pattern library."""
    print("Testing pattern library...")

    # Test each pattern independently

    # Test 1: Base pattern
    build1 = BuildState()
    base_parts = PatternLibrary.create_base(
        build_state=build1,
        start_x=0,
        start_z=0,
        width=8,
        length=8,
        color=71,
    )
    assert len(base_parts) > 0, "Should create base parts"

    # Test 2: Wall pattern
    build2 = BuildState()
    wall_parts = PatternLibrary.create_wall(
        build_state=build2,
        start_x=0,
        start_z=0,
        start_y=0,  # Start at ground
        length=8,
        height=12,
        direction="x",
        color=4,
        style="solid",
    )
    assert len(wall_parts) > 0, "Should create wall parts"

    # Test 3: Column pattern
    build3 = BuildState()
    column_parts = PatternLibrary.create_column(
        build_state=build3,
        x=0,
        z=0,
        height=12,
        thickness=2,
        color=72,
    )
    assert len(column_parts) > 0, "Should create column parts"

    # Validate each pattern has no collisions
    validator = PhysicalValidator()

    for name, build in [("base", build1), ("wall", build2), ("column", build3)]:
        result = validator.validate_build(build)
        collision_errors = [e for e in result.errors if "collision" in e.lower()]
        assert len(collision_errors) == 0, f"{name} pattern should not have collisions"

    print("✅ Pattern library works!")


def test_coordinate_conversion():
    """Test coordinate system conversions."""
    print("Testing coordinate conversions...")

    # Test stud to LDU conversion
    coord = StudCoordinate(4, 2, 3)
    x, y, z = coord.to_ldu()

    assert x == 80.0, f"X should be 80.0, got {x}"
    assert y == 24.0, f"Y should be 24.0, got {y}"
    assert z == 40.0, f"Z should be 40.0, got {z}"

    # Test round-trip conversion
    back = StudCoordinate.from_ldu(x, y, z)
    assert coord == back, "Round-trip conversion should match"

    # Test rotation matrix
    rot = Rotation(0)
    matrix = rot.to_matrix()
    assert matrix.shape == (3, 3), "Rotation matrix should be 3×3"

    print("✅ Coordinate conversions work!")


def test_bom_generation():
    """Test BOM generation."""
    print("Testing BOM generation...")

    build = BuildState()

    # Add 3 red bricks
    for _ in range(3):
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

    # Add 2 blue bricks
    for _ in range(2):
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=1,
            position=StudCoordinate(10, 10, 10),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

    bom = build.get_bom()

    assert len(bom) == 2, "Should have 2 entries in BOM"
    assert bom[("3001", 4)] == 3, "Should have 3 red bricks"
    assert bom[("3001", 1)] == 2, "Should have 2 blue bricks"

    print("✅ BOM generation works!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  LEGO ARCHITECT - QUICK TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        test_basic_functionality,
        test_collision_detection,
        test_connection_validation,
        test_pattern_library,
        test_coordinate_conversion,
        test_bom_generation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 All tests passed! Core functionality is working correctly.\n")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review errors above.\n")
        return 1


if __name__ == "__main__":
    exit(main())
