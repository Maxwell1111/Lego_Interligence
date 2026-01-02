"""
Parametric pattern library for common LEGO structures.

Provides pre-validated templates for:
- Walls (solid, windowed, castle style)
- Bases (stable platform layers)
- Columns (vertical supports)
- Wings (vehicle/spacecraft structures)
"""

from typing import List

from lego_architect.core.data_structures import (
    BuildState,
    PartDimensions,
    PlacedPart,
    Rotation,
    StudCoordinate,
)


class PatternLibrary:
    """
    Library of parametric patterns for common structures.

    Each pattern is a function that expands into individual brick placements.
    """

    @staticmethod
    def create_base(
        build_state: BuildState,
        start_x: int,
        start_z: int,
        width: int,
        length: int,
        color: int,
    ) -> List[PlacedPart]:
        """
        Create a base plate layer using non-overlapping plates.

        Args:
            build_state: Build state to add parts to
            start_x: Starting X position
            start_z: Starting Z position
            width: Width in studs
            length: Length in studs
            color: LDraw color code

        Returns:
            List of created parts
        """
        parts: List[PlacedPart] = []

        # Use 2×4 plates (3037) for efficiency
        plate_2x4 = "3037"
        plate_dims = PartDimensions(studs_width=2, studs_length=4, plates_height=1)

        # Fill area with plates (no overlap)
        y = 0  # Ground level
        z = start_z

        while z < start_z + length:
            x = start_x

            while x < start_x + width:
                # Determine plate size
                remaining_width = (start_x + width) - x
                remaining_length = (start_z + length) - z

                # Choose appropriate plate size
                if remaining_width >= 2 and remaining_length >= 4:
                    # Use 2×4 plate
                    part = build_state.add_part(
                        part_id=plate_2x4,
                        part_name="Plate 2×4",
                        color=color,
                        position=StudCoordinate(x, z, y),
                        rotation=Rotation(0),
                        dimensions=plate_dims,
                    )
                    parts.append(part)
                    x += 2
                elif remaining_width >= 4 and remaining_length >= 2:
                    # Use 2×4 plate rotated
                    part = build_state.add_part(
                        part_id=plate_2x4,
                        part_name="Plate 2×4",
                        color=color,
                        position=StudCoordinate(x, z, y),
                        rotation=Rotation(90),
                        dimensions=plate_dims,
                    )
                    parts.append(part)
                    x += 4
                elif remaining_width >= 2 and remaining_length >= 2:
                    # Use 2×2 plate
                    plate_2x2 = "3022"
                    dims_2x2 = PartDimensions(studs_width=2, studs_length=2, plates_height=1)
                    part = build_state.add_part(
                        part_id=plate_2x2,
                        part_name="Plate 2×2",
                        color=color,
                        position=StudCoordinate(x, z, y),
                        rotation=Rotation(0),
                        dimensions=dims_2x2,
                    )
                    parts.append(part)
                    x += 2
                else:
                    # Fill remaining with 1×1 plates
                    plate_1x1 = "3024"
                    dims_1x1 = PartDimensions(studs_width=1, studs_length=1, plates_height=1)
                    part = build_state.add_part(
                        part_id=plate_1x1,
                        part_name="Plate 1×1",
                        color=color,
                        position=StudCoordinate(x, z, y),
                        rotation=Rotation(0),
                        dimensions=dims_1x1,
                    )
                    parts.append(part)
                    x += 1

            # Move to next row - increment by 4 (length of plate) or 2 (width)
            if remaining_length >= 4:
                z += 4
            elif remaining_length >= 2:
                z += 2
            else:
                z += 1

        return parts

    @staticmethod
    def create_wall(
        build_state: BuildState,
        start_x: int,
        start_z: int,
        start_y: int,
        length: int,
        height: int,
        direction: str,
        color: int,
        style: str = "solid",
    ) -> List[PlacedPart]:
        """
        Create a wall using brick pattern.

        Args:
            build_state: Build state to add parts to
            start_x: Starting X position
            start_z: Starting Z position
            start_y: Starting Y position (in plates)
            length: Length in studs
            height: Height in plates
            direction: "x" or "z" (direction of wall)
            color: LDraw color code
            style: "solid", "window", or "castle"

        Returns:
            List of created parts
        """
        parts: List[PlacedPart] = []

        # Use 2×4 bricks (3001) for main structure
        brick_2x4 = "3001"
        brick_dims = PartDimensions(studs_width=2, studs_length=4, plates_height=3)

        # Determine orientation
        is_x_direction = direction == "x"

        # Build wall layer by layer
        current_y = start_y

        while current_y < start_y + height:
            # Alternate pattern for stability (running bond)
            offset = 2 if ((current_y - start_y) // 3) % 2 == 0 else 0

            if is_x_direction:
                # Wall extends in X direction
                x = start_x + offset
                while x < start_x + length:
                    remaining = (start_x + length) - x

                    if remaining >= 4:
                        # Use 2×4 brick
                        part = build_state.add_part(
                            part_id=brick_2x4,
                            part_name="Brick 2×4",
                            color=color,
                            position=StudCoordinate(x, start_z, current_y),
                            rotation=Rotation(0),
                            dimensions=brick_dims,
                        )
                        parts.append(part)
                        x += 4
                    elif remaining >= 2:
                        # Use 2×2 brick
                        brick_2x2 = "3003"
                        dims_2x2 = PartDimensions(
                            studs_width=2, studs_length=2, plates_height=3
                        )
                        part = build_state.add_part(
                            part_id=brick_2x2,
                            part_name="Brick 2×2",
                            color=color,
                            position=StudCoordinate(x, start_z, current_y),
                            rotation=Rotation(0),
                            dimensions=dims_2x2,
                        )
                        parts.append(part)
                        x += 2
                    else:
                        x += 1
            else:
                # Wall extends in Z direction
                z = start_z + offset
                while z < start_z + length:
                    remaining = (start_z + length) - z

                    if remaining >= 4:
                        # Use 2×4 brick rotated
                        part = build_state.add_part(
                            part_id=brick_2x4,
                            part_name="Brick 2×4",
                            color=color,
                            position=StudCoordinate(start_x, z, current_y),
                            rotation=Rotation(90),
                            dimensions=brick_dims,
                        )
                        parts.append(part)
                        z += 4
                    elif remaining >= 2:
                        # Use 2×2 brick
                        brick_2x2 = "3003"
                        dims_2x2 = PartDimensions(
                            studs_width=2, studs_length=2, plates_height=3
                        )
                        part = build_state.add_part(
                            part_id=brick_2x2,
                            part_name="Brick 2×2",
                            color=color,
                            position=StudCoordinate(start_x, z, current_y),
                            rotation=Rotation(0),
                            dimensions=dims_2x2,
                        )
                        parts.append(part)
                        z += 2
                    else:
                        z += 1

            current_y += 3  # Move up one brick height

        return parts

    @staticmethod
    def create_column(
        build_state: BuildState,
        x: int,
        z: int,
        height: int,
        thickness: int,
        color: int,
    ) -> List[PlacedPart]:
        """
        Create a vertical support column.

        Args:
            build_state: Build state to add parts to
            x: X position
            z: Z position
            height: Height in plates
            thickness: Thickness in studs (1-4)
            color: LDraw color code

        Returns:
            List of created parts
        """
        parts: List[PlacedPart] = []

        # Determine brick size based on thickness
        if thickness == 1:
            brick_id = "3005"  # 1×1 brick
            brick_dims = PartDimensions(studs_width=1, studs_length=1, plates_height=3)
        elif thickness == 2:
            brick_id = "3004"  # 1×2 brick
            brick_dims = PartDimensions(studs_width=1, studs_length=2, plates_height=3)
        elif thickness == 3:
            brick_id = "3622"  # 1×3 brick
            brick_dims = PartDimensions(studs_width=1, studs_length=3, plates_height=3)
        else:  # thickness >= 4
            brick_id = "3010"  # 1×4 brick
            brick_dims = PartDimensions(studs_width=1, studs_length=4, plates_height=3)

        # Stack bricks
        current_y = 0
        rotation = Rotation(0)

        while current_y < height:
            part = build_state.add_part(
                part_id=brick_id,
                part_name=f"Brick 1×{thickness}",
                color=color,
                position=StudCoordinate(x, z, current_y),
                rotation=rotation,
                dimensions=brick_dims,
            )
            parts.append(part)

            current_y += 3
            # Alternate rotation for strength
            rotation = rotation.rotate_cw()

        return parts

    @staticmethod
    def create_wing(
        build_state: BuildState,
        start_x: int,
        start_z: int,
        start_y: int,
        length: int,
        sweep_angle: int,
        thickness: int,
        color: int,
    ) -> List[PlacedPart]:
        """
        Create a wing structure using slopes.

        Args:
            build_state: Build state to add parts to
            start_x: Starting X position
            start_z: Starting Z position
            start_y: Starting Y position (in plates)
            length: Wing length in studs
            sweep_angle: Sweep angle (0-45 degrees)
            thickness: Wing thickness in plates
            color: LDraw color code

        Returns:
            List of created parts
        """
        parts: List[PlacedPart] = []

        # Use plates for thin wings
        plate_2x4 = "3037"
        plate_dims = PartDimensions(studs_width=2, studs_length=4, plates_height=1)

        # Use slopes for leading edge
        slope_2x2 = "3041"  # 45° slope 2×2
        slope_dims = PartDimensions(studs_width=2, studs_length=2, plates_height=3)

        # Build wing from root to tip
        for layer in range(thickness):
            z = start_z
            for i in range(0, length, 2):
                # Calculate sweep offset
                sweep_offset = int((i / length) * sweep_angle / 10)

                part = build_state.add_part(
                    part_id=plate_2x4,
                    part_name="Plate 2×4",
                    color=color,
                    position=StudCoordinate(start_x + sweep_offset, z + i, start_y + layer),
                    rotation=Rotation(0),
                    dimensions=plate_dims,
                )
                parts.append(part)

        # Add leading edge slope
        part = build_state.add_part(
            part_id=slope_2x2,
            part_name="Slope 45° 2×2",
            color=color,
            position=StudCoordinate(start_x, start_z, start_y + thickness),
            rotation=Rotation(0),
            dimensions=slope_dims,
        )
        parts.append(part)

        return parts
