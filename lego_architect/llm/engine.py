"""
LLM Engine for AI-powered LEGO generation.

This module implements:
- Claude API integration
- Prompt caching strategy
- Tool calling (place_brick, pattern functions)
- Smart error suggestions
- Model routing (Sonnet → Haiku)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from lego_architect.config import config
from lego_architect.core.data_structures import (
    BuildState,
    PartDimensions,
    PlacedPart,
    Rotation,
    StudCoordinate,
)
from lego_architect.patterns import PatternLibrary
from lego_architect.validation import PhysicalValidator


@dataclass
class LLMResult:
    """Result from LLM generation."""

    success: bool
    tokens_used: int
    cached_tokens: int
    response: Any
    errors: List[str] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


class LLMEngine:
    """
    Manages LLM interactions with Claude.

    Features:
    - Prompt caching for part catalog (90% token savings)
    - Tool calling for brick placement
    - Smart error suggestions
    - Model routing (Sonnet for generation, Haiku for refinement)
    """

    def __init__(self) -> None:
        """Initialize LLM engine."""
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.validator = PhysicalValidator()

        # Build cached system prompt
        self.system_prompt_cached = self._build_cached_system_prompt()

        # Part database (simplified for MVP)
        self.part_catalog = self._build_part_catalog()

    def _build_part_catalog(self) -> Dict[str, Dict]:
        """
        Build simplified part catalog.

        For MVP, using a curated set of common parts.
        In production, this would load from MongoDB.
        """
        return {
            # Bricks
            "3001": {
                "id": "3001",
                "name": "Brick 2×4",
                "category": "brick",
                "dimensions": {"studs_width": 2, "studs_length": 4, "plates_height": 3},
            },
            "3002": {
                "id": "3002",
                "name": "Brick 2×3",
                "category": "brick",
                "dimensions": {"studs_width": 2, "studs_length": 3, "plates_height": 3},
            },
            "3003": {
                "id": "3003",
                "name": "Brick 2×2",
                "category": "brick",
                "dimensions": {"studs_width": 2, "studs_length": 2, "plates_height": 3},
            },
            "3004": {
                "id": "3004",
                "name": "Brick 1×2",
                "category": "brick",
                "dimensions": {"studs_width": 1, "studs_length": 2, "plates_height": 3},
            },
            "3005": {
                "id": "3005",
                "name": "Brick 1×1",
                "category": "brick",
                "dimensions": {"studs_width": 1, "studs_length": 1, "plates_height": 3},
            },
            "3010": {
                "id": "3010",
                "name": "Brick 1×4",
                "category": "brick",
                "dimensions": {"studs_width": 1, "studs_length": 4, "plates_height": 3},
            },
            # Plates
            "3022": {
                "id": "3022",
                "name": "Plate 2×2",
                "category": "plate",
                "dimensions": {"studs_width": 2, "studs_length": 2, "plates_height": 1},
            },
            "3023": {
                "id": "3023",
                "name": "Plate 1×2",
                "category": "plate",
                "dimensions": {"studs_width": 1, "studs_length": 2, "plates_height": 1},
            },
            "3024": {
                "id": "3024",
                "name": "Plate 1×1",
                "category": "plate",
                "dimensions": {"studs_width": 1, "studs_length": 1, "plates_height": 1},
            },
            "3037": {
                "id": "3037",
                "name": "Plate 2×4",
                "category": "plate",
                "dimensions": {"studs_width": 2, "studs_length": 4, "plates_height": 1},
            },
            # Slopes
            "3040": {
                "id": "3040",
                "name": "Slope 45° 1×2",
                "category": "slope",
                "dimensions": {"studs_width": 1, "studs_length": 2, "plates_height": 3},
            },
            "3041": {
                "id": "3041",
                "name": "Slope 45° 2×2",
                "category": "slope",
                "dimensions": {"studs_width": 2, "studs_length": 2, "plates_height": 3},
            },
            "3043": {
                "id": "3043",
                "name": "Slope 45° 2×4",
                "category": "slope",
                "dimensions": {"studs_width": 2, "studs_length": 4, "plates_height": 3},
            },
        }

    def _build_cached_system_prompt(self) -> str:
        """
        Build system prompt with cacheable static content.

        This prompt is cached by Claude to save ~90% on tokens.
        """
        prompt = """You are an expert LEGO architect AI. Your task is to design physically valid LEGO builds from natural language descriptions.

