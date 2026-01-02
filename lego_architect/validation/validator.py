"""
Physical validation for LEGO builds.

This module implements:
- Collision detection (AABB + occupancy grid)
- Connection validation (stud/tube alignment)
- Stability checking (center of gravity, support)
"""

from typing import List, Optional, Set

import numpy as np

from lego_architect.core.data_structures import (
    BuildState,
    PlacedPart,
    StudCoordinate,
    ValidationResult,
)


class CollisionDetector:
    """
    Detects collisions between LEGO parts using AABB algorithm.

    Uses Axis-Aligned Bounding Box (AABB) collision detection for speed.
    """

    def check_collision(self, build_state: BuildState, new_part: PlacedPart) -> bool:
        """
        Check if new part collides with existing parts.

        Args:
            build_state: Current build state
            new_part: Part to check

        Returns:
            True if collision detected, False otherwise
        """
        new_min, new_max = new_part.get_bounding_box()

        for existing_part in build_state.parts:
            ex_min, ex_max = existing_part.get_bounding_box()

            if self._aabb_overlap(new_min, new_max, ex_min, ex_max):
                return True

        return False

    def _aabb_overlap(
        self,
        min1: StudCoordinate,
        max1: StudCoordinate,
        min2: StudCoordinate,
        max2: StudCoordinate,
    ) -> bool:
        """
        Check if two axis-aligned bounding boxes overlap.

        Args:
            min1: Minimum corner of box 1
            max1: Maximum corner of box 1
            min2: Minimum corner of box 2
            max2: Maximum corner of box 2

        Returns:
            True if boxes overlap
        """
        return not (
            max1.stud_x <= min2.stud_x
            or max2.stud_x <= min1.stud_x
            or max1.stud_z <= min2.stud_z
            or max2.stud_z <= min1.stud_z
            or max1.plate_y <= min2.plate_y
            or max2.plate_y <= min1.plate_y
        )

    def validate_all(self, build_state: BuildState) -> ValidationResult:
        """
        Validate entire build for collisions.

        Args:
            build_state: Build to validate

        Returns:
            ValidationResult with any collision errors
        """
        result = ValidationResult(is_valid=True)

        # Check each pair of parts
        for i, part1 in enumerate(build_state.parts):
            for part2 in build_state.parts[i + 1 :]:
                min1, max1 = part1.get_bounding_box()
                min2, max2 = part2.get_bounding_box()

                if self._aabb_overlap(min1, max1, min2, max2):
                    result.add_error(
                        f"Collision between part #{part1.id} ({part1.part_id}) "
                        f"and part #{part2.id} ({part2.part_id})"
                    )

        return result


class ConnectionValidator:
    """
    Validates that parts are properly connected via studs.

    Ensures no floating parts and that connections are physically valid.
    """

    def validate_connections(self, build_state: BuildState) -> ValidationResult:
        """
        Validate all connections in the build.

        Checks:
        1. All parts above ground are connected
        2. Connections are via aligned studs

        Args:
            build_state: Build to validate

        Returns:
            ValidationResult with connection errors
        """
        result = ValidationResult(is_valid=True)

        # Build stud map (position -> part ID)
        stud_map = self._build_stud_map(build_state)

        # Check each part for connection
        for part in build_state.parts:
            if part.position.plate_y == 0:
                # Ground layer is always valid
                continue

            is_connected = self._check_part_connected(part, stud_map, build_state)

            if not is_connected:
                result.add_error(
                    f"Part #{part.id} ({part.part_name}) at {part.position} "
                    f"is not connected to the structure"
                )
                result.add_suggestion(
                    f"Add support below part #{part.id} or move to connected position"
                )

        return result

    def _build_stud_map(self, build_state: BuildState) -> dict[StudCoordinate, int]:
        """
        Build a map of stud positions to part IDs.

        Args:
            build_state: Build state

        Returns:
            Dictionary mapping stud positions to part IDs
        """
        stud_map: dict[StudCoordinate, int] = {}

        for part in build_state.parts:
            # Get top studs of this part
            for stud_pos in part.get_stud_positions():
                stud_map[stud_pos] = part.id

        return stud_map

    def _check_part_connected(
        self, part: PlacedPart, stud_map: dict[StudCoordinate, int], build_state: BuildState
    ) -> bool:
        """
        Check if a part is connected to parts below it.

        Args:
            part: Part to check
            stud_map: Map of stud positions
            build_state: Build state

        Returns:
            True if part is connected
        """
        # Get bottom positions where this part would connect
        min_corner, max_corner = part.get_bounding_box()

        # Check each position at the bottom of this part
        for x in range(min_corner.stud_x, max_corner.stud_x):
            for z in range(min_corner.stud_z, max_corner.stud_z):
                # Look for stud at this position, one layer below
                check_pos = StudCoordinate(x, z, part.position.plate_y)

                if check_pos in stud_map:
                    # Found a stud below - connected!
                    support_part_id = stud_map[check_pos]
                    part.connected_to.append(support_part_id)
                    return True

        return False


