"""Tests for validation module."""

import pytest

from lego_architect.core.data_structures import (
    BuildState,
    PartDimensions,
    PlacedPart,
    Rotation,
    StudCoordinate,
)
from lego_architect.validation import (
    CollisionDetector,
    ConnectionValidator,
    PhysicalValidator,
    StabilityChecker,
)


class TestCollisionDetector:
    """Test collision detection."""

    def test_no_collision(self):
        """Test parts that don't collide."""
        build = BuildState()
        detector = CollisionDetector()

        # Add first part
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        # Create second part that doesn't collide
        new_part = PlacedPart(
            id=2,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(4, 0, 0),  # Offset, no collision
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        assert detector.check_collision(build, new_part) is False

    def test_collision_overlap(self):
        """Test parts that overlap."""
        build = BuildState()
        detector = CollisionDetector()

        # Add first part
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        # Create second part that overlaps
        new_part = PlacedPart(
            id=2,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(1, 1, 0),  # Overlaps with first
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        assert detector.check_collision(build, new_part) is True

    def test_collision_vertical_clearance(self):
        """Test parts stacked vertically don't collide."""
        build = BuildState()
        detector = CollisionDetector()

        # Add first part at ground level
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        # Create second part stacked on top
        new_part = PlacedPart(
            id=2,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 3),  # One brick higher
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        assert detector.check_collision(build, new_part) is False

    def test_validate_all(self):
        """Test full build validation."""
        build = BuildState()
        detector = CollisionDetector()

        # Add non-colliding parts
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(4, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        result = detector.validate_all(build)
        assert result.is_valid is True
        assert len(result.errors) == 0


class TestConnectionValidator:
    """Test connection validation."""

    def test_ground_level_always_valid(self):
        """Test ground level parts are always considered connected."""
        build = BuildState()
        validator = ConnectionValidator()

        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        result = validator.validate_connections(build)
        assert result.is_valid is True

    def test_connected_parts(self):
        """Test properly connected parts."""
        build = BuildState()
        validator = ConnectionValidator()

        # Add base brick
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        # Add brick on top (properly connected)
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 3),  # Sits on top
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        result = validator.validate_connections(build)
        assert result.is_valid is True

    def test_floating_parts(self):
        """Test detection of floating parts."""
        build = BuildState()
        validator = ConnectionValidator()

        # Add base brick
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        # Add brick floating in air (not connected)
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(10, 10, 3),  # Far away from base
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        result = validator.validate_connections(build)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "not connected" in result.errors[0].lower()


class TestStabilityChecker:
    """Test stability checking."""

    def test_stable_build(self):
        """Test stable build (wide base, low height)."""
        build = BuildState()
        checker = StabilityChecker()

        # Create wide base (4×4 studs)
        for x in range(0, 4, 2):
            for z in range(0, 4, 2):
                build.add_part(
                    part_id="3003",
                    part_name="Brick 2×2",
                    color=4,
                    position=StudCoordinate(x, z, 0),
                    rotation=Rotation(0),
                    dimensions=PartDimensions(studs_width=2, studs_length=2, plates_height=3),
                )

        result = checker.check_stability(build)
        # Should have no errors (only warnings possible)
        assert len(result.errors) == 0

    def test_tall_unstable_build(self):
        """Test very tall build generates warning."""
        build = BuildState()
        checker = StabilityChecker()

        # Create very tall, narrow tower (1×1 studs, 30 plates high)
        for y in range(0, 30, 3):
            build.add_part(
                part_id="3005",
                part_name="Brick 1×1",
                color=4,
                position=StudCoordinate(0, 0, y),
                rotation=Rotation(0),
                dimensions=PartDimensions(studs_width=1, studs_length=1, plates_height=3),
            )

        result = checker.check_stability(build)
        # Should generate warning about tall build
        assert len(result.warnings) > 0


class TestPhysicalValidator:
    """Test main physical validator."""

    def test_valid_build(self):
        """Test completely valid build."""
        build = BuildState()
        validator = PhysicalValidator()

        # Create simple valid structure
        # Base layer
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        # Second layer on top
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 3),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        result = validator.validate_build(build)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_invalid_build_collision(self):
        """Test build with collision."""
        build = BuildState()
        validator = PhysicalValidator()

        # Add two overlapping parts
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(1, 1, 0),  # Overlaps
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        result = validator.validate_build(build)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "collision" in result.errors[0].lower()

    def test_invalid_build_floating(self):
        """Test build with floating parts."""
        build = BuildState()
        validator = PhysicalValidator()

        # Add base and floating part
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(10, 10, 10),  # Floating
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        result = validator.validate_build(build)
        assert result.is_valid is False
        assert "not connected" in result.errors[0].lower()

    def test_quick_validate_placement(self):
        """Test quick validation during generation."""
        build = BuildState()
        validator = PhysicalValidator()

        # Add first part
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        # Try to place colliding part
        new_part = PlacedPart(
            id=2,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(1, 1, 0),  # Collides
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        result = validator.quick_validate_placement(build, new_part)
        assert result["valid"] is False
        assert result["error"] is not None
        assert len(result["suggestions"]) > 0  # Should have suggestions

    def test_quick_validate_placement_valid(self):
        """Test quick validation with valid placement."""
        build = BuildState()
        validator = PhysicalValidator()

        # Add first part
        build.add_part(
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(0, 0, 0),
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        # Try to place non-colliding part
        new_part = PlacedPart(
            id=2,
            part_id="3001",
            part_name="Brick 2×4",
            color=4,
            position=StudCoordinate(4, 0, 0),  # No collision
            rotation=Rotation(0),
            dimensions=PartDimensions(studs_width=2, studs_length=4, plates_height=3),
        )

        result = validator.quick_validate_placement(build, new_part)
        assert result["valid"] is True
        assert result["error"] is None