# PART CATALOG

You have access to common LEGO parts organized into categories:

## Category: BRICK
Standard structural bricks (3 plates tall = 1 brick height)

Available parts:
- 3001: Brick 2×4 (2 studs wide, 4 studs long, 3 plates high)
- 3002: Brick 2×3 (2 studs wide, 3 studs long, 3 plates high)
- 3003: Brick 2×2 (2 studs wide, 2 studs long, 3 plates high)
- 3004: Brick 1×2 (1 stud wide, 2 studs long, 3 plates high)
- 3005: Brick 1×1 (1 stud wide, 1 stud long, 3 plates high)
- 3010: Brick 1×4 (1 stud wide, 4 studs long, 3 plates high)

## Category: PLATE
Thin pieces (1 plate high = 1/3 brick height)

Available parts:
- 3022: Plate 2×2 (2 studs wide, 2 studs long, 1 plate high)
- 3023: Plate 1×2 (1 stud wide, 2 studs long, 1 plate high)
- 3024: Plate 1×1 (1 stud wide, 1 stud long, 1 plate high)
- 3037: Plate 2×4 (2 studs wide, 4 studs long, 1 plate high)

## Category: SLOPE
Angled pieces for aerodynamics, roofs, etc. (3 plates tall)

Available parts:
- 3040: Slope 45° 1×2 (1 stud wide, 2 studs long, 3 plates high)
- 3041: Slope 45° 2×2 (2 studs wide, 2 studs long, 3 plates high)
- 3043: Slope 45° 2×4 (2 studs wide, 4 studs long, 3 plates high)

# PATTERN FUNCTIONS

You can use these pre-validated templates for efficiency:

## create_base(start_x, start_z, width, length, color)
Creates a stable base plate layer.
- start_x, start_z: Starting position
- width, length: Size in studs (4-48)
- color: LDraw color code

Example: create_base(0, 0, 16, 16, 71) creates a 16×16 gray base

## create_wall(start_x, start_z, start_y, length, height, direction, color)
Creates a vertical wall with running bond pattern.
- start_x, start_z, start_y: Starting position
- length: Length in studs (4-32)
- height: Height in plates (3-30)
- direction: "x" or "z" (orientation)
- color: LDraw color code

Example: create_wall(0, 0, 1, 12, 9, "x", 4) creates a red wall

## create_column(x, z, height, thickness, color)
Creates a vertical support column.
- x, z: Position
- height: Height in plates (6-60)
- thickness: Thickness in studs (1-4)
- color: LDraw color code

Example: create_column(0, 0, 24, 2, 72) creates a dark gray column

# COORDINATE SYSTEM

**IMPORTANT**: Understand the coordinate system:
- X-axis: Width (left to right), measured in studs
- Z-axis: Depth (back to front), measured in studs
- Y-axis: Height (upward), measured in PLATES (not bricks!)
- Rotation: 0°, 90°, 180°, or 270° around Y-axis

**Height Units**:
- 1 brick = 3 plates
- Ground level = plate_y: 0
- One brick up = plate_y: 3
- Two bricks up = plate_y: 6

# BUILDING RULES

1. **Placement Rules**:
   - All parts must be at plate_y >= 0 (ground or above)
   - Parts must not overlap in 3D space
   - Parts must connect via studs (no floating parts)
   - Build from bottom to top for stability