class StabilityChecker:
    """
    Checks structural stability of builds.

    Simple implementation using:
    - Center of gravity must be over base
    - No top-heavy structures without support
    """

    def check_stability(self, build_state: BuildState) -> ValidationResult:
        """
        Check if build is stable.

        Args:
            build_state: Build to check

        Returns:
            ValidationResult with stability warnings
        """
        result = ValidationResult(is_valid=True)

        if not build_state.parts:
            return result

        # Calculate center of gravity
        cog = self._calculate_center_of_gravity(build_state)

        # Check if center of gravity is over the base
        base_bounds = self._get_base_bounds(build_state)

        if not self._point_in_bounds(cog, base_bounds):
            result.add_warning(
                f"Center of gravity ({cog[0]:.1f}, {cog[2]:.1f}) "
                f"is outside base - structure may be unstable"
            )
            result.add_suggestion("Widen the base or add counterweight")

        # Check height-to-width ratio
        dims = build_state.get_dimensions()
        if dims[0] > 0 and dims[1] > 0:
            height = dims[2] / 3  # Convert plates to bricks
            base_size = min(dims[0], dims[1])

            if height > base_size * 3:
                result.add_warning(
                    f"Build is very tall ({height:.1f} bricks) "
                    f"compared to base ({base_size} studs) - may be unstable"
                )
                result.add_suggestion("Add wider base or internal support structure")

        return result

    def _calculate_center_of_gravity(self, build_state: BuildState) -> tuple[float, float, float]:
        """
        Calculate center of gravity (simplified, assumes uniform density).

        Args:
            build_state: Build state

        Returns:
            Tuple of (x, y, z) in stud units
        """
        total_mass = 0.0
        weighted_sum = np.array([0.0, 0.0, 0.0])

        for part in build_state.parts:
            # Mass proportional to volume
            mass = (
                part.dimensions.studs_width
                * part.dimensions.studs_length
                * part.dimensions.plates_height
            )

            # Center of part
            min_c, max_c = part.get_bounding_box()
            center = np.array(
                [
                    (min_c.stud_x + max_c.stud_x) / 2,
                    (min_c.plate_y + max_c.plate_y) / 2,
                    (min_c.stud_z + max_c.stud_z) / 2,
                ]
            )

            weighted_sum += mass * center
            total_mass += mass

        if total_mass == 0:
            return (0.0, 0.0, 0.0)

        cog = weighted_sum / total_mass
        return (cog[0], cog[1], cog[2])

    def _get_base_bounds(self, build_state: BuildState) -> tuple[float, float, float, float]:
        """
        Get bounding box of base layer.

        Args:
            build_state: Build state

        Returns:
            Tuple of (min_x, max_x, min_z, max_z)
        """
        base_parts = [part for part in build_state.parts if part.position.plate_y < 3]

        if not base_parts:
            # No clear base, use all parts
            base_parts = build_state.parts

        min_x = min(part.get_bounding_box()[0].stud_x for part in base_parts)
        max_x = max(part.get_bounding_box()[1].stud_x for part in base_parts)
        min_z = min(part.get_bounding_box()[0].stud_z for part in base_parts)
        max_z = max(part.get_bounding_box()[1].stud_z for part in base_parts)

        return (min_x, max_x, min_z, max_z)

    def _point_in_bounds(
        self, point: tuple[float, float, float], bounds: tuple[float, float, float, float]
    ) -> bool:
        """Check if point is within bounding box."""
        min_x, max_x, min_z, max_z = bounds
        x, _, z = point
        return min_x <= x <= max_x and min_z <= z <= max_z


