"""
Core data structures for LEGO Architect.

This module defines all the fundamental data types used throughout the system:
- Coordinate systems (StudCoordinate, Rotation)
- Part definitions (PartDimensions, PartDefinition, ConnectionPoint)
- Build state (PlacedPart, BuildState)
- Validation results (ValidationResult)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np


# ===== Enumerations =====


class PartCategory(str, Enum):
    """Part category taxonomy (shallow hierarchy)."""

    BRICK = "brick"
    PLATE = "plate"
    SLOPE = "slope"
    TILE = "tile"
    TECHNIC = "technic"
    CONNECTOR = "connector"  # Hinges, clips, bars
    SPECIAL = "special"


class ConnectionType(str, Enum):
    """Types of LEGO connections."""

    STUD = "stud"  # Standard top stud
    ANTI_STUD = "anti_stud"  # Bottom tubes
    TECHNIC_PIN = "technic_pin"
    TECHNIC_HOLE = "technic_hole"
    CLIP = "clip"
    BAR = "bar"
    HINGE_MALE = "hinge_male"
    HINGE_FEMALE = "hinge_female"


class BuildStatus(str, Enum):
    """Build generation status."""

    CLARIFYING = "clarifying"
    DESIGNING = "designing"
    VALIDATING = "validating"
    REFINING = "refining"
    COMPLETE = "complete"
    FAILED = "failed"


# ===== Coordinate System =====


@dataclass(frozen=True)
class StudCoordinate:
    """
    Immutable position in stud-grid coordinates.

    This is the high-level coordinate system used by the LLM for brick placement.
    Integer coordinates in stud/plate units make it easy to reason about.

    Attributes:
        stud_x: X position in studs (width, left to right)
        stud_z: Z position in studs (depth, back to front)
        plate_y: Y position in plates (height, 0 = ground)
    """

    stud_x: int
    stud_z: int
    plate_y: int

    def to_ldu(self) -> Tuple[float, float, float]:
        """
        Convert to LDraw Units for export.

        LDU Conversion:
        - 1 stud = 20 LDU (X/Z plane)
        - 1 plate = 8 LDU (Y axis)

        Returns:
            Tuple of (x, y, z) in LDraw Units
        """
        return (
            self.stud_x * 20.0,
            self.plate_y * 8.0,
            self.stud_z * 20.0,
        )

    @staticmethod
    def from_ldu(x: float, y: float, z: float) -> "StudCoordinate":
        """
        Parse LDraw coordinates into stud grid.

        Args:
            x: X coordinate in LDU
            y: Y coordinate in LDU
            z: Z coordinate in LDU

        Returns:
            StudCoordinate with rounded values
        """
        return StudCoordinate(
            stud_x=round(x / 20.0),
            stud_z=round(z / 20.0),
            plate_y=round(y / 8.0),
        )

    def offset(self, dx: int = 0, dz: int = 0, dy: int = 0) -> "StudCoordinate":
        """
        Create new coordinate with offset.

        Args:
            dx: X offset in studs
            dz: Z offset in studs
            dy: Y offset in plates

        Returns:
            New StudCoordinate with offset applied
        """
        return StudCoordinate(
            self.stud_x + dx,
            self.stud_z + dz,
            self.plate_y + dy,
        )

    def __add__(self, other: "StudCoordinate") -> "StudCoordinate":
        """Add two coordinates component-wise."""
        return StudCoordinate(
            self.stud_x + other.stud_x,
            self.stud_z + other.stud_z,
            self.plate_y + other.plate_y,
        )

    def __repr__(self) -> str:
        return f"({self.stud_x}, {self.stud_z}, {self.plate_y})"


@dataclass(frozen=True)
class Rotation:
    """
    Rotation around Y-axis in 90° increments.

    LEGO builds typically use 90° rotations for part placement.
    """

    degrees: int = 0  # Must be 0, 90, 180, or 270

    def __post_init__(self) -> None:
        if self.degrees not in [0, 90, 180, 270]:
            raise ValueError(f"Rotation must be 0/90/180/270, got {self.degrees}")

    def to_matrix(self) -> np.ndarray:
        """
        Convert to 3x3 rotation matrix for LDraw export.

        Returns:
            3x3 rotation matrix (numpy array)
        """
        rad = np.radians(self.degrees)
        cos_theta = np.cos(rad)
        sin_theta = np.sin(rad)

        # Rotation around Y-axis (down in LDraw coordinate system)
        return np.array(
            [[cos_theta, 0, sin_theta], [0, 1, 0], [-sin_theta, 0, cos_theta]],
            dtype=float,
        )

    def rotate_cw(self) -> "Rotation":
        """Rotate 90° clockwise."""
        return Rotation((self.degrees + 90) % 360)

    def rotate_ccw(self) -> "Rotation":
        """Rotate 90° counter-clockwise."""
        return Rotation((self.degrees - 90) % 360)


# ===== Part Definitions =====


@dataclass(frozen=True)
class PartDimensions:
    """
    Part dimensions in LEGO units.

    Attributes:
        studs_width: Width in studs (X dimension)
        studs_length: Length in studs (Z dimension)
        plates_height: Height in plates (Y dimension, 3 plates = 1 brick)
    """

    studs_width: int
    studs_length: int
    plates_height: int

    def to_ldu(self) -> Tuple[float, float, float]:
        """Convert dimensions to LDraw Units."""
        return (
            self.studs_width * 20.0,
            self.plates_height * 8.0,
            self.studs_length * 20.0,
        )

    @property
    def brick_height(self) -> float:
        """Height in brick units (1 brick = 3 plates)."""
        return self.plates_height / 3.0

    def __repr__(self) -> str:
        return f"{self.studs_width}×{self.studs_length}×{self.plates_height}"


@dataclass
class ConnectionPoint:
    """
    A connection point on a part.

    Attributes:
        position: Position in LDU coordinates relative to part origin
        type: Type of connection (stud, pin, clip, etc.)
        direction: Normal vector indicating connection direction
    """

    position: Tuple[float, float, float]  # LDU coordinates
    type: ConnectionType
    direction: Tuple[float, float, float] = (0, 1, 0)  # Normal vector

    def to_stud_coord(self) -> StudCoordinate:
        """Convert to stud coordinates (approximate)."""
        x, y, z = self.position
        return StudCoordinate.from_ldu(x, y, z)


@dataclass
class PartDefinition:
    """
    Part metadata from database.

    Attributes:
        part_id: LEGO part number (e.g., "3001")
        name: Human-readable name
        category: Part category
        dimensions: Part dimensions
        connection_points: Dictionary of connection point lists
        available_colors: List of valid LDraw color codes
        ldraw_file: Filename of LDraw part file
    """

    part_id: str
    name: str
    category: PartCategory
    dimensions: PartDimensions
    connection_points: Dict[str, List[ConnectionPoint]]
    available_colors: List[int]
    ldraw_file: str

    @property
    def top_studs(self) -> List[ConnectionPoint]:
        """Get top stud connection points."""
        return self.connection_points.get("top_studs", [])

    @property
    def bottom_tubes(self) -> List[ConnectionPoint]:
        """Get bottom tube (anti-stud) connection points."""
        return self.connection_points.get("bottom_tubes", [])


# ===== Placed Parts =====


@dataclass
class PlacedPart:
    """
    A part instance in the build.

    Attributes:
        id: Unique ID within build
        part_id: LEGO part number
        part_name: Human-readable name
        color: LDraw color code
        position: Position in stud grid
        rotation: Rotation around Y-axis
        dimensions: Part dimensions
        layer: Building layer (for instruction sequencing)
        sub_assembly: Optional sub-assembly name (e.g., "wing_left")
        connected_to: List of part IDs this part connects to
    """

    id: int
    part_id: str
    part_name: str
    color: int
    position: StudCoordinate
    rotation: Rotation
    dimensions: PartDimensions

    # Metadata
    layer: int = 0
    sub_assembly: Optional[str] = None
    connected_to: List[int] = field(default_factory=list)

    def get_bounding_box(self) -> Tuple[StudCoordinate, StudCoordinate]:
        """
        Get axis-aligned bounding box in stud coordinates.

        Returns:
            Tuple of (min_corner, max_corner)
        """
        min_corner = self.position

        # Apply rotation to dimensions
        if self.rotation.degrees in [0, 180]:
            width = self.dimensions.studs_width
            length = self.dimensions.studs_length
        else:  # 90 or 270
            width = self.dimensions.studs_length
            length = self.dimensions.studs_width

        max_corner = StudCoordinate(
            self.position.stud_x + width,
            self.position.stud_z + length,
            self.position.plate_y + self.dimensions.plates_height,
        )

        return (min_corner, max_corner)

    def get_stud_positions(self) -> List[StudCoordinate]:
        """
        Get positions of studs on top of this part.

        Returns:
            List of stud positions
        """
        studs = []
        min_c, max_c = self.get_bounding_box()

        # Studs at each stud position on top surface
        for x in range(min_c.stud_x, max_c.stud_x):
            for z in range(min_c.stud_z, max_c.stud_z):
                studs.append(StudCoordinate(x, z, max_c.plate_y))

        return studs

    def to_ldraw_line(self) -> str:
        """
        Convert to LDraw file format line.

        LDraw format:
        1 <color> <x> <y> <z> <a> <b> <c> <d> <e> <f> <g> <h> <i> <part.dat>

        Where <a-i> is the 3x3 rotation matrix flattened row-wise.

        Returns:
            LDraw format line
        """
        x, y, z = self.position.to_ldu()
        matrix = self.rotation.to_matrix()

        # Flatten matrix row-wise
        m = matrix.flatten()

        return (
            f"1 {self.color} "
            f"{x:.4f} {y:.4f} {z:.4f} "
            f"{m[0]:.6f} {m[1]:.6f} {m[2]:.6f} "
            f"{m[3]:.6f} {m[4]:.6f} {m[5]:.6f} "
            f"{m[6]:.6f} {m[7]:.6f} {m[8]:.6f} "
            f"{self.part_id}.dat"
        )

    def __repr__(self) -> str:
        return f"PlacedPart({self.part_id} at {self.position}, color={self.color})"


# ===== Build State =====


@dataclass
class BuildState:
    """
    Complete state of a LEGO build.

    This is the central data structure that holds the entire build.

    Attributes:
        parts: List of all placed parts
        name: Build name
        description: Build description
        prompt: Original user prompt
        status: Current build status
        iteration_count: Number of refinement iterations
        total_tokens_used: Total LLM tokens consumed
        generation_time_seconds: Total generation time
        is_valid: Whether build passed validation
        validation_errors: List of validation errors
        validation_warnings: List of validation warnings
    """

    parts: List[PlacedPart] = field(default_factory=list)

    # Metadata
    name: str = "Untitled Build"
    description: str = ""
    prompt: str = ""
    status: BuildStatus = BuildStatus.DESIGNING

    # Generation tracking
    iteration_count: int = 0
    total_tokens_used: int = 0
    generation_time_seconds: float = 0.0

    # Validation results
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

    # Internal state
    _occupancy_grid: Optional[np.ndarray] = field(default=None, repr=False)
    _next_part_id: int = field(default=1, repr=False)

    def add_part(
        self,
        part_id: str,
        part_name: str,
        color: int,
        position: StudCoordinate,
        rotation: Rotation,
        dimensions: PartDimensions,
    ) -> PlacedPart:
        """
        Add a part to the build.

        Args:
            part_id: LEGO part number
            part_name: Part name
            color: LDraw color code
            position: Position in stud grid
            rotation: Rotation
            dimensions: Part dimensions

        Returns:
            The created PlacedPart
        """
        part = PlacedPart(
            id=self._next_part_id,
            part_id=part_id,
            part_name=part_name,
            color=color,
            position=position,
            rotation=rotation,
            dimensions=dimensions,
        )

        self.parts.append(part)
        self._next_part_id += 1

        # Update occupancy grid if exists
        if self._occupancy_grid is not None:
            self._mark_occupied(part)

        return part

    def get_part_by_id(self, part_id: int) -> Optional[PlacedPart]:
        """Find part by ID."""
        for part in self.parts:
            if part.id == part_id:
                return part
        return None

    def remove_part(self, part_id: int) -> bool:
        """
        Remove a part from the build.

        Args:
            part_id: ID of part to remove

        Returns:
            True if part was found and removed
        """
        for i, part in enumerate(self.parts):
            if part.id == part_id:
                del self.parts[i]
                self._occupancy_grid = None  # Invalidate grid
                return True
        return False

    def get_dimensions(self) -> Tuple[int, int, int]:
        """
        Get overall dimensions of the build.

        Returns:
            Tuple of (studs_x, studs_z, plates_y)
        """
        if not self.parts:
            return (0, 0, 0)

        all_corners = [part.get_bounding_box() for part in self.parts]

        min_x = min(min_c.stud_x for min_c, _ in all_corners)
        min_z = min(min_c.stud_z for min_c, _ in all_corners)
        min_y = min(min_c.plate_y for min_c, _ in all_corners)

        max_x = max(max_c.stud_x for _, max_c in all_corners)
        max_z = max(max_c.stud_z for _, max_c in all_corners)
        max_y = max(max_c.plate_y for _, max_c in all_corners)

        return (max_x - min_x, max_z - min_z, max_y - min_y)

    def get_bom(self) -> Dict[Tuple[str, int], int]:
        """
        Get Bill of Materials.

        Returns:
            Dictionary mapping (part_id, color) to quantity
        """
        bom: Dict[Tuple[str, int], int] = {}
        for part in self.parts:
            key = (part.part_id, part.color)
            bom[key] = bom.get(key, 0) + 1
        return bom

    def _mark_occupied(self, part: PlacedPart) -> None:
        """Mark cells as occupied in occupancy grid (internal)."""
        # TODO: Implement when building collision detector
        pass

    def __repr__(self) -> str:
        dims = self.get_dimensions()
        return (
            f"BuildState({len(self.parts)} parts, "
            f"{dims[0]}×{dims[1]}×{dims[2]} studs/plates)"
        )


# ===== Validation Results =====


@dataclass
class ValidationResult:
    """
    Result of physical validation.

    Attributes:
        is_valid: Whether the build passed all validation checks
        errors: List of validation errors (blocks success)
        warnings: List of validation warnings (doesn't block)
        suggestions: List of improvement suggestions
    """

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add validation warning."""
        self.warnings.append(message)

    def add_suggestion(self, message: str) -> None:
        """Add improvement suggestion."""
        self.suggestions.append(message)

    def __bool__(self) -> bool:
        return self.is_valid

    def __repr__(self) -> str:
        status = "✓ Valid" if self.is_valid else "✗ Invalid"
        return f"ValidationResult({status}, {len(self.errors)} errors)"
