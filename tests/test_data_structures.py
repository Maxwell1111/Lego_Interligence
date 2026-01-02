"""Tests for core data structures."""

import numpy as np
import pytest

from lego_architect.core.data_structures import (
    BuildState,
    BuildStatus,
    PartDimensions,
    PlacedPart,
    Rotation,
    StudCoordinate,
    ValidationResult,
)


class TestStudCoordinate:
    """Test StudCoordinate class."""

    def test_creation(self):
        """Test coordinate creation."""
        coord = StudCoordinate(stud_x=4, stud_z=2, plate_y=3)
        assert coord.stud_x == 4
        assert coord.stud_z == 2
        assert coord.plate_y == 3

    def test_to_ldu(self):
        """Test conversion to LDraw Units."""
        coord = StudCoordinate(stud_x=4, stud_z=2, plate_y=3)
        x, y, z = coord.to_ldu()

        assert x == 80.0  # 4 * 20
        assert y == 24.0  # 3 * 8
        assert z == 40.0  # 2 * 20

    def test_from_ldu(self):
        """Test parsing from LDraw Units."""
        coord = StudCoordinate.from_ldu(80.0, 24.0, 40.0)

        assert coord.stud_x == 4
        assert coord.stud_z == 2
        assert coord.plate_y == 3

    def test_offset(self):
        """Test coordinate offset."""
        coord = StudCoordinate(stud_x=4, stud_z=2, plate_y=3)
        new_coord = coord.offset(dx=1, dz=2, dy=3)

        assert new_coord.stud_x == 5
        assert new_coord.stud_z == 4
        assert new_coord.plate_y == 6

    def test_addition(self):
        """Test coordinate addition."""
        coord1 = StudCoordinate(stud_x=4, stud_z=2, plate_y=3)
        coord2 = StudCoordinate(stud_x=1, stud_z=2, plate_y=3)
        result = coord1 + coord2

        assert result.stud_x == 5
        assert result.stud_z == 4
        assert result.plate_y == 6

    def test_immutability(self):
        """Test that StudCoordinate is immutable."""
        coord = StudCoordinate(stud_x=4, stud_z=2, plate_y=3)

        with pytest.raises(AttributeError):
            coord.stud_x = 10


class TestRotation:
    """Test Rotation class."""

    def test_valid_rotations(self):
        """Test valid rotation values."""
        for degrees in [0, 90, 180, 270]:
            rot = Rotation(degrees)
            assert rot.degrees == degrees

    def test_invalid_rotation(self):
        """Test invalid rotation raises error."""
        with pytest.raises(ValueError):
            Rotation(45)

    def test_to_matrix(self):
        """Test rotation matrix generation."""
        rot = Rotation(0)
        matrix = rot.to_matrix()

        # Identity matrix for 0 degrees
        expected = np.eye(3)
        np.testing.assert_array_almost_equal(matrix, expected)

    def test_rotate_cw(self):
        """Test clockwise rotation."""
        rot = Rotation(0)
        rot = rot.rotate_cw()
        assert rot.degrees == 90

        rot = rot.rotate_cw()
        assert rot.degrees == 180

        rot = rot.rotate_cw()
        assert rot.degrees == 270

        rot = rot.rotate_cw()
        assert rot.degrees == 0  # Wraps around

    def test_rotate_ccw(self):
        """Test counter-clockwise rotation."""
        rot = Rotation(0)
        rot = rot.rotate_ccw()
        assert rot.degrees == 270

        rot = rot.rotate_ccw()
        assert rot.degrees == 180


class TestPartDimensions:
    """Test PartDimensions class."""

    def test_creation(self):
        """Test dimension creation."""
        dims = PartDimensions(studs_width=2, studs_length=4, plates_height=3)

        assert dims.studs_width == 2
        assert dims.studs_length == 4
        assert dims.plates_height == 3

    def test_brick_height(self):
        """Test brick height calculation."""
        dims = PartDimensions(studs_width=2, studs_length=4, plates_height=3)

        assert dims.brick_height == 1.0  # 3 plates = 1 brick

        dims = PartDimensions(studs_width=2, studs_length=4, plates_height=6)
        assert dims.brick_height == 2.0

    def test_to_ldu(self):
        """Test conversion to LDU."""
        dims = PartDimensions(studs_width=2, studs_length=4, plates_height=3)
        width, height, depth = dims.to_ldu()

        assert width == 40.0  # 2 * 20
        assert height == 24.0  # 3 * 8
        assert depth == 80.0  # 4 * 20