class PhysicalValidator:
    """
    Main validation class that coordinates all validation checks.

    Orchestrates collision detection, connection validation, and stability checks.
    """

    def __init__(self) -> None:
        self.collision_detector = CollisionDetector()
        self.connection_validator = ConnectionValidator()
        self.stability_checker = StabilityChecker()

    def validate_build(self, build_state: BuildState) -> ValidationResult:
        """
        Run all validation checks on a build.

        Args:
            build_state: Build to validate

        Returns:
            Combined ValidationResult
        """
        result = ValidationResult(is_valid=True)

        # Check collisions
        collision_result = self.collision_detector.validate_all(build_state)
        result.errors.extend(collision_result.errors)
        result.warnings.extend(collision_result.warnings)
        result.suggestions.extend(collision_result.suggestions)

        # Check connections
        connection_result = self.connection_validator.validate_connections(build_state)
        result.errors.extend(connection_result.errors)
        result.warnings.extend(connection_result.warnings)
        result.suggestions.extend(connection_result.suggestions)

        # Check stability (only warnings, doesn't fail build)
        stability_result = self.stability_checker.check_stability(build_state)
        result.warnings.extend(stability_result.warnings)
        result.suggestions.extend(stability_result.suggestions)

        # Set overall validity
        result.is_valid = len(result.errors) == 0

        return result

    def quick_validate_placement(
        self, build_state: BuildState, new_part: PlacedPart
    ) -> dict[str, object]:
        """
        Quick validation for a single part placement (used during generation).

        Args:
            build_state: Current build state
            new_part: Part being placed

        Returns:
            Dictionary with validation result and suggestions
        """
        # Check collision
        has_collision = self.collision_detector.check_collision(build_state, new_part)

        if has_collision:
            suggestions: List[str] = []

            # Try adjacent positions
            for dx in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    if dx == 0 and dz == 0:
                        continue

                    alt_pos = new_part.position.offset(dx=dx, dz=dz)
                    alt_part = PlacedPart(
                        id=-1,
                        part_id=new_part.part_id,
                        part_name=new_part.part_name,
                        color=new_part.color,
                        position=alt_pos,
                        rotation=new_part.rotation,
                        dimensions=new_part.dimensions,
                    )

                    if not self.collision_detector.check_collision(build_state, alt_part):
                        suggestions.append(
                            f"Try position ({alt_pos.stud_x}, {alt_pos.stud_z}, {alt_pos.plate_y})"
                        )
                        if len(suggestions) >= 2:
                            break
                if len(suggestions) >= 2:
                    break

            # Try rotation
            if len(suggestions) < 2:
                alt_rot = new_part.rotation.rotate_cw()
                alt_part = PlacedPart(
                    id=-1,
                    part_id=new_part.part_id,
                    part_name=new_part.part_name,
                    color=new_part.color,
                    position=new_part.position,
                    rotation=alt_rot,
                    dimensions=new_part.dimensions,
                )

                if not self.collision_detector.check_collision(build_state, alt_part):
                    suggestions.append(f"Try rotation {alt_rot.degrees}°")

            return {
                "valid": False,
                "error": f"Collision at ({new_part.position.stud_x}, "
                f"{new_part.position.stud_z}, {new_part.position.plate_y})",
                "suggestions": suggestions[:2],
            }

        return {"valid": True, "error": None, "suggestions": []}