2. **Connection Requirements**:
   - Parts above ground MUST connect to parts below
   - Studs on top of one brick connect to bottom of brick above
   - Stack bricks directly on top for proper connection

3. **Stability**:
   - Use wide bases for tall structures
   - Center of gravity should be over the base
   - Support heavy elements with strong connections

4. **Color Codes** (LDraw standard):
   - 1: Blue
   - 4: Red
   - 14: Yellow
   - 15: White
   - 71: Light Gray
   - 72: Dark Gray

# YOUR TASK

When given a build description:

1. **Plan the structure**: Think about overall shape, base, support
2. **Start with a base**: Use create_base() or place base plates
3. **Build layer by layer**: Start at plate_y=0, work upward
4. **Use place_brick for details**: Individual brick placement
5. **Use patterns for structures**: Walls, columns for efficiency
6. **Ensure connections**: Every brick above ground must connect

**CRITICAL**: The place_brick tool gives real-time feedback. If a placement fails:
- Read the error message carefully
- Use the suggestions provided
- Try alternative positions or rotations
- Don't repeat the same invalid placement

**Remember**: Heights are in PLATES (1 brick = 3 plates). Always use plate_y for positioning.
"""
        return prompt

    def _get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions for Claude."""
        return [
            {
                "name": "place_brick",
                "description": "Place a LEGO brick at specified coordinates. Use this for individual brick placement and details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "part_id": {
                            "type": "string",
                            "description": "LEGO part number (e.g., '3001' for 2×4 brick)",
                        },
                        "color": {
                            "type": "integer",
                            "description": "LDraw color code (1=blue, 4=red, 14=yellow, 15=white, 71=light gray, 72=dark gray)",
                        },
                        "stud_x": {
                            "type": "integer",
                            "description": "X position in studs (0 = left edge)",
                        },
                        "stud_z": {
                            "type": "integer",
                            "description": "Z position in studs (0 = back edge)",
                        },
                        "plate_y": {
                            "type": "integer",
                            "description": "Y position in PLATES (0 = ground, 3 = one brick up, 6 = two bricks up)",
                        },
                        "rotation": {
                            "type": "integer",
                            "enum": [0, 90, 180, 270],
                            "description": "Rotation in degrees around Y-axis",
                            "default": 0,
                        },
                    },
                    "required": ["part_id", "color", "stud_x", "stud_z", "plate_y"],
                },
            },
            {
                "name": "create_base",
                "description": "Create a base plate layer using pre-validated pattern. Efficient for creating stable foundations.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_x": {"type": "integer", "description": "Starting X position"},
                        "start_z": {"type": "integer", "description": "Starting Z position"},
                        "width": {
                            "type": "integer",
                            "minimum": 4,
                            "maximum": 48,
                            "description": "Width in studs",
                        },
                        "length": {
                            "type": "integer",
                            "minimum": 4,
                            "maximum": 48,
                            "description": "Length in studs",
                        },
                        "color": {"type": "integer", "description": "LDraw color code"},
                    },
                    "required": ["start_x", "start_z", "width", "length", "color"],
                },
            },
            {
                "name": "create_wall",
                "description": "Create a wall using running bond pattern. Efficient for vertical structures.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "start_x": {"type": "integer"},
                        "start_z": {"type": "integer"},
                        "start_y": {
                            "type": "integer",
                            "description": "Starting Y in plates (0 for ground)",
                        },
                        "length": {
                            "type": "integer",
                            "minimum": 4,
                            "maximum": 32,
                            "description": "Length in studs",
                        },
                        "height": {
                            "type": "integer",
                            "minimum": 3,
                            "maximum": 30,
                            "description": "Height in plates",
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["x", "z"],
                            "description": "Direction of wall (x or z)",
                        },
                        "color": {"type": "integer"},
                    },
                    "required": [
                        "start_x",
                        "start_z",
                        "start_y",
                        "length",
                        "height",
                        "direction",
                        "color",
                    ],
                },
            },
            {
                "name": "create_column",
                "description": "Create a vertical support column. Good for structural support.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X position"},
                        "z": {"type": "integer", "description": "Z position"},
                        "height": {
                            "type": "integer",
                            "minimum": 6,
                            "maximum": 60,
                            "description": "Height in plates",
                        },
                        "thickness": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 4,
                            "description": "Thickness in studs",
                        },
                        "color": {"type": "integer"},
                    },
                    "required": ["x", "z", "height", "thickness", "color"],
                },
            },
        ]

    def generate_build(self, prompt: str, build_state: BuildState) -> LLMResult:
        """
        Generate build from natural language prompt.

        Args:
            prompt: User's natural language description
            build_state: BuildState to add parts to

        Returns:
            LLMResult with generation statistics
        """
        user_prompt = f"""Create a LEGO build: "{prompt}"

Think through your design:
1. What's the overall shape and size?
2. What's the best base structure?
3. How will you ensure stability?
4. What parts will you use?

Then build it step by step, starting with the base and working upward.
Remember: Heights are in PLATES (3 plates = 1 brick).
"""

        try:
            response = self.client.messages.create(
                model=config.DEFAULT_MODEL,
                max_tokens=config.MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt_cached,
                        "cache_control": {"type": "ephemeral"}
                        if config.ENABLE_PROMPT_CACHING
                        else None,
                    }
                ],
                tools=self._get_tool_definitions(),
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Calculate tokens
            usage = response.usage
            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            cached_tokens = getattr(usage, "cache_read_input_tokens", 0)

            # Process tool calls
            errors = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    error = self._handle_tool_call(content_block, build_state)
                    if error:
                        errors.append(error)

            return LLMResult(
                success=len(errors) == 0,
                tokens_used=input_tokens + output_tokens,
                cached_tokens=cached_tokens,
                response=response,
                errors=errors,
            )

        except Exception as e:
            return LLMResult(
                success=False, tokens_used=0, cached_tokens=0, response=None, errors=[str(e)]
            )

    def refine_build(
        self, build_state: BuildState, validation_errors: List[str], iteration: int
    ) -> LLMResult:
        """
        Refine build based on validation errors.

        Uses cheaper model (Haiku) for cost optimization.

        Args:
            build_state: Current build state
            validation_errors: List of validation errors
            iteration: Iteration number

        Returns:
            LLMResult with refinement statistics
        """
        # Build context about current state
        context = f"""Current build has {len(build_state.parts)} parts.

Validation errors:
"""
        for i, error in enumerate(validation_errors[:5], 1):
            context += f"{i}. {error}\n"

        if len(validation_errors) > 5:
            context += f"... and {len(validation_errors) - 5} more errors\n"

        user_prompt = f"""{context}

Please fix these validation errors. This is refinement iteration {iteration}.

Analyze the errors and make targeted fixes:
1. Remove or reposition any colliding parts
2. Ensure all parts above ground are properly connected
3. Maintain the overall design intent

Make the minimum changes needed to fix the errors.
"""

        try:
            # Use cheaper model for refinements
            model = config.REFINEMENT_MODEL if iteration > 1 else config.DEFAULT_MODEL

            response = self.client.messages.create(
                model=model,
                max_tokens=config.MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt_cached,
                        "cache_control": {"type": "ephemeral"}
                        if config.ENABLE_PROMPT_CACHING
                        else None,
                    }
                ],
                tools=self._get_tool_definitions(),
                messages=[{"role": "user", "content": user_prompt}],
            )

            usage = response.usage
            input_tokens = usage.input_tokens
            output_tokens = usage.output_tokens
            cached_tokens = getattr(usage, "cache_read_input_tokens", 0)

            # Process tool calls
            errors = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    error = self._handle_tool_call(content_block, build_state)
                    if error:
                        errors.append(error)

            return LLMResult(
                success=len(errors) == 0,
                tokens_used=input_tokens + output_tokens,
                cached_tokens=cached_tokens,
                response=response,
                errors=errors,
            )

        except Exception as e:
            return LLMResult(
                success=False, tokens_used=0, cached_tokens=0, response=None, errors=[str(e)]
            )

    def _handle_tool_call(self, tool_use: Any, build_state: BuildState) -> Optional[str]:
        """
        Handle tool call from LLM.

        Args:
            tool_use: Tool use block from Claude
            build_state: Build state to modify

        Returns:
            Error message if failed, None if successful
        """
        tool_name = tool_use.name
        args = tool_use.input

        try:
            if tool_name == "place_brick":
                return self._handle_place_brick(args, build_state)
            elif tool_name == "create_base":
                return self._handle_create_base(args, build_state)
            elif tool_name == "create_wall":
                return self._handle_create_wall(args, build_state)
            elif tool_name == "create_column":
                return self._handle_create_column(args, build_state)
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error in {tool_name}: {str(e)}"

    def _handle_place_brick(self, args: Dict, build_state: BuildState) -> Optional[str]:
        """Handle place_brick tool call with validation."""
        part_id = args["part_id"]

        # Get part metadata
        if part_id not in self.part_catalog:
            return f"Unknown part ID: {part_id}"

        part = self.part_catalog[part_id]

        # Create position and rotation
        position = StudCoordinate(
            stud_x=args["stud_x"], stud_z=args["stud_z"], plate_y=args["plate_y"]
        )
        rotation = Rotation(args.get("rotation", 0))

        # Create dimensions
        dims = part["dimensions"]
        dimensions = PartDimensions(
            studs_width=dims["studs_width"],
            studs_length=dims["studs_length"],
            plates_height=dims["plates_height"],
        )

        # Quick validation
        temp_part = PlacedPart(
            id=-1,
            part_id=part_id,
            part_name=part["name"],
            color=args["color"],
            position=position,
            rotation=rotation,
            dimensions=dimensions,
        )

        validation = self.validator.quick_validate_placement(build_state, temp_part)

        if not validation["valid"]:
            # Return error with suggestions
            error_msg = validation["error"]
            if validation["suggestions"]:
                error_msg += f" Suggestions: {', '.join(validation['suggestions'][:2])}"
            return error_msg

        # Add to build
        build_state.add_part(
            part_id=part_id,
            part_name=part["name"],
            color=args["color"],
            position=position,
            rotation=rotation,
            dimensions=dimensions,
        )

        return None  # Success

    def _handle_create_base(self, args: Dict, build_state: BuildState) -> Optional[str]:
        """Handle create_base pattern call."""
        try:
            PatternLibrary.create_base(
                build_state=build_state,
                start_x=args["start_x"],
                start_z=args["start_z"],
                width=args["width"],
                length=args["length"],
                color=args["color"],
            )
            return None
        except Exception as e:
            return f"create_base failed: {str(e)}"

    def _handle_create_wall(self, args: Dict, build_state: BuildState) -> Optional[str]:
        """Handle create_wall pattern call."""
        try:
            PatternLibrary.create_wall(
                build_state=build_state,
                start_x=args["start_x"],
                start_z=args["start_z"],
                start_y=args["start_y"],
                length=args["length"],
                height=args["height"],
                direction=args["direction"],
                color=args["color"],
                style="solid",  # Default style
            )
            return None
        except Exception as e:
            return f"create_wall failed: {str(e)}"

    def _handle_create_column(self, args: Dict, build_state: BuildState) -> Optional[str]:
        """Handle create_column pattern call."""
        try:
            PatternLibrary.create_column(
                build_state=build_state,
                x=args["x"],
                z=args["z"],
                height=args["height"],
                thickness=args["thickness"],
                color=args["color"],
            )
            return None
        except Exception as e:
            return f"create_column failed: {str(e)}"