class TestPlacedPart:
    """Test PlacedPart class."""

    def test_creation(self):
        """Test part creation."""
        part = PlacedPart(
            id=1,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        assert part.id == 1
        assert part.part_id == "3001"
        assert part.color == 4

    def test_bounding_box(self):
        """Test bounding box calculation."""
        part = PlacedPart(
            id=1,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(2, 3, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        min_corner, max_corner = part.get_bounding_box()

        assert min_corner.stud_x == 2
        assert min_corner.stud_z == 3
        assert min_corner.plate_y == 0

        assert max_corner.stud_x == 4  # 2 + 2
        assert max_corner.stud_z == 7  # 3 + 4
        assert max_corner.plate_y == 3  # 0 + 3

    def test_bounding_box_rotated(self):
        """Test bounding box with rotation."""
        part = PlacedPart(
            id=1,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(90),  # Rotated
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        min_corner, max_corner = part.get_bounding_box()

        # Dimensions swap when rotated
        assert max_corner.stud_x == 4  # Length becomes width
        assert max_corner.stud_z == 2  # Width becomes length

    def test_stud_positions(self):
        """Test stud position calculation."""
        part = PlacedPart(
            id=1,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        studs = part.get_stud_positions()

        # 2×4 brick has 8 studs
        assert len(studs) == 8

        # All studs should be at height 3 (top of brick)
        assert all(s.plate_y == 3 for s in studs)

    def test_to_ldraw_line(self):
        """Test LDraw line generation."""
        part = PlacedPart(
            id=1,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        line = part.to_ldraw_line()

        # Should start with "1 4 0.0000 0.0000 0.0000" (color, position)
        assert line.startswith("1 4 0.0000 0.0000 0.0000")
        # Should end with "3001.dat"
        assert line.endswith("3001.dat")


class TestBuildState:
    """Test BuildState class."""

    def test_creation(self):
        """Test build state creation."""
        build = BuildState(name="Test Build", description="A test build")

        assert build.name == "Test Build"
        assert build.description == "A test build"
        assert len(build.parts) == 0

    def test_add_part(self):
        """Test adding parts to build."""
        build = BuildState()

        part = build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        assert len(build.parts) == 1
        assert part.id == 1  # First part gets ID 1

        # Add another part
        part2 = build.add_part(
            part_id="3002",
            part_name="Brick 2×3",
            color=4,
            position=StudCoordinate(4, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=3, plates_height=3),
        )

        assert len(build.parts) == 2
        assert part2.id == 2  # Second part gets ID 2

    def test_get_dimensions(self):
        """Test overall dimension calculation."""
        build = BuildState()

        # Add a 2×4 brick at origin
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        # Add another 2×4 brick offset
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(4, 2, 3),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        width, depth, height = build.get_dimensions()

        assert width == 6  # 0 to 6 in X
        assert depth == 6  # 0 to 6 in Z
        assert height == 6  # 0 to 6 in Y (plates)

    def test_get_bom(self):
        """Test bill of materials generation."""
        build = BuildState()

        # Add three 2×4 bricks in red
        for i in range(3):
            build.add_part(
                part_id="3001",
                part_name="Brick 2×4",
                color=4,  # Red
                position=StudCoordinate(i * 4, 0, 0),
                rotation=Rotation(0),
                dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
            )

        # Add two 2×4 bricks in blue
        for i in range(2):
            build.add_part(
                part_id="3001",
                part_name="Brick 2×4",
                color=1,  # Blue
                position=StudCoordinate(i * 4, 4, 0),
                rotation=Rotation(0),
                dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
            )

        bom = build.get_bom()

        # Should have 2 entries: (3001, red) and (3001, blue)
        assert len(bom) == 2
        assert bom[("3001", 4)] == 3  # 3 red bricks
        assert bom[("3001", 1)] == 2  # 2 blue bricks

    def test_remove_part(self):
        """Test removing parts."""
        build = BuildState()

        part = build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        assert len(build.parts) == 1

        result = build.remove_part(part.id)

        assert result is True
        assert len(build.parts) == 0


class TestValidationResult:
    """Test ValidationResult class."""

    def test_creation(self):
        """Test validation result creation."""
        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult(is_valid=True)

        result.add_error("Test error")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult(is_valid=True)

        result.add_warning("Test warning")

        # Warnings don't change validity
        assert result.is_valid is True
        assert len(result.warnings) == 1

    def test_bool_conversion(self):
        """Test bool conversion."""
        result = ValidationResult(is_valid=True)
        assert bool(result) is True

        result.add_error("Error")
        assert bool(result) is False
